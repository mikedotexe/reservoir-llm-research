#!/usr/bin/env python3
"""Read completed, preserved laptop cohorts; never contact a model or live store.

Usage: python3 probes/compare_sustained_peer_runs.py COMPARISON_PACKET OUTPUT_DIR
The packet is produced only after the three new snapshots pass native replay.
Counts describe these saved trajectories, not independent subjects or causal effects.
Standard library only. Output includes private response text and supplied prompts.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics


def read(path):
    return json.loads(path.read_text())


def body(journal):
    # Scheduled conversations are passive and retain text without an action body.
    entry = journal["pending"]["entry"]
    return entry.get("body", entry["text"])


def distribution(values):
    return {"n": len(values), "min": min(values), "median": statistics.median(values),
            "max": max(values)} if values else {"n": 0}


def summarize(root):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    checkpoint_bytes = (root / "checkpoints" / (manifest["checkpointSha256"] + ".json")).read_bytes()
    assert hashlib.sha256(checkpoint_bytes).hexdigest() == manifest["checkpointSha256"]
    state = json.loads(checkpoint_bytes)["state"]
    assert manifest["phase"] == "scheduleComplete", root
    outcomes = state["checkInState"]["outcomes"]
    assert [o["ordinal"] for o in outcomes] == [1, 2, 3]
    assert all(o["status"] == "applied" for o in outcomes)
    journals = {}
    for path in (root / "journals").glob("*.json"):
        journal = read(path)
        journals[journal["pending"]["entry"]["id"]] = journal
    assert len(journals) == manifest["journalCount"]
    hourly_ids = {o["journalId"] for o in outcomes}
    ordered = sorted(journals.values(), key=lambda j: j["pending"]["entry"]["attemptId"])
    ordinary = [j for j in ordered if j["pending"]["entry"]["id"] not in hourly_ids]
    receipts, events, captures = {}, {}, []
    for path in (root / "segments").glob("*.json"):
        segment = read(path)["segment"]
        for key in ("initialCheckpoint", "finalCheckpoint"):
            action = segment[key]["state"].get("actionState") or {}
            for receipt in action.get("recentReceipts", []):
                previous = receipts.setdefault(receipt["journalId"], receipt)
                assert previous == receipt
        for event in segment["events"]:
            previous = events.setdefault(event["id"], event)
            assert previous == event
    for event in sorted(events.values(), key=lambda e: e["id"]):
        if event["kind"]["type"] == "peersCaptured":
            capture = event["kind"]["data"]
            captures.append({"attemptId": capture["attemptId"], "peers": [
                {"participant": p["participant"], "unavailable": p["unavailable"],
                 "journalId": (p["entry"] or {}).get("journalId")}
                for p in capture["peers"]]})
    action = state["actionState"]
    assert len(receipts) == action["decisionCount"] == len(ordinary)
    statuses = Counter(r["status"] for r in receipts.values())
    assert statuses["applied"] == action["appliedCount"]
    assert statuses["rejected"] == action["rejectedCount"]
    selected_ordinary = {ordinary[0]["pending"]["entry"]["id"]: ["first ordinary"]}
    samples = []
    for outcome in outcomes:
        journal = journals[outcome["journalId"]]
        pending = journal["pending"]
        earlier = [j for j in ordinary if j["pending"]["entry"]["attemptId"] < pending["entry"]["attemptId"]]
        if earlier:
            selected_ordinary.setdefault(earlier[-1]["pending"]["entry"]["id"], []).append(
                "ordinary before hour " + str(outcome["ordinal"]))
        samples.append({"hour": outcome["ordinal"], "outcome": outcome,
                        "bodyWhitespaceWords": len(body(journal).split()),
                        "bodyUtf8Bytes": len(body(journal).encode()),
                        "journal": journal})
    peer_traces = []
    for receipt in sorted(receipts.values(), key=lambda r: r["attemptId"]):
        if receipt.get("peerRead"):
            following = next((j for j in ordinary if j["pending"]["entry"]["attemptId"] > receipt["attemptId"]), None)
            peer_traces.append({"receipt": receipt, "firstFollowingOrdinary": following})
    responses = [j["pending"]["response"] for j in ordered]
    return {
        "snapshot": str(root), "manifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "config": manifest["config"], "journals": len(journals), "ordinary": len(ordinary),
        "step": manifest["step"], "elapsedMillis": manifest["elapsedMillis"],
        "actionStatuses": dict(statuses),
        "actionRequests": dict(Counter((r.get("request") or {}).get("kind", "missing") for r in receipts.values())),
        "inputDispositions": dict(Counter((r.get("reservoirInput") or {}).get("disposition", "missing") for r in receipts.values())),
        "inquiryStatuses": dict(Counter((r.get("inquiry") or {}).get("status", "absent") for r in receipts.values())),
        "eventCounts": dict(Counter(e["kind"]["type"] for e in events.values())),
        "responseStopReasons": dict(Counter(r.get("stopReason", "missing") for r in responses)),
        "responseTokens": distribution([r["tokenCount"] for r in responses if r.get("tokenCount") is not None]),
        "promptTokens": distribution([r["providerPromptEvaluation"]["count"] for r in responses if (r.get("providerPromptEvaluation") or {}).get("count") is not None]),
        "transportMillis": distribution([j["timing"]["transportDurationMs"] for j in ordered if (j.get("timing") or {}).get("transportDurationMs") is not None]),
        "ordinaryBodyWords": distribution([len(body(j).split()) for j in ordinary]),
        "samples": samples, "ordinarySamples": [{"reasons": reasons, "journal": journals[jid]} for jid, reasons in selected_ordinary.items()],
        "peerCaptures": captures, "peerReadTraces": peer_traces,
        "receipts": sorted(receipts.values(), key=lambda r: r["attemptId"]),
        "diagnostics": manifest["diagnostics"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    packet = read(args.packet)
    result = {"sourcePacket": str(args.packet.resolve()), "arms": []}
    response_only = []
    for arm in packet["arms"]:
        item = {"arm": arm["arm"], "cohorts": {}}
        for cohort, source in arm["cohorts"].items():
            item["cohorts"][cohort] = summarize(Path(source["snapshot"]))
        for sample in item["cohorts"]["peer"]["samples"]:
            response_only.append("MODEL " + arm["arm"] + " / HOUR " + str(sample["hour"]) + "\n\n" + body(sample["journal"]))
        result["arms"].append(item)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (args.output / "new-hourly-response-only.txt").write_text("\n\n\f\n\n".join(response_only) + "\n")
    print(json.dumps({"arms": [{"arm": a["arm"], "cohorts": {c: {k: r[k] for k in
        ["journals", "ordinary", "step", "actionStatuses", "actionRequests", "inputDispositions", "inquiryStatuses", "ordinaryBodyWords"]}
        for c, r in a["cohorts"].items()}} for a in result["arms"]]}, indent=2))


if __name__ == "__main__":
    main()
