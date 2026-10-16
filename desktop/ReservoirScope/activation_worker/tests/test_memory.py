"""Allocator lifecycle tests with no MLX import, model load or device work."""
from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

from activation_worker.backend import (CLEAR_CACHE_EVERY_GENERATED_TOKENS,
                                       FREE_CACHE_LIMIT_BYTES, MLXBackend,
                                       memory_policy)
from activation_worker.qualify import clean_memory_receipt


class Allocation:
    def __init__(self, allocator, size):
        self.allocator, self.size = allocator, size
        allocator.active += size
        allocator.peak = max(allocator.peak, allocator.active)

    def __del__(self):
        self.allocator.active -= self.size
        self.allocator.cached += self.size


class FakeAllocator:
    def __init__(self):
        self.active = self.cached = self.peak = 0
        self.cache_limit = 1024**3
        self.calls = []
        self.random = types.SimpleNamespace(seed=lambda seed: self.calls.append(("seed", seed)))

    def set_cache_limit(self, limit):
        self.calls.append(("cache_limit", limit))
        old, self.cache_limit = self.cache_limit, limit
        return old

    def synchronize(self):
        self.calls.append(("synchronize",))

    def reset_peak_memory(self):
        self.calls.append(("reset_peak",))
        self.peak = 0

    def clear_cache(self):
        self.calls.append(("clear_cache",))
        self.cached = 0

    def get_active_memory(self):
        return self.active

    def get_cache_memory(self):
        return self.cached

    def get_peak_memory(self):
        return self.peak


def unloaded_backend():
    backend = object.__new__(MLXBackend)
    backend.mx = FakeAllocator()
    backend.model = object()
    backend.cache = None
    backend.direction = None
    backend.gain = 0
    backend._release_diagnostics()
    backend._operation_active = False
    backend.memory_rows = []
    backend.periodic_cache_clears = 0
    backend.make_prompt_cache = lambda model: [Allocation(backend.mx, 64)]
    backend.make_sampler = lambda **kwargs: object()
    backend._forward = lambda ids: "synthetic-logits"
    return backend


