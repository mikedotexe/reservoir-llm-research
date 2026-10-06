"""One historical S-006 recovery and explicit-input S-006/S-008 closeout.

The September collectors remain frozen. Only recover() reads original sources;
build_report() and verify() read declared retained files and never provenance paths.
Standard library only. This bounded closeout does not implement a new study selector.
"""
from __future__ import annotations

import copy
import json
import os
import re
import signal
import time
from contextlib import contextmanager
from pathlib import Path

from . import research_followups as old

ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = ("reservoir_research/followup_closeout.py", "probes/research_followups_closeout.py",
              "tests/test_research_followups_closeout.py", "reservoir_research/research_followups.py")
LIMITS = dict(file_bytes=8 * 1024**2, total_bytes=256 * 1024**2,
              raw_bytes=256 * 1024, directory_entries=20000, directory_seconds=10,
              collector_seconds=150, packet_claim_summary_files=40, provider_dispatches=5000)
SCHEMA = "bounded_followup_closeout_inputs_v1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity():
    return {name: old.sha((ROOT / name).read_bytes()) for name in CODE_FILES}


def safe(root, relative):
    root = Path(root).resolve()
    return old.source_path(root, relative)


def write_json(path, value):
    old.exclusive_json(path, value)


def output_directory(path):
    path = Path(path).absolute()
    require(path == path.resolve() and path.is_relative_to(ROOT / "research/outputs"),
            "Output must be a nonsymlink path under this repository's research/outputs")
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    return path


def seal(folder):
    names = sorted(p.name for p in folder.iterdir() if p.is_file())
    require("packet-manifest.json" not in names, "Packet is already sealed")
    write_json(folder / "packet-manifest.json", {n: old.sha((folder / n).read_bytes()) for n in names})


class Inputs:
    """Hash-checked explicit files, with no implicit traversal or source-path replay."""
    def __init__(self, manifest, root):
        self.manifest, self.root = manifest, Path(root).resolve()
        self.cache, self.bytes = {}, 0

    def raw(self, name):
        require(name in self.manifest["files"], "Undeclared retained input: " + name)
        if name not in self.cache:
            p = safe(self.root, name)
            size = p.stat().st_size
            require(p.is_file() and size <= 256 * 1024**2, "Retained file cap")
            require(self.bytes + size <= 512 * 1024**2, "Retained input budget")
            raw = p.read_bytes()
            require(len(raw) == size and old.sha(raw) == self.manifest["files"][name],
                    "Retained input hash mismatch: " + name)
            self.cache[name] = raw
            self.bytes += size
        return self.cache[name]

    def json(self, name):
        return json.loads(self.raw(name))


def provider_protocol(protocol, amendment):
    require(amendment["original_protocol_sha256"] == old.sha(old.encoded(protocol)),
            "Provider amendment does not bind protocol")
    require(amendment["original_cohort_t0"] == protocol["t0"] and
            amendment["original_intake_end"] == protocol["intake_end"] and
            amendment["original_final_end"] == protocol["final_end"], "Cohort clocks changed")
    start = old.epoch(amendment["provider_t0"])
    require(old.epoch(amendment["provider_end"]) == start + 86400 and
            amendment["provider_collection_allowance_seconds"] == 120, "Provider clocks changed")
    p = copy.deepcopy(protocol)
    p.update(t0=old.iso(start), provider_end=old.iso(start + 86400),
             intake_end=old.iso(start + 7 * 86400), final_end=old.iso(start + 9 * 86400))
    return old.validate_protocol(p)


