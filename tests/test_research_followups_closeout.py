import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reservoir_research import followup_closeout as close
from reservoir_research import research_followups as old


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.start = 1700000000
        self.old_source, self.new_source = b"A\nLOOP\nB\n", b"P\nA\nLOOP\nB\n"
        self.old_hash, self.new_hash = old.sha(self.old_source), old.sha(self.new_source)
        case = dict(anchor_generation="anchor", quote="false assertion", source="astrid/source.rs",
                    source_sha256=self.old_hash, critical_byte_start=2, critical_byte_end=9,
                    saved_note_origin_sha256=None, historical_storage="authored_prose_not_established_in_saved_note")
        self.p = dict(schema=old.SCHEMA, qualification=dict(passed=True), frozen_at=old.iso(self.start - 1),
            t0=old.iso(self.start), intake_end=old.iso(self.start + 7 * 86400),
            final_end=old.iso(self.start + 9 * 86400), provider_end=old.iso(self.start + 86400),
            run_limit=10, exposure_limit=3, followup_seconds=48 * 3600, provider_attempt_limit=5000,
            provider_collection_allowance_seconds=120, unattended_actor="claude-heartbeat",
            cases={"worker-single-item": case, "comment-as-call": dict(case, source="astrid/other.rs", historical_storage="saved_note")},
            allowlist=dict(authority="read_only_existing_files_no_source_commands", astrid_root=str(self.root / "source"),
                runs_directory="runs", notes_directory="notes", provider_spool=str(self.root / "source/provider")),
            code={}, anchors_sha256=old.sha(old.encoded({"anchors": "fixture"})))
        self.a = dict(schema="bounded_followups_provider_amendment_v1", original_protocol_sha256=old.sha(old.encoded(self.p)),
            original_cohort_t0=self.p["t0"], original_intake_end=self.p["intake_end"], original_final_end=self.p["final_end"],
            provider_t0=old.iso(self.start + 60), provider_end=old.iso(self.start + 86460), provider_collection_allowance_seconds=120)
        for name in ("runs", "notes", "provider/events", "provider/raw", "capsules/spectral-bridge/workspace/introspections"):
            (self.root / "source" / name).mkdir(parents=True, exist_ok=True)
        self.mapping = dict(schema="bounded_followups_source_equivalence_v1", case="worker-single-item",
                            old_revision=self.old_hash, new_revision=self.new_hash,
                            old_interval=[2, 9], new_interval=[4, 11])

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(old.encoded(value))
        return path

    def runfile(self, offset, **changes):
        ident = f"run_{int((self.start + offset) * 10**9)}_a"
        value = dict(schema="steward_run_receipt_v1", run_id=ident, actor="claude-heartbeat", adapter_kind="subprocess",
                     started_at=old.iso(self.start + offset), finished_at=old.iso(self.start + offset + 10),
                     status="finished", outcome="failed", secret="never retained")
        value.update(changes)
        self.put(self.root / "source/runs" / (ident + ".json"), value)
        return ident

    def page(self, body, digest, lo, hi, ident):
        text = "".join(f"{n} | {line}\n" for n, line in enumerate(body[lo:hi].decode().splitlines(), 1))
        return dict(source="astrid/source.rs", revision=dict(sha256=digest, bytes=len(body), lines=body.count(b"\n")),
                    id=ident, start=dict(byte=lo, line=1), end=dict(byte=hi, line=2), eof=hi == len(body), text=text)

    def record(self, page):
        return old.retained("/original/source/never-follow.json", old.encoded(dict(page=page)), "delivery")

    def fixture(self):
        data = self.root / "retained"
        pages = [self.page(self.new_source, self.new_hash, 0, 9, "p1"),
                 self.page(self.new_source, self.new_hash, 9, 11, "p2")]
        records = [self.record(self.page(self.old_source, self.old_hash, 0, 9, "old")),
                   *[self.record(p) for p in pages]]
        rows = []
        for n, page in enumerate(pages, 1):
            rows.append(dict(id=f"g{n}", completed=old.iso(self.start + n), record_sha256=str(n) * 64,
                response_sha256="b" * 64, text="A fixture response.", user_text="source fixture", actual_route="source_study",
                receipt_verified=True, notebook=dict(status="included_in_submitted_user_text", sha256="n" * 64,
                    fields=dict(note=None, question=None, previous=None)), system_hashes=["s" * 64], era="reviewed", pid=1,
                pages=[{k: v for k, v in page.items() if k != "text"}]))
        report = dict(schema="source_study_fidelity_daily_v6", studies=rows, capture_errors=[], join_issues=[],
                      selection=dict(since=old.iso(self.start - 100), until_exclusive=old.iso(self.start + 86400)))
        report_raw = old.encoded(report)
        verification = dict(report_sha256=old.sha(report_raw), replay_identical=True)
        capture = dict(records=records)
        daily_manifest = {"final-report/report.json": old.sha(report_raw), "verification.json": old.sha(old.encoded(verification)),
                          "capture.json": old.sha(old.encoded(capture))}
        packet_hash = old.sha(old.encoded(daily_manifest))
        finalization = dict(schema="s007-daily-finalization-v1", packet_manifest_sha256=packet_hash)
        replay = dict(status="passed", exit_code=0, packet_manifest_sha256=packet_hash,
                      network_denied=True, ledger_modified=False)
        empty = dict(status="captured", records=[], errors=[], inventories=[])
        historical = dict(protocol_sha256=old.sha(old.encoded(self.p)), runs=empty, provider=empty)
        plan = dict(code=close.identity())
        recovered = dict(historical, plan_sha256=old.sha(old.encoded(plan)), source_metadata={})
        definitions = {"protocol.json": self.p, "amendment.json": self.a, "anchors.json": {"anchors": "fixture"},
            "old-capture.json": historical, "recovery.json": recovered, "recovery-plan.json": plan,
            "source-review.json": self.mapping, "daily/packet-manifest.json": daily_manifest,
            "daily/final-report/report.json": report, "daily/verification.json": verification, "daily/capture.json": capture,
            "daily-finalization.json": finalization, "daily-replay.json": replay}
        for name, value in definitions.items():
            self.put(data / name, value)
        manifest = dict(schema=close.SCHEMA, files={n: old.sha(old.encoded(v)) for n, v in definitions.items()},
            protocol="protocol.json", provider_amendment="amendment.json", anchors="anchors.json",
            historical_captures=["old-capture.json"], recovery_capture="recovery.json", recovery_plan="recovery-plan.json",
            daily_packets=["daily"], source_captures=["daily/capture.json"], source_review="source-review.json",
            daily_acceptance={"daily": dict(finalization="daily-finalization.json", replay="daily-replay.json")},
            excluded_packets=[dict(packet="blocked-day", reason="verification_blocked")])
        return data, manifest

    def test_fixed_original_window_failed_runs_and_no_success_replacement(self):
        ids = [self.runfile(n) for n in range(1, 13)]
        self.runfile(-1)
        self.runfile(7 * 86400)
        cap = old.capture_runs(self.p, old.epoch(self.p["final_end"]), close.RecoveryReader(self.p))
        self.assertEqual(cap["selected_run_ids"], ids[:10])
        self.assertEqual(cap["eligible_run_count"], 12)
        self.assertNotIn("never retained", json.dumps(cap))
        self.assertTrue(all(r["terminal_state"] == "failed" for r in old.analyze_runs(self.p, [cap], old.epoch(self.p["final_end"]))["runs"]))

    def test_different_actor_and_deadline_remain_separate(self):
        self.runfile(1, actor="interactive")
        self.runfile(2, finished_at=old.iso(self.start + 2 + 48 * 3600))
        cap = old.capture_runs(self.p, old.epoch(self.p["final_end"]), close.RecoveryReader(self.p))
        result = old.analyze_runs(self.p, [cap], old.epoch(self.p["final_end"]))
        self.assertEqual(result["excluded_actor_counts"], {"interactive": 1})
        self.assertEqual(result["runs"][0]["terminal_state"], "right_censored")

    def test_combined_claim_summary_cap(self):
        base = self.root / "source/notes" / f"claude-heartbeat_{self.start + 2}_test"
        for sub in ("claims", "summaries"):
            for n in range(21):
                self.put(base / sub / f"{n}.json", {})
        reader = close.RecoveryReader(self.p)
        self.assertEqual(len(reader.names(base / "claims")), 21)
        with self.assertRaisesRegex(ValueError, "Combined"):
            reader.names(base / "summaries")

    def test_forbidden_path_and_symlink(self):
        outside = self.put(self.root / "source/lease.json", {"private": True})
        reader = close.RecoveryReader(self.p)
        with self.assertRaises(ValueError):
            reader.read(outside)
        link = self.root / "source/runs" / f"run_{self.start}_link.json"
        link.symlink_to(outside)
        with self.assertRaises(ValueError):
            reader.read(link)
        with self.assertRaises(ValueError):
            reader.names(self.root / "source")

    def test_directory_cap_cannot_produce_complete_selection(self):
        self.runfile(1)
        self.runfile(2)
        reader = close.RecoveryReader(self.p)
        reader.entry_limit = 1
        cap = old.capture_runs(self.p, self.start + 10, reader)
        self.assertEqual(cap["selected_run_ids"], [])
        self.assertFalse(cap["inventories"][0]["complete"])
        self.assertTrue(cap["errors"])

    def test_collector_uses_original_cutoff_and_shared_total_budget(self):
        observed = []
        def fake(p, now, reader):
            observed.append((p["t0"], now, reader.total_limit))
            reader.bytes = 123
            return dict(status="captured", records=[], errors=[], inventories=[])
        with mock.patch.object(old, "capture_runs", side_effect=fake), mock.patch.object(old, "capture_provider", side_effect=fake):
            result = close.collect_once(self.p, self.a)
        self.assertEqual([x[1] for x in observed], [old.epoch(self.p["final_end"])] * 2)
        self.assertEqual(observed[1][0], self.a["provider_t0"])
        self.assertEqual(observed[1][2], close.LIMITS["total_bytes"] - 123)
        self.assertEqual(result["source_bytes_read"], 246)

    def test_partial_or_absent_local_data_remains_incomplete_after_deadline(self):
        data, manifest = self.fixture()
        result = close.build_report(manifest, data)
        self.assertEqual(result["s006"]["runs"]["status"], "ready_for_review")
        self.assertEqual(result["s006"]["disposition"], "closed_incomplete_historical_evidence")
        self.assertIsNone(result["s006"]["actual_eligible_run_count"])
        self.assertFalse(result["s008"]["coverage"]["exhaustive"])
        self.assertEqual(result["s008"]["source_review"]["cases"]["worker-single-item"]["eligible_exposures"], 0)
        self.assertEqual(len(result["s008"]["source_review"]["cases"]["worker-single-item"]["revision_dispositions"]), 2)

    def test_exact_mapping_and_separate_pages_do_not_merge_exposures(self):
        data, manifest = self.fixture()
        result = close.build_report(manifest, data)
        review = result["s008"]["source_review"]
        self.assertEqual(review["anchor_bytes"], 7)
        self.assertTrue(all(x["full_hash_verified"] for x in review["reconstructed_sources"].values()))
        changed = copy.deepcopy(self.mapping)
        changed["new_interval"] = [5, 11]
        self.put(data / "source-review.json", changed)
        manifest["files"]["source-review.json"] = old.sha(old.encoded(changed))
        with self.assertRaisesRegex(ValueError, "exact and unique"):
            close.build_report(manifest, data)

    def test_fully_delivered_equivalent_anchor_requires_review(self):
        sources = {self.old_hash: (self.old_source, []), self.new_hash: (self.new_source, [])}
        case = dict(selected=[], historical_storage="saved_note", revision_review_candidates=[dict(generation_id="g",
            source_pages=[dict(revision=dict(sha256=self.new_hash), start=dict(byte=0), end=dict(byte=11))])])
        with self.assertRaisesRegex(ValueError, "requires separate"):
            close.resolve_revisions(self.p, dict(cases={"worker-single-item": case}), self.mapping, sources)

    def test_hash_changed_blocked_or_unknown_daily_packet_rejected(self):
        data, manifest = self.fixture()
        p = data / "daily/final-report/report.json"
        original = p.read_bytes()
        p.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            close.build_report(manifest, data)
        for changes in (dict(schema="unknown"), dict(join_issues=["blocked"]), dict(capture_errors=["missing"])):
            value = json.loads(original)
            value.update(changes)
            self.put(p, value)
            manifest["files"]["daily/final-report/report.json"] = old.sha(p.read_bytes())
            # Reseal the altered report: rejection must also inspect semantics.
            v = dict(report_sha256=old.sha(p.read_bytes()), replay_identical=True)
            self.put(data / "daily/verification.json", v)
            manifest["files"]["daily/verification.json"] = old.sha(old.encoded(v))
            packet = json.loads((data / "daily/packet-manifest.json").read_bytes())
            packet.update({"final-report/report.json": old.sha(p.read_bytes()), "verification.json": old.sha(old.encoded(v))})
            self.put(data / "daily/packet-manifest.json", packet)
            manifest["files"]["daily/packet-manifest.json"] = old.sha(old.encoded(packet))
            with self.assertRaises(ValueError):
                close.build_report(manifest, data)

    def test_explicit_inputs_refuse_escape_and_symlink(self):
        data, manifest = self.fixture()
        with self.assertRaises(ValueError):
            close.Inputs(manifest, data).raw("../outside")
        p = data / "anchors.json"
        p.unlink()
        p.symlink_to(self.put(self.root / "outside.json", {}))
        with self.assertRaises(ValueError):
            close.build_report(manifest, data)

    def test_relocated_replay_never_calls_capture_or_reads_original_paths(self):
        data, manifest = self.fixture()
        expected = close.build_report(manifest, data)
        moved = self.root / "moved"
        shutil.copytree(data, moved)
        shutil.rmtree(data)
        with mock.patch.object(old, "capture_runs", side_effect=AssertionError("live read")), \
             mock.patch.object(old, "capture_provider", side_effect=AssertionError("live read")), \
             mock.patch("socket.socket", side_effect=AssertionError("network")):
            self.assertEqual(close.build_report(manifest, moved), expected)

    def test_output_and_seal_refuse_overwrite(self):
        folder = self.root / "sealed"
        self.put(folder / "result.json", {})
        close.seal(folder)
        with self.assertRaises(ValueError):
            close.seal(folder)

    def test_recovered_run_requires_review_instead_of_zero_only_failure(self):
        run = dict(run_id="run1", followup_end=self.p["final_end"], terminal_state="failed")
        value = close.episode_dispositions(dict(runs=[run]), [dict(runs=dict(records=[]))])
        self.assertEqual(value[0]["disposition"], "needs_episode_review")
        review = dict(schema="s006_closeout_episode_reviews_v1", episodes=[dict(run_id="run1",
            undated_or_late_evidence_is_censored=True,
            stages={k: dict(status="unknown", summary="No retained evidence", evidence_sha256=[])
                    for k in ("authorship", "review", "response", "commit", "activation", "outcome")})])
        value = close.episode_dispositions(dict(runs=[run]), [dict(runs=dict(records=[]))], review)
        self.assertEqual(value[0]["disposition"], "reviewed_with_explicit_shortfalls")
        review["episodes"][0]["stages"]["outcome"]["status"] = "supported"
        with self.assertRaises(ValueError):
            close.episode_dispositions(dict(runs=[run]), [dict(runs=dict(records=[]))], review)

    def test_successful_integrity_without_accepted_research_replay_is_rejected(self):
        data, manifest = self.fixture()
        replay = json.loads((data / "daily-replay.json").read_bytes())
        replay["status"] = "blocked"
        self.put(data / "daily-replay.json", replay)
        manifest["files"]["daily-replay.json"] = old.sha(old.encoded(replay))
        with self.assertRaisesRegex(ValueError, "accepted offline replay"):
            close.build_report(manifest, data)

    def test_one_shot_claim_prevents_a_second_source_collection(self):
        data = self.root / "oneshot"
        code = close.identity()
        values = {"protocol.json": self.p, "amendment.json": self.a,
                  "qualification.json": dict(passed=True, code=code, test_log_sha256=old.sha(b"passed\n"))}
        for name, value in values.items():
            self.put(data / name, value)
        (data / "tests.log").write_bytes(b"passed\n")
        plan = dict(schema="bounded_followups_recovery_plan_v1", limits=close.LIMITS, code=code,
                    attempt_limit=1, remote_fallback=False, s007_access=False, frozen_at=old.iso(self.start),
                    files={p.name: old.sha(p.read_bytes()) for p in data.iterdir()},
                    protocol="protocol.json", provider_amendment="amendment.json",
                    qualification="qualification.json", qualification_log="tests.log", output="recovery",
                    windows=dict(t0=self.p["t0"], intake_end=self.p["intake_end"], final_end=self.p["final_end"],
                                 provider_t0=self.a["provider_t0"], provider_end=self.a["provider_end"],
                                 provider_outcome_end=old.iso(old.epoch(self.a["provider_end"]) + 120)))
        path = self.put(data / "plan.json", plan)
        empty = dict(status="captured", records=[], errors=[], inventories=[])
        captured = dict(runs=empty, provider=empty, source_bytes_read=0)
        def mkdir(p):
            p.mkdir(exist_ok=False)
            return p
        with mock.patch.object(close, "output_directory", side_effect=mkdir), \
             mock.patch.object(close, "collect_once", return_value=captured) as collect:
            close.recover(path, data)
            with self.assertRaises(FileExistsError):
                close.recover(path, data)
        self.assertEqual(collect.call_count, 1)
        self.assertTrue((data / "recovery/recovery-started.json").is_file())


if __name__ == "__main__":
    unittest.main()
