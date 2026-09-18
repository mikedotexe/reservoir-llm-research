"""Offline generic S-007 context verification from a frozen typed definition.

Host releases, selected helpers, exact prompt exposure and clock strata are separate.
Historical probes and the maintained reporting core remain unchanged.
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
from reservoir_research.study_sequences import user_text
from reservoir_research.daily.inputs import DailyError, require
from reservoir_research.daily.eras import resolve_eras
from reservoir_research.daily.compat import notebook_exposure
from source_study_daily_context_v2 import source_context_releases, direction_release

ERA_PACKETS = ["era-supplement.json", "catchup-era.json", "catchup-activation.json",
               "new-era.json", "new-era-validation.json", "interface-era.json"]
PRIVATE_OLD = "7d6510ae9537726f136d6ad58c4a2ffac7fbcf79d84de644918b32b51e51256f"
PRIVATE_NEW = "2b0bce76ad7fbca246a0840aab9abd7b6f0136e24f972c1d8686a0730aaa423e"


def checked_records(packet):
    require(not packet["errors"], "Context input has capture errors")
    rows = packet["records"]
    require(len({r["path"] for r in rows}) == len(rows), "Duplicate context paths")
    for row in rows:
        raw = row["text"].encode()
        require(sha(raw) == row["sha256"] and len(raw) == row["bytes"], "Context record bytes differ")
    return rows


def private_binding(packet, review):
    require(packet["schema"] == "s007_private_prompt_binding_v1", "Unknown private binding")
    rows = {r["relative"]: r for r in checked_records(packet)}
    owner = json.loads(rows["manifest.json"]["text"])
    manifest = {r["path"]: r for r in owner["files"]}
    require(rows["manifest.json"]["sha256"] == review["owning_manifest"]["sha256"], "Owning manifest differs")
    for name in ["source/astrid-interface.patch", "evidence/qualified-helper.json",
                 "bridge-stage-02/source-inputs.json", "bridge-stage-02/manifest.json"]:
        require(rows[name]["sha256"] == manifest[name]["sha256"] == review["retained_release_inputs"][name]["sha256"], "Private source binding differs")
        require(rows[name]["bytes"] == manifest[name]["bytes"], "Private source length differs")
    patch = rows["source/astrid-interface.patch"]["text"]
    prompts = {}
    for sign, digest in [("-", PRIVATE_OLD), ("+", PRIVATE_NEW)]:
        literals = re.findall(r"^" + re.escape(sign) + r'const PROMPT: &str = "(.*)";$', patch, re.M)
        require(len(literals) == 1, "Private prompt literal is ambiguous")
        exact = "You are Minime.\n" + literals[0]
        require(sha(exact.encode()) == digest, "Reviewed private prompt literal changed")
        require(review["prompts"][digest]["text"] == exact, "Private review and literal differ")
        require(review["prompts"][digest]["sha256"] == digest and review["prompts"][digest]["bytes"] == len(exact.encode()), "Private review identity differs")
        prompts[digest] = exact
    stage = json.loads(rows["bridge-stage-02/manifest.json"]["text"])
    inputs = json.loads(rows["bridge-stage-02/source-inputs.json"]["text"])
    qualified = json.loads(rows["evidence/qualified-helper.json"]["text"])
    require(stage["source_inputs"]["sha256"] == rows["bridge-stage-02/source-inputs.json"]["sha256"], "Private stage inventory differs")
    writing = [r for r in inputs["files"] if r["path"].endswith("/crates/astrid-source-study/src/writing.rs")]
    require(len(writing) == 1, "Ambiguous writing source inventory")
    require(writing[0]["sha256"] == qualified["source_files"]["crates/astrid-source-study/src/writing.rs"] == review["source_file"]["sha256"], "Qualified writing source differs")
    require(stage["artifacts"]["source-study-reader"]["sha256"] == review["helper_sha256"], "Reviewed helper identity differs")
    return prompts, dict(source_sha256=writing[0]["sha256"], helper_sha256=review["helper_sha256"],
        stage_manifest_sha256=rows["bridge-stage-02/manifest.json"]["sha256"],
        full_source_bytes_retained=False, per_invocation_helper_identity="unestablished")


def prompt_family(route, hashes, variants):
    require(len(hashes) == 1, "Exactly one system prompt is required")
    require(hashes[0] in variants, "Unknown submitted system prompt")
    variant = variants[hashes[0]]
    require(route == variant["route"], "Prompt family and route contradict")
    return variant["family"]


def host_mapping(start, end, pid, eras, basepid):
    active, expected, transitions = "shared-reader", basepid, []
    for name, era in eras.items():
        if end >= era["minime"]["boundary"]:
            active, expected = name, era["minime"]["new_pid"]
        if start < era["minime"]["boundary"] <= end:
            transitions.append(name + ":process")
        if start < era["astrid"]["boundary"] <= end or era["astrid"]["boundary"] <= end < era["minime"]["boundary"]:
            transitions.append(name + ":shared-helper")
    require(pid == expected, "Generation host PID lacks verified release mapping")
    return active + (":transition" if transitions else ""), transitions


def rejects(fn):
    try:
        fn()
    except (AssertionError, DailyError, KeyError, ValueError, TypeError, StopIteration):
        return True
    return False


def build_outputs(folder, report_path="final-report/report.json"):
    require(not sys.flags.optimize, "Context verification requires Python without -O")
    folder = Path(folder).resolve()
    definition_raw = (folder / "context-definition.json").read_bytes()
    definition = json.loads(definition_raw)
    require(definition["schema"] == "s007_daily_context_definition_v1", "Unknown context definition")
    require(set(definition) == {"schema", "frozen_at", "authority", "inputs", "host", "helper", "prompts", "timing", "notebook", "selection", "unknowns"}, "Unknown context definition field")
    require(definition["host"] == {"validator": "maintained-era-registry-v1", "definitions": "context-era-definitions.json"}, "Unknown host definition")
    require(definition["helper"]["validator"] == "retained-source-context-direction-interface-v1", "Unknown helper definition")
    require(definition["notebook"] == {"validator": "maintained-structured-notebook-compatibility-v1", "unknown_fields": "block"}, "Unknown notebook definition")
    documents, input_hashes, total = {}, {}, 0
    for name, item in definition["inputs"].items():
        require(Path(name).name == name and set(item) == {"sha256", "bytes"}, "Unsafe context input")
        path = folder / name
        require(not path.is_symlink() and path.stat().st_size <= 256*1024*1024, "Unsafe or oversized context input")
        raw = path.read_bytes(); total += len(raw)
        require(total <= 512*1024*1024, "Context input byte limit")
        require(sha(raw) == item["sha256"] and len(raw) == item["bytes"], "Frozen context input differs: " + name)
        input_hashes[name] = item["sha256"]
        documents[name] = json.loads(raw)
    read = lambda name: documents[name]
    rp = (folder / report_path).resolve()
    require(rp.is_relative_to(folder) and rp.is_file() and rp.stat().st_size <= 64*1024*1024, "Unsafe report path")
    report_raw = rp.read_bytes(); report = json.loads(report_raw)
    protocol, tracking = read("protocol.json"), read("tracking-before.json")
    require(report["schema"] == "source_study_fidelity_daily_v6", "Unknown report schema")
    require(report["selection"] == protocol, "Report selection differs from frozen protocol")
    require(protocol["ledger_sha256"] == input_hashes["tracking-before.json"] == input_hashes["ledger-before.json"] and read("ledger-before.json") == tracking, "Prior ledger differs")
    require(tracking["last_completed_cutoff"] == protocol["since"], "Prior cutoff differs")
    require(report["capture_sha256"] == input_hashes["capture.json"] and report["supplement_sha256"] == input_hashes["supplement.json"], "Report capture identity differs")
    require(not report["capture_errors"] and not report["join_issues"], "Report contains unresolved capture or join errors")
    base = checked_records(read("capture.json"))
    require(read("capture.json")["selection"]["since"] == protocol["since"] and read("capture.json")["selection"]["until_exclusive"] == protocol["until_exclusive"], "Capture window differs")
    selectors = [selector for spec in read("context-era-definitions.json") for selector in spec["records"].values()]
    def selected_era_record(row):
        return any(row["path"] == s.get("path") or ("suffix" in s and row["path"].endswith(s["suffix"])) for s in selectors)
    era_records = [r for r in base + checked_records(read("supplement.json")) if selected_era_record(r)]
    for name in ERA_PACKETS: era_records += checked_records(read(name))
    unique = {}
    for r in era_records:
        require(r["path"] not in unique or unique[r["path"]]["sha256"] == r["sha256"], "Contradictory retained release versions")
        unique[r["path"]] = r
    eras = resolve_eras(list(unique.values()), read("context-era-definitions.json"))
    require(eras == report["release_eras"], "Independent host registry resolution differs")
    initial = json.loads(next(r["text"] for r in base if r["path"].endswith("source-study-v1-validation/live-rollout.json")))
    basepid = initial["minime"]["new_pid"]
    helpers = source_context_releases(read("helper-era.json"))
    direction = direction_release(read("direction-era.json"), read("post-cutoff-recovery.json"), read("direction-prompt-binding.json"))
    helpers.append(direction)
    interface = eras["study-interface-sep17"]
    interface_rows = {r["relative"]: r for r in checked_records(read("interface-era.json"))}
    for i in [1, 2]:
        source_inputs = json.loads(interface_rows[f"bridge-stage-0{i}/source-inputs.json"]["text"])
        prompts = [r for r in source_inputs["files"] if r["path"].endswith("/crates/astrid-source-study/prompt.txt")]
        require(len(prompts) == 1 and prompts[0]["sha256"] == direction["source_prompt_sha256"], "Interface source prompt differs")
        stage = interface["astrid"] if i == 1 else interface["astrid"]["final_stage"]
        helpers.append(dict(name=f"study-interface-stage0{i}", boundary=stage["boundary"], commit=stage["commit"],
            bridge_pid=stage["new_pid"], manifest_sha256=stage["manifest_sha256"], helper_sha256=interface["helper_sha256"],
            source_prompt_sha256=direction["source_prompt_sha256"], adapted_prompt_sha256=direction["adapted_prompt_sha256"]))
    private_prompts, private = private_binding(read("private-prompt-binding.json"), read("private-prompt-review-draft.json"))
    require(private["helper_sha256"] == interface["helper_sha256"] and private["stage_manifest_sha256"] == interface["astrid"]["final_stage"]["manifest_sha256"], "Private guidance and host-era evidence contradict")
    variants = {}
    accepted_bindings = {helpers[0]["adapted_prompt_sha256"]: "source-context-release-template",
        direction["adapted_prompt_sha256"]: "direction-release-template", PRIVATE_OLD: "reviewed-private-patch-old-literal", PRIVATE_NEW: "reviewed-private-patch-new-literal"}
    for item in definition["prompts"]:
        require(set(item) == {"sha256", "route", "family", "binding"}, "Unknown prompt definition field")
        require(item["sha256"] not in variants and accepted_bindings.get(item["sha256"]) == item["binding"], "Unreviewed prompt definition")
        require(item["route"] == ("extended_writing" if item["sha256"] in private_prompts else "source_study"), "Prompt definition route contradicts binding")
        variants[item["sha256"]] = item
    require(set(variants) == set(accepted_bindings), "Incomplete reviewed prompt definition")
    submitted = {r["sha256"]: r["text"] for r in base if r["kind"] == "system_prompt"}
    for digest, text in submitted.items():
        require(digest in variants, "Unknown retained system prompt")
        if digest in private_prompts: require(text == private_prompts[digest], "Submitted private prompt differs")
    generations = {json.loads(r["text"])["generation_id"]: (r, json.loads(r["text"])) for r in base if r["kind"] == "generation"}
    studies = report["studies"]; ids = [s["id"] for s in studies]
    require(len(ids) == len(set(ids)) and set(ids) == set(generations), "Report generation census differs")
    require(not set(ids).intersection(tracking["seen_generations"]), "Already tracked generation reselected")
    rows = []
    for s in studies:
        rec, g = generations[s["id"]]
        require(s["record_sha256"] == rec["sha256"] and s["pid"] == g["pid"], "Generation identity differs")
        hashes = [m["content_sha256"] for m in g["messages"] if m["role"] == "system"]
        require(s["system_hashes"] == hashes and all(h in submitted for h in hashes), "Submitted system identity differs")
        family = prompt_family(s["actual_route"], hashes, variants)
        require(g["prompt_class"] == ("private_writing" if s["actual_route"] == "extended_writing" else "source_study"), "Recorded prompt class contradicts route")
        require(s["user_text"] == user_text(g), "Submitted user text differs")
        start, precise_end = epoch(s["started_utc"]), epoch(s["completed"])
        end = g["created_at_unix_ms"]/1000
        require(start == int(g["generation_id"].split("-")[0])/1000 and s["completed"] == g["created_at"]
            and 0 <= precise_end-end < 0.0011, "Generation clocks differ")
        require(epoch(protocol["since"]) <= end < epoch(protocol["until_exclusive"]), "Generation outside frozen window")
        host, transitions = host_mapping(start, end, s["pid"], eras, basepid)
        require(host == s["era"] and transitions == s["transitions"], "Report host-era classification differs")
        notebook = notebook_exposure(s["user_text"])
        require(notebook == s["notebook"] and notebook["status"] != "malformed", "Unknown or contradictory notebook schema")
        if s["actual_route"] == "source_study": require(notebook["status"] == "included_in_submitted_user_text", "Source notebook absent")
        strata = [h["name"] for h in helpers if end >= h["boundary"]]
        crossing = [h["name"] for h in helpers if start < h["boundary"] <= end]
        rows.append(dict(id=s["id"], pid=s["pid"], host_era=host, prompt_family=family, system_sha256=hashes[0],
            completion_clock_stratum=strata[-1] if strata else "before-reviewed-helper-releases",
            crosses_helper_clock_boundary=crossing, helper_applicability="source-study-channel" if s["actual_route"] == "source_study" else "not_inferred_for_private_writing",
            per_invocation_helper_identity="unestablished", preparation_identity="unestablished", notebook_status=notebook["status"],
            delivered_line_header_present=bool(re.search(r"Exact source bytes \d+\.\.\d+ \(end exclusive\)\. Delivered source lines", s["user_text"])),
            finding_capacity_header_present="FINDING CAPACITY —" in s["user_text"]))
    require(studies == sorted(studies, key=lambda s:(epoch(s["completed"]),s["id"])), "Report completion order differs")
    expected_sample = [s["id"] for s in studies if s["status"] == "ok" and s["text"].strip()][:3]
    require(expected_sample == report["close_reading_ids"], "Fixed first-three selection differs")
    source = [s for s in studies if s["actual_route"] == "source_study"]
    own = next((s for s in source if s["receipt_verified"] and any(p["source"].startswith("minime/") for p in s["pages"])), None)
    # Negative controls change only in-memory evidence, including recomputed outer identities.
    controls = {}
    controls["unknown_system_prompt_rejected"] = rejects(lambda: prompt_family("source_study", ["0"*64], variants))
    controls["wrong_channel_for_known_prompt_rejected"] = rejects(lambda: prompt_family("source_study", [PRIVATE_NEW], variants))
    controls["unknown_host_pid_rejected"] = rejects(lambda: host_mapping(epoch(studies[0]["started_utc"]), epoch(studies[0]["completed"]), -1, eras, basepid)) if studies else True
    changed = copy.deepcopy(list(unique.values()))
    hostrow = next(r for r in changed if r.get("relative") == "evidence/minime-host-after.json")
    value = json.loads(hostrow["text"]); value["pid"] = -1
    hostrow["text"] = json.dumps(value); hostrow["bytes"] = len(hostrow["text"].encode()); hostrow["sha256"] = sha(hostrow["text"].encode())
    controls["rehashed_host_release_contradiction_rejected"] = rejects(lambda: resolve_eras(changed, read("context-era-definitions.json")))
    changed = copy.deepcopy(read("private-prompt-binding.json"))
    patchrow = next(r for r in changed["records"] if r["relative"] == "source/astrid-interface.patch")
    patchrow["text"] = patchrow["text"].replace("+const PROMPT: &str = \"You are writing privately.", "+const PROMPT: &str = \"Changed private guidance.")
    patchrow["bytes"] = len(patchrow["text"].encode()); patchrow["sha256"] = sha(patchrow["text"].encode())
    ownerrow = next(r for r in changed["records"] if r["relative"] == "manifest.json")
    ownmanifest = json.loads(ownerrow["text"]); item = next(x for x in ownmanifest["files"] if x["path"] == patchrow["relative"])
    item.update(bytes=patchrow["bytes"], sha256=patchrow["sha256"])
    ownerrow["text"] = json.dumps(ownmanifest); ownerrow["bytes"] = len(ownerrow["text"].encode()); ownerrow["sha256"] = sha(ownerrow["text"].encode())
    changed_review = copy.deepcopy(read("private-prompt-review-draft.json")); changed_review["owning_manifest"]["sha256"] = ownerrow["sha256"]
    changed_review["retained_release_inputs"][patchrow["relative"]]["sha256"] = patchrow["sha256"]
    controls["rehashed_private_literal_contradiction_rejected"] = rejects(lambda: private_binding(changed, changed_review))
    # Schema checks do not depend on a particular day's notebook contents.
    synthetic = next((s for s in source if s["notebook"]["status"] == "included_in_submitted_user_text"), None)
    if synthetic:
        n = synthetic["notebook"]; original = synthetic["user_text"]; body = original.find("\n", n["start"]+2)+1
        for key in ["root", "source_findings"]:
            fields = copy.deepcopy(n["fields"])
            if key == "root": fields["unknown_future_field"] = True
            else: fields["source_findings"] = {"authored":[], "supplied_locations":[], "updates":[], "unknown_future_field":True}
            altered = original[:body] + json.dumps(fields) + original[n["end"]:]
            controls["unknown_notebook_"+key+"_field_rejected"] = notebook_exposure(altered)["status"] == "malformed"
    else:
        controls["notebook_negative_controls"] = "not_applicable_no_source_notebook"
    require(all(v is True or v == "not_applicable_no_source_notebook" for v in controls.values()), "Context negative control failed")
    negative = dict(schema="s007_daily_context_negative_controls_v1", context_definition_sha256=sha(definition_raw),
        report_sha256=sha(report_raw), scope="In-memory changes only; original packets and historical records unchanged.", checks=controls)
    result = dict(schema="s007_daily_context_verification_v3", status="verified", context_definition_sha256=sha(definition_raw),
        protocol_sha256=input_hashes["protocol.json"], report_sha256=sha(report_raw), prior_ledger_sha256=protocol["ledger_sha256"],
        input_hashes=input_hashes, negative_controls_sha256=sha(encoded(negative)),
        prior_generations=len(tracking["seen_generations"]), new_generations=len(ids), resulting_generations=len(ids)+len(tracking["seen_generations"]),
        duplicate_ids=[], fixed_first_three_verified=expected_sample, helper_releases=helpers, host_releases=eras,
        reviewed_prompt_variants=definition["prompts"], private_prompt_binding=private, generation_context_rows=rows,
        prompt_families=dict(Counter(x["prompt_family"] for x in rows)), process_counts=dict(Counter(str(x["pid"]) for x in rows)),
        completion_clock_strata=dict(Counter(x["completion_clock_stratum"] for x in rows)),
        source_notebooks=len(source), source_notebook_status=dict(Counter(s["notebook"]["status"] for s in source)),
        supplied_interface_markers=dict(delivered_line_headers=sum(x["delivered_line_header_present"] for x in rows), finding_capacity_headers=sum(x["finding_capacity_header_present"] for x in rows)),
        own_repository_followup=dict(selection=protocol["followup"], observed=own is not None, generation_id=own["id"] if own else None,
            record_sha256=own["record_sha256"] if own else None, reason=None if own else "No verified Minime-owned numbered source page occurs in this fixed window."),
        limits=["Host release identity, selected helper identity, exact submitted prompt and clock strata remain separate.",
            "Exact prompt hashes establish submitted guidance; they do not establish the helper binary or preparation time for each invocation.",
            "Private-writing rows carry wall-clock release context without inferring source-study helper use or natural continuation uptake.",
            "The private prompt literal matches retained reviewed patch bytes and qualified/staged source inventory identities; the complete writing source file is not retained in this packet.",
            "Notebook and interface inclusion are transport evidence, not correctness or durable correction. No outcome-quality scoring or exhaustive later-correction search occurs here."])
    return result, negative


def build(folder, report_path="final-report/report.json"):
    return build_outputs(folder, report_path)[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path); parser.add_argument("--report", default="final-report/report.json")
    parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    result, negative = build_outputs(args.packet, args.report)
    for name, value in [("context-negative-controls.json", negative), ("context-verification.json", result)]:
        path = args.packet / name; raw = encoded(value)
        if args.check: require(path.read_bytes() == raw, "Context replay differs: " + name)
        else:
            with path.open("xb") as f: f.write(raw)
            path.chmod(0o600)
    print(json.dumps({k:result[k] for k in ["schema", "status", "new_generations", "prompt_families", "process_counts", "own_repository_followup"]}, indent=2))
