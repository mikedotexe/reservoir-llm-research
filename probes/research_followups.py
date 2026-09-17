#!/usr/bin/env python3
"""Qualify, freeze and observe bounded S-006/S-008 protocols; research writes only."""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_research.research_followups import (SCHEMA, encoded, sha, epoch, iso, exclusive_json, validate_protocol,
    capture_runs, capture_provider, analyze_runs, analyze_provider, analyze_durable, load_daily_packet, Reader, DAILY_RE)

FILES=["reservoir_research/research_followups.py","probes/research_followups.py","tests/test_research_followups.py"]


def code_identity():
    return {n:sha((ROOT/n).read_bytes()) for n in FILES}


def output_path(value):
    path=Path(value).resolve()
    if not path.is_relative_to(ROOT/"research/outputs"):
        raise ValueError("Output must be in research/outputs")
    return path


def qualify(out):
    out=output_path(out)
    if out.exists(): raise ValueError("Qualification output already exists")
    before=code_identity()
    result=subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","tests","-p","test_research_followups.py","-v"],
        cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),capture_output=True,timeout=120)
    log=result.stdout+result.stderr
    out.mkdir(mode=0o700,parents=True)
    (out/"tests.log").write_bytes(log); (out/"tests.log").chmod(0o600)
    receipt=dict(schema="bounded_followups_qualification_v1",recorded_at=iso(time.time()),passed=result.returncode==0,
        exit_code=result.returncode,code=before,code_unchanged=before==code_identity(),test_log_sha256=sha(log),
        scope="Isolated standard-library fixtures only. No live source reads, model calls, service operations or source writes.")
    if not receipt["code_unchanged"]: receipt["passed"]=False
    exclusive_json(out/"qualification.json",receipt)
    print(json.dumps(receipt,indent=2))
    return 0 if receipt["passed"] else 1


def anchors():
    reader=Reader(total=128*1024*1024,file_limit=64*1024*1024)
    definitions=[("worker-single-item","2026-09-10-source-study-fidelity-day2","1788979002676-a5e5e6c0","1788979138281-ac81dc62","day2-single-item"),
        ("comment-as-call","2026-09-13-source-study-fidelity-day5","1789238215387-9a53ef13","1789238351900-b6ce3b1b","day5-comment-as-call")]
    cases,evidence={},[]
    for key,folder,ident,later,claim_id in definitions:
        base=ROOT/"research/outputs"/folder
        report,provenance=load_daily_packet(base,reader)
        source=json.loads((base/"claim-annotations.json").read_bytes())
        manifest=json.loads((base/"packet-manifest.json").read_bytes())
        assert sha((base/"claim-annotations.json").read_bytes())==manifest["claim-annotations.json"]
        claim=next(c for c in source["claims"] if c["id"]==claim_id)
        first=next(s for s in report["studies"] if s["id"]==ident)
        next_row=next(s for s in report["studies"] if s["id"]==later)
        assert claim["generation_id"]==ident and claim["quote"] in first["text"]
        fields=next_row["notebook"]["fields"]
        if key=="worker-single-item":
            assert not any(line.startswith(("STUDY_NOTE:","STUDY_FINDING:")) for line in first["text"].splitlines())
            assert claim["quote"] not in fields["previous"]["text"] and "excerpt truncated" in fields["previous"]["text"]
            page=first["pages"][0]
            storage="authored_prose_not_established_in_saved_note"
            note_origin=None
            explanation="No authored note/finding update in the anchor. The next prompt's previous-response excerpt truncates before this exact assertion; older generic note remains."
            tokens=["while let Some(work)","rx.recv().await"]
        else:
            assert "This line is part of the `handle_watchdog_tick` interceptor." in fields["note"]["text"]
            assert fields["note"]==first["notebook"]["fields"]["note"]
            assert not any(line.startswith(("STUDY_NOTE:","STUDY_FINDING:")) for line in next_row["text"].splitlines())
            page=next_row["pages"][0]; storage="saved_note"; note_origin=fields["note"]["response_sha256"]
            explanation="A source-navigation note preserves the interceptor premise. Reopened-source prose calls it a comment, while the note remains unchanged and no note/finding update is authored."
            tokens=["///","handle_watchdog_tick","check_phase_timeout"]
        cases[key]=dict(anchor_generation=ident,known_followup_generation=later,claim_id=claim_id,quote=claim["quote"],
            anchor_response_sha256=first["response_sha256"],historical_storage=storage,storage_explanation=explanation,
            historical_saved_note_sha256=sha(encoded(fields["note"])) if storage=="saved_note" else None,
            saved_note_origin_sha256=note_origin,source=page["source"],source_sha256=page["revision"]["sha256"],
            critical_byte_start=page["start"]["byte"],critical_byte_end=page["end"]["byte"],source_tokens=tokens,
            source_packet=provenance,annotation_sha256=sha((base/"claim-annotations.json").read_bytes()))
        evidence.append(dict(case=key,anchor_record_sha256=first["record_sha256"],followup_record_sha256=next_row["record_sha256"],
            quote=claim["quote"],anchor_response=first["text"],known_followup_response=next_row["text"],
            anchor_notebook=first["notebook"],known_followup_notebook=next_row["notebook"]))
    return cases,evidence


