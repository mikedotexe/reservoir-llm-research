"""Offline S-007 day-9 helper context and independent host-era verification.
Only retained research packet bytes are read. Unknown source prompts/PIDs/notebook schemas fail.
"""
import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_research.study_capture import encoded, sha, epoch
from source_study_daily_compat import notebook_exposure
from source_study_daily_eras_v6 import clock, interface_release

SOURCE_CONTEXT = "6a1fa13e6f13a9f61b39e9dabd07764ea5df83b00830b7bdf0a53945494273b5"
DIRECTION = "6be5d66520914812695fdba7962d7bc6f541e0d3cf1626ae7935c2a3948b6112"
PRIVATE = "7d6510ae9537726f136d6ad58c4a2ffac7fbcf79d84de644918b32b51e51256f"
INHERITED = ["era-supplement.json","source-bindings.json","catchup-era.json","catchup-activation.json","catchup-bindings.json","new-era.json","new-era-validation.json","new-era-bindings.json"]
CONTEXT = ["helper-era.json","direction-era.json","post-cutoff-recovery.json","prior-prompt.json","direction-prompt-binding.json","interface-era.json","private-prompt-history.json"]

def checked_records(packet):
    assert not packet["errors"]
    records = packet["records"]
    assert len({r["path"] for r in records}) == len(records)
    for r in records:
        raw = r["text"].encode()
        assert sha(raw) == r["sha256"] and len(raw) == r["bytes"], r["path"]
    return records

def prompt_family(route, hashes):
    assert len(hashes) == 1, "exactly one system prompt required"
    if route == "extended_writing":
        assert hashes[0] == PRIVATE, "unknown private-writing prompt"
        return "private-writing"
    assert route == "source_study", "unknown route"
    names = {SOURCE_CONTEXT:"source-context", DIRECTION:"study-direction-and-interface"}
    assert hashes[0] in names, "unknown source-study prompt"
    return names[hashes[0]]

def source_context_releases(packet):
    rows = checked_records(packet)
    records = {r["relative"]:r for r in rows}
    get = lambda name: json.loads(records[name]["text"])
    releases = []
    for prefix, activation in [("","activation-transaction/receipt.json"),("separator-","separator-activation-receipt.json")]:
        manifest = get(prefix+"stage-manifest.json"); inputs = get(prefix+"stage-inputs.json")
        act = get(activation); host = get(prefix+"minime-host-after.json"); audit = get(prefix+"activation-independent-audit.json")
        mh = records[prefix+"stage-manifest.json"]["sha256"]
        assert audit["status"] == "passed" and not audit["errors"] and audit["manifest_sha256"] == mh
        assert act["status"] == "activated_verified" and act["activation_performed"]
        if "manifest_sha256" in act: assert act["manifest_sha256"] == mh
        assert act["new_process"]["deployment_identity"].split(":")[3] == manifest["artifacts"]["spectral-bridge"]["sha256"]
        assert manifest["source_inputs"]["sha256"] == records[prefix+"stage-inputs.json"]["sha256"]
        assert act["new_process"]["deployment_identity"].split(":")[1] == manifest["repository"]["head"]
        assert host["pid"] == 37507 and host["changed"] == [] and host["startup_inputs"] == 82
        assert host["selected_helper"] == manifest["artifacts"]["source-study-reader"]["path"]
        assert host["selected_helper_sha256"] == manifest["artifacts"]["source-study-reader"]["sha256"]
        template = records[manifest["repository"]["head"]+"-prompt.txt"]
        candidates = [f for f in inputs["files"] if f["path"].endswith("/crates/astrid-source-study/prompt.txt")]
        assert len(candidates) == 1 and candidates[0]["sha256"] == template["sha256"]
        adapted = sha(("You are Minime.\n"+template["text"]).encode())
        assert adapted == SOURCE_CONTEXT
        releases.append(dict(name="source-context"+("-separator" if prefix else ""),commit=manifest["repository"]["head"],
            boundary=clock(act["new_process"]["started_at"]),bridge_pid=act["new_process"]["pid"],minime_pid=host["pid"],
            selection_checked_at=host.get("captured_at",host.get("at")),helper_sha256=host["selected_helper_sha256"],
            manifest_sha256=mh,source_prompt_sha256=template["sha256"],adapted_prompt_sha256=adapted))
    return releases

