#!/usr/bin/env python3
"""Offline maintained-pipeline qualification against explicit retained golden outputs.
No capture, model calls, historical edits or ledger writes. Synthetic controls are
labeled and saved separately, with a new manifest for their changed bytes.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_research.daily import load_packet, build_report, verify_report, DailyError
from reservoir_research.daily.inputs import PACKET_NAMES, write_new_json, require
from reservoir_research.daily.eras import resolve_eras
from reservoir_research.study_capture import encoded, sha, epoch
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--golden-packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    packet = load_packet(args.manifest, args.data_root)
    report_raw = (args.golden_packet / "final-report/report.json").read_bytes()
    report = build_report(packet)
    require(encoded(report) == report_raw, "Golden report differs")
    result = verify_report(packet, args.golden_packet / "final-report/report.json")
    require(encoded(result["verification"]) == (args.golden_packet / "verification.json").read_bytes(),
            "Golden verification differs")
    require(encoded(result["verified_claims"]) == (args.golden_packet / "verified-claim-checks.json").read_bytes(),
            "Golden claim spans differ")
    args.out.mkdir(mode=0o700)
    records = list({r["path"]: r for name in PACKET_NAMES for r in packet.json(name)["records"]}.values())
    controls = {}
    for label, suffix, alter in [
        ("rehashed_host_pid", "evidence/minime-host-after.json", lambda value: value.__setitem__("pid", value["pid"] + 1)),
        ("rehashed_loaded_source", "evidence/paired-after/minime/runtime/autonomous_agent_source_status.json",
            lambda value: value["source_inputs_at_start"].__setitem__(next(iter(value["source_inputs_at_start"])), "0" * 64)),
    ]:
        copied = copy.deepcopy(records)
        row = next(r for r in copied if r["path"].endswith(suffix))
        value = json.loads(row["text"]); alter(value)
        raw = encoded(value); row.update(text=raw.decode(), sha256=sha(raw), bytes=len(raw))
        require(all(sha(r["text"].encode()) == r["sha256"] and len(r["text"].encode()) == r["bytes"] for r in copied),
                "Control outer integrity was not valid")
        try:
            resolve_eras(copied, packet.era_definitions)
        except DailyError as exc:
            controls[label] = {"rejected": True, "outer_integrity_valid": True, "error": str(exc)}
        else:
            raise DailyError("Altered cross-evidence binding was accepted: " + label)

    # Qualify a later, genuinely empty synthetic window, never masquerading as a
    # new observation. Keep the same retained release history and no study rows.
    synthetic = args.out / "synthetic-empty-window"; synthetic.mkdir(mode=0o700)
    new_manifest = copy.deepcopy(packet.manifest)
    documents = dict(packet.documents)
    end = epoch(packet.json("capture.json")["selection"]["until_exclusive"])
    lo = datetime.fromtimestamp(end, timezone.utc).isoformat()
    hi = datetime.fromtimestamp(end + 86400, timezone.utc).isoformat()
    for name in PACKET_NAMES:
        value = packet.json(name)
        value["records"] = [r for r in value["records"] if r["kind"] not in ("generation", "job_job.json", "linked_job_job.json", "action", "delivery", "journal", "source_study_failure")]
        if name == "capture.json":
            value["selection"].update(since=lo, until_exclusive=hi)
        documents[name] = encoded(value)
    protocol = packet.json("protocol.json")
    protocol.update(since=lo, until_exclusive=hi, qualification_only="Synthetic empty-window fixture; not an observed daily packet.")
    documents["protocol.json"] = encoded(protocol)
    claims = packet.json("claim-annotations.json"); claims["claims"] = []
    documents["claim-annotations.json"] = encoded(claims)
    for name, raw in documents.items():
        path = synthetic / name
        path.write_bytes(raw); path.chmod(0o600)
        new_manifest["inputs"][name] = dict(path=path.resolve().relative_to(args.data_root.resolve()).as_posix(),
                                          sha256=sha(raw), bytes=len(raw))
    new_manifest["qualification_only"] = True
    write_new_json(synthetic / "inputs.json", new_manifest)
    future = load_packet(synthetic / "inputs.json", args.data_root)
    future_report = build_report(future)
    require(future_report["generation_count"] == 0 and not future_report["close_reading_ids"], "Empty-window selection differs")
    write_new_json(synthetic / "report.json", future_report)
    future_result = verify_report(future, synthetic / "report.json")
    write_new_json(synthetic / "verification.json", future_result)
    sources = list((ROOT / "reservoir_research/daily").glob("*.py"))
    sources += [ROOT / "reservoir_research/daily/era-definitions-v1.json",
                ROOT / "reservoir_research/study_sequences.py", ROOT / "reservoir_research/study_capture.py",
                Path(__file__)]
    receipt = dict(schema="maintained-daily-qualification-v1", golden_report_identical=True,
                   golden_verification_identical=True, golden_claims_identical=True,
                   golden_report_sha256=sha(report_raw), cross_evidence_controls=controls,
                   synthetic_empty_window_verified=True,
                   synthetic_empty_window_source_control=future_result["verification"]["negative_controls"]["missing_wire_source_rejected"],
                   implementation_sha256={str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(sources)},
                   pipeline=result["pipeline"])
    write_new_json(args.out / "qualification.json", receipt)
    print(json.dumps(receipt, indent=2))
if __name__ == "__main__":
    main()
