from __future__ import annotations

import io
import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path

import numpy as np

from activation_worker import GAIN, HIDDEN_DIM, STATE_DIM
from activation_worker.engine import Engine, WorkerError
from activation_worker.math_core import (calibration_texts, canonical_hash, load_projection,
                                        make_calibration, project, steer_numpy,
                                        steering_direction, validate_calibration)
from activation_worker.worker import Server, parse_request


class FakeBackend:
    """Deterministic token model with observable cache and same-pass capture history."""
    def __init__(self, path="fake"):
        self.eos_ids = {0}
        self.special_ids = {0, 99}
        self.plan = [41, 42, 0]
        self.sample_calls = 0
        self.cache_count = 0
        self.released = 0
        self.begin_calls = []
        self.norm_rows = []
        self.processed_ids = []
        self.after_advance = None
        self.raise_on_advance = False

    def encode_raw(self, text):
        return [7, 10 + sum(map(ord, text)) % 70]

    def encode_journal(self, text):
        return [1, 2, 3]

    def begin(self, ids, direction, gain, seed, temperature):
        self.cache_count += 1
        self.cache = object()
        self.direction, self.gain = direction, gain
        self.begin_calls.append({"ids": list(ids), "gain": gain, "direction": direction.copy()})
        self.norm_rows, self.processed_ids = [], []
        self.cursor = 0
        return self._forward(ids)

    def _forward(self, ids):
        for token in ids:
            h = (np.linspace(-1, 1, HIDDEN_DIM) + token / 100).astype(np.float32)
            self.last_activation = h.copy()
            out = steer_numpy(h, self.direction, self.gain)
            pre, post = np.linalg.norm(h), np.linalg.norm(out)
            delta = np.linalg.norm(out - h)
            self.norm_rows.append({"tokenId": token, "preSteerL2": float(pre),
                                   "postSteerL2": float(post), "actualDeltaL2": float(delta),
                                   "requestedDeltaL2": float(self.gain * pre if np.any(self.direction) else 0),
                                   "actualDeltaRatio": float(delta / pre)})
            self.processed_ids.append(token)
        return None

    def advance(self, token):
        if self.raise_on_advance:
            raise RuntimeError("injected native failure")
        result = self._forward([token])
        if self.after_advance:
            self.after_advance()
        return result

    def sample(self, logits):
        self.sample_calls += 1
        token = self.plan[min(self.cursor, len(self.plan) - 1)]
        self.cursor += 1
        return token

    def decode(self, ids):
        return " ".join(f"word{x}" for x in ids)

    def release_cache(self):
        self.released += 1
        self.cache = None
        self.direction = None
        self.gain = 0


