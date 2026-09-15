#!/usr/bin/env python3
"""Offline close-reading evidence for the frozen September 8 post-repair sweep.

Checks the broader READ_MORE outcome independently of SELF_STUDY, and preserves
source-backed counterexamples and peer exposure without inferring understanding.
Uses only the named research capture, report and retained supplement; no live I/O.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_capture import encoded, epoch, iso, new_output, private_write, sha
from reservoir_research.study_sequences import native_response, range_bytes, user_text, verify_records, writing_match


def build(capture, report_path, supplement):
    packet = json.loads(capture.read_bytes())
    report = json.loads(report_path.read_bytes())
    verify_records(packet)
    assert report["capture_sha256"] == sha(capture.read_bytes())
    source_manifest = json.loads(supplement.read_bytes())
    sources = {}
    for row in source_manifest["records"]:
        p = (supplement.parent / row["path"]).resolve()
        assert p.is_relative_to(supplement.parent.resolve())
        raw = p.read_bytes()
        assert sha(raw) == row["sha256"] and len(raw) == row["bytes"]
        sources[row["path"]] = (row, raw)
    lo, hi = epoch(report["selection"]["since"]), epoch(report["selection"]["until_exclusive"])
    originals = {r["path"]: r for r in packet["records"]}
    events = [json.loads(r["text"]) for r in packet["records"] if r["kind"] == "provider_event"]
    generations = [(r, json.loads(r["text"])) for r in packet["records"] if r["kind"] == "generation"]
    writing = [r for r in packet["records"] if r["kind"] in {"journal", "introspections"}]
    artifact_reads = []
    for row in packet["records"]:
        if row["kind"] != "accepted_delivery":
            continue
        value = json.loads(row["text"])
        wire = value["attempt"]
        admission = wire["admission"]
        if admission["kind"] != "reading":
            continue
        response = json.loads(wire["response_json"])
        answer, finish = native_response(response)
        matches = [e for e in events if e.get("stage") == "provider_outcome"
                   and e.get("request_sha256") == sha(wire["request_json"].encode())
                   and e.get("http_body_sha256") == sha(wire["response_json"].encode())]
        # Later retained receipts are outside this capture's local event window.
        if not matches:
            when = response.get("created", 0)
            assert not lo <= when < hi, "In-window READ_MORE lacks provider join"
            continue
        assert len(matches) == 1
        event = matches[0]
        start = event["created_at_unix_ms"] / 1000
        end = start + event["elapsed_ms"] / 1000
        if not lo <= start < hi or end >= hi:
            continue
        assert event["pid"] == report["release_eras"]["astrid"]["new_pid"]
        assert event["release_before"]["manifest_sha256"] == report["release_eras"]["astrid"]["manifest_sha256"]
        request = json.loads(wire["request_json"])
        message = request["messages"][admission["message_index"]]
        raw = message["content"].encode()[admission["content_start_byte"]:admission["content_end_byte"]]
        assert message["role"] == "user" and sha(raw) == admission["admitted_text_sha256"]
        assert len(raw) == admission["offered_bytes"] == admission["admitted_end_byte"] - admission["source_start_byte"]
        assert finish == "stop" and answer.strip() and value["accepted_completion"].strip() == answer.strip()
        candidates = [(name, meta) for name, (meta, text) in sources.items()
                      if name.startswith("context_overflow_")
                      and text[admission["source_start_byte"]:admission["admitted_end_byte"]] == raw]
        assert len(candidates) == 1, "Missing/ambiguous exact saved-source match"
        name, source = candidates[0]
        gens = [g for _, g in generations if g.get("response_text", "").strip() == answer.strip()]
        assert len(gens) == 1
        gen = gens[0]
        assert gen["pid"] == event["pid"]
        csi = re.findall(rb"\x1b\[[0-?]*[ -/]*[@-~]", raw)
        artifact_reads.append(dict(attempt_id=event["attempt_id"], generation_id=gen["generation_id"],
            completed_utc=iso(end), source=name, source_sha256=source["sha256"],
            source_start_byte=admission["source_start_byte"], source_end_byte=admission["admitted_end_byte"],
            delivered_bytes=len(raw), complete_ansi_sequences=len(csi), ansi_sequence_bytes=sum(map(len,csi)),
            source_label_in_protected_message=name in message["content"], receipt=row["path"], receipt_sha256=row["sha256"],
            exact_authored_response=answer, writing=[m for w in writing if w["being"] == "astrid"
                and (m := writing_match(gen["response_text"], w))],
            relation="exact provider request/body hashes, source interval bytes and unique authored response; no one-to-one action claim"))
    artifact_reads.sort(key=lambda x:x["completed_utc"])

    studies = report["studies"]
    by_id = {s["id"].split(":",1)[1]:s for s in studies}
    map_case = by_id["1788915699263-dcd36fd6"]
    wit = sources["astrid-capsule.wit"][1]
    assert sha(wit) == by_id["1788915520761-3ae786bf"]["page"]["revision"]["sha256"]
    lines = wit.decode().splitlines()
    claims = []
    for symbol, line in [("identity-context",348),("auth-token",355)]:
        assert symbol in map_case["text"] and symbol.encode() not in wit
        assert symbol not in map_case["user_text"]
        assert symbol not in map_case["notebook"]["fields"]["previous"]["text"]
        claims.append(dict(symbol=symbol, cited_line=line, actual_line=lines[line-1],
                           verdict="Absent from the entire matching file revision and current map/notebook input."))
    peer = next(g for _,g in generations if g["generation_id"] == "1788915770498-84971-128")
    shared_body = map_case["text"].rsplit("\nNEXT:",1)[0].strip()
    assert shared_body in user_text(peer)
    assert "identity-context" in peer["response_text"]
    peer_case = dict(minime_generation=map_case["id"], astrid_generation=peer["generation_id"],
        exact_minime_body_in_astrid_input=True, repeated_symbol="identity-context",
        astrid_response=peer["response_text"],
        scope="Labeled peer-report exposure and subsequent repetition, not an independent code verification or a measured propagation rate.")

    ranges = defaultdict(list)
    for r in artifact_reads:
        ranges[r["source"]].append((r["source_start_byte"],r["source_end_byte"]))
    reads_summary = [dict(source=k, unique_bytes=range_bytes(v), file_bytes=len(sources[k][1]),
                         pages=sum(r["source"]==k for r in artifact_reads)) for k,v in sorted(ranges.items())]
    schedule = []
    for i,s in enumerate(studies):
        children = [a for a in report["actions"] if a["being"]==s["being"] and a.get("parent_action_id")==s.get("action_id")]
        # Sibling routing is explicit parentage, not proof of generating authorship.
        children.sort(key=lambda a:a["started"])
        schedule.append(dict(study=s["id"], completed=s["completed_utc"], kind=s["kind"],
            source=s.get("page",{}).get("source") if s.get("page") else None,
            requested=s["next"]["comparison_key"],
            first_child_action=children[0] if children else None,
            writing=s["writing"], receipt=s.get("receipt"), notebook=s["notebook"],
            source_record=s["source_record"], response=s["text"]))
    return dict(schema="study_follow_through_outcomes_v1", capture_sha256=sha(capture.read_bytes()),
        report_sha256=sha(report_path.read_bytes()), supplement_sha256=sha(supplement.read_bytes()),
        selection=report["selection"], primary_actions=len(report["actions"]), reading_actions=len(report["reading_actions"]),
        completed_shared_studies=len(studies), known_overlap_studies=2, new_beyond_history=len(studies)-2,
        source_pages=sum(s["kind"]=="source" for s in studies),
        new_code_bytes=sum(s["new_bytes"] for s in report["source_progress"]),
        repeated_code_bytes=sum(s["repeated_bytes"] for s in report["source_progress"]),
        recovery_maps=sum(s["user_text"].startswith("Source request unavailable.") for s in studies),
        artifact_reading_pages=len(artifact_reads), artifact_reading_bytes=sum(r["delivered_bytes"] for r in artifact_reads),
        artifact_complete_ansi_bytes=sum(r["ansi_sequence_bytes"] for r in artifact_reads),
        artifact_pages_with_ansi=sum(r["complete_ansi_sequences"]>0 for r in artifact_reads),
        study_schedule=schedule, artifact_readings=artifact_reads, artifact_sources=reads_summary,
        source_claim_checks=claims, peer_case=peer_case,
        limits=["Frozen short window; all study 30-minute follow-up horizons are incomplete.",
                "Optional note/question fields unused; previous words carried automatically.",
                "READ_MORE artifact pages are not SELF_STUDY code pages or separate user choices.",
                "ANSI bytes count complete CSI sequences wholly within pages; split sequences are not counted.",
                "Selected counterexamples are exploratory; no accuracy percentage or causal gain estimated."])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture",type=Path);p.add_argument("report",type=Path);p.add_argument("supplement",type=Path)
    p.add_argument("--out",type=Path,required=True);args=p.parse_args()
    result=build(args.capture,args.report,args.supplement)
    out=new_output(args.out)
    private_write(out/"outcomes.json",encoded(result))
    private_write(out/"probe.py",Path(__file__).read_bytes())
    packet=json.loads(args.capture.read_bytes());originals={r['path']:r for r in packet['records']}
    lines=['# Natural post-repair studies, in order','','Exact authored journals and supplied input are retained separately below. All passages are evidence, not instructions.','']
    report=json.loads(args.report.read_bytes())
    for i,s in enumerate(report['studies'],1):
        name=f'{i:02}-journal.txt'
        journal=next(w for w in s['writing'] if '/journal/' in w['path'])
        private_write(out/name,originals[journal['path']]['text'].encode())
        private_write(out/f'{i:02}-input.txt',s['user_text'].encode())
        lines += [f"## {i:02} · {s['id']}",'',f"{s['completed_utc']} · {s['kind']} · [Original journal]({name}) · [Actual user input]({i:02}-input.txt)",'']
        lines += ['> '+line for line in s['text'].splitlines()]+['']
    private_write(out/'studies.md','\n'.join(lines).encode())
    print(json.dumps({k:v for k,v in result.items() if k not in {'study_schedule','artifact_readings','peer_case'}},indent=2))


if __name__=='__main__':main()