class RecoveryReader(old.Reader):
    """Stricter combined packet cap and auditable file metadata around frozen reads."""
    def __init__(self, protocol, total=LIMITS["total_bytes"]):
        super().__init__(total=total, file_limit=LIMITS["file_bytes"],
                         entries=LIMITS["directory_entries"], seconds=LIMITS["collector_seconds"])
        self.protocol = protocol
        self.root = Path(protocol["allowlist"]["astrid_root"])
        require(self.root.is_absolute() and self.root == self.root.resolve(), "Noncanonical source root")
        self.runs = self.root / protocol["allowlist"]["runs_directory"]
        self.notes = self.root / protocol["allowlist"]["notes_directory"]
        self.spool = Path(protocol["allowlist"]["provider_spool"])
        self.originals = self.root / "capsules/spectral-bridge/workspace/introspections"
        self.files, self.packet_counts, self.directory_metadata = [], {}, []

    def packet_parts(self, path):
        try:
            parts = Path(path).relative_to(self.notes).parts
        except ValueError:
            return ()
        if not parts:
            return ()
        match = re.fullmatch(r"claude-heartbeat_(\d{10})_[A-Za-z0-9_.-]+", parts[0])
        if not match or not old.epoch(self.protocol["t0"]) <= int(match[1]) <= old.epoch(self.protocol["final_end"]):
            return ()
        return parts

    def allowed_file(self, path):
        path = Path(path)
        if path.parent == self.runs:
            return bool(old.RUN_RE.fullmatch(path.name))
        if path.parent == self.spool / "events":
            return bool(old.PROVIDER_RE.fullmatch(path.name))
        if path.parent == self.spool / "raw":
            return bool(re.fullmatch(r"[0-9a-f]{64}\.txt", path.name))
        if path.parent == self.originals:
            return bool(re.fullmatch(r"introspection_[A-Za-z0-9_.-]+\.txt", path.name))
        parts = self.packet_parts(path)
        return bool((len(parts) == 2 and parts[1] in old.PACKET_NAMES) or
                    (len(parts) == 3 and parts[1] in ("claims", "summaries") and
                     re.fullmatch(r"[A-Za-z0-9_.-]+\.(json|md)", parts[2])))

    def read(self, path, limit=None):
        path = Path(path)
        require(self.allowed_file(path), "Source file outside recovery allowlist")
        require(path == path.resolve() and not path.is_symlink(), "Noncanonical source file")
        before = path.stat()
        before_bytes = self.bytes
        try:
            raw = super().read(path, limit)
        except BaseException:
            # A changed or interrupted file may have consumed bytes before the
            # frozen reader rejects it; charge conservatively, never reset budget.
            self.bytes = max(self.bytes, min(self.total_limit, before_bytes + before.st_size))
            raise
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
                "Source changed across metadata capture")
        self.files.append(dict(path=str(path), bytes=len(raw), sha256=old.sha(raw),
                               mtime_ns=after.st_mtime_ns, observed_at=old.iso(time.time())))
        return raw

    def names(self, folder):
        folder = Path(folder)
        parts = self.packet_parts(folder)
        packet_children = len(parts) == 2 and parts[1] in ("claims", "summaries")
        require(folder in (self.runs, self.notes, self.spool / "events") or packet_children,
                "Directory outside recovery allowlist")
        before = folder.stat()
        meta = dict(path=str(folder), mtime_ns=before.st_mtime_ns, bytes=before.st_size)
        self.directory_metadata.append(meta)
        names = super().names(folder)
        after = folder.stat()
        meta.update(after_mtime_ns=after.st_mtime_ns, names_sha256=old.sha(old.encoded(names)))
        require((before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size),
                "Directory changed during inventory")
        if packet_children:
            n = self.packet_counts.get(parts[0], 0) + len(names)
            self.packet_counts[parts[0]] = n
            require(n <= LIMITS["packet_claim_summary_files"], "Combined claim/summary cap")
        if folder == self.runs:
            times = []
            for name in names:
                if match := old.RUN_RE.fullmatch(name):
                    digits = match[1]
                    times.append(int(digits) / 10 ** (len(digits) - 10))
            meta["latest_controller_filename_time"] = old.iso(max(times)) if times else None
        return names


class RecoveryDeadline(BaseException):
    pass


