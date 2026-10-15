#!/usr/bin/env python3
"""Compare only the two explicitly handed-off immutable episode03 exports.

Both exports have already passed the frozen checker and pinned production
replay. This script reads those files; it does not run a verifier or access a
model, service, process, UI, or live application store. Outputs are exclusive.
"""
from pathlib import Path
import datetime as dt
import json

import check_real_model_export as check

BASE = Path(__file__).resolve().parent
DESKTOP = BASE.parent.parent
EXPECTED_EXECUTABLE = "65462e49b6301d89856e28496c3c51b25383935a46b1aa8b8832c7af68c83211"
EXPECTED_RECEIPTS = (
    "246e608dfb0c3140ee2831110567ae5522a102f4a1ff45b62576b21c7cd5aad8",
    "dcc0f6afbd4999fa371c96b5e5615fc7e6ea64e9abe4f3b1fef1564a4c43c8ac",
)
EXPECTED_EXPORTS = (
    "sustained-1792001665258-1-1-423",
    "sustained-1792001665258-1-2-424",
)


def main():
    output = BASE / "recovery-comparison-01.json"
    if output.exists():
        raise FileExistsError(output)
    result = {
        "schema": "reservoir-v7-episode03-recovery-comparison-v1",
        "startedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "failed",
        "script": check.identity(Path(__file__).resolve()),
        "checkerDependency": check.identity(BASE / "check_real_model_export.py"),
        "modelsContacted": False,
        "scope": "Read-only exported files and existing passing verification receipts; no new replay, runtime, model, process, network, UI, or live-store actions.",
    }
    paths = [BASE / name / "receipt.json" for name in ("real-model-export-01", "recovered-export-01")]
    receipts_before = [check.identity(path) for path in paths]
    inputs = []
    try:
        check.require([row["sha256"] for row in receipts_before] == list(EXPECTED_RECEIPTS),
                      "Handed-off verification receipt identity differs")
        records = [check.read(path) for path in paths]
        for index, record in enumerate(records):
            check.require(record["schema"] == "reservoir-real-model-export-check-v7"
                          and record["status"] == "passed"
                          and record["originalUnchanged"] is True
                          and record["modelsContactedByChecker"] is False
                          and record["expectedPromptVersion"] == "reservoir-journal-v7",
                          "Both frozen checker receipts must pass and preserve originals")
            check.require(record["pinnedExecutable"]["sha256"] == EXPECTED_EXECUTABLE
                          and record["sourceExecutable"]["sha256"] == EXPECTED_EXECUTABLE,
                          "Unexpected pinned production verifier")
            replay = record["verification"]
            check.require(replay["exitCode"] == 0 and replay["result"]["status"] == "passed"
                          and replay["result"]["modelsContacted"] is False,
                          "Missing successful offline production replay")
            bundle = Path(record["bundle"])
            expected = DESKTOP / "target/qa/0.19-v7-writing-episode03/exports" / EXPECTED_EXPORTS[index]
            check.require(bundle == expected, "Receipt identifies an unexpected export path")
            before = check.inventory(bundle)
            inputs.append((bundle, before))
            check.require(check.exact(before, record["inventoryBefore"]),
                          "Export differs from its verification inventory")
            actual_manifest = check.read(bundle / "manifest.json")
            check.require(check.exact(actual_manifest, record["evidence"]["manifest"]),
                          "Actual manifest differs from the checked manifest")

        a, b = [before for _, before in inputs]
        check.require(a.keys() == b.keys() and len(a) == 73, "Expected the same 73 exported files")
        changed = sorted(name for name in a if a[name] != b[name])
        check.require(changed == ["manifest.json"], "A non-manifest retained file changed")
        # Independently compare actual bytes, in addition to inventory hashes.
        identical = [name for name in sorted(a)
                     if name != "manifest.json"
                     and check.data(inputs[0][0] / name) == check.data(inputs[1][0] / name)]
        check.require(len(identical) == 72, "A retained file is not byte-identical")
        original, recovered = [record["evidence"]["manifest"] for record in records]
        differences = {
            key: {"original": original.get(key), "recovered": recovered.get(key)}
            for key in sorted(original.keys() | recovered.keys())
            if not check.exact(original.get(key), recovered.get(key))
        }
        expected = {
            "generation": {"original": "1", "recovered": "2"},
            "revision": {"original": "423", "recovered": "424"},
            "phase": {"original": "budgetReached", "recovered": "paused"},
        }
        check.require(check.exact(differences, expected), "Unexpected manifest change")
        evidence = [record["evidence"] for record in records]
        for key in ("continuity", "journals", "receivedResponses", "finalCorePhase"):
            check.require(check.exact(evidence[0][key], evidence[1][key]),
                          f"Retained {key} differs after recovery")
        check.require(check.exact(evidence[1]["finalCorePhase"], {"kind": "ready"}),
                      "Unexpected retained numerical core phase")
        totals = {"reached": 12, "attempted": 12, "responseReceived": 12,
                  "complete": 12, "saved": 12, "applied": 12, "unstarted": 0}
        check.require(check.exact(evidence[1]["continuity"]["totals"], totals)
                      and evidence[1]["continuity"]["exactLatestAppliedMemoryJoins"] == 11,
                      "Twelve-slot completion or memory joins differ")
        result.update(
            original=str(inputs[0][0]), recovered=str(inputs[1][0]),
            verificationReceipts=receipts_before,
            inventoryOriginal=a, inventoryRecovered=b,
            filesEach=len(a), identicalNonManifestFiles=len(identical),
            byteIdenticalFiles=identical, changedFiles=changed,
            manifestDifferences=differences, otherManifestFieldsExact=True,
            retainedCorePhase=evidence[1]["finalCorePhase"],
            unchangedCheckpointSha256=original["checkpointSha256"],
            continuity=evidence[1]["continuity"],
            step=recovered["step"], durableStep=recovered["durableStep"],
            journalCount=recovered["journalCount"], segmentCount=recovered["segmentCount"],
            elapsedMillis=recovered["elapsedMillis"],
            limits=[
                "Native quit, idle relaunch, explicit Restore and disabled Resume are parent UI observations; this comparison verifies retained files only.",
                "The retained core is ready with no unresolved opportunity. The paused wrapper does not reset the unchanged 361-step/12-attempt bounds or create another application.",
                "Clean-quit recovery is not crash or power-loss qualification, provider authentication, complete context-processing proof, or a writing-quality judgment.",
            ],
        )
        result["status"] = "passed"
    except Exception as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        result["receiptsUnchanged"] = [check.identity(path) for path in paths] == receipts_before
        result["inputsUnchanged"] = all(check.inventory(path) == before for path, before in inputs)
        result["helpersUnchanged"] = (
            check.identity(Path(__file__).resolve()) == result["script"]
            and check.identity(BASE / "check_real_model_export.py") == result["checkerDependency"]
        )
        if not all(result[key] for key in ("receiptsUnchanged", "inputsUnchanged", "helpersUnchanged")):
            result["status"] = "failed"
        result["endedAtUtc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        check.write_new(output, result)
    print(json.dumps({"status": result["status"], "receipt": str(output), "error": result.get("error")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
