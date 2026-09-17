#!/usr/bin/env python3
"""Provider-only prospective amendment; immutable v1 cohort and replay preserved."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("frozen_followups_v1", ROOT / "probes/research_followups.py")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
from reservoir_research.research_followups import (encoded, sha, epoch, iso, exclusive_json,
    validate_protocol, capture_runs, capture_provider, analyze_runs, analyze_provider, analyze_durable)

FILES = ["probes/research_followups_v2.py", "tests/test_research_followups_v2.py"]


def identity():
    return {n: sha((ROOT / n).read_bytes()) for n in FILES}


def provider_protocol(protocol, amendment):
    """The v1 collector receives a provider-only clock; cohort clocks stay untouched."""
    p = copy.deepcopy(protocol)
    start = epoch(amendment["provider_t0"])
    p.update(t0=iso(start), provider_end=iso(start + 86400),
             intake_end=iso(start + 7 * 86400), final_end=iso(start + 9 * 86400))
    return validate_protocol(p)


def validate_amendment(a, protocol, preflight, now=None):
    assert a["schema"] == "bounded_followups_provider_amendment_v1"
    assert preflight["schema"] == "provider_observer_preflight_v1"
    assert epoch(a["provider_end"]) == epoch(a["provider_t0"]) + 86400
    assert epoch(preflight["completed_at"]) <= epoch(a["frozen_at"]) < epoch(a["provider_t0"])
    assert preflight["outcomes_read"] == preflight["raw_responses_read"] == preflight["service_operations"] == preflight["live_source_writes"] == 0
    assert preflight["coverage_status"] in {"limited_observed_dispatch_identity", "unavailable_within_frozen_scope"}
    assert preflight["exhaustive_denominator_verified"] is False
    assert a["coverage_status"] == preflight["coverage_status"] and a["exhaustive_denominator_verified"] is False
    assert a["original_cohort_t0"] == protocol["t0"]
    assert a["original_intake_end"] == protocol["intake_end"] and a["original_final_end"] == protocol["final_end"]
    assert a["provider_collection_allowance_seconds"] == 120
    if now is not None:
        assert epoch(a["frozen_at"]) <= now
    return a


def qualify(out):
    out = v1.output_path(out)
    if out.exists(): raise ValueError("Qualification output already exists")
    before = identity()
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_research_followups_v2.py", "-v"], cwd=ROOT,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), capture_output=True, timeout=120)
    log = result.stdout + result.stderr
    out.mkdir(mode=0o700, parents=True)
    (out / "tests.log").write_bytes(log)
    receipt = dict(schema="bounded_followups_amendment_qualification_v1", recorded_at=iso(time.time()),
        passed=result.returncode == 0 and before == identity(), code=before,
        test_log_sha256=sha(log), scope="Isolated fixtures; no live reads or model/service calls.")
    exclusive_json(out / "qualification.json", receipt)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["passed"] else 1


def amend(study, qualification):
    study, p, ph = v1.load_protocol(study)
    qpath = v1.output_path(qualification)
    qraw = qpath.read_bytes(); q = json.loads(qraw)
    assert q["schema"] == "bounded_followups_amendment_qualification_v1" and q["passed"] and q["code"] == identity()
    assert sha((qpath.parent / "tests.log").read_bytes()) == q["test_log_sha256"]
    preflight_raw = (study / "provider-preflight.json").read_bytes(); preflight = json.loads(preflight_raw)
    allow_raw = (study / "provider-preflight-allowlist.json").read_bytes()
    assert preflight["allowlist_sha256"] == sha(allow_raw)
    assert json.loads(allow_raw)["protocol_sha256"] == ph
    assert epoch(json.loads(allow_raw)["frozen_at"]) <= epoch(preflight["started_at"]) <= epoch(preflight["completed_at"])
    # No provider outcomes from the superseded window may enter this registration.
    for path in study.glob("capture-*.json"):
        cap = json.loads(path.read_bytes())
        assert cap["protocol_sha256"] == ph and not cap["provider"]["records"] and not cap["runs"]["records"]
    frozen = time.time(); start = int(frozen) + 60
    a = dict(schema="bounded_followups_provider_amendment_v1", frozen_at=iso(frozen),
        original_protocol_sha256=ph, original_cohort_t0=p["t0"], original_intake_end=p["intake_end"],
        original_final_end=p["final_end"], superseded_provider_t0=p["t0"], superseded_provider_end=p["provider_end"],
        provider_t0=iso(start), provider_end=iso(start + 86400), provider_collection_allowance_seconds=120,
        preflight_sha256=sha(preflight_raw), allowlist_sha256=sha(allow_raw), code=identity(),
        qualification=dict(path=str(qpath.relative_to(ROOT)), sha256=sha(qraw)),
        coverage_status=preflight["coverage_status"], exhaustive_denominator_verified=False,
        reason="Observer preflight finished after original shared T0. This separate provider-only window starts prospectively after preflight and qualification; S006 consecutive runs and S008 cohort clocks remain unchanged.",
        limitation="Preflight coverage is limited or unavailable. Counts concern only the declared spool. Missing coverage cannot establish zero opportunities; no scope extension, replacement spool, or service action is authorized.")
    validate_amendment(a, p, preflight, frozen)
    exclusive_json(study / "provider-amendment.json", a)
    print(json.dumps({k:a[k] for k in ["provider_t0", "provider_end", "original_cohort_t0", "original_intake_end", "original_final_end", "coverage_status"]}, indent=2))


def load(study):
    study, p, ph = v1.load_protocol(study)
    raw = (study / "provider-amendment.json").read_bytes(); a = json.loads(raw)
    pre_raw = (study / "provider-preflight.json").read_bytes(); pre = json.loads(pre_raw)
    assert a["original_protocol_sha256"] == ph and a["code"] == identity()
    assert a["preflight_sha256"] == sha(pre_raw)
    allow_raw = (study / "provider-preflight-allowlist.json").read_bytes()
    assert a["allowlist_sha256"] == pre["allowlist_sha256"] == sha(allow_raw)
    qraw = (ROOT / a["qualification"]["path"]).read_bytes(); q = json.loads(qraw)
    assert a["qualification"]["sha256"] == sha(qraw) and q["passed"] and q["code"] == identity()
    validate_amendment(a, p, pre, time.time())
    return study, p, ph, a, sha(raw), provider_protocol(p, a)


def summary(p, pp, captures, now, packets, a):
    provider = analyze_provider(pp, [x["provider"] for x in captures], now)
    provider["preflight_coverage_status"] = a["coverage_status"]
    provider["exhaustive_denominator_verified"] = False
    return dict(s006_runs=analyze_runs(p, [x["runs"] for x in captures], now), s006_provider=provider,
                s008_durable=analyze_durable(p, packets, now))


def previous_captures(study, ph, ah):
    caps = []
    for path in sorted(study.glob("v2-capture-*.json")):
        cap = json.loads(path.read_bytes())
        assert cap["protocol_sha256"] == ph and cap["provider_amendment_sha256"] == ah
        caps.append(cap)
    return caps


def refresh(study):
    study, p, ph, a, ah, pp = load(study); now = time.time()
    cap = dict(schema="bounded_followups_capture_v2", captured_at=iso(now), protocol_sha256=ph,
        provider_amendment_sha256=ah, runs=capture_runs(p, now), provider=capture_provider(pp, now))
    previous = previous_captures(study, ph, ah)
    result = dict(schema="bounded_followups_status_v2", as_of=iso(now), protocol_sha256=ph,
        provider_amendment_sha256=ah, future_observation_complete=False,
        interpretation="Pending bounded observation and evidence-coded review. Provider coverage is limited; no automatic benefit claim.",
        **summary(p, pp, previous + [cap], now, v1.packet_inputs(p), a))
    stem = datetime.fromtimestamp(now, timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    cname, sname = "v2-capture-" + stem + ".json", "v2-status-" + stem + ".json"
    exclusive_json(study / cname, cap); exclusive_json(study / sname, result)
    exclusive_json(study / ("v2-receipt-" + stem + ".json"), dict(schema="bounded_followups_checkpoint_v2",
        capture=cname, capture_sha256=sha((study/cname).read_bytes()), status=sname,
        status_sha256=sha((study/sname).read_bytes()), protocol_sha256=ph, provider_amendment_sha256=ah))
    print(json.dumps(dict(checkpoint=cname, as_of=result["as_of"], runs=result["s006_runs"]["status"],
        provider=result["s006_provider"]["status"], durable=result["s008_durable"]["status"],
        run_count=result["s006_runs"]["run_count"], dispatches=result["s006_provider"]["dispatches"]), indent=2))


def verify(study):
    v1.verify(study)
    study, p, ph, a, ah, pp = load(study); caps = []
    for path in sorted(study.glob("v2-receipt-*.json")):
        receipt = json.loads(path.read_bytes())
        assert receipt["protocol_sha256"] == ph and receipt["provider_amendment_sha256"] == ah
        cr = (study / receipt["capture"]).read_bytes(); sr = (study / receipt["status"]).read_bytes()
        assert sha(cr) == receipt["capture_sha256"] and sha(sr) == receipt["status_sha256"]
        cap = json.loads(cr); status = json.loads(sr)
        assert cap["protocol_sha256"] == status["protocol_sha256"] == ph
        assert cap["provider_amendment_sha256"] == status["provider_amendment_sha256"] == ah
        caps.append(cap); now = epoch(status["as_of"])
        paths = [Path(x["path"]) for x in status["s008_durable"]["packet_inputs"]]
        assert all(x.resolve().is_relative_to(ROOT / "research/outputs") for x in paths)
        expected = summary(p, pp, caps, now, paths, a)
        assert all(status[k] == value for k, value in expected.items())
    print(json.dumps(dict(verified=True, amended_checkpoints=len(caps), scope="Offline retained-evidence replay; no live reads."), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    q = sub.add_parser("qualify"); q.add_argument("--out", required=True)
    q = sub.add_parser("amend"); q.add_argument("--study", required=True); q.add_argument("--qualification", required=True)
    for name in ["refresh", "verify"]:
        q = sub.add_parser(name); q.add_argument("--study", required=True)
    args = parser.parse_args()
    if args.command == "qualify": return qualify(args.out)
    if args.command == "amend": amend(args.study, args.qualification)
    if args.command == "refresh": refresh(args.study)
    if args.command == "verify": verify(args.study)
    return 0


if __name__ == "__main__": sys.exit(main())
