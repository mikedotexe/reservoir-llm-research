"""Episode evidence stays bounded, attributed, reproducible, and cache-only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.episodes import collect_episode, export_episode


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE catalog (
                id TEXT PRIMARY KEY, being TEXT, canonical_name TEXT, occurred_at REAL,
                lane TEXT, content_kind TEXT, body_text TEXT, header_text TEXT, raw_text TEXT,
                body_sha256 TEXT, raw_sha256 TEXT, metadata_json TEXT, warnings_json TEXT,
                next_raw TEXT, next_verb TEXT, source_path TEXT, backend TEXT, prompt_available INTEGER);
            CREATE TABLE generations (
                id TEXT PRIMARY KEY, being TEXT, occurred_at REAL, lane TEXT, backend TEXT,
                status TEXT, prompt_text TEXT, prompt_available INTEGER, response_text TEXT,
                response_sha256 TEXT, journal_refs_json TEXT, metadata_json TEXT,
                warnings_json TEXT, source_path TEXT, source_sha256 TEXT);
            CREATE TABLE observations (
                id TEXT PRIMARY KEY, import_id TEXT, being TEXT, kind TEXT, source_record_id TEXT,
                occurred_at REAL, ended_at REAL, action_id TEXT, parent_action_id TEXT,
                thread_id TEXT, job_id TEXT, raw_next TEXT, effective_action TEXT, route TEXT,
                status TEXT, outcome_summary TEXT, source_path TEXT, source_sha256 TEXT, record_json TEXT);
            CREATE TABLE evidence_imports (
                id TEXT PRIMARY KEY, bundle_path TEXT, bundle_sha256 TEXT, imported_at REAL,
                capture_json TEXT, coverage_json TEXT, bundle_json TEXT, run_id INTEGER);
            CREATE TABLE sources (id TEXT PRIMARY KEY, path TEXT, status TEXT);
            CREATE TABLE runs (id INTEGER PRIMARY KEY, options_json TEXT, summary_json TEXT);
            INSERT INTO sources VALUES ('s1','/never-read/live','partial');
            INSERT INTO runs VALUES (1,'{"since":100,"until":200}','{"coverage":"partial"}');
            PRAGMA user_version=7;
        """)
        self.conn.execute("INSERT INTO evidence_imports VALUES (?,?,?,?,?,?,?,?)", (
            "imp", "/never-read/bundle.json", "a" * 64, 300,
            json.dumps({"captured_at": 300}),
            json.dumps([{"being": "astrid", "status": "partial", "since": 100, "until": 200}]),
            "{}", 1))

    def tearDown(self):
        self.conn.close()

    def add(self, table, values):
        columns = ",".join(values)
        placeholders = ",".join("?" for _ in values)
        self.conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(values.values()))

    def journal(self, record_id, being="minime", at=120, text="I wonder what changes.", **extras):
        raw = "Date: declared\n\n" + text
        self.add("catalog", {"id": record_id, "being": being, "canonical_name": record_id + ".txt",
            "occurred_at": at, "lane": "self_study", "content_kind": "prose", "body_text": text,
            "header_text": "Date: declared", "raw_text": raw, "body_sha256": digest(text),
            "raw_sha256": digest(raw), "metadata_json": "{}", "warnings_json": "[]",
            "next_raw": "NEXT: SCRIPT inspect", "next_verb": "SCRIPT",
            "source_path": "/never-read/" + record_id + ".txt", "backend": None, "prompt_available": 0, **extras})

    def generation(self, record_id, being="minime", at=120, source=None, **extras):
        self.add("generations", {"id": record_id, "being": being, "occurred_at": at,
            "lane": "legacy", "status": "recorded", "prompt_text": "partial prompt", "prompt_available": 0,
            "response_text": "cached response", "response_sha256": digest("cached response"),
            "journal_refs_json": "[]", "metadata_json": json.dumps({"source_record": source or {}}),
            "warnings_json": "[]", "source_path": "/never-read/" + record_id + ".json",
            "source_sha256": "b" * 64, **extras})

    def observation(self, record_id, being="minime", at=120, kind="action", end=None, action_id=None, record=None, **extras):
        source_record = {"kind": kind, "occurred_at": at, "ended_at": end, "payload": {"original": record_id}, **(record or {})}
        self.add("observations", {"id": record_id, "import_id": "imp", "being": being, "kind": kind,
            "source_record_id": record_id, "occurred_at": at, "ended_at": end, "action_id": action_id,
            "raw_next": "NEXT: READ_MORE", "effective_action": "READ_MORE", "status": "requested",
            "route": "queue", "source_path": "/never-read/actions.jsonl", "source_sha256": "c" * 64,
            "record_json": json.dumps(source_record), **extras})

    def denominator(self, result, being, kind):
        return next(d for d in result["denominators"] if d["being"] == being and d["kind"] == kind)

    def test_both_archives_half_open_points_complete_cached_text_and_hashes(self):
        self.journal("start", "astrid", 100, "```\nsource text\n````\nΩ")
        self.journal("middle", "minime", 150)
        self.journal("before", "astrid", 99.999)
        self.journal("end", "minime", 200)
        self.journal("undated", at=None)
        with patch("builtins.open", side_effect=AssertionError("must not read sources")), patch.object(Path, "read_text", side_effect=AssertionError("must not read sources")):
            result = collect_episode(self.conn, 100, 200, "America/Los_Angeles")
        self.assertEqual([r["id"] for r in result["records"]], ["start", "middle"])
        row = result["records"][0]
        self.assertEqual(row["cached_field_sha256"]["raw_text"], row["data"]["raw_sha256"])
        self.assertEqual(row["data"]["next_raw"], "NEXT: SCRIPT inspect")
        self.assertEqual(row["data"]["body_text"], "```\nsource text\n````\nΩ")
        self.assertIn("-08:00", row["start_local"])
        self.assertEqual(self.denominator(result, "minime", "journal")["undated_before_time_filter"], 1)
        self.assertEqual(result["index_snapshot"]["user_version"], 7)
        self.assertEqual(result["evidence_imports"][0]["coverage"][0]["status"], "partial")

    def test_intervals_spanning_and_ending_at_start_plus_outside_completion(self):
        self.observation("touch-start", at=90, end=100, action_id="a")
        self.observation("span", at=80, end=210, action_id="b")
        self.observation("too-early", at=80, end=99)
        self.observation("at-until", at=200, action_id="c")
        self.observation("later-completion", at=220, action_id="a", status="completed")
        self.observation("unrelated", at=220, action_id="unrelated")
        self.observation("other-being-same-id", being="astrid", at=220, action_id="a")
        self.observation("end-only", at=None, end=130)
        self.observation("invalid-interval", at=150, end=120)
        result = collect_episode(self.conn, 100, 200)
        self.assertEqual({r["id"] for r in result["records"]}, {"touch-start", "span", "end-only", "invalid-interval"})
        self.assertEqual([r["id"] for r in result["identity_context"]], ["later-completion"])
        self.assertEqual(result["identity_context"][0]["selection"], "same_explicit_action_id_outside_window")
        self.assertEqual(self.denominator(result, "minime", "action")["matching_in_window"], 4)
        self.assertTrue(next(r for r in result["records"] if r["id"] == "span")["ends_after_window"])
        self.assertIn("end precedes start", next(r for r in result["records"] if r["id"] == "invalid-interval")["timing_warning"])

    def test_generations_explicit_duration_creation_meaning_and_normalized_cap_order(self):
        self.generation("creation-late-start-early", at=190, source={"started_at": 80, "duration_ms": 40000})
        self.generation("creation-early-start-late", at=101, source={"started_at": 180, "ended_at": 185})
        self.generation("creation-only", being="astrid", at=110, source={"duration_ms": 40000})
        result = collect_episode(self.conn, 100, 200, limit=1)
        self.assertEqual([r["id"] for r in result["records"]], ["creation-late-start-early", "creation-only"])
        self.assertEqual(result["records"][0]["end_at"], 120)
        self.assertIn("derived from declared duration", result["records"][0]["time_basis"])
        self.assertIsNone(result["records"][1]["end_at"])
        self.assertIn("execution start not inferred", result["records"][1]["time_basis"])
        self.assertEqual(self.denominator(result, "minime", "generation")["omitted_by_cap"], 1)

    def test_lifecycle_dedup_unknown_identity_and_status_remain_evidence(self):
        self.observation("request", at=110, action_id="same")
        self.observation("handled", at=115, action_id="same", status="handled", parent_action_id="previous")
        self.observation("blocked", being="astrid", at=120, action_id="same", status="blocked", route="unwired")
        self.observation("anonymous", at=125, status="timeout", outcome_summary="worker did not reply")
        result = collect_episode(self.conn, 100, 200, limit=1)
        counts = {c["being"]: c for c in result["action_counts"]}
        self.assertEqual(counts["minime"]["matching_action_records"], 3)
        self.assertEqual(counts["minime"]["observed_distinct_action_ids"], 1)
        self.assertEqual(counts["minime"]["records_without_action_id"], 1)
        self.assertEqual(counts["astrid"]["observed_distinct_action_ids"], 1)
        lifecycle = next(a for a in result["actions"] if a["being"] == "minime")["lifecycle"]
        self.assertEqual([r["status"] for r in lifecycle], ["requested", "handled"])
        self.assertNotIn("success", result)
        self.assertEqual({lead["record_id"] for lead in result["review_leads"]}, {"blocked"})
        self.assertIn("all matched", result["summary_scope"])
        uncapped = collect_episode(self.conn, 100, 200)
        with tempfile.TemporaryDirectory() as directory:
            paths = export_episode(uncapped, Path(directory) / "pack")
            markdown = Path(paths["markdown"]).read_text()
        self.assertIn("action identity unknown · anonymous", markdown)
        self.assertIn("worker did not reply", markdown)
        self.assertIn("Handled is not assumed successful", markdown)

    def test_telemetry_named_units_producer_subsystem_notes_and_all_matched_scope(self):
        base = {"producer": "minime", "subsystem": "sensory_field_covariance", "handle": None,
                "session_id": 5316, "engine_t_ms": 300000, "units": {"lambda1_ambiguous": "fraction"},
                "measurement_note": "action start proxy, capture time unknown"}
        for i, value in enumerate((0.3, 0.1, 0.8)):
            self.observation("t" + str(i), at=110+i, kind="telemetry", record={"metrics": {**base, "lambda1_ambiguous": value}})
        self.observation("other-subsystem", at=113, kind="telemetry", record={"metrics": {**base, "subsystem": "native_reservoir_state_covariance", "lambda1_ambiguous": 0.9}})
        self.observation("Hz", at=114, kind="telemetry", record={"unit": "Hz", "metrics": {"rate": 1.0}})
        self.observation("kHz", at=115, kind="telemetry", record={"unit": "kHz", "metrics": {"rate": 1.0}})
        result = collect_episode(self.conn, 100, 200, limit=1)
        self.assertEqual(len(result["telemetry"]), 4)
        sensory = next(m for m in result["telemetry"] if m["subsystem"] == "sensory_field_covariance")
        self.assertEqual(sensory["producer"], "minime")
        self.assertEqual(sensory["unit"], "fraction")
        self.assertEqual(sensory["count"], 3)
        self.assertEqual(sensory["first"]["value"], 0.3)
        self.assertEqual(sensory["last"]["value"], 0.8)
        self.assertEqual(sensory["min"]["observation_id"], "t1")
        self.assertEqual(sensory["max"]["at"], 112)
        self.assertEqual(sensory["measurement_notes"], [base["measurement_note"]])
        self.assertEqual({m["unit"] for m in result["telemetry"] if m["metric"] == "rate"}, {"Hz", "kHz"})
        self.assertEqual(self.denominator(result, "minime", "telemetry")["omitted_by_cap"], 5)
        self.assertEqual(result["returned"], 1)

    def test_missing_evidence_distinct_from_zero_cached_and_undated(self):
        self.observation("undated", at=None, action_id="unknown-time")
        result = collect_episode(self.conn, 100, 200)
        self.assertEqual(self.denominator(result, "minime", "action")["matching_in_window"], 0)
        self.assertEqual(self.denominator(result, "minime", "action")["undated_before_time_filter"], 1)
        self.assertIn("does not establish zero live activity", next(g for g in result["gaps"] if g["kind"] == "action")["note"])
        self.conn.execute("DROP TABLE observations")
        result = collect_episode(self.conn, 100, 200)
        self.assertIsNone(self.denominator(result, "minime", "action")["matching_in_window"])
        self.assertIsNone(result["action_counts"][0]["observed_distinct_action_ids"])
        self.assertIn("unavailable", next(g for g in result["gaps"] if g["kind"] == "action")["note"])

    def test_mirror_declared_authorship_unique_source_and_ambiguous_source(self):
        declarations = [{"name": "Provenance", "value": "minime_observed_expression"},
            {"name": "Authorship", "value": "minime_owned_reflected_without_reauthoring"},
            {"name": "Source-ID", "value": "minime_journal:original.txt"}]
        self.journal("mirror", "astrid", 110, lane="mirror", metadata_json=json.dumps({"header_fields": declarations}))
        self.journal("original", "minime", 50)
        result = collect_episode(self.conn, 100, 200)
        provenance = result["records"][0]["declared_provenance"]
        self.assertEqual(provenance["declared_source_links"][0]["target"]["id"], "original")
        with tempfile.TemporaryDirectory() as directory:
            paths = export_episode(result, Path(directory) / "pack")
            markdown = Path(paths["markdown"]).read_text()
        self.assertIn("Recorded mirror material", markdown)
        self.assertIn("minime_owned_reflected_without_reauthoring", markdown)
        self.assertIn("not inferred authored writings", markdown)
        self.journal("alias", at=51, canonical_name="original.txt")
        linked = collect_episode(self.conn, 100, 200)["records"][0]["declared_provenance"]["declared_source_links"][0]
        self.assertEqual(linked["matching_cached_records"], 2)
        self.assertIsNone(linked["target"])

    def test_fresh_private_reproducible_export_and_reader_notes_preserved(self):
        self.journal("body", text="````\nbody\n```\nΩ")
        result = collect_episode(self.conn, 100, 200)
        self.assertEqual(result, collect_episode(self.conn, 100, 200))
        with tempfile.TemporaryDirectory() as directory:
            one = export_episode(result, Path(directory) / "one")
            two = export_episode(result, Path(directory) / "two")
            self.assertEqual(Path(one["json"]).read_bytes(), Path(two["json"]).read_bytes())
            self.assertEqual(Path(one["markdown"]).read_bytes(), Path(two["markdown"]).read_bytes())
            self.assertEqual(Path(one["json"]).stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(one["json"]).parent.stat().st_mode & 0o777, 0o700)
            Path(one["markdown"]).write_text("reader notes")
            with self.assertRaises(FileExistsError):
                export_episode(result, Path(directory) / "one")
            self.assertEqual(Path(one["markdown"]).read_text(), "reader notes")
            changed = deepcopy(result)
            changed["records"][0]["data"]["body_text"] = "changed"
            with self.assertRaisesRegex(ValueError, "integrity"):
                export_episode(changed, Path(directory) / "tampered")
            self.assertFalse((Path(directory) / "tampered").exists())

    def test_invalid_parameters_and_caller_transaction_unchanged(self):
        self.journal("pending")
        self.assertTrue(self.conn.in_transaction)
        collect_episode(self.conn, 100, 200)
        self.assertTrue(self.conn.in_transaction)
        for kwargs in ({"since": 200, "until": 100}, {"since": float("nan"), "until": 200},
                       {"since": True, "until": 200}, {"since": 100, "until": 200, "limit": 0},
                       {"since": 100, "until": 200, "timezone_name": "not/a/timezone"}):
            with self.assertRaises(ValueError):
                collect_episode(self.conn, **kwargs)
        self.conn.rollback()
        self.assertEqual(self.conn.execute("SELECT count(*) FROM catalog").fetchone()[0], 0)

    def test_time_bounded_raw_queries_preserve_global_denominators(self):
        self.journal("inside", at=150)
        self.journal("outside", at=10)
        self.observation("old", at=10)
        self.observation("inside-action", at=150)
        queries = []
        self.conn.set_trace_callback(queries.append)
        result = collect_episode(self.conn, 100, 200)
        self.conn.set_trace_callback(None)
        self.assertEqual(self.denominator(result, "minime", "journal")["total_indexed"], 2)
        self.assertEqual(self.denominator(result, "minime", "action")["total_indexed"], 2)
        self.assertEqual({r["id"] for r in result["records"]}, {"inside", "inside-action"})
        journal_query = next(q for q in queries if q.startswith("SELECT * FROM catalog"))
        observation_query = next(q for q in queries if q.startswith("SELECT * FROM observations"))
        self.assertIn("occurred_at>=100.0 AND occurred_at<200.0", journal_query)
        self.assertIn("ended_at>=100.0", observation_query)
        self.assertIn("occurred_at<200.0", observation_query)

    def test_long_shared_prefix_ids_have_distinct_stable_paired_references(self):
        for suffix in ("a" * 64, "b" * 64):
            self.observation("observation_" + suffix, action_id=suffix)
            self.generation("minime:legacy:job_" + suffix + ":status.json")
        result = collect_episode(self.conn, 100, 200)
        with tempfile.TemporaryDirectory() as directory:
            paths = export_episode(result, Path(directory) / "pack")
            markdown = Path(paths["markdown"]).read_text()
        sequence = markdown.split("## Recorded sequence", 1)[1].split("## Astrid", 1)[0]
        rows = [line.split(" | ") for line in sequence.splitlines() if "minime / " in line]
        references = [row[2] for row in rows]
        self.assertEqual(len(references), 4)
        self.assertEqual(len(set(references)), 4)
        for reference in references:
            self.assertIn(reference.split(":", 1)[0], {"action", "generation"})
            self.assertIn('"reference": "' + reference + '"', markdown)
        self.assertNotIn("observation_…", sequence)
        self.assertNotIn("minime:legac…", sequence)
        self.assertEqual(result, collect_episode(self.conn, 100, 200))


if __name__ == "__main__":
    unittest.main()