def register(out,qualification):
    out=output_path(out); qpath=output_path(qualification)
    q=json.loads(qpath.read_bytes())
    assert q["schema"]=="bounded_followups_qualification_v1" and q["passed"] and q["code_unchanged"]
    assert q["code"]==code_identity()
    assert sha((qpath.parent/"tests.log").read_bytes())==q["test_log_sha256"]
    if out.exists(): raise ValueError("Study directory already exists")
    cases,evidence=anchors()
    frozen=time.time(); start=int(frozen)+60
    protocol=dict(schema=SCHEMA,frozen_at=iso(frozen),t0=iso(start),intake_end=iso(start+7*86400),
        final_end=iso(start+9*86400),provider_end=iso(start+86400),run_limit=10,unattended_actor="claude-heartbeat",
        followup_seconds=48*3600,provider_attempt_limit=5000,provider_collection_allowance_seconds=120,exposure_limit=3,
        qualification=dict(path=str(qpath.relative_to(ROOT)),sha256=sha(qpath.read_bytes()),passed=True),code=q["code"],cases=cases,
        allowlist=dict(authority="read_only_existing_files_no_source_commands",astrid_root="/Users/v/other/astrid",
            runs_directory="capsules/spectral-bridge/workspace/diagnostics/steward_control_v1/runs",
            notes_directory="docs/steward-notes",packet_directories="claude-heartbeat_<unix>_<name>; selected controller run ID required",
            packet_files=["RUN_REPORT.md","read_manifest.json","source_receipts.json","addressing_links.json","test_results.json","unprocessed_selected.json","verification_receipt.json","claims/*.{json,md}","summaries/*.{json,md}"],
            original_reports="Only exact introspection_*.txt references in selected read_manifest.json, matching its hash",
            provider_spool="/Users/v/other/astrid/capsules/spectral-bridge/workspace/provider_observations/20260908-live-01",
            provider_files="events/provider-<ms>-<pid>-<seq>-dispatch/outcome.json in fixed window; exact raw/<sha256>.txt references only",
            excluded=["lease.json","authority tokens","databases","source executables","model/services","recursive workspace scans","automatic provider-spool substitution"]),
        limits=dict(live_file_bytes=8*1024*1024,live_capture_bytes=256*1024*1024,live_capture_seconds=150,directory_entries=20000,directory_seconds=10,
            raw_artifact_bytes=256*1024,research_daily_report_bytes=64*1024*1024,research_refresh_bytes=512*1024*1024,research_daily_packets=10),
        daily_packet_selection="Explicit sealed S007 daily packet directories from T0 UTC date through final_end UTC date; no S007 ledger or selection edits.",
        success="Complete bounded provenance and explicit shortfalls. Productive review, eligible natural repair benefit and durable semantic correction require separate evidence-coded assessment.",
        stop="No replacement runs, claims, retries or broadened source scopes to obtain a positive result. New paths/schema require a separately recorded amendment.")
    validate_protocol(protocol)
    out.mkdir(mode=0o700,parents=True)
    exclusive_json(out/"anchors.json",dict(schema="bounded_followups_historical_anchors_v1",cases=cases,evidence=evidence))
    protocol["anchors_sha256"]=sha((out/"anchors.json").read_bytes())
    exclusive_json(out/"protocol.json",protocol)
    exclusive_json(out/"registration.json",dict(schema="bounded_followups_registration_v1",protocol_sha256=sha((out/"protocol.json").read_bytes()),
        registered_at=iso(time.time()),status="registered_awaiting_window",live_reads_performed=False,code=code_identity()))
    print(json.dumps({k:protocol[k] for k in ["t0","intake_end","provider_end","final_end"]},indent=2))


