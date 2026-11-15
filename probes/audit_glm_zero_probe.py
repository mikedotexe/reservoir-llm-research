#!/usr/bin/env python3
"""Preserve the user-selected GLM zero-input episode, read-only toward its store.

Consumes the existing startup review, a stable current checkpoint and three
immutable journals. This is a narrow case audit, not native whole-run verification.
"""
import argparse
import hashlib
import json
from pathlib import Path

from observe_sonar_exploration import read_regular, utc_now
from review_sonar_startup import capture, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("startup_review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    root = Path(next(a for a in protocol["arms"] if a["arm"] == "glm")["sessionPath"])
    assert not args.output.resolve().is_relative_to(root.resolve())
    review = json.loads(args.startup_review.read_text())
    arm = next(a for a in review["arms"] if a["arm"] == "glm")
    selected = next(e for e in arm["entries"] if e["observedStep"] == 60)
    scan_entry = next(e for e in arm["entries"] if e["observedStep"] == 90)
    manifest, state, raw, checkpoint = capture(root)
    assert manifest["sessionId"] == arm["sessionId"]
    question = state["sonarState"]["latestQuestion"]
    assert question["id"] == scan_entry["receipt"]["sonarQuestion"]["id"]
    journals = {}
    for step in (60, 90, 120):
        paths = list((root / "journals").glob(f"journal-{step}-*.json"))
        assert len(paths) == 1, paths
        content = read_regular(paths[0])
        journal = json.loads(content)
        assert journal["pending"]["entry"]["observedStep"] == step
        journals[step] = (paths[0], content, journal)
    assert hashlib.sha256(journals[60][1]).hexdigest() == selected["fileSha256"]
    assert hashlib.sha256(journals[90][1]).hexdigest() == scan_entry["fileSha256"]
    receipt = selected["receipt"]
    assert len(receipt["probe"]["appliedVector"]) == 48
    assert not any(receipt["probe"]["appliedVector"])
    assert receipt["stateDeltaL2"] == 0 and receipt["status"] == "applied"
    assert receipt["reservoirInput"]["disposition"] == "withhold"
    assert question["origin"] == question["alternativeOrigin"]
    assert question["actualMapId"] == question["alternativeMapId"]
    assert question["unitInput"] is None and not question["linearPredictionValid"]
    prompt = journals[120][2]["pending"]["prompt"]
    rendered = json.loads(prompt.split("MODEL-SELECTED QUESTION\n", 1)[1].splitlines()[0])
    assert rendered["questionId"] == question["id"] and not rendered["directionResolved"]
    assert not rendered["linearPredictionValid"]
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "manifest.capture.json").write_bytes(raw)
    (args.output / "checkpoint.capture.json").write_bytes(checkpoint)
    for path, content, _ in journals.values():
        (args.output / path.name).write_bytes(content)
    result = {
        "observedAtUtc": utc_now(), "sessionId": manifest["sessionId"],
        "scope": "One user-selected episode: steps 60, 90 and 120; not an incidence estimate.",
        "probeReceipt": receipt, "scanReceipt": scan_entry["receipt"],
        "questionReport": question, "suppliedQuestionReportAt120": rendered,
        "journals": [{"observedStep": step, "file": path.name,
                      "sha256": hashlib.sha256(content).hexdigest()}
                     for step, (path, content, _) in journals.items()],
        "sourceWrites": False, "providerCalls": False,
    }
    save(args.output / "audit.json", result)
    print(json.dumps({"output": str(args.output), "checksPassed": True,
                      "probeEffectL2": receipt["stateDeltaL2"],
                      "scanDirectionResolved": rendered["directionResolved"]}))


if __name__ == "__main__":
    main()