@contextmanager
def deadline(seconds):
    previous = signal.getsignal(signal.SIGALRM)
    def expire(_signum, _frame):
        raise RecoveryDeadline("Collector time cap")
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def collect_once(protocol, amendment):
    """Only function that reads the original source tree; never invokes source code."""
    old.validate_protocol(protocol)
    pp = provider_protocol(protocol, amendment)
    captures, metadata, used = {}, {}, 0
    for key, function, frame in (("runs", old.capture_runs, protocol),
                                  ("provider", old.capture_provider, pp)):
        reader = RecoveryReader(protocol, total=LIMITS["total_bytes"] - used)
        try:
            with deadline(LIMITS["collector_seconds"]):
                # This is the original event cutoff, not the later collection clock.
                capture = function(frame, old.epoch(protocol["final_end"]), reader)
        except (RecoveryDeadline, OSError, ValueError, KeyError, TypeError) as exc:
            capture = dict(status="capture_unavailable", records=[],
                           errors=[dict(path=key, error=str(exc))], inventories=reader.inventories)
        used += reader.bytes
        captures[key] = capture
        metadata[key] = dict(files=reader.files, directories=reader.directory_metadata,
                             bytes_read=reader.bytes)
    return dict(schema="bounded_followups_historical_recovery_v1", captured_at=old.iso(time.time()),
                event_cutoff=protocol["final_end"], **captures, source_metadata=metadata,
                source_bytes_read=used, historical_directory_completeness="not_established",
                limitation="One later read of the available local source tree; missing or removed historical records cannot be ruled out.")


def recover(plan_path, data_root):
    plan_raw = Path(plan_path).read_bytes()
    plan = json.loads(plan_raw)
    require(plan["schema"] == "bounded_followups_recovery_plan_v1", "Unknown recovery plan")
    require(plan["limits"] == LIMITS and plan["code"] == identity(), "Unqualified collector identity or limits")
    require(plan["attempt_limit"] == 1 and plan["remote_fallback"] is False and
            plan["s007_access"] is False, "Recovery boundary changed")
    require(old.epoch(plan["frozen_at"]) < time.time(), "Plan must precede collection")
    inputs = Inputs(plan, data_root)
    p = inputs.json(plan["protocol"])
    a = inputs.json(plan["provider_amendment"])
    old.validate_protocol(p)
    q = inputs.json(plan["qualification"])
    require(q["passed"] is True and q["code"] == identity(), "Qualification must pass for this code")
    require(old.sha(inputs.raw(plan["qualification_log"])) == q["test_log_sha256"], "Qualification log differs")
    require(plan["windows"] == dict(t0=p["t0"], intake_end=p["intake_end"], final_end=p["final_end"],
                                    provider_t0=a["provider_t0"], provider_end=a["provider_end"],
                                    provider_outcome_end=old.iso(old.epoch(a["provider_end"]) + 120)),
            "Frozen recovery clocks differ")
    for name, digest in p["code"].items():
        require(old.sha((ROOT / name).read_bytes()) == digest, "Original collector source changed")
    folder = output_directory(safe(data_root, plan["output"]))
    # The directory and claim survive a failure; the plan cannot be rerun elsewhere.
    write_json(folder / "recovery-started.json", dict(plan_sha256=old.sha(plan_raw), started_at=old.iso(time.time())))
    write_json(folder / "plan.json", plan)
    capture = collect_once(p, a)
    capture["plan_sha256"] = old.sha(plan_raw)
    capture["protocol_sha256"] = old.sha(inputs.raw(plan["protocol"]))
    capture["provider_amendment_sha256"] = old.sha(inputs.raw(plan["provider_amendment"]))
    write_json(folder / "capture.json", capture)
    write_json(folder / "completion.json", dict(schema="bounded_followups_recovery_completion_v1",
               completed_at=old.iso(time.time()), capture_sha256=old.sha(old.encoded(capture)),
               source_writes=0, network_requests=0, source_commands=0, attempt=1,
               collection_completed=True, historical_coverage_complete=False))
    seal(folder)
    return dict(output=str(folder), selected_run_ids=capture["runs"].get("selected_run_ids", []),
                run_status=capture["runs"]["status"], provider_status=capture["provider"]["status"],
                source_bytes_read=capture["source_bytes_read"])


