"""Offline S-007 day-8 lineage, helper/prompt eras and notebook/transport compatibility.
Reads only the research repository. Exposure and interpretation remain separate.
"""
import argparse,copy,json,re,sys
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_research.study_capture import sha,epoch,encoded
from reservoir_research.study_sequences import user_text
from source_study_daily_compat import notebook_exposure,failed_wire

def build(p):
    read=lambda name:json.loads((p/name).read_bytes())
    report=read("final-report/report.json");tracking=read("tracking-before.json");protocol=read("protocol.json")
    assert sha((p/"tracking-before.json").read_bytes())==protocol["ledger_sha256"]
    assert tracking["last_completed_cutoff"]==protocol["since"]
    assert tracking["next_window"]["until_exclusive"]==protocol["until_exclusive"]
    history={}
    for window in tracking["windows"]:
        old=(ROOT/window["capture"]).parent
        manifest=json.loads((old/"packet-manifest.json").read_bytes())
        for name,digest in manifest.items():assert sha((old/name).read_bytes())==digest,(old,name)
        history[old.name]=len(manifest)
    week=tracking["first_week_synthesis"]
    assert week["status"]=="complete"
    week_path=ROOT/week["manifest"]
    assert sha(week_path.read_bytes())==week["manifest_sha256"]
    week_manifest=json.loads(week_path.read_bytes())
    for name,digest in week_manifest.items():assert sha((week_path.parent/name).read_bytes())==digest,name
    last=(ROOT/tracking["windows"][-1]["capture"]).parent
    inherited={}
    for name in ["era-supplement.json","source-bindings.json","catchup-era.json","catchup-activation.json","catchup-bindings.json","new-era.json","new-era-validation.json","new-era-bindings.json"]:
        raw=(p/name).read_bytes();assert raw==(last/name).read_bytes();inherited[name]=sha(raw)
    studies=report["studies"];ids=[s["id"] for s in studies]
    assert len(ids)==len(set(ids)) and not set(ids)&set(tracking["seen_generations"])
    old_report=read("preliminary-v4-report/report.json")
    assert old_report["close_reading_ids"]==report["close_reading_ids"]
    for a,b in zip(old_report["studies"],studies,strict=True):
        assert {k:v for k,v in a.items() if k!="notebook"}=={k:v for k,v in b.items() if k!="notebook"}
        if a["notebook"]["status"]!="malformed":assert a["notebook"]==b["notebook"]
    helper=read("helper-era.json")
    assert not helper["errors"]
    records={r["relative"]:r for r in helper["records"]}
    for r in records.values():assert sha(r["text"].encode())==r["sha256"] and len(r["text"].encode())==r["bytes"]
    get=lambda name:json.loads(records[name]["text"])
    releases=[]
    def clock(s):return datetime.strptime(s,"%a %b %d %H:%M:%S %Y").replace(tzinfo=ZoneInfo("America/Los_Angeles")).timestamp()
    for prefix,activation in [("","activation-transaction/receipt.json"),("separator-","separator-activation-receipt.json")]:
        manifest=get(prefix+"stage-manifest.json");inputs=get(prefix+"stage-inputs.json")
        act=get(activation);host=get(prefix+"minime-host-after.json");audit=get(prefix+"activation-independent-audit.json")
        manifest_hash=records[prefix+"stage-manifest.json"]["sha256"]
        assert audit["status"]=="passed" and not audit["errors"] and audit["manifest_sha256"]==manifest_hash
        assert act["status"]=="activated_verified" and act["activation_performed"]
        assert manifest["source_inputs"]["sha256"]==records[prefix+"stage-inputs.json"]["sha256"]
        assert act["new_process"]["deployment_identity"].split(":")[1]==manifest["repository"]["head"]
        assert host["pid"]==37507 and host["changed"]==[] and host["startup_inputs"]==82
        assert host["selected_helper"]==manifest["artifacts"]["source-study-reader"]["path"]
        assert host["selected_helper_sha256"]==manifest["artifacts"]["source-study-reader"]["sha256"]
        template=records[manifest["repository"]["head"]+"-prompt.txt"]
        candidates=[f for f in inputs["files"] if f["path"].endswith("/crates/astrid-source-study/prompt.txt")]
        assert len(candidates)==1 and candidates[0]["sha256"]==template["sha256"]
        adapted=sha(("You are Minime.\n"+template["text"]).encode())
        releases.append(dict(name="source-context"+("-separator" if prefix else ""),commit=manifest["repository"]["head"],
            boundary=clock(act["new_process"]["started_at"]),bridge_pid=act["new_process"]["pid"],minime_pid=host["pid"],
            selection_checked_at=host.get("captured_at",host.get("at")),helper_sha256=host["selected_helper_sha256"],
            manifest_sha256=manifest_hash,adapted_prompt_sha256=adapted))
    prior=read("prior-prompt.json")
    assert sha(prior["text"].encode())==prior["sha256"]
    assert sha(("You are Minime.\n"+prior["text"]).encode())==prior["adapted_minime_sha256"]
    assert releases[0]["adapted_prompt_sha256"]==releases[1]["adapted_prompt_sha256"]
    source_rows=[s for s in studies if s["actual_route"]=="source_study"]
    hashes={prior["adapted_minime_sha256"]:"catalog-navigation",releases[0]["adapted_prompt_sha256"]:"source-context"}
    arm_rows=[]
    for s in studies:
        assert s["pid"]==37507
        family="private-writing" if s["actual_route"]=="extended_writing" else hashes[tuple(s["system_hashes"])[0]]
        assert len(s["system_hashes"])==1
        start=epoch(s["started_utc"]);end=epoch(s["completed"])
        stage="catalog-navigation"
        for rel in releases:
            if end>=rel["boundary"]:stage=rel["name"]
        crossings=[rel["name"] for rel in releases if start<rel["boundary"]<=end]
        arm_rows.append(dict(id=s["id"],prompt_family=family,completion_clock_stratum=stage,crosses_helper_boundary=crossings))
    source_counts=Counter()
    for source in report["sources"]:source_counts[source["repository"]]+=source["page_opportunities"]
    own=next((s for s in studies if s["receipt_verified"] and any(page["source"].startswith("minime/") for page in s["pages"])),None)
    # Exactly parsed additive metadata is not scored as verified authored truth.
    assert all(s["notebook"]["status"]=="included_in_submitted_user_text" for s in source_rows)
    with_findings=[s for s in source_rows if "source_findings" in s["notebook"]["fields"]]
    authored_present=sum(bool(s["notebook"]["fields"].get("source_findings",{}).get("authored")) for s in source_rows)
    sample=next(s for s in with_findings)
    fields=copy.deepcopy(sample["notebook"]["fields"]);fields["unknown_field"]=True
    text=sample["user_text"];a=sample["notebook"]["start"];b=sample["notebook"]["end"];body=text.find("\n",a+2)+1
    bad=text[:body]+json.dumps(fields)+text[b:]
    assert notebook_exposure(bad)["status"]=="malformed"
    supplement=read("supplement.json")
    failures=[r for r in supplement["records"] if r["kind"]=="source_study_failure"]
    transport=next(r for r in failures if json.loads(r["text"])["source_study_failure"]=="transport_error")
    t=json.loads(transport["text"]);s=next(s for s in source_rows if s["backend_timing"].get("source_study_diagnostic_path")==transport["path"])
    assert failed_wire(t,s,user_text)["response_absent"]
    bad=copy.deepcopy(t);bad["response"]={"text":"invented response"}
    try:failed_wire(bad,s,user_text)
    except AssertionError:pass
    else:raise AssertionError("Invented transport response accepted")
    bad=copy.deepcopy(t);bad["request"]["text"]+="tampered"
    try:failed_wire(bad,s,user_text)
    except AssertionError:pass
    else:raise AssertionError("Altered failed request accepted")
    # Carry of the selected note is distinct from correctness of the note.
    third=next(s for s in studies if s["id"]==report["close_reading_ids"][2])
    after=studies[studies.index(third)+1]
    note=next(line[len("STUDY_NOTE: "):] for line in third["text"].splitlines() if line.startswith("STUDY_NOTE: "))
    assert after["notebook"]["fields"]["note"]["text"]==note
    assert after["action_text"]==third["next_action"] and after["receipt_verified"]
    # Captured active selection is a later release; do not assign it to this cohort.
    direction=read("direction-era.json");recovery=read("post-cutoff-recovery.json")
    for record in direction["records"]+recovery["records"]:
        assert sha(record["text"].encode())==record["sha256"] and len(record["text"].encode())==record["bytes"]
    original=json.loads(next(r["text"] for r in direction["records"] if r["path"].endswith("/receipt.json")))
    review=json.loads(next(r["text"] for r in recovery["records"] if r["relative"].endswith("direction-activation-review.json")))
    assert original["status"]=="failed_requires_review" and epoch(original["recorded_at"])>epoch(protocol["until_exclusive"])
    assert review["status"]=="passed" and review["checks"]["recovery_completed"]
    active=json.loads(next(r["text"] for r in read("capture.json")["records"] if r["path"].endswith("/bridge-deployment/active.json")))
    manifest=next(r for r in direction["records"] if r["path"].endswith("/manifest.json"))
    assert active["manifest_sha256"]==manifest["sha256"]
    return dict(schema="s007_daily_context_verification_v1",prior_ledger_sha256=protocol["ledger_sha256"],
        preserved_historical_files=history,historical_files=sum(history.values()),week_one_files=len(week_manifest),
        prior_generations=len(tracking["seen_generations"]),new_generations=len(ids),resulting_generations=len(ids)+len(tracking["seen_generations"]),
        duplicate_ids=[],inherited_release_hashes=inherited,source_page_opportunities_by_repository=dict(source_counts),
        own_repository_followup=dict(selection=protocol["followup"],observed=own is not None,generation=own),
        helper_releases=releases,generation_era_rows=arm_rows,prompt_families=dict(Counter(r["prompt_family"] for r in arm_rows)),
        completion_clock_strata=dict(Counter(r["completion_clock_stratum"] for r in arm_rows)),
        helper_boundary_crossings=[r for r in arm_rows if r["crosses_helper_boundary"]],
        source_notebooks=len(source_rows),additive_source_findings_inputs=len(with_findings),inputs_with_retained_authored_findings=authored_present,
        compatibility=dict(original_v4_labels=dict(Counter(s["notebook"]["status"] for s in old_report["studies"])),final_labels=dict(Counter(s["notebook"]["status"] for s in studies)),first_three_and_non_notebook_fields_unchanged=True),
        selected_note_carry=dict(from_id=third["id"],to_id=after["id"],next_action=third["next_action"],text=note,correctness="Not established by retention"),
        after_cutoff_selection=dict(manifest_sha256=active["manifest_sha256"],source=review["source_head"],status="original failure retained; owning recovery review passed",reviewed_at=review["reviewed_at"],next_window_review_required=True),
        negative_controls=dict(unknown_notebook_field_rejected=True,invented_transport_response_rejected=True,altered_failed_request_rejected=True),
        limits=["Helper clock strata do not identify the binary of every in-flight invocation. Initial and separator releases share one exact prompt; new prompt exposure cannot distinguish their binaries.",
        "Source-linked findings are authored interpretations. Inclusion and save receipts do not validate their content.",
        "The after-cutoff direction cohort is excluded; its evidence is next-window context. No exhaustive later-correction search or improvement score."])

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("packet",type=Path);args=a.parse_args()
    assert args.packet.resolve().is_relative_to(ROOT/"research/outputs")
    data=build(args.packet)
    with (args.packet/"context-verification.json").open("xb") as f:f.write(encoded(data))
    print(json.dumps({k:v for k,v in data.items() if k not in ["generation_era_rows","inherited_release_hashes"]},indent=2))