class MemoryLifecycleTests(unittest.TestCase):
    def test_limit_is_set_before_model_load_and_load_cache_is_released(self):
        mx = FakeAllocator()
        mlx = types.ModuleType("mlx")
        mlx.core, mlx.nn = mx, types.SimpleNamespace(Module=object)
        loaded_weights = []

        def fake_load(path, **kwargs):
            mx.calls.append(("load", path))
            loaded_weights.append(Allocation(mx, 4096))
            mx.cached = 1024
            model = types.SimpleNamespace(model=types.SimpleNamespace(layers=[object()] * 36),
                                          args=types.SimpleNamespace(hidden_size=2560))
            tokenizer = types.SimpleNamespace(eos_token_ids=[0], all_special_ids=[0, 99])
            return model, tokenizer

        modules = {"mlx": mlx, "mlx.core": mx, "mlx.nn": mlx.nn,
                   "mlx_lm": types.SimpleNamespace(load=fake_load),
                   "mlx_lm.models.cache": types.SimpleNamespace(make_prompt_cache=lambda _: []),
                   "mlx_lm.sample_utils": types.SimpleNamespace(make_sampler=lambda **_: None)}
        with patch.dict(sys.modules, modules):
            backend = MLXBackend("synthetic-model")
        self.assertLess(mx.calls.index(("cache_limit", FREE_CACHE_LIMIT_BYTES)),
                        mx.calls.index(("load", "synthetic-model")))
        self.assertEqual(mx.cache_limit, 67108864)
        rows = backend.load_memory["snapshots"]
        self.assertEqual([row["phase"] for row in rows],
                         ["before-model-load", "model-loaded", "load-cache-cleared"])
        self.assertEqual(rows[1]["peakActiveBytesSinceReset"], 4096)
        self.assertEqual(rows[-1]["activeBytes"], 4096)
        self.assertEqual(rows[-1]["freeCacheBytes"], 0)
        self.assertFalse(memory_policy()["wiredLimitChanged"])
        self.assertFalse(memory_policy()["memoryLimitChanged"])

    def test_cleanup_releases_kv_direction_and_diagnostics_but_keeps_model_allocations(self):
        backend = unloaded_backend()
        weights = Allocation(backend.mx, 4096)
        self.assertEqual(backend.begin([1, 2], np.zeros(2560), 0.0, 17, 0.0), "synthetic-logits")
        for field in ("captured", "before", "after", "actual_delta", "intended_delta", "direction"):
            setattr(backend, field, Allocation(backend.mx, 32))
        backend.gain = .01
        backend.release_cache()
        receipt = backend.memory_receipt()
        self.assertTrue(clean_memory_receipt(receipt))
        self.assertGreater(receipt["snapshots"][-2]["activeBytes"], 4096)
        self.assertEqual(receipt["snapshots"][-1]["activeBytes"], 4096)
        self.assertEqual(receipt["snapshots"][-1]["freeCacheBytes"], 0)
        self.assertIsNone(backend.cache)
        self.assertIsNone(backend.direction)
        self.assertEqual(backend.gain, 0)
        for field in ("captured", "before", "after", "actual_delta", "intended_delta", "sampler"):
            self.assertIsNone(getattr(backend, field))
        del weights

    def test_periodic_clears_are_bounded_and_do_not_change_forward_results(self):
        backend = unloaded_backend()
        backend.begin([1], np.zeros(2560), 0.0, 0, 0.0)
        for token in range(2 * CLEAR_CACHE_EVERY_GENERATED_TOKENS + 2):
            self.assertEqual(backend.advance(token), "synthetic-logits")
        self.assertEqual(backend.periodic_cache_clears, 2)
        self.assertEqual(backend.mx.calls.count(("clear_cache",)), 2)
        self.assertEqual(len(backend.memory_rows), 2)
        backend.release_cache()
        self.assertEqual(len(backend.memory_receipt()["snapshots"]), 4)

    def test_new_operation_resets_receipt_and_rejects_unreleased_cache(self):
        backend = unloaded_backend()
        backend.begin([1], np.zeros(2560), 0.0, 0, 0.0)
        with self.assertRaisesRegex(RuntimeError, "previous operation"):
            backend.begin([2], np.zeros(2560), 0.0, 0, 0.0)
        backend.release_cache()
        saved = backend.memory_receipt()
        backend.release_cache()
        self.assertEqual(backend.memory_receipt(), saved)
        saved["snapshots"][0]["activeBytes"] = 9000
        self.assertNotEqual(backend.memory_rows[0]["activeBytes"], 9000)
        backend.prepare_operation()
        self.assertEqual(backend.memory_receipt()["snapshots"], [])
        self.assertIsNone(backend.memory_receipt()["peakResetBoundary"])
        backend.begin([2], np.zeros(2560), 0.0, 0, 0.0)
        self.assertEqual(backend.generated_processed, 0)
        backend.release_cache()

    def test_qualification_rejects_retained_free_cache_or_unreleased_operation(self):
        backend = unloaded_backend()
        backend.begin([1], np.zeros(2560), 0.0, 0, 0.0)
        backend.release_cache()
        receipt = backend.memory_receipt()
        receipt["snapshots"][-1]["freeCacheBytes"] = 1
        self.assertFalse(clean_memory_receipt(receipt))
        receipt = backend.memory_receipt()
        receipt["operationReleased"] = False
        self.assertFalse(clean_memory_receipt(receipt))
        receipt = backend.memory_receipt()
        receipt["snapshots"] = receipt["snapshots"][:-1]
        self.assertFalse(clean_memory_receipt(receipt))


if __name__ == "__main__":
    unittest.main()