def direction_release(direction, recovery, binding):
    ds = checked_records(direction); rs = checked_records(recovery); bs = checked_records(binding)
    original_row = next(r for r in ds if r["path"].endswith("/receipt.json"))
    original = json.loads(original_row["text"])
    manifest_row = next(r for r in ds if r["path"].endswith("/manifest.json"))
    manifest = json.loads(manifest_row["text"])
    review = json.loads(next(r["text"] for r in rs if r["relative"].endswith("direction-activation-review.json")))
    host = json.loads(next(r["text"] for r in rs if r["relative"].endswith("minime-host-after.json")))
    act = json.loads(next(r["text"] for r in rs if "stopped-transition-recoveries/" in r["relative"] and r["relative"].endswith("/receipt.json")))
    assert original["status"] == "failed_requires_review" and not original["activation_performed"]
    assert act["status"] == "transition_recovered" and act["activation_performed"]
    assert not any(act[k] for k in ["signal_sent","drain_requested","force_used"])
    assert act["original_failure_sha256"] == original_row["sha256"]
    assert act["manifest_sha256"] == original["manifest_sha256"] == manifest_row["sha256"] == host["manifest_sha256"]
    assert review["status"] == "passed" and not review["material_gaps"] and all(review["checks"].values())
    assert review["source_head"] == manifest["repository"]["head"] == act["new_process"]["deployment_identity"].split(":")[1]
    assert host["pid"] == 37507 and host["startup_inputs"] == 82 and host["changed"] == []
    assert host["selected_helper_sha256"] == review["helper_sha256"] == manifest["artifacts"]["source-study-reader"]["sha256"]
    byname = {r["relative"]:r for r in bs}
    assert byname["stage/manifest.json"]["sha256"] == manifest_row["sha256"]
    assert byname["stage/source-inputs.json"]["sha256"] == manifest["source_inputs"]["sha256"]
    template = byname["evidence/natural/released-prompt.txt"]
    inputs = json.loads(byname["stage/source-inputs.json"]["text"])
    candidates = [f for f in inputs["files"] if f["path"].endswith("/crates/astrid-source-study/prompt.txt")]
    assert len(candidates) == 1 and candidates[0]["sha256"] == template["sha256"] == review["prompt_source_sha256"]
    adapted = sha(("You are Minime.\n"+template["text"]).encode())
    assert adapted == DIRECTION
    return dict(name="study-direction",commit=review["source_head"],boundary=clock(act["new_process"]["started_at"]),
        bridge_pid=act["new_process"]["pid"],minime_pid=37507,selection_checked_at=host["at"],
        helper_sha256=host["selected_helper_sha256"],manifest_sha256=manifest_row["sha256"],
        source_prompt_sha256=template["sha256"],adapted_prompt_sha256=adapted,
        original_failed_activation_at=original["recorded_at"],recovery_completed_at=act["recorded_at"],
        independent_review_at=review["reviewed_at"])

def rejects(fn):
    try: fn()
    except (AssertionError, KeyError, ValueError, TypeError): return True
    return False