def reconstruct(captures, source, revisions):
    groups = {digest: {} for digest in revisions}
    for name, cap in captures:
        for record in cap["records"]:
            if record["kind"] != "delivery":
                continue
            value = json.loads(record["text"])
            page = value.get("page")
            if not isinstance(page, dict) or page.get("source") != source:
                continue
            digest = page.get("revision", {}).get("sha256")
            if digest not in groups:
                continue
            old.check_records([record])
            key = page["id"]
            if key in groups[digest]:
                require(groups[digest][key][0] == page, "Same page ID changed")
            groups[digest][key] = (page, dict(capture=name, record_sha256=record["sha256"],
                                             receipt_path=record["path"], page_id=key))
    result = {}
    for digest, pages in groups.items():
        require(bool(pages), "No retained pages for source revision")
        first = next(iter(pages.values()))[0]
        size = first["revision"]["bytes"]
        require(isinstance(size, int) and 0 < size <= 8 * 1024**2, "Source reconstruction size cap")
        data, seen = bytearray(size), bytearray(size)
        for page, _reference in pages.values():
            require(page["revision"]["bytes"] == size, "Source sizes conflict")
            lo, hi = page["start"]["byte"], page["end"]["byte"]
            require(0 <= lo < hi <= size, "Invalid source range")
            raw = "".join(m[1] + "\n" for line in page["text"].splitlines()
                          if (m := re.fullmatch(r"\s*\d+ \| (.*)", line))).encode()
            require(len(raw) in (hi - lo, hi - lo + 1), "Delivered source byte extent mismatch")
            for i, byte in enumerate(raw[:hi - lo], lo):
                require(not seen[i] or data[i] == byte, "Source overlap differs")
                data[i], seen[i] = byte, 1
        require(all(seen) and old.sha(bytes(data)) == digest, "Incomplete or wrong full source hash")
        result[digest] = (bytes(data), [ref for _page, ref in pages.values()])
    return result


def resolve_revisions(protocol, durable, mapping, sources):
    require(mapping["schema"] == "bounded_followups_source_equivalence_v1", "Unknown source review")
    case = protocol["cases"][mapping["case"]]
    require(mapping["old_revision"] == case["source_sha256"] and
            mapping["old_interval"] == [case["critical_byte_start"], case["critical_byte_end"]],
            "Source review changed original anchor")
    original, _ = sources[mapping["old_revision"]]
    new, _ = sources[mapping["new_revision"]]
    lo, hi = mapping["old_interval"]
    nlo, nhi = mapping["new_interval"]
    anchor = original[lo:hi]
    require(anchor and anchor == new[nlo:nhi] and new.find(anchor) == nlo and
            new.find(anchor, nlo + 1) == -1, "Anchor mapping is not exact and unique")
    cases = {}
    for key, result in durable["cases"].items():
        require(not result["selected"], "Selected exposure requires separate evidence-coded review")
        dispositions = []
        for candidate in result["revision_review_candidates"]:
            require(key == mapping["case"], "Unreviewed revision in other case")
            for page in candidate["source_pages"]:
                require(page["revision"]["sha256"] == mapping["new_revision"], "Unreviewed new revision")
                require(not (page["start"]["byte"] <= nlo and page["end"]["byte"] >= nhi),
                        "Equivalent full-anchor exposure requires separate evidence-coded review")
            dispositions.append(dict(generation_id=candidate["generation_id"],
                record_sha256=candidate["record_sha256"], source_pages=candidate["source_pages"],
                disposition="ineligible_complete_anchor_not_delivered_in_one_page"))
        cases[key] = dict(historical_storage=result["historical_storage"], eligible_exposures=0,
                          selected=[], revision_dispositions=dispositions,
                          selection_in_supplied_packets_final=True,
                          result="no_eligible_exposure_in_supplied_verified_packets",
                          correction="unresolved", planned_window_coverage="incomplete")
    return dict(mapping=mapping, anchor_bytes=hi - lo, anchor_sha256=old.sha(anchor),
                reconstructed_sources={d: dict(bytes=len(raw), full_hash_verified=True,
                    page_references=refs) for d, (raw, refs) in sources.items()}, cases=cases)


