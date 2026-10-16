"""Explicit, bounded real-model qualification. Never imported by unit discovery.

The owning task must admit resources before invoking this program. It loads one
owned model and makes no live-system contact. Failures are retained, not retuned.
"""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import math
import os
import time
from pathlib import Path
from threading import Event

import numpy as np

from activation_worker import GAIN, HIDDEN_DIM, STATE_DIM, TAP_BLOCK_INDEX
from activation_worker.engine import Engine
from activation_worker.manifest import inspect_model
from activation_worker.math_core import array_hash, canonical_hash, sha256_file, steering_direction

PARITY_RTOL = 1e-5
PARITY_ATOL = 1e-5
INTENDED_RATIO_ATOL = 1e-7
FIXED_TEXT = "A brass button lies beside a length of plain thread."
FIXED_CONTINUATION = " The thread is cotton."
QUIET_TEXT = "A wicker basket rests near the wall."
JOURNAL_PROBE = "Write exactly the word pebble, then stop."
MAX_PROBE_TOKENS = 64


def save(path: Path, value):
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with path.open("x") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def dtype_rounding_allowance(dtype: str) -> float:
    # For rounded delta and h+delta, relative L2 error against h is bounded by
    # u*gain + u*(1+gain+u*gain), excluding underflow. This bounds both the
    # rounded delta and the rounded final sum. Activations must also be finite.
    unit_roundoff = {"mlx.core.bfloat16": 2**-8, "bfloat16": 2**-8,
                     "mlx.core.float16": 2**-11, "float16": 2**-11,
                     "mlx.core.float32": 2**-24, "float32": 2**-24}
    if dtype not in unit_roundoff:
        raise ValueError(f"unqualified residual dtype: {dtype}")
    u = unit_roundoff[dtype]
    return u * GAIN + u * (1 + GAIN + u * GAIN)


