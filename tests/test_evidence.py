"""Captured evidence stays separate from source attestation and action inference."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.evidence import (
    EXTENSION_KEY, ensure_schema, import_evidence, read_bundle, validate_bundle,
)
from reservoir_research.store import connect


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.path = self.base / "capture.json"
        self.conn = connect(self.base / "cache" / "index.sqlite3", writable=True)
        self.addCleanup(self.conn.close)

    def record(self, record_id="requested", **changes):
        result = {
            "being": "minime", "kind": "action", "source_record_id": record_id,
            "occurred_at": 100, "ended_at": None, "action_id": "shared-action",
            "raw_next": "NEXT: READ local note", "effective_action": "read",
            "status": "requested", "payload": {"quoted": "literal ' ; -- text"},
            "source": {"path": "/unmounted/source/action.sqlite3", "sha256": "a" * 64,
                       "locator": {"table": "action_events", "row": record_id},
                       "hash_basis": "captured source row JSON, before normalization"},
        }
        result.update(changes)
        return result

    def bundle(self, records=None, **changes):
        records = [self.record()] if records is None else records
        result = {
            "schema_version": 1, "kind": "reservoir_episode_evidence",
            "capture": {"method": "synthetic read-only fixture", "clock": "declared epoch"},
            "coverage": [
                {"being": being, "kind": kind, "source_path": "/unmounted/source/records.sqlite3",
                 "since": 90, "until": 120, "status": "captured",
                 "rows_examined": len(records), "rows_selected": len(records),
                 "notes": ["This fixture is not a live-source attestation."]}
                for being, kind in sorted({(r["being"], r["kind"]) for r in records} or {("minime", "action")})
            ],
            "records": records,
        }
        result.update(changes)
        return result

    def write(self, bundle=None, path=None, **json_options):
        path = path or self.path
        path.write_text(json.dumps(self.bundle() if bundle is None else bundle, **json_options), encoding="utf-8")
        return path

    def rows(self, table):
        self.assertIn(table, {"observations", "evidence_imports", "runs"})
        return self.conn.execute(f"SELECT * FROM {table}").fetchall()

    def test_optional_schema_is_idempotent_and_preserves_base_version(self):
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        before_meta = self.conn.execute("SELECT * FROM research_meta").fetchall()
        ensure_schema(self.conn)
        ensure_schema(self.conn)
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], version)
        self.assertEqual(self.conn.execute("SELECT value FROM research_meta WHERE key=?", (EXTENSION_KEY,)).fetchone()[0], "1")
        self.assertEqual(len(self.conn.execute("SELECT * FROM research_meta").fetchall()), len(before_meta) + 1)
        self.assertEqual(self.rows("observations"), [])

    def test_provenance_payload_and_metric_ownership_are_preserved(self):
        telemetry = self.record("sample", kind="telemetry", occurred_at=None, action_id=None,
                                metrics={"sensory_field.lambda1": 0.4, "reservoir.lambda1": 0.8},
                                handle="reservoir-A", subsystem="ESN", unit="dimensionless",
                                time_semantics="source timestamp unavailable")
        bundle = self.bundle([self.record(), telemetry])
        original = copy.deepcopy(bundle)
        path = self.write(bundle)
        raw = path.read_bytes()
        summary = import_evidence(self.conn, path)
        self.assertEqual(summary["counts"]["observations_added"], 2)
        self.assertEqual(bundle, original)
        imported = self.rows("evidence_imports")[0]
        self.assertEqual(imported["bundle_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(imported["capture_json"]), bundle["capture"])
        observation = self.conn.execute("SELECT * FROM observations WHERE kind='telemetry'").fetchone()
        stored = json.loads(observation["record_json"])
        for key in ("source", "metrics", "payload", "handle", "subsystem", "unit", "time_semantics"):
            self.assertEqual(stored[key], telemetry[key])
        self.assertIsNone(observation["occurred_at"])
        self.assertEqual(observation["source_sha256"], "a" * 64)
        self.assertNotEqual(observation["source_sha256"], imported["bundle_sha256"])
        self.assertIsNone(stored["outcome_summary"])
        self.assertIn("not verified", summary["scope"])

    def test_semantically_identical_imports_do_not_duplicate_records_or_captures(self):
        first = import_evidence(self.conn, self.write())
        second_path = self.base / "indented.json"
        second = import_evidence(self.conn, self.write(path=second_path, indent=3))
        self.assertEqual(first["import_id"], second["import_id"])
        self.assertNotEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertEqual(len(self.rows("observations")), 1)
        self.assertEqual(len(self.rows("evidence_imports")), 1)
        self.assertEqual(second["counts"]["observations_existing"], 1)
        self.assertEqual(second["counts"]["imports_added"], 0)
        runs = self.rows("runs")
        self.assertEqual([r["status"] for r in runs], ["complete", "complete"])
        self.assertEqual(json.loads(runs[1]["options_json"])["path"], str(second_path))

    def test_new_capture_can_retain_existing_record_without_reassigning_origin(self):
        first = import_evidence(self.conn, self.write())
        bundle = self.bundle(capture={"method": "second capture", "notes": "same retained source record"})
        second = import_evidence(self.conn, self.write(bundle))
        self.assertNotEqual(first["import_id"], second["import_id"])
        self.assertEqual(len(self.rows("evidence_imports")), 2)
        self.assertEqual(len(self.rows("observations")), 1)
        self.assertEqual(self.rows("observations")[0]["import_id"], first["import_id"])
        self.assertEqual(len(json.loads(self.rows("evidence_imports")[1]["bundle_json"])["records"]), 1)

    def test_lifecycle_and_conflicting_captures_keep_separate_observations(self):
        requested = self.record()
        completed = self.record("completed", occurred_at=105, ended_at=108,
                                status="complete", outcome_summary="source reported completion")
        conflicting = copy.deepcopy(completed)
        conflicting["status"] = "failed"
        conflicting["source"]["sha256"] = "b" * 64
        import_evidence(self.conn, self.write(self.bundle([requested, completed, conflicting])))
        rows = self.rows("observations")
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["action_id"] for r in rows}, {"shared-action"})
        self.assertEqual({r["status"] for r in rows}, {"requested", "complete", "failed"})
        self.assertEqual(len({r["id"] for r in rows}), 3)
        self.assertEqual(sum(r["source_record_id"] == "completed" for r in rows), 2)

    def test_invalid_record_rejects_entire_bundle_before_any_database_change(self):
        invalid_cases = [
            ("occurred_at", True), ("occurred_at", float("nan")),
            ("ended_at", 99), ("being", "someone_else"), ("kind", "journal"),
            ("source_record_id", ""), ("metrics", {"x": float("inf")}),
            ("payload", []), ("action_id", 123),
        ]
        baseline = self.conn.iterdump()
        before = list(baseline)
        for field, value in invalid_cases:
            with self.subTest(field=field, value=value):
                invalid = self.record("invalid")
                invalid[field] = value
                with self.assertRaises(ValueError):
                    import_evidence(self.conn, self.write(self.bundle([self.record(), invalid])))
                self.assertEqual(list(self.conn.iterdump()), before)

    def test_provenance_coverage_and_timing_validation(self):
        changes = [
            lambda b: b["records"][0]["source"].pop("hash_basis"),
            lambda b: b["records"][0]["source"].update(sha256="not a digest"),
            lambda b: b["records"][0]["source"].update(locator={}),
            lambda b: b["coverage"][0].update(since=120),
            lambda b: b["coverage"][0].update(until=False),
            lambda b: b["coverage"][0].update(rows_examined=0, rows_selected=1),
            lambda b: b["coverage"][0].update(being="astrid"),
            lambda b: b["coverage"][0].update(kind=[]),
            lambda b: b["records"][0].update(being={}),
            lambda b: b.update(schema_version=True),
        ]
        for change in changes:
            with self.subTest(change=change):
                bundle = self.bundle()
                change(bundle)
                with self.assertRaises(ValueError):
                    validate_bundle(bundle)

    def test_finite_epochs_must_also_be_representable_in_reports(self):
        for section, field, value in (("records", "ended_at", 1e100),
                                      ("records", "occurred_at", -1e100),
                                      ("coverage", "since", -1e100),
                                      ("coverage", "until", 1e100)):
            with self.subTest(section=section, field=field):
                bundle = self.bundle()
                bundle[section][0][field] = value
                with self.assertRaisesRegex(ValueError, "calendar range"):
                    validate_bundle(bundle)

    def test_source_pointers_are_never_opened_or_modified(self):
        source = self.base / "retained-source.sqlite3"
        source.write_bytes(b"not a sqlite database; never open this")
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        record = self.record()
        record["source"]["path"] = str(source)
        record["source"]["locator"] = {"path": "/nonexistent/do-not-follow", "sql": "DROP TABLE observations"}
        path = self.write(self.bundle([record]))
        real_open = os.open
        def guarded_open(candidate, *args, **kwargs):
            if str(candidate) == source.name or str(candidate) == str(source):
                raise AssertionError("Importer followed an encoded source pointer")
            return real_open(candidate, *args, **kwargs)
        with patch("reservoir_research.evidence.os.open", side_effect=guarded_open):
            import_evidence(self.conn, path)
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
        self.assertEqual(len(self.rows("observations")), 1)
        run_options = json.loads(self.rows("runs")[0]["options_json"])
        self.assertFalse(run_options["source_pointers_followed"])

    def test_reader_is_bounded_and_refuses_symlink_inputs(self):
        path = self.write()
        with self.assertRaises(ValueError):
            read_bundle(path, max_bytes=8)
        link = self.base / "linked.json"
        link.symlink_to(path)
        with self.assertRaises(OSError):
            read_bundle(link)
        directory_link = self.base / "linked-directory"
        directory_link.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(OSError):
            read_bundle(directory_link / path.name)
        path.write_text('{"schema_version": 1, "bad": NaN}')
        with self.assertRaisesRegex(ValueError, "Invalid evidence JSON"):
            read_bundle(path)

    def test_runtime_failure_rolls_back_whole_import_and_retains_failed_run(self):
        baseline = import_evidence(self.conn, self.write())
        old_observations = [dict(r) for r in self.rows("observations")]
        self.conn.execute("""CREATE TRIGGER reject_fixture BEFORE INSERT ON observations
            WHEN NEW.source_record_id='reject' BEGIN SELECT RAISE(FAIL, 'fixture failure'); END""")
        self.conn.commit()
        bundle = self.bundle([self.record("new-first"), self.record("reject")])
        with self.assertRaisesRegex(sqlite3.IntegrityError, "fixture failure"):
            import_evidence(self.conn, self.write(bundle))
        self.assertEqual([dict(r) for r in self.rows("observations")], old_observations)
        self.assertEqual([r["id"] for r in self.rows("evidence_imports")], [baseline["import_id"]])
        failed = self.rows("runs")[-1]
        self.assertEqual(failed["status"], "failed")
        self.assertTrue(json.loads(failed["summary_json"])["rolled_back"])

    def test_write_guard_protects_registered_and_declared_sources(self):
        self.conn.execute("INSERT INTO sources(being,root,kind) VALUES (?,?,?)",
                          ("minime", str(self.base / "cache"), "journal"))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "source tree"):
            ensure_schema(self.conn)
        self.conn.execute("DELETE FROM sources")
        self.conn.commit()
        bundle = self.bundle()
        bundle["coverage"][0]["source_path"] = str(self.base / "cache")
        with self.assertRaisesRegex(ValueError, "declared evidence source"):
            import_evidence(self.conn, self.write(bundle))
        self.assertEqual(self.rows("runs"), [])
        with patch("reservoir_research.store.protected_roots", return_value=[self.base / "cache"]):
            with self.assertRaisesRegex(ValueError, "source tree"):
                ensure_schema(self.conn)

    def test_unrelated_or_unversioned_tables_and_pending_transactions_are_refused(self):
        unrelated = sqlite3.connect(":memory:")
        self.addCleanup(unrelated.close)
        with self.assertRaisesRegex(ValueError, "existing reservoir-research cache"):
            ensure_schema(unrelated)
        self.conn.execute("CREATE TABLE observations(unrelated TEXT)")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "Unversioned"):
            ensure_schema(self.conn)
        self.assertEqual(self.conn.execute("PRAGMA table_info(observations)").fetchone()[1], "unrelated")
        self.conn.execute("INSERT INTO research_meta VALUES ('pending', 'value')")
        with self.assertRaisesRegex(ValueError, "pending transaction"):
            import_evidence(self.conn, self.write())


if __name__ == "__main__":
    unittest.main()