def episode_dispositions(runs, captures, review=None):
    """Require separately authored evidence coding when historical episodes exist."""
    records = [r for cap in captures for r in cap["runs"]["records"]]
    selected = {r["run_id"] for r in runs["runs"]}
    supplied = {}
    if review is not None:
        require(review["schema"] == "s006_closeout_episode_reviews_v1", "Unknown episode review")
        supplied = {r["run_id"]: r for r in review["episodes"]}
        require(len(supplied) == len(review["episodes"]) and set(supplied) == selected,
                "Episode review must cover exactly the selected runs")
    result = []
    for run in runs["runs"]:
        evidence = {r["sha256"] for r in records if r.get("run_id") == run["run_id"]}
        item = dict(run_id=run["run_id"], followup_end=run["followup_end"],
                    declared_terminal_state=run["terminal_state"],
                    retrospective_packet_timing="not_established_from_filename_or_read_time",
                    disposition="needs_episode_review")
        if run["run_id"] in supplied:
            coding = supplied[run["run_id"]]
            require(set(coding["stages"]) == {"authorship", "review", "response", "commit", "activation", "outcome"},
                    "Separate attribution/change/outcome stages required")
            for stage in coding["stages"].values():
                require(stage["status"] in ("supported", "unknown", "censored") and bool(stage["summary"]),
                        "Invalid evidence-coded stage")
                require(set(stage["evidence_sha256"]).issubset(evidence), "Episode citation outside selected records")
                require(stage["status"] != "supported" or bool(stage["evidence_sha256"]), "Support needs exact references")
            require(coding["undated_or_late_evidence_is_censored"] is True, "Late evidence cannot be promoted")
            item.update(disposition="reviewed_with_explicit_shortfalls", review=coding)
        result.append(item)
    return result