def qualify(model_path: str, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    inspected = inspect_model(model_path)
    plan = {
        "schemaVersion": "activation-mechanical-qualification/1", "manifest": inspected["manifest"],
        "modelPath": inspected["modelPath"], "parityRtol": PARITY_RTOL, "parityAtol": PARITY_ATOL,
        "intendedGain": GAIN, "intendedRatioAtol": INTENDED_RATIO_ATOL,
        "actualRatioAllowance": "u*gain+u*(1+gain+u*gain), u=2^-8(bf16),2^-11(fp16),2^-24(fp32)",
        "fixedRawText": FIXED_TEXT, "interveningQuietText": QUIET_TEXT,
        "fixedContinuation": FIXED_CONTINUATION, "fixedContinuationTokenLimit": 3,
        "journalProbe": JOURNAL_PROBE, "maxProbeTokens": MAX_PROBE_TOKENS,
        "seed": 0, "temperature": 0.0, "retry": False,
        "checks": ["tap/no-tap/zero-gain/zero-state logits and cache-offset parity",
                   "unsteered calibration and bounded projection", "quiet zero samples",
                   "fresh-cache independent-probe isolation", "per-position intervention norm",
                   "same-pass final content/EOS association", "cleared steering after generation"],
    }
    save(output / "plan.json", plan)
    result = {"planSha256": canonical_hash(plan), "planPath": str(output / "plan.json"),
              "planFileSha256": sha256_file(output / "plan.json"),
              "modelManifestSha256": inspected["manifest"]["sha256"],
              "workerSources": inspected["manifest"]["workerSources"],
              "checks": {}, "passed": False, "status": "failed"}
    engine = None
    started = time.monotonic()
    try:
        engine = Engine(inspector=lambda _: inspected)
        initialized = engine.initialize({"modelPath": model_path}, Event())
        save(output / "initialization.json", initialized)
        save(output / "calibration.json", initialized["calibration"])
        result["calibrationPath"] = str(output / "calibration.json")
        result["calibrationFileSha256"] = sha256_file(output / "calibration.json")
        result["calibrationSha256"] = initialized["calibration"]["sha256"]
        backend = engine.backend
        mx = backend.mx
        ids = backend.encode_raw(FIXED_TEXT)
        continuation = backend.encode_raw(FIXED_CONTINUATION)[:3]
        if len(continuation) != 3 or any(token in backend.special_ids for token in continuation):
            raise RuntimeError("fixed continuation must supply three content token IDs")
        direction = steering_direction(np.linspace(-1.0, 1.0, STATE_DIM), engine.q)

        # Uninstrumented source block, same owned model weights, fresh cache.
        backend.model.model.layers[TAP_BLOCK_INDEX] = backend.original_block
        base_cache = backend.make_prompt_cache(backend.model)
        baseline = []
        for step, tokens in enumerate([ids] + [[token] for token in continuation]):
            baseline_logits = backend.model(mx.array([tokens]), cache=base_cache)[:, -1, :]
            mx.eval(baseline_logits)
            baseline.append({"stage": step, "inputTokenIds": tokens,
                             "array": np.asarray(baseline_logits.astype(mx.float32)).copy(),
                             "offsets": [int(c.offset) for c in base_cache]})
        base_cache, baseline_logits = None, None
        backend.model.model.layers[TAP_BLOCK_INDEX] = backend.tap

        parity_records = []
        for name, vector, gain in (("capture_only", np.zeros(HIDDEN_DIM), 0.0),
                                   ("zero_gain", direction, 0.0),
                                   ("zero_return", np.zeros(HIDDEN_DIM), GAIN)):
            logits = backend.begin(ids, vector, gain, 0, 0.0)
            stages = []
            for stage, expected in enumerate(baseline):
                if stage:
                    logits = backend.advance(continuation[stage - 1])
                array = np.asarray(logits.astype(mx.float32))
                offsets = [int(c.offset) for c in backend.cache]
                stages.append({"stage": stage, "inputTokenIds": expected["inputTokenIds"],
                               "logitsSha256": array_hash(array),
                               "maxAbsoluteLogitDifference": float(np.max(np.abs(array - expected["array"]))),
                               "bitwiseEqual": bool(np.array_equal(array, expected["array"])),
                               "withinTolerance": bool(np.allclose(array, expected["array"], rtol=PARITY_RTOL, atol=PARITY_ATOL)),
                               "cacheOffsets": offsets, "cacheOffsetsEqual": offsets == expected["offsets"]})
            record = {"name": name, "stages": stages,
                      "bitwiseEqual": all(x["bitwiseEqual"] for x in stages),
                      "withinTolerance": all(x["withinTolerance"] for x in stages),
                      "cacheOffsetsEqual": all(x["cacheOffsetsEqual"] for x in stages),
                      "norms": engine._norms(backend)}
            parity_records.append(record)
            backend.release_cache()
        save(output / "parity.json", {"promptTokenIds": ids, "continuationTokenIds": continuation,
                                      "baseline": [{"stage": x["stage"], "inputTokenIds": x["inputTokenIds"],
                                                    "logitsSha256": array_hash(x["array"]),
                                                    "cacheOffsets": x["offsets"]} for x in baseline],
                                      "comparisons": parity_records})
        result["checks"]["logitParity"] = all(x["withinTolerance"] for x in parity_records)
        result["checks"]["zeroAdditionBitwiseParity"] = all(x["bitwiseEqual"] for x in parity_records)
        result["checks"]["cacheOffsetParity"] = all(x["cacheOffsetsEqual"] for x in parity_records)
        if not all(result["checks"].values()):
            raise RuntimeError("tap/zero-path parity failed at the frozen tolerance")

        # The production tap computes every position's pre/post/delta norms.
        backend.begin(ids, direction, GAIN, 0, 0.0)
        norms = engine._norms(backend)
        allowance = dtype_rounding_allowance(norms["residualDtype"])
        norm_records = []
        for row in norms["perPosition"]:
            before = row["preSteerL2"]
            intended_ratio = row["intendedDeltaL2"] / before if before else 0.0
            finite = all(math.isfinite(float(value)) for value in row.values())
            norm_records.append({"tokenId": row["tokenId"], "intendedRatio": intended_ratio,
                                 "actualRatio": row["actualDeltaRatio"], "finite": finite,
                                 "intendedPass": abs(intended_ratio - GAIN) <= INTENDED_RATIO_ATOL,
                                 "roundedPass": abs(row["actualDeltaRatio"] - GAIN) <= allowance})
        save(output / "intervention.json", {"norms": norms, "actualRatioAllowance": allowance,
                                            "checks": norm_records})
        result["checks"]["perPositionNorms"] = all(x["finite"] and x["intendedPass"] and x["roundedPass"] for x in norm_records)
        backend.release_cache()
        if not result["checks"]["perPositionNorms"]:
            raise RuntimeError("intervention norm failed the declared dtype-aware bound")

        probe = {"prompt": JOURNAL_PROBE, "steeringState": [0.0] * 32,
                 "gain": 0.0, "arm": "mechanical-no-steering", "seed": 0,
                 "temperature": 0.0, "maxTokens": MAX_PROBE_TOKENS}
        first = engine.generate_journal(probe, Event())
        save(output / "probe-before.json", first)
        if not first["complete"]:
            raise RuntimeError("first bounded generation probe did not complete")
        quiet = engine.quiet_capture({"text": QUIET_TEXT}, Event())
        save(output / "quiet.json", quiet)
        second = engine.generate_journal(probe, Event())
        save(output / "probe-after.json", second)
        result["checks"]["quietZeroSamples"] = quiet["sampledTokenIds"] == [] and quiet["receipt"]["sampleCount"] == 0
        result["checks"]["independentProbeIsolation"] = (
            second["complete"] and first["generatedTokenIds"] == second["generatedTokenIds"]
            and first["receipt"]["activationSha256"] == second["receipt"]["activationSha256"])
        result["checks"]["boundedCaptures"] = (
            len(quiet["activation"]) == HIDDEN_DIM and np.isfinite(quiet["activation"]).all()
            and len(quiet["projection"]) == STATE_DIM and np.all(np.abs(quiet["projection"]) <= 1))

        steered = engine.generate_journal({**probe, "gain": GAIN,
                                           "arm": "mechanical-steered",
                                           "steeringState": np.linspace(-1, 1, 32).tolist()}, Event())
        save(output / "probe-steered.json", steered)
        result["checks"]["samePassContentToken"] = bool(steered["complete"] and
            steered["receipt"]["capturedTokenId"] == steered["generatedTokenIds"][-1] and
            steered["receipt"]["capturedPosition"] == len(steered["promptTokenIds"]) + len(steered["generatedTokenIds"]) - 1 and
            steered["receipt"]["processedTokenCount"] == len(steered["promptTokenIds"]) + len(steered["generatedTokenIds"]) and
            steered["sampledTokenIds"] == steered["generatedTokenIds"] + [steered["stopTokenId"]] and
            steered["stopTokenId"] in backend.eos_ids and not steered["receipt"]["captureReplayed"])
        # Exercise the actual cleanup after a nonzero return, before fresh quiet input.
        result["checks"]["clearedSteering"] = backend.direction is None and backend.gain == 0 and backend.cache is None
        after_steered = engine.quiet_capture({"text": QUIET_TEXT}, Event())
        save(output / "quiet-after-steered.json", after_steered)
        result["checks"]["noStaleSteering"] = (after_steered["norms"]["maxActualDeltaRatio"] == 0 and
            after_steered["receipt"]["activationSha256"] == quiet["receipt"]["activationSha256"])
        result["passed"] = all(result["checks"].values())
        result["status"] = "passed" if result["passed"] else "failed"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if engine is not None and engine.backend is not None:
            engine.backend.release_cache()
        result["elapsedSeconds"] = time.monotonic() - started
        save(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = qualify(args.model, Path(args.output).expanduser().resolve())
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
