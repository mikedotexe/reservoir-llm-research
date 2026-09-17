"""Bounded S-006/S-008 research follow-ups. Standard library; no source execution.

All source reads are explicit, stable and bounded. Captures are append-only research
files. Semantic judgments remain evidence-coded review, never a keyword score.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "bounded_research_followups_v1"
RUN_KEYS = ("schema", "run_id", "actor", "adapter_kind", "started_at", "finished_at", "status", "outcome", "exit_code", "requested_outcome")
PACKET_NAMES = ("RUN_REPORT.md", "read_manifest.json", "source_receipts.json", "addressing_links.json", "test_results.json", "unprocessed_selected.json", "verification_receipt.json")
RUN_RE = re.compile(r"run_(\d{10,19})_[A-Za-z0-9_-]+\.json$")
PROVIDER_RE = re.compile(r"provider-(\d{13})-[A-Za-z0-9_-]+-(dispatch|outcome)\.json$")
DAILY_RE = re.compile(r"\d{4}-\d{2}-\d{2}-source-study-fidelity-day\d+$")


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def epoch(value):
    if isinstance(value, (float, int)):
        return float(value)
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Explicit timezone required")
    return stamp.timestamp()


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as stream:
        stream.write(encoded(value))
    path.chmod(0o600)


def source_path(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Relative path traversal refused")
    path = root / relative
    if path.resolve() != path or not path.is_relative_to(root):
        raise ValueError("Symlink or noncanonical path refused")
    return path


class Reader:
    def __init__(self, total=256*1024*1024, file_limit=8*1024*1024, entries=20000, seconds=150):
        self.total_limit, self.file_limit, self.entry_limit = total, file_limit, entries
        self.seconds, self.started, self.bytes = seconds, time.monotonic(), 0
        self.inventories, self.errors = [], []

    def read(self, path, limit=None):
        path = Path(path)
        if path.resolve() != path or path.is_symlink():
            raise ValueError("Symlink or noncanonical source refused")
        if time.monotonic() - self.started > self.seconds:
            raise ValueError("Capture time cap")
        cap = self.file_limit if limit is None else min(limit, self.file_limit)
        before = path.stat()
        if not path.is_file() or before.st_size > cap:
            raise ValueError("Per-file cap or nonregular source")
        if self.bytes + before.st_size > self.total_limit:
            raise ValueError("Total read cap")
        with path.open("rb") as stream:
            raw = stream.read(cap + 1)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(raw) != before.st_size:
            raise ValueError("Source changed during read")
        self.bytes += len(raw)
        return raw

    def names(self, folder):
        folder = Path(folder)
        if folder.resolve() != folder or folder.is_symlink():
            raise ValueError("Noncanonical directory")
        names, start = [], time.monotonic()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    if len(names) >= self.entry_limit or time.monotonic()-start > 10:
                        raise ValueError("Directory inventory cap; no exhaustive selection possible")
                    names.append(entry.name)
        except (OSError, ValueError) as exc:
            self.inventories.append(dict(path=str(folder), entries=len(names), complete=False))
            raise exc
        self.inventories.append(dict(path=str(folder), entries=len(names), complete=True))
        return sorted(names)

    def error(self, path, error):
        self.errors.append(dict(path=str(path), error=str(error)))


def retained(path, raw, kind, **extra):
    return dict(path=str(path), kind=kind, bytes=len(raw), sha256=sha(raw), text=raw.decode(), **extra)


def check_records(records):
    for row in records:
        raw = row["text"].encode()
        if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
            raise ValueError("Captured record hash mismatch")


def validate_protocol(p):
    assert p["schema"] == SCHEMA and p["qualification"]["passed"] is True
    start = epoch(p["t0"])
    assert epoch(p["frozen_at"]) < start
    assert epoch(p["intake_end"]) == start + 7*86400
    assert epoch(p["final_end"]) == start + 9*86400
    assert epoch(p["provider_end"]) == start + 86400
    assert p["run_limit"] == 10 and p["provider_attempt_limit"] == 5000
    assert p["exposure_limit"] == 3 and p["followup_seconds"] == 48*3600
    assert p["provider_collection_allowance_seconds"] == 120
    assert p["allowlist"]["authority"] == "read_only_existing_files_no_source_commands"
    assert set(p["cases"]) == {"worker-single-item", "comment-as-call"}
    return p


def capture_runs(protocol, now, reader=None):
    """Read existing controller/packet files only, never invoke queue or controller."""
    p = validate_protocol(protocol); reader = reader or Reader()
    start, end = epoch(p["t0"]), epoch(p["intake_end"])
    if now < start:
        return dict(status="awaiting_window", records=[], errors=[], inventories=[], selected_run_ids=[])
    root = Path(p["allowlist"]["astrid_root"]).resolve()
    runs = source_path(root, p["allowlist"]["runs_directory"])
    notes = source_path(root, p["allowlist"]["notes_directory"])
    records, candidates = [], []
    try:
        names = reader.names(runs)
    except (OSError, ValueError) as exc:
        reader.error(runs, exc); names = []
    for name in names:
        match = RUN_RE.fullmatch(name)
        if not match:
            continue
        digits = match[1]
        stamp = int(digits) / (10 ** (len(digits)-10))
        if not start-1 <= stamp < min(end, now)+1:
            continue
        path = source_path(runs, name)
        try:
            raw = reader.read(path); data = json.loads(raw)
            if data.get("schema") != "steward_run_receipt_v1":
                raise ValueError("Unknown controller receipt schema")
            if not start <= epoch(data["started_at"]) < min(end, now):
                continue
            if data["run_id"] + ".json" != name:
                raise ValueError("Controller ID differs from filename")
            projection = {k:data.get(k) for k in RUN_KEYS}
            projection["original_source_sha256"] = sha(raw)
            # Lease/token fields never enter the retained projection.
            if data.get("actor") != p["unattended_actor"] or data.get("adapter_kind") != "subprocess":
                records.append(retained(path,encoded(projection),"excluded_controller_projection"))
                continue
            candidates.append((epoch(data["started_at"]), data["run_id"], path, projection))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            reader.error(path, exc)
    candidates.sort(key=lambda x:(x[0],x[1]))
    selected = candidates[:p["run_limit"]]
    for _, _, path, projection in selected:
        records.append(retained(path, encoded(projection), "controller_projection"))
    selected_ids = {row[1] for row in selected}
    try:
        names = reader.names(notes) if selected_ids else []
    except (OSError, ValueError) as exc:
        reader.error(notes, exc); names = []
    for name in names:
        match = re.fullmatch(r"claude-heartbeat_(\d{10})_[A-Za-z0-9_.-]+", name)
        if not match or not start <= int(match[1]) <= min(now, epoch(p["final_end"])):
            continue
        folder = source_path(notes, name)
        receipt_path = source_path(folder, "verification_receipt.json")
        if not receipt_path.exists():
            # An in-progress round need not have published its final packet yet.
            continue
        try:
            raw = reader.read(receipt_path); receipt = json.loads(raw)
            run_id = receipt.get("controller", {}).get("run_id")
            if run_id not in selected_ids:
                continue
            if receipt.get("schema") != "flywheel_verification_receipt_v1":
                raise ValueError("Unknown round receipt schema")
            for child in PACKET_NAMES:
                path = source_path(folder, child)
                try:
                    body = raw if child == "verification_receipt.json" else reader.read(path)
                    # Recursively omit authority tokens from JSON receipts, preserving original hash.
                    if child.endswith(".json"):
                        data = json.loads(body)
                        def clean(value):
                            if isinstance(value, dict):
                                return {k:clean(v) for k,v in value.items() if not re.search(r"token|secret|credential",k,re.I)}
                            if isinstance(value, list): return [clean(v) for v in value]
                            return value
                        safe = encoded(clean(data))
                    else:
                        safe = body
                    records.append(retained(path, safe, "round_packet", run_id=run_id, original_source_sha256=sha(body)))
                except (OSError, ValueError, TypeError) as exc:
                    reader.error(path, exc)
            for childdir in ["claims", "summaries"]:
                directory = source_path(folder, childdir)
                if not directory.exists(): continue
                children = reader.names(directory)
                if len(children) > 40:
                    raise ValueError("More than 40 claim/summary files")
                for child in children:
                    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(json|md)",child): continue
                    path = source_path(directory, child)
                    records.append(retained(path, reader.read(path), "round_claim", run_id=run_id))
            manifests = [x for x in records if x.get("run_id")==run_id and x["path"].endswith("/read_manifest.json")]
            for manifest in manifests:
                data = json.loads(manifest["text"])
                for report in data.get("reports", []):
                    rel = report.get("path", "")
                    if not re.fullmatch(r"capsules/spectral-bridge/workspace/introspections/introspection_[A-Za-z0-9_.-]+\.txt",rel):
                        reader.error(rel,"Original report outside frozen allowlist"); continue
                    path = source_path(root,rel)
                    body = reader.read(path)
                    if sha(body) != report["sha256"]: raise ValueError("Original report differs from declared read hash")
                    records.append(retained(path,body,"original_report",run_id=run_id))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            reader.error(receipt_path, exc)
    return dict(status="captured_with_gaps" if reader.errors else "captured", records=records, errors=reader.errors,
                inventories=reader.inventories, selected_run_ids=[x[1] for x in selected], eligible_run_count=len(candidates))


def capture_provider(protocol, now, reader=None):
    p = validate_protocol(protocol); reader = reader or Reader()
    start, end = epoch(p["t0"]), epoch(p["provider_end"])
    if now < start:
        return dict(status="awaiting_window",records=[],errors=[],inventories=[])
    spool = Path(p["allowlist"]["provider_spool"]).resolve()
    folder = source_path(spool,"events")
    records, dispatches = [], []
    try: names = reader.names(folder)
    except (OSError,ValueError) as exc:
        reader.error(folder,exc); names=[]
    for name in names:
        match = PROVIDER_RE.fullmatch(name)
        if not match or match[2] != "dispatch" or not start*1000 <= int(match[1]) < min(end,now)*1000:
            continue
        path = source_path(folder,name)
        try:
            raw=reader.read(path); data=json.loads(raw)
            if data.get("schema") != "provider_attempt_observation_v1" or data.get("stage") != "dispatch_started":
                raise ValueError("Unknown provider dispatch schema")
            if data["attempt_id"]+"-dispatch.json" != name or int(data["created_at_unix_ms"]) != int(match[1]):
                raise ValueError("Provider filename/identity mismatch")
            dispatches.append((data["created_at_unix_ms"],data["attempt_id"],path,raw,data))
        except (OSError,ValueError,KeyError,TypeError) as exc: reader.error(path,exc)
    dispatches.sort(key=lambda x:(x[0],x[1]))
    if len(dispatches)>p["provider_attempt_limit"]:
        reader.error(folder,"Provider attempt cap; selection is partial")
    for _,aid,path,raw,dispatch in dispatches[:p["provider_attempt_limit"]]:
        records.append(retained(path,raw,"provider_dispatch"))
        path=source_path(folder,aid+"-outcome.json")
        if not path.exists(): continue
        try:
            raw=reader.read(path); outcome=json.loads(raw)
            if outcome.get("schema") != "provider_attempt_observation_v1" or outcome.get("stage") != "provider_outcome":
                raise ValueError("Unknown provider outcome schema")
            for key in ["attempt_id","pid","created_at_unix_ms","request_sha256","provider"]:
                if outcome.get(key)!=dispatch.get(key): raise ValueError("Provider dispatch/outcome mismatch")
            completed=(outcome["created_at_unix_ms"]+outcome["elapsed_ms"])/1000
            if completed >= end+p["provider_collection_allowance_seconds"]:
                records.append(retained(path,encoded(dict(attempt_id=aid,completed=completed,original_sha256=sha(raw))),"late_provider_outcome"))
                continue
            records.append(retained(path,raw,"provider_outcome"))
            if outcome.get("raw_artifact"):
                rel=outcome["raw_artifact"]
                if not re.fullmatch(r"raw/[0-9a-f]{64}\.txt",rel): raise ValueError("Raw artifact outside allowlist")
                rawpath=source_path(spool,rel); body=reader.read(rawpath,256*1024)
                if sha(body)!=outcome["raw_response_sha256"]: raise ValueError("Raw response hash mismatch")
                records.append(retained(rawpath,body,"provider_raw",attempt_id=aid))
        except (OSError,ValueError,KeyError,TypeError) as exc: reader.error(path,exc)
    return dict(status="captured_with_gaps" if reader.errors else "captured",records=records,errors=reader.errors,inventories=reader.inventories)


def analyze_runs(protocol, captures, now):
    latest, packets, excluded, errors = {}, {}, {}, []
    for capture in captures:
        check_records(capture["records"]); errors.extend(capture["errors"])
        for row in capture["records"]:
            if row["kind"]=="controller_projection":
                value=json.loads(row["text"]); latest[value["run_id"]]=value
            elif row["kind"]=="excluded_controller_projection":
                value=json.loads(row["text"]); excluded[value["run_id"]]=value
            elif row["kind"]=="round_packet": packets[(row["run_id"],Path(row["path"]).name)]=row
    ordered=sorted(latest.values(),key=lambda x:(epoch(x["started_at"]),x["run_id"]))[:protocol["run_limit"]]
    results=[]
    for run in ordered:
        rid=run["run_id"]; deadline=epoch(run["started_at"])+protocol["followup_seconds"]
        finished=epoch(run["finished_at"]) if run.get("finished_at") else None
        q=packets.get((rid,"unprocessed_selected.json")); selected=None
        if q:
            data=json.loads(q["text"])
            if data.get("schema")!="flywheel_unprocessed_selected_v1": raise ValueError("Unknown queue summary schema")
            processed=data.get("processed",[]); unprocessed=data.get("unprocessed_in_queue_order",[])
            if len(processed)+len(unprocessed)!=data["selected_count"] or len(set(processed+unprocessed))!=data["selected_count"]:
                raise ValueError("Queue summary counts or IDs inconsistent")
            selected=dict(processed=processed,unprocessed=unprocessed,selected_count=data["selected_count"],stop_reason=data.get("stop_reason"))
        results.append(dict(run_id=rid,started_at=run["started_at"],followup_end=iso(deadline),
            terminal_state="right_censored" if not finished or finished>=deadline else run["outcome"],
            elapsed_seconds=(finished-epoch(run["started_at"])) if finished and finished<deadline else None,
            declared_status=run["status"],queue=selected,queue_missing=selected is None,
            interpretation="awaiting_evidence_coded_episode_review",deployment="not_established",benefit="unmeasured"))
    intake_closed=len(results)==protocol["run_limit"] or now>=epoch(protocol["intake_end"])
    deadlines=[epoch(x["followup_end"]) for x in results]
    temporal_done=intake_closed and now>=max(deadlines,default=epoch(protocol["intake_end"]))
    return dict(status="coverage_blocked" if errors else "ready_for_review" if temporal_done else "observing",
        intake_closed=intake_closed,followup_closed=temporal_done,runs=results,run_count=len(results),errors=errors,
        excluded_actor_counts=dict(Counter(str(x.get("actor")) for x in excluded.values())),
        limits="Controller success is not a productive change; packet classifications and deployment/benefit need separate evidence.")


def analyze_provider(protocol,captures,now):
    dispatch,outcomes,raws,errors={},{},{},[]
    for cap in captures:
        check_records(cap["records"]); errors.extend(cap["errors"])
        for row in cap["records"]:
            if row["kind"]=="provider_dispatch":
                d=json.loads(row["text"])
                if d["attempt_id"] in dispatch and dispatch[d["attempt_id"]]!=d: raise ValueError("Immutable dispatch changed")
                dispatch[d["attempt_id"]]=d
            elif row["kind"]=="provider_outcome":
                d=json.loads(row["text"])
                if d["attempt_id"] in outcomes and outcomes[d["attempt_id"]]!=d: raise ValueError("Immutable outcome changed")
                outcomes[d["attempt_id"]]=d
            elif row["kind"]=="provider_raw": raws[row["attempt_id"]]=row["sha256"]
    for aid,d in outcomes.items():
        if aid not in dispatch: raise ValueError("Outcome lacks selected dispatch")
        for key in ["pid","request_sha256","provider","created_at_unix_ms"]:
            if d.get(key)!=dispatch[aid].get(key): raise ValueError("Captured provider identity mismatch")
        if d.get("raw_artifact") and raws.get(aid)!=d.get("raw_response_sha256"):
            errors.append(dict(path=aid,error="Raw artifact missing or unverifiable"))
    end=epoch(protocol["provider_end"])+protocol["provider_collection_allowance_seconds"]
    unknown=[aid for aid,d in outcomes.items() if d.get("marker_observed_total") is None]
    markers=[aid for aid,d in outcomes.items() if (d.get("marker_observed_total") or 0)>0]
    bindings=Counter(d.get("release_before",{}).get("manifest_sha256","unknown") for d in dispatch.values())
    return dict(status="coverage_blocked" if errors else "ready_for_review" if now>=end else "observing",
        window_closed=now>=end,dispatches=len(dispatch),outcomes=len(outcomes),pending_attempts=sorted(set(dispatch)-set(outcomes)),
        unknown_marker_inputs=unknown,marker_bearing_attempts=markers,release_manifests=dict(bindings),
        outcome_counts=dict(Counter(d.get("outcome","unknown") for d in outcomes.values())),errors=errors,
        exposure="requires_independent_release_binding",repair_benefit="unmeasured",
        limits="The frozen spool is an observation surface, not an exhaustive provider denominator; absence without current coverage proof is not zero opportunity.")


def load_daily_packet(folder,reader):
    folder=Path(folder)
    manifest_raw=reader.read(folder/"packet-manifest.json",1024*1024)
    manifest=json.loads(manifest_raw)
    report_raw=reader.read(folder/"final-report/report.json")
    if manifest.get("final-report/report.json")!=sha(report_raw): raise ValueError("Daily report is not sealed at its declared hash")
    verification_raw=reader.read(folder/"verification.json",1024*1024)
    verification=json.loads(verification_raw)
    if manifest.get("verification.json")!=sha(verification_raw): raise ValueError("Daily verification receipt is not sealed")
    if verification.get("report_sha256")!=sha(report_raw) or verification.get("replay_identical") is not True:
        raise ValueError("Daily report lacks a matching successful offline verification")
    report=json.loads(report_raw)
    if report.get("schema") not in {f"source_study_fidelity_daily_v{x}" for x in [2,3,4,5,6]}:
        raise ValueError("Unknown daily report schema")
    if report.get("capture_errors") or report.get("join_issues") or any("unverified-pid" in x.get("era","") for x in report["studies"]):
        raise ValueError("Daily packet has unresolved coverage or host-era errors")
    return report,dict(path=str(folder),manifest_sha256=sha(manifest_raw),report_sha256=sha(report_raw),verification_sha256=sha(verification_raw))


def exposure_basis(case,study):
    if study.get("actual_route")!="source_study" or not study.get("receipt_verified"):
        return []
    basis=[]; nb=study.get("notebook",{})
    if nb.get("status")=="malformed": raise ValueError("Unknown notebook schema")
    fields=nb.get("fields",{})
    if case["quote"] in json.dumps(fields,ensure_ascii=False): basis.append("exact_claim_in_notebook")
    if case.get("saved_note_origin_sha256") and (fields.get("note") or {}).get("response_sha256")==case["saved_note_origin_sha256"]:
        basis.append("same_authored_saved_note_origin")
    for page in study.get("pages",[]):
        if page.get("source")!=case["source"]: continue
        if page.get("revision",{}).get("sha256")==case["source_sha256"] and page["start"]["byte"]<=case["critical_byte_start"] and page["end"]["byte"]>=case["critical_byte_end"]:
            basis.append("verified_anchor_source_interval")
        elif page.get("revision",{}).get("sha256")!=case["source_sha256"]:
            # Daily reports intentionally retain metadata, not page text. Do not
            # infer equivalent evidence from the source path or reused line numbers.
            basis.append("changed_source_revision_requires_review")
    return sorted(set(basis))


def analyze_durable(protocol,packets,now):
    validate_protocol(protocol); reader=Reader(total=512*1024*1024,file_limit=64*1024*1024,seconds=300)
    if len(packets)>10: raise ValueError("At most ten explicit daily packets")
    studies,provenance={},[]
    for packet in packets:
        report,identity=load_daily_packet(packet,reader); provenance.append(identity)
        for study in report["studies"]:
            if not epoch(protocol["t0"])<=epoch(study["completed"])<min(epoch(protocol["final_end"]),now): continue
            if study["id"] in studies and studies[study["id"]]!=study: raise ValueError("Duplicate generation identity changed")
            studies[study["id"]]=study
    ordered=sorted(studies.values(),key=lambda x:(epoch(x["completed"]),x["id"]))
    notebooks=[]
    for s in ordered:
        n=s.get("notebook",{})
        if n.get("status")=="malformed": raise ValueError("Notebook schema requires review")
        if n.get("status")=="included_in_submitted_user_text":
            notebooks.append(dict(generation_id=s["id"],completed=s["completed"],record_sha256=s["record_sha256"],
                notebook_sha256=n["sha256"],field_identity={k:sha(encoded(v)) for k,v in n["fields"].items()},
                note_origin=(n["fields"].get("note") or {}).get("response_sha256"),
                retention="Exact fields remain in the sealed referenced daily report; hashes identify every observed version."))
    cases={}
    for key,case in protocol["cases"].items():
        eligible=[]; unresolved=[]
        for s in ordered:
            basis=exposure_basis(case,s)
            if "changed_source_revision_requires_review" in basis:
                unresolved.append(dict(generation_id=s["id"],completed=s["completed"],record_sha256=s["record_sha256"],
                    source_pages=[page for page in s.get("pages",[]) if page.get("source")==case["source"]]))
                # An independently carried exact claim remains observable; changed
                # source alone cannot establish exposure to contrary evidence.
                basis=[x for x in basis if x!="changed_source_revision_requires_review"]
            if epoch(s["completed"])>=epoch(protocol["intake_end"]): continue
            if basis:
                eligible.append(dict(generation_id=s["id"],completed=s["completed"],basis=basis,
                    record_sha256=s["record_sha256"],response_sha256=s["response_sha256"],
                    response_text=s["text"],user_text_sha256=sha(s["user_text"].encode()),
                    system_hashes=s["system_hashes"],era=s["era"],pid=s["pid"],
                    followup_end=iso(min(epoch(s["completed"])+protocol["followup_seconds"],epoch(protocol["final_end"])))))
        selected=eligible[:protocol["exposure_limit"]]
        followups=[]
        for initial in selected:
            subsequent=[s for s in ordered if epoch(initial["completed"])<epoch(s["completed"])<epoch(initial["followup_end"]) and any(b!="changed_source_revision_requires_review" for b in exposure_basis(case,s))]
            followups.append(dict(generation_id=initial["generation_id"],next_relevant_generations=[s["id"] for s in subsequent[:2]],
                horizon_closed=now>=epoch(initial["followup_end"]),shortfall=max(0,2-len(subsequent))))
        cases[key]=dict(anchor=case["anchor_generation"],historical_storage=case["historical_storage"],selected=selected,
            eligible_exposures=len(eligible),followups=followups,correction="not_adjudicated",revision_review_candidates=unresolved,
            selection_final=not unresolved,
            status="source_revision_review_required" if unresolved else "awaiting_evidence_coded_review" if selected else "no_eligible_exposure_yet" if now<epoch(protocol["intake_end"]) else "no_eligible_exposure_in_supplied_packets")
    return dict(status="observing" if now<epoch(protocol["final_end"]) else "ready_for_coverage_and_claim_review",
        packet_inputs=provenance,cases=cases,notebook_versions=notebooks,unique_generations=len(studies),
        coverage="Only explicit sealed daily packets; missing days and incomplete horizons must be reviewed before any absence conclusion.",
        limits="Eligibility retrieves evidence. Source revision patterns need review; neither changed text nor a saved note proves correction.")


def validate_correction_review(review,protocol,durable):
    """Strict evidence requirements for a human/agent-coded correction, no auto-scoring."""
    if review.get("schema")!="durable_correction_review_v1": raise ValueError("Unknown review schema")
    key=review["case"]; case=protocol["cases"][key]
    if durable["cases"][key].get("selection_final") is not True:
        raise ValueError("Unresolved source revisions prevent a final selected-sample judgment")
    selected={x["generation_id"]:x for x in durable["cases"][key]["selected"]}
    if review["generation_id"] not in selected: raise ValueError("Review outside selected sample")
    if review["response_sha256"]!=selected[review["generation_id"]]["response_sha256"]: raise ValueError("Review response hash differs")
    if not review.get("quote") or review["quote"] not in selected[review["generation_id"]]["response_text"]:
        raise ValueError("Exact selected response quote required")
    if review.get("durable_correction_observed"):
        if case["historical_storage"]!="saved_note": raise ValueError("No established historical false saved note")
        if not review.get("explicit_supported_revision") or not review.get("saved_revision_sha256"):
            raise ValueError("Explicit supported saved revision required")
        ids=review.get("later_relevant_generation_ids",[])
        allowed=next(x["next_relevant_generations"] for x in durable["cases"][key]["followups"] if x["generation_id"]==review["generation_id"])
        if len(ids)!=2 or len(set(ids))!=2 or ids!=allowed[:2]: raise ValueError("Two preselected later exposures required")
        if review.get("reassertion_observed") is not False or len(review.get("later_saved_revision_hashes",[]))!=2 or any(h!=review["saved_revision_sha256"] for h in review["later_saved_revision_hashes"]):
            raise ValueError("Saved revision persistence and no reassertion required")
        notebooks={x["generation_id"]:x for x in durable["notebook_versions"]}
        if any(notebooks.get(ident,{}).get("field_identity",{}).get("note")!=review["saved_revision_sha256"] for ident in ids):
            raise ValueError("Saved revision hash is not present in actual later notebook inputs")
        if review["saved_revision_sha256"]==case.get("historical_saved_note_sha256"):
            raise ValueError("Unchanged historical note is not a saved correction")
    return True