def build_report(manifest, data_root):
    require(manifest["schema"] == SCHEMA, "Unknown closeout input schema")
    inputs = Inputs(manifest, data_root)
    for name in manifest["files"]:
        inputs.raw(name)
    protocol = inputs.json(manifest["protocol"])
    old.validate_protocol(protocol)
    amendment = inputs.json(manifest["provider_amendment"])
    pp = provider_protocol(protocol, amendment)
    require(old.sha(inputs.raw(manifest["anchors"])) == protocol["anchors_sha256"], "Anchors changed")
    caps = [inputs.json(n) for n in manifest["historical_captures"]]
    recovery = inputs.json(manifest["recovery_capture"])
    recovery_plan = inputs.json(manifest["recovery_plan"])
    require(recovery["plan_sha256"] == old.sha(inputs.raw(manifest["recovery_plan"])), "Recovery plan changed")
    require(recovery_plan["code"] == identity(), "Recovery code differs from replay code")
    for cap in [*caps, recovery]:
        require(cap["protocol_sha256"] == old.sha(inputs.raw(manifest["protocol"])), "Capture protocol changed")
        if "provider_amendment_sha256" in cap:
            require(cap["provider_amendment_sha256"] == old.sha(inputs.raw(manifest["provider_amendment"])),
                    "Capture amendment changed")
        old.check_records(cap["runs"]["records"])
        old.check_records(cap["provider"]["records"])
    paths, reports = [], []
    for name in manifest["daily_packets"]:
        for part in ("packet-manifest.json", "final-report/report.json", "verification.json"):
            inputs.raw(name + "/" + part)
        path = safe(inputs.root, name)
        report, _ = old.load_daily_packet(path, old.Reader(file_limit=64 * 1024**2))
        acceptance = manifest["daily_acceptance"][name]
        finalization = inputs.json(acceptance["finalization"])
        replay = inputs.json(acceptance["replay"])
        digest = old.sha(inputs.raw(name + "/packet-manifest.json"))
        require(finalization["schema"] == "s007-daily-finalization-v1" and
                finalization["packet_manifest_sha256"] == digest and
                finalization.get("research_verification") != "blocked", "Daily finalization is not accepted")
        require(replay["status"] == "passed" and replay["exit_code"] == 0 and
                replay["packet_manifest_sha256"] == digest and replay["network_denied"] is True and
                replay["ledger_modified"] is False, "Daily accepted offline replay required")
        paths.append(path)
        reports.append(report)
    now = old.epoch(protocol["final_end"])
    durable = old.analyze_durable(protocol, paths, now)
    # Normalize retained packet identities for replay after relocation.
    for entry, name in zip(durable["packet_inputs"], manifest["daily_packets"]):
        entry["path"] = name
    mapping = inputs.json(manifest["source_review"])
    source_captures = []
    for name in manifest["source_captures"]:
        packet_manifest = inputs.json(str(Path(name).parent / "packet-manifest.json"))
        require(packet_manifest[Path(name).name] == old.sha(inputs.raw(name)), "Source capture is not sealed")
        source_captures.append((name, inputs.json(name)))
    sources = reconstruct(source_captures, protocol["cases"][mapping["case"]]["source"],
                          [mapping["old_revision"], mapping["new_revision"]])
    reviewed = resolve_revisions(protocol, durable, mapping, sources)
    runs = old.analyze_runs(protocol, [c["runs"] for c in [*caps, recovery]], now)
    provider = old.analyze_provider(pp, [c["provider"] for c in [*caps, recovery]], now)
    episodes = episode_dispositions(runs, [*caps, recovery],
                  inputs.json(manifest["episode_review"]) if manifest.get("episode_review") else None)
    needs_review = any(e["disposition"] == "needs_episode_review" for e in episodes) or provider["dispatches"] > 0
    verified_spans = [dict(packet=name, since=max(protocol["t0"], report["selection"]["since"]),
                          until_exclusive=report["selection"]["until_exclusive"])
                      for name, report in zip(manifest["daily_packets"], reports)]
    require(len(verified_spans) == 1, "This closeout admits only the explicit verified day10 packet")
    # Coverage is interval evidence, not the wall clock advancing past a deadline.
    coverage = dict(planned_intake=[protocol["t0"], protocol["intake_end"]],
                    planned_followup_end=protocol["final_end"], verified_spans=verified_spans,
                    unverified_or_uncaptured=[verified_spans[0]["until_exclusive"], protocol["final_end"]],
                    excluded_packets=manifest["excluded_packets"], exhaustive=False)
    return dict(schema="bounded_followup_closeout_report_v1", inputs_sha256=old.sha(old.encoded(manifest)),
                code=identity(), event_cutoff=protocol["final_end"],
                s006=dict(disposition="needs_episode_review" if needs_review else "closed_incomplete_historical_evidence",
                          runs=runs, provider=provider, episode_dispositions=episodes,
                          provider_review="required" if provider["dispatches"] else "no_retained_attempts_to_adjudicate",
                          retained_eligible_run_count=runs["run_count"], actual_eligible_run_count=None,
                          historical_coverage="not_established", benefit="unmeasured",
                          recovery_source_metadata=recovery["source_metadata"]),
                s008=dict(disposition="retained_slice_assessment_complete_planned_coverage_incomplete",
                          coverage=coverage, original_analysis=durable, source_review=reviewed),
                s007="verification_blocked_unchanged", source_paths_followed=False,
                limits="Administrative closeout of these bounded extensions. Missing records do not establish absent runs, opportunities or correction; broad questions remain open.")


def build(manifest_path, data_root, out):
    manifest = json.loads(Path(manifest_path).read_bytes())
    report = build_report(manifest, data_root)
    folder = output_directory(out)
    write_json(folder / "inputs.json", manifest)
    write_json(folder / "report.json", report)
    write_json(folder / "construction.json", dict(schema="bounded_followup_closeout_construction_v1",
                report_sha256=old.sha(old.encoded(report)), status="constructed_verification_pending",
                original_sources_read=False, ledger_written=False))
    seal(folder)
    return dict(output=str(folder), s006=report["s006"]["disposition"], s008=report["s008"]["disposition"])


def verify(manifest_path, data_root, report_path):
    manifest = json.loads(Path(manifest_path).read_bytes())
    raw = Path(report_path).read_bytes()
    expected = old.encoded(build_report(manifest, data_root))
    require(expected == raw, "Closeout report does not replay exactly")
    return dict(verified=True, report_sha256=old.sha(raw), source_paths_followed=False, ledger_written=False)
