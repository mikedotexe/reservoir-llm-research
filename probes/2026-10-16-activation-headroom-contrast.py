#!/usr/bin/env python3
"""Read-only historical contrast of retained unsteered and trace material.

No model imports/calls. This is a partial cross-attempt contrast, not the missing
three-condition comparison. The initial context is checked before comparing it;
later prompts also carry the different earlier prose. Output contains no prose.
"""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def session(directory):
    manifest = read(directory / "latest.json")
    record_path = directory / manifest["recordFile"]
    assert sha(record_path) == manifest["recordSha256"]
    record = read(record_path)
    operations = []
    for event in record["events"]:
        if event["kind"] != "requestStarted":
            continue
        request = event["request"]
        response_path = directory / f'{request["id"]}-response.json'
        if response_path.exists():
            operations.append((request, read(response_path), sha(response_path)))
    return manifest, record, operations


def first_difference(left, right):
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b),
                min(len(left), len(right)) if len(left) != len(right) else None)


def analyze(cohort, earlier):
    current_result = read(cohort / "cohort/cohort-result.json")
    current_dir = Path(current_result["sessions"][0]["directory"])
    previous_dir = next((earlier / "condition-1").glob("activation-*"))
    cm, cr, current = session(current_dir)
    pm, pr, previous = session(previous_dir)
    assert cm["config"]["arm"] == "no_steering" and pm["config"]["arm"] == "decaying_trace"
    cc, pc = read(current_dir / "calibration.json"), read(previous_dir / "calibration.json")
    omitted = {"sha256", "modelManifestSha256"}
    numerical_equal = {k: v for k, v in cc.items() if k not in omitted} == {
        k: v for k, v in pc.items() if k not in omitted}
    quiet = []
    for n, (a, b) in enumerate(zip(
            [x for x in current if x[0]["kind"] == "quiet_capture"],
            [x for x in previous if x[0]["kind"] == "quiet_capture"]), 1):
        quiet.append({"observation": n, "textIdentical": a[0]["prompt"] == b[0]["prompt"],
                      **{key + "Identical": a[1][key] == b[1][key]
                         for key in ("promptTokenIds", "activation", "projection")}})
    journals = []
    for n, (a, b) in enumerate(zip(
            [x for x in current if x[0]["kind"] == "generate_journal"],
            [x for x in previous if x[0]["kind"] == "generate_journal"]), 1):
        ar, br = a[1], b[1]
        journals.append({"opportunity": n,
            "promptIdentical": a[0]["prompt"] == b[0]["prompt"],
            "promptTokenIdsIdentical": ar["promptTokenIds"] == br["promptTokenIds"],
            "currentComplete": ar["complete"], "previousComplete": br["complete"],
            "currentStopReason": ar["stopReason"], "previousStopReason": br["stopReason"],
            "currentContentTokens": len(ar["generatedTokenIds"]),
            "previousContentTokens": len(br["generatedTokenIds"]),
            "textIdentical": ar["text"] == br["text"],
            "firstDifferingContentTokenIndex": first_difference(ar["generatedTokenIds"], br["generatedTokenIds"]),
            "firstDifferingTextCharacterIndex": first_difference(ar["text"], br["text"]),
            "currentResponseSha256": a[2], "previousResponseSha256": b[2]})
    return {"schema": "activation-headroom-historical-contrast-v1",
        "analysisSourceSha256": sha(Path(__file__)), "modelCalls": 0,
        "evidenceFilesModified": False, "scope": "partial-cross-attempt-contrast",
        "currentSession": cm["sessionId"], "previousSession": pm["sessionId"],
        "currentRecordSha256": cm["recordSha256"], "previousRecordSha256": pm["recordSha256"],
        "currentModelManifestSha256": cm["modelManifestSha256"],
        "previousModelManifestSha256": pm["modelManifestSha256"],
        "numericalCalibrationIdentical": numerical_equal,
        "completedJournals": [len(cr["state"]["journals"]), len(pr["state"]["journals"])],
        "quietComparisons": quiet, "journalOpportunityComparisons": journals,
        "limitations": ["Different attempts and worker manifests; this does not complete the frozen three-condition cohort.",
            "Only the first journal has matched text context; later opportunities include different exact previous prose.",
            "The current third response is incomplete and was never saved as a journal or applied as feedback.",
            "Token differences do not establish semantic benefit, recurrence benefit, or experiential claims."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--earlier-pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cohort, earlier, output = (p.resolve() for p in (args.cohort, args.earlier_pilot, args.output))
    assert not output.is_relative_to(cohort) and not output.is_relative_to(earlier)
    value = analyze(cohort, earlier)
    with output.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": sha(output), "scope": value["scope"]}))
