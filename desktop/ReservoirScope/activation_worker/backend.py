"""One local MLX model, manual serial decode, one tap, fresh caches per operation."""
from __future__ import annotations

import numpy as np

from . import HIDDEN_DIM, LAYER_COUNT, TAP_BLOCK_INDEX


class MLXBackend:
    def __init__(self, model_path: str):
        # Only initialize invokes this: inspect, protocol tests and import are inert.
        import mlx.core as mx
        import mlx.nn as nn
        from mlx_lm import load
        from mlx_lm.models.cache import make_prompt_cache
        from mlx_lm.sample_utils import make_sampler

        self.mx, self.make_prompt_cache, self.make_sampler = mx, make_prompt_cache, make_sampler
        self.model, self.tokenizer = load(model_path, tokenizer_config={"trust_remote_code": False})
        if len(self.model.model.layers) != LAYER_COUNT or self.model.args.hidden_size != HIDDEN_DIM:
            raise ValueError("loaded architecture differs from the inspected manifest")
        self.eos_ids = set(self.tokenizer.eos_token_ids)
        if not self.eos_ids:
            raise ValueError("tokenizer has no EOS identifiers")
        self.special_ids = set(self.tokenizer.all_special_ids)
        self.direction = None
        self.gain = 0.0
        self.cache = None
        self.captured = None
        self.norm_rows = []
        self.processed_ids = []
        owner = self

        class Tap(nn.Module):
            def __init__(self, block):
                super().__init__()
                self.block = block

            def __call__(self, *args, **kwargs):
                h = self.block(*args, **kwargs)
                owner.captured = h[:, -1, :].astype(mx.float32)
                owner.residual_dtype = str(h.dtype)
                before = mx.sqrt(mx.sum(h.astype(mx.float32) ** 2, axis=-1))
                owner.before = before
                if owner.gain == 0.0 or owner.direction is None:
                    # Return the exact object; no add-zero or dtype round trip.
                    owner.after = before
                    owner.actual_delta = mx.zeros_like(before)
                    owner.intended_delta = mx.zeros_like(before)
                    return h
                delta = owner.gain * before[..., None] * owner.direction
                owner.intended_delta = mx.sqrt(mx.sum(delta ** 2, axis=-1))
                out = h + delta.astype(h.dtype)
                owner.after = mx.sqrt(mx.sum(out.astype(mx.float32) ** 2, axis=-1))
                owner.actual_delta = mx.sqrt(mx.sum((out.astype(mx.float32) - h.astype(mx.float32)) ** 2, axis=-1))
                return out

        self.original_block = self.model.model.layers[TAP_BLOCK_INDEX]
        self.tap = Tap(self.original_block)
        self.model.model.layers[TAP_BLOCK_INDEX] = self.tap

    def encode_raw(self, text: str) -> list[int]:
        return list(self.tokenizer.encode(text, add_special_tokens=False))

    def encode_journal(self, prompt: str) -> list[int]:
        return list(self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=True,
            add_generation_prompt=True, enable_thinking=False))

    def begin(self, ids: list[int], direction: np.ndarray, gain: float, seed: int, temperature: float):
        self.cache = self.make_prompt_cache(self.model)
        self.gain = gain
        self.direction = self.mx.array(direction.astype(np.float32)) if gain != 0 and np.any(direction) else None
        self.norm_rows, self.processed_ids = [], []
        self.mx.random.seed(seed)
        self.sampler = self.make_sampler(temp=temperature)
        return self._forward(ids)

    def _forward(self, ids: list[int]):
        mx = self.mx
        logits = self.model(mx.array([ids]), cache=self.cache)[:, -1, :]
        mx.eval(logits, self.captured, self.before, self.after, self.actual_delta, self.intended_delta)
        self.last_activation = np.asarray(self.captured[0], dtype=np.float32).copy()
        before = np.asarray(self.before[0], dtype=np.float64)
        after = np.asarray(self.after[0], dtype=np.float64)
        delta = np.asarray(self.actual_delta[0], dtype=np.float64)
        intended = np.asarray(self.intended_delta[0], dtype=np.float64)
        self.norm_rows.extend({"tokenId": token, "preSteerL2": float(b),
                               "postSteerL2": float(a), "actualDeltaL2": float(d),
                               "requestedDeltaL2": float(self.gain * b if self.direction is not None else 0),
                               "intendedDeltaL2": float(i),
                               "actualDeltaRatio": float(d / b) if b else 0.0}
                              for token, b, a, d, i in zip(ids, before, after, delta, intended))
        self.processed_ids.extend(ids)
        return logits

    def advance(self, token: int):
        return self._forward([token])

    def sample(self, logits) -> int:
        probabilities = logits - self.mx.logsumexp(logits, axis=-1, keepdims=True)
        token = self.sampler(probabilities)
        self.mx.eval(token)
        return int(token.item())

    def decode(self, ids: list[int]) -> str:
        return self.tokenizer.decode(ids, skip_special_tokens=False)

    def release_cache(self):
        self.cache = None
        self.captured = None
        self.direction = None
        self.gain = 0.0
        self.mx.clear_cache()