def load_protocol(study):
    study=output_path(study); raw=(study/"protocol.json").read_bytes(); p=validate_protocol(json.loads(raw))
    reg=json.loads((study/"registration.json").read_bytes())
    assert reg["protocol_sha256"]==sha(raw) and p["code"]==code_identity()
    assert p["anchors_sha256"]==sha((study/"anchors.json").read_bytes())
    return study,p,sha(raw)


def packet_inputs(protocol):
    lo=datetime.fromtimestamp(epoch(protocol["t0"]),timezone.utc).date().isoformat()
    hi=datetime.fromtimestamp(epoch(protocol["final_end"]),timezone.utc).date().isoformat()
    result=[]
    for path in sorted((ROOT/"research/outputs").iterdir()):
        if DAILY_RE.fullmatch(path.name) and lo<=path.name[:10]<=hi and (path/"packet-manifest.json").is_file(): result.append(path)
    if len(result)>10: raise ValueError("Daily packet input cap")
    return result


def refresh(study):
    study,p,ph=load_protocol(study); now=time.time()
    runs=capture_runs(p,now); provider=capture_provider(p,now)
    checkpoint=dict(schema="bounded_followups_capture_v1",captured_at=iso(now),protocol_sha256=ph,runs=runs,provider=provider)
    previous=[]
    for path in sorted(study.glob("capture-*.json")):
        old=json.loads(path.read_bytes()); assert old["protocol_sha256"]==ph; previous.append(old)
    durable=analyze_durable(p,packet_inputs(p),now)
    result=dict(schema="bounded_followups_status_v1",as_of=iso(now),protocol_sha256=ph,
        s006_runs=analyze_runs(p,[x["runs"] for x in previous]+[runs],now),
        s006_provider=analyze_provider(p,[x["provider"] for x in previous]+[provider],now),s008_durable=durable,
        future_observation_complete=False,interpretation="Pending bounded observation and evidence-coded review; no automatic semantic benefit claim.")
    name="capture-"+datetime.fromtimestamp(now,timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json"
    exclusive_json(study/name,checkpoint)
    status_name=name.replace("capture-","status-")
    exclusive_json(study/status_name,result)
    receipt=dict(schema="bounded_followups_checkpoint_v1",capture=name,capture_sha256=sha((study/name).read_bytes()),
        status=status_name,status_sha256=sha((study/status_name).read_bytes()),protocol_sha256=ph)
    exclusive_json(study/name.replace("capture-","receipt-"),receipt)
    print(json.dumps(dict(checkpoint=name,as_of=result["as_of"],runs=result["s006_runs"]["status"],provider=result["s006_provider"]["status"],durable=durable["status"],run_count=result["s006_runs"]["run_count"],dispatches=result["s006_provider"]["dispatches"]),indent=2))


def verify(study):
    study,p,ph=load_protocol(study); previous=[]; count=0
    for path in sorted(study.glob("receipt-*.json")):
        receipt=json.loads(path.read_bytes()); assert receipt["protocol_sha256"]==ph
        capraw=(study/receipt["capture"]).read_bytes(); statraw=(study/receipt["status"]).read_bytes()
        assert sha(capraw)==receipt["capture_sha256"] and sha(statraw)==receipt["status_sha256"]
        cap=json.loads(capraw); status=json.loads(statraw); previous.append(cap); now=epoch(status["as_of"])
        assert cap["protocol_sha256"]==status["protocol_sha256"]==ph
        assert analyze_runs(p,[x["runs"] for x in previous],now)==status["s006_runs"]
        assert analyze_provider(p,[x["provider"] for x in previous],now)==status["s006_provider"]
        paths=[Path(x["path"]) for x in status["s008_durable"]["packet_inputs"]]
        assert all(x.resolve().is_relative_to(ROOT/"research/outputs") for x in paths)
        assert analyze_durable(p,paths,now)==status["s008_durable"]
        count+=1
    print(json.dumps(dict(verified=True,checkpoints=count,scope="Offline replay; no live source reads or efficacy claim."),indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest="command",required=True)
    q=sub.add_parser("qualify");q.add_argument("--out",required=True)
    q=sub.add_parser("register");q.add_argument("--out",required=True);q.add_argument("--qualification",required=True)
    for name in ["refresh","verify"]:
        q=sub.add_parser(name);q.add_argument("--study",required=True)
    a=parser.parse_args()
    if a.command=="qualify":return qualify(a.out)
    if a.command=="register":register(a.out,a.qualification)
    if a.command=="refresh":refresh(a.study)
    if a.command=="verify":verify(a.study)
    return 0


if __name__=="__main__":sys.exit(main())
