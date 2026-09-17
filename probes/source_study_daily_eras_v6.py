"""Offline binding of the September-17 interface release from retained research evidence.
The host reload is distinct from helper selection; shared study prompts are not binary IDs.
"""
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from source_study_daily_eras_v4 import additional_eras as older_eras

BASE = "research/outputs/2026-09-17-study-interface-repairs/"
MINIME_COMMIT = "5f4925f54580f1fd44666058b126a121ff32880f"
FINAL_COMMIT = "374024a02a5bcfae92f228570b9efe337d85b729"
HELPER = "7636b8dc675e97ed6d7dce4c30df6d04ae802c7cac983c6b1028788ba224a100"

def clock(text):
    return datetime.strptime(text, "%a %b %d %H:%M:%S %Y").replace(tzinfo=ZoneInfo("America/Los_Angeles")).timestamp()

def interface_release(records):
    def row(relative):
        rows = [r for r in records if r["path"] == BASE + relative]
        assert len(rows) == 1, (relative, len(rows))
        r = rows[0]; raw = r["text"].encode()
        assert len(raw) == r["bytes"] and hashlib.sha256(raw).hexdigest() == r["sha256"], relative
        return r
    def get(relative, last=False):
        raw = row(relative)["text"]
        return json.loads(raw.splitlines()[-1] if last else raw)
    first = get("evidence/stage01-transaction/receipt.json")
    recovery_path = "evidence/stage01-transaction/stopped-transition-recoveries/eebb4acb2e7d434dbcbc57a8681c5a78/receipt.json"
    recovery = get(recovery_path)
    final_path = "evidence/stage02-transaction/receipt.json"
    final = get(final_path)
    reload_path = "evidence/minime-reload.jsonl"
    reload = get(reload_path, True)
    m1 = get("bridge-stage-01/manifest.json"); m2 = get("bridge-stage-02/manifest.json")
    source = get("evidence/paired-after/minime/runtime/autonomous_agent_source_status.json")
    host = get("evidence/minime-host-after.json")
    pair = get("evidence/paired-verification.json")
    integration = get("evidence/integration.json")
    followup = get("evidence/manifest-integration/receipt.json")
    review = get("evidence/stage02-independent-review.json")
    assert first["status"] == "failed_requires_review" and not first["activation_performed"]
    assert recovery["status"] == "transition_recovered" and recovery["activation_performed"]
    assert not any(recovery[k] for k in ["signal_sent", "drain_requested", "force_used"])
    assert recovery["original_failure_sha256"] == row("evidence/stage01-transaction/receipt.json")["sha256"]
    assert recovery["manifest_sha256"] == row("bridge-stage-01/manifest.json")["sha256"] == first["manifest_sha256"]
    assert final["status"] == "activated_verified" and final["activation_performed"]
    assert final["old_pid"] == recovery["new_process"]["pid"] == 67595
    assert final["new_process"]["pid"] == pair["astrid_pid"] == 77906
    assert final["manifest_sha256"] == row("bridge-stage-02/manifest.json")["sha256"] == pair["manifest_sha256"] == host["manifest_sha256"]
    assert final["new_process"] == pair["astrid_startup"]
    assert final["new_process"]["deployment_identity"].split(":")[1] == m2["repository"]["head"] == FINAL_COMMIT
    assert integration["minime_new"] == MINIME_COMMIT
    assert integration["astrid_new"] == m1["repository"]["head"] == followup["old"]
    assert followup["new"] == FINAL_COMMIT
    assert reload["outcome"] == "success" and not reload["forced_termination"]
    assert reload["old_pid"] == 37507 and reload["new_pid"] == host["pid"] == source["pid"] == pair["minime_pid"] == 71419
    assert reload["source_inputs"] == source["source_inputs_at_start"]
    assert len(reload["source_inputs"]) == host["startup_inputs"] == pair["minime_sources"] == 82
    assert not source["source_changed_since_start"] and not source["reload_required"] and host["changed"] == []
    assert host["no_launchd_helper_or_root_override"]
    assert host["selected_helper"] == m2["artifacts"]["source-study-reader"]["path"]
    assert host["selected_helper_sha256"] == m1["artifacts"]["source-study-reader"]["sha256"] == m2["artifacts"]["source-study-reader"]["sha256"] == HELPER
    assert review["verified"] and review["failures"] == [] and all(review["checks"].values())
    assert review["manifest_sha256"] == final["manifest_sha256"] and review["expected_commit"] == FINAL_COMMIT
    for index, manifest in [(1,m1),(2,m2)]:
        name = f"bridge-stage-0{index}/source-inputs.json"
        assert row(name)["sha256"] == manifest["source_inputs"]["sha256"]
    assert clock(recovery["new_process"]["started_at"]) < clock(reload["new_started_at"]) < clock(final["new_process"]["started_at"])
    return {
        "minime": dict(boundary=clock(reload["new_started_at"]), old_pid=37507, new_pid=71419,
            commit=MINIME_COMMIT, commit_basis="owning integration metadata; exact 82 declared reload hashes independently equal recorded loaded inputs",
            receipt_sha256=row(reload_path)["sha256"], manifest_sha256=final["manifest_sha256"]),
        "astrid": dict(boundary=clock(recovery["new_process"]["started_at"]), old_pid=75546, new_pid=67595,
            commit=m1["repository"]["head"], receipt_sha256=row(recovery_path)["sha256"],
            manifest_sha256=recovery["manifest_sha256"], old_manifest_sha256=first["old_identity"]["manifest_sha256"],
            final_stage=dict(boundary=clock(final["new_process"]["started_at"]), new_pid=77906,
                commit=FINAL_COMMIT, manifest_sha256=final["manifest_sha256"], receipt_sha256=row(final_path)["sha256"])),
        "helper_sha256": HELPER,
        "helper_identity_limit": "Both interface stages have identical helper bytes. Study-direction and interface releases share an exact study system prompt; clock strata and prompts do not prove each invocation binary.",
        "paired_verification_utc": pair["paired_verification_utc"],
        "host_reload_verified_at": reload["recorded_at"],
    }

def additional_eras(records):
    result = older_eras(records)
    result["study-interface-sep17"] = interface_release(records)
    return result
