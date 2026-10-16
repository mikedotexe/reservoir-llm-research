#!/usr/bin/env python3
"""Derive a private, portable reading collection from explicitly selected evidence.

Standard library only. Source records remain untouched; this is a reading derivative,
not an executable session or a substitute for the retained numerical evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORMAT = "activation-reading-collection-v1"
MODEL = "mlx-community/Qwen3-4B-4bit"
REVISION = "4dcb3d101c2a062e5c1d4bb173588c54ea6c4d25"
# These receipts predate this derivative and are retained at commit 85e36c7.
# The closure authenticates inventories, rather than accepting hashes first
# observed during derivation as evidence that the original bytes were unchanged.
ANCHORS = {
    "desktop/ReservoirScope/validation/2026-10-16-activation-headroom/closure-receipt.json": "510b95f0f9d5ff7e41d13a382725cb1187ddd47b8834058caa465322a88f4bb0",
    "desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/pilot-reading-receipt.json": "b4ea7ef448692f067804a2987cfc4bfc213f7e59ae42519b39b4ab4563fbb55c",
}
SOURCES = [
    ("reading-a", "research/outputs/activation-0.26.0-20261015/pilot-01/condition-1/activation-1792119989350565000", "bcd2421348d8ced6e5ca23b52b2b9e6d7947e8e6bdf52193fe9f9b6c5becfe0c", "October 15 pilot", 6, 0),
    ("reading-b", "research/outputs/activation-headroom-20261016/cohort-01/cohort/activation-1792171510521169000", "5b0e06113ad7d61f05ac3e241d20452db041841093b0da6f687f65a43b338ab6", "October 16 headroom cohort", 2, 1),
]


def digest(data):
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


class FrozenInventory(dict):
    def __init__(self):
        super().__init__()
        self.expected = dict(ANCHORS)

    def bind(self, relative, sha256):
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Frozen source must be repository-relative")
        prior = self.expected.get(relative)
        if prior is not None and prior != sha256:
            raise ValueError("Conflicting frozen source identity")
        self.expected[relative] = sha256


def read_source(path, inventory):
    relative = str(path.relative_to(ROOT))
    expected = inventory.expected.get(relative)
    if expected is None:
        raise ValueError(f"Source has no prior frozen identity: {relative}")
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError(f"Frozen source identity differs: {relative}")
    inventory[relative] = expected
    return raw


def read_json(path, inventory):
    return json.loads(read_source(path, inventory))


def frozen_inventory():
    inventory = FrozenInventory()
    closure = read_json(ROOT / next(iter(ANCHORS)), inventory)
    for artifact in closure["artifacts"]:
        inventory.bind(artifact["path"], artifact["sha256"])
    older = read_json(ROOT / "research/outputs/activation-headroom-20261016/previous-attempt-inventories.json", inventory)
    for attempt in older:
        for source in attempt["files"]:
            inventory.bind(f'{attempt["directory"]}/{source["path"]}', source["sha256"])
    cohort = read_json(ROOT / "research/outputs/activation-headroom-20261016/cohort-inventory-after-analysis.json", inventory)
    for source in cohort:
        inventory.bind(f'research/outputs/activation-headroom-20261016/cohort-01/{source["path"]}', source["sha256"])
    pilot_receipt = read_json(ROOT / "desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/pilot-reading-receipt.json", inventory)
    inventory.bind("desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/PILOT-READING-BLIND.md", pilot_receipt["blindNoteSha256"])
    return inventory


def checked_text(text):
    if not isinstance(text, str) or not text or len(text.encode()) > 65536:
        raise ValueError("Missing or oversized exact text")
    return text


def note(path, title, start, end, inventory):
    raw = read_source(path, inventory)
    body = raw.decode()
    text = body.split(start, 1)[1].split(end, 1)[0].strip()
    return {"title": title, "text": checked_text(text), "sha256": digest(text),
            "sourceSha256": digest(raw), "attribution": "Retained research reading, selected passage; source account remains unchanged"}


def derive_reading(root, reading_id, expected_record, attempt, inventory):
    manifest = read_json(root / "latest.json", inventory)
    record_path = root / manifest["recordFile"]
    record = read_json(record_path, inventory)
    if digest(record_path.read_bytes()) != expected_record or manifest["recordSha256"] != expected_record:
        raise ValueError("Frozen source record identity differs")
    events, entries, requests = [], [], {}
    step, observations, pending, current_journal = 0, 0, None, None
    journals = record["state"]["journals"]
    for index, event in enumerate(record["events"]):
        kind = event["kind"]
        event_id = f"event-{index + 1}"
        observation = None
        if kind == "requestStarted":
            pending = event["request"]
            requests[pending["id"]] = pending
            if pending["kind"] == "quiet_capture":
                step = (observations + 1) * manifest["config"]["stepsBetween"] - 1
                observation = pending["prompt"]
                wire = read_json(root / f'{pending["id"]}-request.json', inventory)
                if wire["text"] != observation:
                    raise ValueError("Quiet request differs from its retained exact observation")
        elif kind == "quietReceived":
            if not pending or pending["kind"] != "quiet_capture":
                raise ValueError("Quiet response has no matching request")
            observation = pending["prompt"]
            response_path = root / f'{event["request_id"]}-response.json'
            response = read_json(response_path, inventory)
            if digest(response_path.read_bytes()) != event["evidence_sha256"] or response["receipt"]["sampledTokenCount"] != 0:
                raise ValueError("Quiet response identity or sample boundary differs")
            step += 1
            observations += 1
            pending = None
        elif kind == "journalReceived":
            journal = journals[len(entries)]
            request = requests[event["request_id"]]
            response_path = root / f'{event["request_id"]}-response.json'
            response = read_json(response_path, inventory)
            wire = read_json(root / f'{event["request_id"]}-request.json', inventory)
            text = checked_text(journal["text"])
            if (digest(response_path.read_bytes()) != event["evidence_sha256"]
                    or response["text"] != text or event["text"] != text
                    or not response["complete"] or digest(text) != journal["sha256"]
                    or wire["prompt"] != request["prompt"]):
                raise ValueError("Journal response, exact prompt or text identity differs")
            journal_path = root / f'{journal["id"]}.txt'
            if read_source(journal_path, inventory) != text.encode():
                raise ValueError("Saved journal readback differs")
            current_journal = {"id": journal["id"], "status": "complete", "text": text,
                "sha256": digest(text), "observedStep": journal["observedStep"],
                "savedStep": None, "appliedStep": None, "requestId": event["request_id"],
                "prompt": wire["prompt"], "promptSha256": digest(wire["prompt"]),
                "stopReason": response["stopReason"], "contentTokens": len(response["generatedTokenIds"]),
                "sourceResponseSha256": digest(response_path.read_bytes()), "eventIds": [event["request_id"].replace("request-", "event-", 1), event_id]}
            entries.append(current_journal)
            pending = None
        elif kind == "journalSaved":
            if not current_journal or event["journal_id"] != current_journal["id"] or event["sha256"] != current_journal["sha256"]:
                raise ValueError("Save boundary differs")
            current_journal["savedStep"] = step
            current_journal["eventIds"].append(event_id)
        elif kind == "journalApplied":
            if not current_journal or event["journal_id"] != current_journal["id"]:
                raise ValueError("Feedback boundary differs")
            step += 1
            current_journal["appliedStep"] = step
            current_journal["eventIds"].append(event_id)
        elif kind == "failed":
            if pending and pending["kind"] == "generate_journal":
                response_path = root / f'{pending["id"]}-response.json'
                response = read_json(response_path, inventory)
                wire = read_json(root / f'{pending["id"]}-request.json', inventory)
                text = checked_text(response["text"])
                if response["complete"] or response["receipt"]["feedbackEligible"] or wire["prompt"] != pending["prompt"]:
                    raise ValueError("Unfinished response eligibility or prompt differs")
                entries.append({"id": f'unfinished-{pending["id"]}', "status": "incomplete",
                    "text": text, "sha256": digest(text), "observedStep": step,
                    "savedStep": None, "appliedStep": None, "requestId": pending["id"],
                    "prompt": wire["prompt"], "promptSha256": digest(wire["prompt"]),
                    "stopReason": response["stopReason"], "contentTokens": len(response["generatedTokenIds"]),
                    "sourceResponseSha256": digest(response_path.read_bytes()), "eventIds": [pending["id"].replace("request-", "event-", 1), event_id]})
        else:
            raise ValueError(f"Unsupported event kind: {kind}")
        events.append({"id": event_id, "kind": kind, "step": step, "observation": observation})
    if step != record["state"]["step"] or observations != record["state"]["observationIndex"]:
        raise ValueError("Derived event boundaries differ from retained terminal state")
    for entry, journal in zip(entries, journals):
        if entry["appliedStep"] != journal["firstAppliedStep"] or entry["savedStep"] != journal["observedStep"]:
            raise ValueError("Derived journal boundaries differ")
    config = manifest["config"]
    return {"id": reading_id, "entries": entries, "events": events,
        "disclosure": {"arm": config["arm"], "sourceAttempt": attempt,
            "sourceSession": manifest["sessionId"], "sourceFormat": manifest["format"],
            "recordSha256": expected_record, "modelManifestSha256": manifest["modelManifestSha256"],
            "calibrationSha256": manifest["calibrationSha256"], "modelId": MODEL, "modelRevision": REVISION,
            "protocol": {key: config[key] for key in ("seed", "stepsBetween", "journalEvery", "maxJournalTokens", "gain")},
            "notes": []}}


def validate(collection):
    if collection["format"] != FORMAT or not 1 <= len(collection["readings"]) <= 3:
        raise ValueError("Unsupported reading collection")
    serialized = json.dumps(collection, ensure_ascii=False)
    if any(marker in serialized for marker in ("/Users/", "/Volumes/", "/private/", "C:\\\\", "pythonPath", "workerPath", "modelPath")):
        raise ValueError("Source-machine path or execution configuration leaked into collection")
    for reading in collection["readings"]:
        event_ids = {e["id"] for e in reading["events"]}
        for entry in reading["entries"]:
            if digest(entry["text"]) != entry["sha256"] or digest(entry["prompt"]) != entry["promptSha256"]:
                raise ValueError("Exact content hash differs")
            if not set(entry["eventIds"]) <= event_ids:
                raise ValueError("Dangling event reference")
            if entry["status"] == "incomplete" and (entry["savedStep"] is not None or entry["appliedStep"] is not None):
                raise ValueError("Incomplete writing cannot be saved or applied")
        for item in reading["disclosure"]["notes"]:
            if digest(item["text"]) != item["sha256"]:
                raise ValueError("Note content hash differs")


def prepare(destination):
    inventory = frozen_inventory()
    readings = []
    for identity, relative, expected, attempt, complete, incomplete in SOURCES:
        reading = derive_reading(ROOT / relative, identity, expected, attempt, inventory)
        if sum(e["status"] == "complete" for e in reading["entries"]) != complete or sum(e["status"] == "incomplete" for e in reading["entries"]) != incomplete:
            raise ValueError("Frozen selection count differs")
        readings.append(reading)
    validation = ROOT / "desktop/ReservoirScope/validation"
    readings[0]["disclosure"]["notes"].append(note(validation / "2026-10-15-activation-0.26.0/PILOT-READING-BLIND.md", "Initial allocation-concealed reading", "## Initial account\n", "## Each entry in context", inventory))
    readings[0]["disclosure"]["notes"].append(note(validation / "2026-10-15-activation-0.26.0/PILOT-READING-BLIND.md", "Each entry in context · exact excerpts and alternative readings", "## Each entry in context\n", "## Recurrence, development, and uncertainty", inventory))
    readings[1]["disclosure"]["notes"].append(note(validation / "2026-10-16-activation-headroom/READING-BLIND.md", "Initial allocation-concealed reading", "The completed journals sustain", "## Source, counts and reading boundary", inventory))
    # Keep the selected note exact, including its opening words.
    readings[1]["disclosure"]["notes"][0]["text"] = "The completed journals sustain " + readings[1]["disclosure"]["notes"][0]["text"]
    readings[1]["disclosure"]["notes"][0]["sha256"] = digest(readings[1]["disclosure"]["notes"][0]["text"])
    readings[1]["disclosure"]["notes"].append(note(validation / "2026-10-16-activation-headroom/READING-BLIND.md", "Attention and change · exact excerpts and alternative readings", "## Attention and change in the completed entries\n", "## Recurrence, development and the unfinished response", inventory))
    readings[1]["disclosure"]["notes"].append(note(validation / "2026-10-16-activation-headroom/READING-POST-DISCLOSURE.md", "After allocation disclosure", "## What the unsteered disclosure changes\n", "## Complete reading of the earlier trace", inventory))
    pilot = read_json(ROOT / "research/outputs/activation-0.26.0-20261015/pilot-01/frozen-plan.json", inventory)["pilot"]
    collection = {"format": FORMAT, "title": "Quiet observations and continuing writing",
        "scope": "Two historical attempts from an isolated Qwen3 model, not journals from live Beings. Reading A has six complete entries; Reading B has two complete entries and an unfinished response. These are separate attempts with different runtime identities, not a matched comparison. No recurrent-condition journal sequence is included.",
        "questions": pilot["readingQuestions"], "readings": readings}
    validate(collection)
    raw = (json.dumps(collection, ensure_ascii=False, indent=2) + "\n").encode()
    for relative, expected in inventory.items():
        if digest((ROOT / relative).read_bytes()) != expected:
            raise ValueError("A source changed while deriving the reading collection")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "activation-preview-v1.json"
    receipt = destination / "activation-preview-v1.derivation.json"
    if output.exists() or receipt.exists():
        raise ValueError("Choose a fresh output directory; existing derivatives are not overwritten")
    output.write_bytes(raw)
    receipt.write_text(json.dumps({"format": "activation-reading-derivation-v1", "collectionSha256": digest(raw),
        "sourceFiles": inventory, "priorReceiptAnchors": ANCHORS, "completeEntries": 8, "incompleteResponses": 1,
        "sourceFilesModified": False, "modelCalls": 0,
        "selection": "Complete original trace sequence plus complete headroom prefix and entire unfinished response; selected attributed reading-note passages; host execution paths omitted by allowlist"}, indent=2) + "\n")
    return {"sha256": digest(raw), "bytes": len(raw), "completeEntries": 8, "incompleteResponses": 1, "sourceFiles": len(inventory)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), sort_keys=True))