def build(folder):
    p = Path(folder)
    read = lambda name: json.loads((p/name).read_bytes())
    protocol = read("protocol.json"); assert protocol["day"] == 9
    assert protocol["since"] == "2026-09-16T18:34:00Z" and protocol["until_exclusive"] == "2026-09-17T18:34:00Z"
    assert protocol["ledger_sha256"] == sha((p/"ledger-before.json").read_bytes())
    report = read("final-report/report.json"); before = read("preliminary-v5-report/report.json")
    assert report["schema"] == "source_study_fidelity_daily_v6"
    assert report["close_reading_ids"] == before["close_reading_ids"]
    assert len(report["studies"]) == len(before["studies"])
    for a,b in zip(before["studies"],report["studies"],strict=True):
        assert {k:v for k,v in a.items() if k not in ["era","transitions"]} == {k:v for k,v in b.items() if k not in ["era","transitions"]}
    lineage = read("historical-lineage.json")
    assert lineage, "historical lineage receipt missing"
    inherited = {name:sha((p/name).read_bytes()) for name in INHERITED}
    source_context = source_context_releases(read("helper-era.json"))
    direction = direction_release(read("direction-era.json"),read("post-cutoff-recovery.json"),read("direction-prompt-binding.json"))
    interface_packet = read("interface-era.json"); interface_records = checked_records(interface_packet)
    interface = interface_release(interface_records)
    assert report["release_eras"]["study-interface-sep17"] == interface
    interface_rows = {r["relative"]:r for r in interface_records}
    for index in [1,2]:
        inventory = json.loads(interface_rows[f"bridge-stage-0{index}/source-inputs.json"]["text"])
        prompts = [f for f in inventory["files"] if f["path"].endswith("/crates/astrid-source-study/prompt.txt")]
        assert len(prompts) == 1 and prompts[0]["sha256"] == direction["source_prompt_sha256"]
    initial = interface["astrid"]
    releases = source_context + [direction]
    for name,boundary,commit,pid,manifest in [
        ("study-interface-stage01",initial["boundary"],initial["commit"],initial["new_pid"],initial["manifest_sha256"]),
        ("study-interface-stage02",initial["final_stage"]["boundary"],initial["final_stage"]["commit"],initial["final_stage"]["new_pid"],initial["final_stage"]["manifest_sha256"])]:
        releases.append(dict(name=name,boundary=boundary,commit=commit,bridge_pid=pid,
            helper_sha256=interface["helper_sha256"],manifest_sha256=manifest,
            source_prompt_sha256=direction["source_prompt_sha256"],adapted_prompt_sha256=DIRECTION,
            selection_limit="same prompt and helper bytes in both interface stages; preparation identity must not be inferred"))
    history = read("private-prompt-history.json")
    record = history["record"]; raw = record["text"].encode()
    assert sha(raw) == record["sha256"] and len(raw) == record["bytes"]
    historical_generation = json.loads(record["text"])
    assert history["recorded_route"] == "extended_writing" and history["expected_system_sha256"] == PRIVATE
    assert [m["content_sha256"] for m in historical_generation["messages"] if m["role"] == "system"] == [PRIVATE]
    prior = read("prior-prompt.json")
    assert sha(prior["text"].encode()) == prior["sha256"]
    assert sha(("You are Minime.\n"+prior["text"]).encode()) == prior["adapted_minime_sha256"]
    studies = report["studies"]; ids = [s["id"] for s in studies]
    tracking = read("tracking-before.json")
    assert len(ids) == len(set(ids)) and not set(ids).intersection(tracking["seen_generations"])
    source_rows = [s for s in studies if s["actual_route"] == "source_study"]
    rows = []
    for s in studies:
        family = prompt_family(s["actual_route"],s["system_hashes"])
        start,end = epoch(s["started_utc"]),epoch(s["completed"])
        expected_pid = 71419 if end >= interface["minime"]["boundary"] else 37507
        assert s["pid"] == expected_pid and "unverified-pid" not in s["era"]
        assert epoch(protocol["since"]) <= end < epoch(protocol["until_exclusive"])
        if family == "study-direction-and-interface": assert end >= direction["boundary"]
        strata = [rel["name"] for rel in releases if end >= rel["boundary"]]
        crossings = [rel["name"] for rel in releases if start < rel["boundary"] <= end]
        notebook = notebook_exposure(s["user_text"])
        assert notebook == s["notebook"] and notebook["status"] != "malformed"
        if s["actual_route"] == "source_study":
            assert notebook["status"] == "included_in_submitted_user_text"
        rows.append(dict(id=s["id"],pid=s["pid"],host_era=s["era"],prompt_family=family,
            system_sha256=s["system_hashes"][0],completion_clock_stratum=strata[-1],
            crosses_helper_boundary=crossings,
            delivered_line_header_present=bool(re.search(r"Exact source bytes \d+\.\.\d+ \(end exclusive\)\. Delivered source lines",s["user_text"])),
            finding_capacity_header_present="FINDING CAPACITY —" in s["user_text"],
            notebook_status=notebook["status"]))
    own = next((s for s in source_rows if s["receipt_verified"] and any(page["source"].startswith("minime/") for page in s["pages"])),None)
    own_result = dict(selection=protocol["followup"],observed=own is not None,generation_id=own["id"] if own else None,
        record_sha256=own["record_sha256"] if own else None,reason=None if own else "No verified Minime-owned numbered source page occurs in this fixed window.")
    # In-memory negative controls do not modify any historical or daily evidence.
    assert rejects(lambda: prompt_family("source_study",["0"*64]))
    assert rejects(lambda: prompt_family("extended_writing",[DIRECTION]))
    bad = copy.deepcopy(interface_records)
    hostrow = next(r for r in bad if r["relative"] == "evidence/minime-host-after.json")
    value = json.loads(hostrow["text"]); value["pid"] = 99999
    hostrow["text"] = json.dumps(value); hostrow["bytes"] = len(hostrow["text"].encode()); hostrow["sha256"] = sha(hostrow["text"].encode())
    assert rejects(lambda: interface_release(bad))
    bad = copy.deepcopy(read("direction-prompt-binding.json"))
    row = next(r for r in bad["records"] if r["relative"] == "evidence/natural/released-prompt.txt")
    row["text"] += "\nAltered prompt"; row["bytes"] = len(row["text"].encode()); row["sha256"] = sha(row["text"].encode())
    assert rejects(lambda: direction_release(read("direction-era.json"),read("post-cutoff-recovery.json"),bad))
    sample = source_rows[0]["user_text"]; n = notebook_exposure(sample)
    body_start = sample.find("\n",n["start"]+2)+1
    changed = copy.deepcopy(n["fields"]); changed["unknown_future_field"] = True
    altered = sample[:body_start]+json.dumps(changed)+sample[n["end"]:]
    assert notebook_exposure(altered)["status"] == "malformed"
    changed = copy.deepcopy(n["fields"]); changed["source_findings"] = {"authored":[],"supplied_locations":[],"updates":[],"unknown":True}
    altered = sample[:body_start]+json.dumps(changed)+sample[n["end"]:]
    assert notebook_exposure(altered)["status"] == "malformed"
    return dict(schema="s007_daily_context_verification_v2",status="verified",
        protocol_sha256=sha((p/"protocol.json").read_bytes()),report_sha256=sha((p/"final-report/report.json").read_bytes()),
        prior_ledger_sha256=protocol["ledger_sha256"],historical_lineage_sha256=sha((p/"historical-lineage.json").read_bytes()),
        inherited_release_hashes=inherited,context_packet_hashes={name:sha((p/name).read_bytes()) for name in CONTEXT},
        prior_generations=len(tracking["seen_generations"]),new_generations=len(ids),resulting_generations=len(ids)+len(tracking["seen_generations"]),duplicate_ids=[],
        first_three_unchanged=True,all_non_era_study_fields_unchanged=True,
        helper_releases=releases,host_release=interface,
        generation_era_rows=rows,prompt_families=dict(Counter(x["prompt_family"] for x in rows)),
        completion_clock_strata=dict(Counter(x["completion_clock_stratum"] for x in rows)),
        helper_boundary_crossings=[x for x in rows if x["crosses_helper_boundary"]],
        process_counts=dict(Counter(str(s["pid"]) for s in studies)),
        source_notebooks=len(source_rows),source_notebook_status=dict(Counter(s["notebook"]["status"] for s in source_rows)),
        supplied_interface_markers=dict(delivered_line_headers=sum(x["delivered_line_header_present"] for x in rows),finding_capacity_headers=sum(x["finding_capacity_header_present"] for x in rows)),
        own_repository_followup=own_result,
        negative_controls=dict(unknown_source_prompt_rejected=True,incorrect_private_prompt_rejected=True,
            rehashed_false_host_mapping_rejected=True,rehashed_altered_prompt_rejected=True,
            unknown_notebook_root_field_rejected=True,unknown_source_findings_field_rejected=True),
        limits=["Clock strata do not identify the binary or preparation time of every in-flight invocation.",
            "Source-context and separator share one prompt; direction and interface share another. Interface stage01/stage02 share helper bytes, but only stage02 has the complete pre-build input witness.",
            "Recorded Minime loaded source identity is independent of selected shared helper identity. No current checkout or host PID is used as proof of historical prompt exposure.",
            "Input framing and notebook inclusion are transport observations, not verification of authored source findings or improvement in understanding.",
            "No exhaustive later-correction search or new live reads; selection and first-three sample remain frozen."])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("packet",type=Path); parser.add_argument("--check",action="store_true"); args=parser.parse_args()
    result = build(args.packet); raw = encoded(result); path = args.packet/"context-verification.json"
    if args.check: assert path.read_bytes() == raw
    else:
        with path.open("xb") as f: f.write(raw)
        path.chmod(0o600)
    print(json.dumps({k:v for k,v in result.items() if k not in ["generation_era_rows","inherited_release_hashes","helper_releases","host_release"]},indent=2))