def fake_inspector(path):
    return {"modelPath": path, "manifest": {"sha256": "f" * 64}}


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q = load_projection()
        cls.activations = np.random.default_rng(17).normal(size=(32, HIDDEN_DIM))
        cls.calibration = make_calibration(cls.activations, "f" * 64)

    def test_committed_projection_and_text_count(self):
        gram = np.einsum("di,dj->ij", self.q, self.q, optimize=False)
        np.testing.assert_allclose(gram, np.eye(32), atol=1e-6, rtol=0)
        self.assertEqual(self.q.shape, (2560, 32))
        self.assertEqual(len(calibration_texts()), 32)
        self.assertEqual(len(set(calibration_texts())), 32)

    def test_projected_center_scale_matches_independent_formula(self):
        raw = np.stack([np.sum(self.activations * column, axis=1) for column in self.q.T], axis=1)
        np.testing.assert_allclose(self.calibration["mean"], raw.mean(0), atol=1e-12)
        np.testing.assert_allclose(self.calibration["scales"], raw.std(0), atol=1e-12)
        result = project(self.activations[0], self.calibration)
        np.testing.assert_allclose(result, np.tanh((raw[0] - raw.mean(0)) / raw.std(0)), atol=1e-12)
        self.assertTrue(np.all(np.abs(result) <= 1))

    def test_calibration_restore_binds_bytes_not_just_outer_hash(self):
        validate_calibration(self.calibration, "f" * 64)
        broken = json.loads(json.dumps(self.calibration))
        broken["projection"][0][0] += 0.001
        broken["sha256"] = canonical_hash({k: v for k, v in broken.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "committed basis"):
            validate_calibration(broken, "f" * 64)
        with self.assertRaisesRegex(ValueError, "different model"):
            validate_calibration(self.calibration, "x" * 64)

    def test_tampered_mean_without_rehash_is_rejected(self):
        broken = dict(self.calibration, mean=[0.0] * 32)
        with self.assertRaisesRegex(ValueError, "digest"):
            validate_calibration(broken, "f" * 64)

    def test_steering_zero_path_is_exact_identity(self):
        h = np.array([[0.1, 2.0, -3.0]], dtype=np.float16)
        self.assertIs(steer_numpy(h, np.ones(3), 0.0), h)
        self.assertIs(steer_numpy(h, np.zeros(3), GAIN), h)
        np.testing.assert_array_equal(steering_direction(np.zeros(32)), np.zeros(HIDDEN_DIM))

    def test_position_norm_relative_steering(self):
        h = np.random.default_rng(1).normal(size=(2, 3, HIDDEN_DIM)).astype(np.float32)
        direction = steering_direction(np.linspace(-1, 1, 32), self.q)
        changed = steer_numpy(h, direction, GAIN)
        ratios = np.linalg.norm(changed - h, axis=-1) / np.linalg.norm(h, axis=-1)
        np.testing.assert_allclose(ratios, GAIN, atol=1e-7, rtol=0)
        self.assertAlmostEqual(np.linalg.norm(direction), 1.0)

    def test_bad_shapes_nonfinite_and_unbounded_state_rejected(self):
        for value in ([0] * 31, [float("nan")] * 32, [1.1] * 32):
            with self.assertRaises(ValueError):
                steering_direction(value, self.q)
        with self.assertRaises(ValueError):
            project([0] * 2559, self.calibration)


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration = make_calibration(np.random.default_rng(8).normal(size=(32, HIDDEN_DIM)), "f" * 64)

    def setUp(self):
        self.backend = FakeBackend()
        self.engine = Engine(lambda path: self.backend, fake_inspector)
        self.engine.initialize({"modelPath": "fake", "existingCalibration": self.calibration}, threading.Event())

    def request(self, **overrides):
        return {"prompt": "An open writing opportunity.", "steeringState": [0.3] * 32,
                "gain": GAIN, "maxTokens": 8, **overrides}

    def test_initialize_restored_does_not_capture_or_sample(self):
        self.assertEqual(self.backend.cache_count, 0)
        self.assertEqual(self.backend.sample_calls, 0)

    def test_fresh_calibration_uses_exactly_32_separate_unsampled_caches(self):
        backend = FakeBackend()
        engine = Engine(lambda path: backend, fake_inspector)
        result = engine.initialize({"modelPath": "fake"}, threading.Event())
        self.assertEqual(backend.cache_count, 32)
        self.assertEqual(backend.released, 32)
        self.assertEqual(backend.sample_calls, 0)
        self.assertEqual(len(result["calibrationObservations"]), 32)
        self.assertTrue(all(x["receipt"]["sampleCount"] == 0 for x in result["calibrationObservations"]))

    def test_quiet_capture_has_zero_sampling_and_fresh_cache(self):
        result = self.engine.quiet_capture({"text": "A quiet observation."}, threading.Event())
        self.assertEqual(self.backend.sample_calls, 0)
        self.assertEqual(result["receipt"]["sampleCount"], 0)
        self.assertEqual(result["receipt"]["capturedTokenId"], result["promptTokenIds"][-1])
        self.assertEqual(result["norms"]["maxActualDeltaRatio"], 0)
        self.assertEqual(len(result["activation"]), HIDDEN_DIM)
        self.assertEqual(len(result["projection"]), STATE_DIM)
        self.assertIsNone(self.backend.cache)

    def test_final_generated_content_capture_is_same_pass_and_excludes_eos(self):
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertTrue(result["complete"])
        self.assertEqual(result["generatedTokenIds"], [41, 42])
        self.assertEqual(result["sampledTokenIds"], [41, 42, 0])
        self.assertEqual(self.backend.processed_ids, [1, 2, 3, 41, 42])
        self.assertEqual(result["receipt"]["capturedPosition"], 4)
        self.assertEqual(result["receipt"]["capturedTokenId"], 42)
        self.assertFalse(result["receipt"]["captureReplayed"])
        np.testing.assert_array_equal(result["activation"], (np.linspace(-1, 1, HIDDEN_DIM) + .42).astype(np.float32))
        self.assertEqual(self.backend.cache_count, 1)
        self.assertIsNone(self.backend.direction)

    def test_maximum_token_stop_retains_prose_but_no_feedback(self):
        result = self.engine.generate_journal(self.request(maxTokens=1), threading.Event())
        self.assertFalse(result["complete"])
        self.assertEqual(result["stopReason"], "max_tokens")
        self.assertEqual(result["text"], "word41")
        self.assertEqual(self.backend.processed_ids, [1, 2, 3, 41])
        self.assertIsNone(result["activation"])
        self.assertIsNone(result["projection"])

    def test_empty_eos_cannot_feed_prompt_activation_back_as_journal(self):
        self.backend.plan = [0]
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertFalse(result["complete"])
        self.assertEqual(result["stopReason"], "empty_eos")
        self.assertIsNone(result["projection"])
        self.assertEqual(self.backend.processed_ids, [1, 2, 3])

    def test_non_eos_special_is_not_a_completed_journal(self):
        self.backend.plan = [41, 99]
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertEqual(result["stopReason"], "non_eos_special_token")
        self.assertFalse(result["complete"])
        self.assertIsNone(result["projection"])

    def test_cancel_after_content_preserves_incomplete_output_only(self):
        cancel = threading.Event()
        self.backend.after_advance = cancel.set
        result = self.engine.generate_journal(self.request(), cancel)
        self.assertEqual(result["stopReason"], "cancelled")
        self.assertEqual(result["generatedTokenIds"], [41])
        self.assertIsNone(result["projection"])

    def test_deadline_after_forward_cannot_publish_feedback(self):
        current = [0.0]
        self.engine.clock = lambda: current[0]
        self.backend.after_advance = lambda: current.__setitem__(0, 181.0)
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertEqual(result["stopReason"], "deadline")
        self.assertIsNone(result["projection"])

    def test_native_failure_preserves_partial_sample_and_releases_cache(self):
        self.backend.raise_on_advance = True
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertEqual(result["stopReason"], "worker_error")
        self.assertEqual(result["generatedTokenIds"], [41])
        self.assertIsNone(result["projection"])
        self.assertIsNone(self.backend.cache)

    def test_decode_failure_retains_tokens_norms_and_no_feedback(self):
        def broken_decode(ids):
            raise ValueError("decoder failure")
        self.backend.decode = broken_decode
        result = self.engine.generate_journal(self.request(), threading.Event())
        self.assertEqual(result["stopReason"], "worker_error")
        self.assertEqual(result["generatedTokenIds"], [41, 42])
        self.assertEqual(result["sampledTokenIds"], [41, 42, 0])
        self.assertEqual(result["norms"]["positionCount"], 5)
        self.assertEqual(result["text"], "")
        self.assertIsNone(result["projection"])

    def test_quiet_does_not_leave_steering_or_change_independent_probe(self):
        first = self.engine.generate_journal(self.request(gain=0), threading.Event())
        self.engine.quiet_capture({"text": "A different observation."}, threading.Event())
        second = self.engine.generate_journal(self.request(gain=0), threading.Event())
        self.assertEqual(first["generatedTokenIds"], second["generatedTokenIds"])
        self.assertEqual(first["activation"], second["activation"])
        self.assertEqual(self.backend.cache_count, 3)
        self.assertEqual(second["norms"]["maxActualDeltaRatio"], 0)

    def test_invalid_generation_values_rejected_before_forward(self):
        for override in ({"gain": .02}, {"gain": True}, {"temperature": float("nan")},
                         {"maxTokens": True}, {"maxTokens": 1025}, {"seed": -1},
                         {"steeringState": [0] * 31}):
            with self.assertRaises(ValueError):
                self.engine.generate_journal(self.request(**override), threading.Event())
        self.assertEqual(self.backend.cache_count, 0)


class ProtocolTests(unittest.TestCase):
    def test_strict_json_ids_fields_and_finiteness(self):
        valid = '{"id":"r-1","command":"inspect"}'
        self.assertEqual(parse_request(valid)["id"], "r-1")
        for line in ('[]', '{"id":null,"command":"inspect"}',
                     '{"id":"a","command":"inspect","command":"shutdown"}',
                     '{"id":"a","command":"generate_journal","gain":NaN}',
                     '{"id":"a","command":"inspect","unknown":1}',
                     '{"id":"a","command":"cancel"}'):
            with self.assertRaises(WorkerError):
                parse_request(line)

    def test_inspect_repeated_id_and_shutdown_have_one_terminal_response_each(self):
        output = io.StringIO()
        source = io.StringIO('\n'.join([
            '{"id":"a","command":"inspect"}',
            '{"id":"a","command":"inspect"}',
            '{"id":"z","command":"shutdown"}',
        ]))
        Server(Engine(FakeBackend, fake_inspector), source, output).run()
        results = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(results), 3)
        self.assertEqual(sum(x["type"] == "error" for x in results), 1)
        self.assertTrue(any(x.get("error", {}).get("code") == "duplicate_id" for x in results))
        self.assertTrue(all(x["workerIdentity"]["runtimeVersions"]["numpy"] for x in results))
        self.assertTrue(all(x["protocolVersion"] == "reservoir-activation/1" for x in results))

    def test_invalid_request_preserves_valid_id_and_emits_runtime_identity(self):
        source = io.StringIO('{"id":"known-1","command":"inspect","unknown":1}\n')
        output = io.StringIO()
        Server(Engine(FakeBackend, fake_inspector), source, output).run()
        result = json.loads(output.getvalue())
        self.assertEqual(result["id"], "known-1")
        self.assertEqual(result["type"], "error")
        self.assertIsNone(result["workerIdentity"]["modelManifestSha256"])

    def test_reader_cancels_queued_or_running_work_without_inference_thread_access(self):
        class WaitingEngine:
            def dispatch(self, request, cancel):
                if not cancel.wait(1):
                    raise AssertionError("cancel was not delivered")
                return {"cancelled": True}
        source = io.StringIO('\n'.join([
            '{"id":"job","command":"inspect"}',
            '{"id":"stop","command":"cancel","targetId":"job"}',
        ]))
        output = io.StringIO()
        Server(WaitingEngine(), source, output).run()
        results = {x["id"]: x for x in map(json.loads, output.getvalue().splitlines())}
        self.assertTrue(results["stop"]["result"]["cancellationRequested"])
        self.assertTrue(results["job"]["result"]["cancelled"])

    def test_absolute_script_entrypoint_is_importable_and_stdout_is_only_json(self):
        entry = Path(__file__).parents[1] / "__main__.py"
        run = subprocess.run([sys.executable, "-B", str(entry)],
                             input='{"id":"inspect-1","command":"inspect"}\n',
                             text=True, capture_output=True, timeout=15, cwd="/tmp")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertFalse(result["result"]["initialized"])
        self.assertEqual(result["result"]["hiddenDim"], 2560)


if __name__ == "__main__":
    unittest.main()
