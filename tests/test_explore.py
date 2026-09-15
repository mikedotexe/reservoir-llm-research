"""Discovery tests use a small, handcrafted cached index, never live journals."""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from reservoir_research.explore import candidate_questions, export_pack, recurrence, sample, search


class ExploreTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE catalog (
              id TEXT PRIMARY KEY, being TEXT, lane TEXT, occurred_at REAL,
              content_kind TEXT, body_text TEXT, header_text TEXT, raw_text TEXT,
              body_sha256 TEXT, raw_sha256 TEXT, metadata_json TEXT, warnings_json TEXT,
              next_raw TEXT, next_verb TEXT, contract TEXT, time_source TEXT,
              canonical_name TEXT, mike_flag INTEGER, source_path TEXT, backend TEXT,
              prompt_available INTEGER);
            CREATE VIRTUAL TABLE entry_fts USING fts5(entry_id UNINDEXED,body_text);
            CREATE TABLE candidates(entry_id TEXT,ordinal INTEGER,kind TEXT,text TEXT,
                                    start_offset INTEGER,end_offset INTEGER);
            PRAGMA user_version=1;
        """)

    def tearDown(self):
        self.conn.close()

    def add(self, entry_id, body="An ordinary observation.", being="astrid", time=0,
            kind="prose", lane="moment", raw=None):
        raw = "Header\n" + body if raw is None else raw
        values = dict(id=entry_id, being=being, lane=lane, occurred_at=time,
                      content_kind=kind, body_text=body, header_text="Header", raw_text=raw,
                      body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                      raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), metadata_json="{}",
                      warnings_json="[]", next_raw=None, next_verb=None, contract=None,
                      time_source="fixture", canonical_name=entry_id + ".txt", mike_flag=0,
                      source_path="/not-mounted/live/" + entry_id + ".txt", backend=None,
                      prompt_available=0)
        self.conn.execute("INSERT INTO catalog (" + ",".join(values) + ") VALUES (" +
                          ",".join("?" for _ in values) + ")", list(values.values()))
        self.conn.execute("INSERT INTO entry_fts VALUES (?,?)", (entry_id, body))

    def populate(self):
        for being, prefix in (("astrid", "a"), ("minime", "m")):
            for i in range(6):
                self.add(prefix + str(i), being=being, time=i * 10)
        self.add("operational", being="astrid", time=15, kind="operational")
        self.add("undated", being="astrid", time=None)
        self.conn.commit()

    def test_candidates_preserve_offsets_and_skip_fenced_material(self):
        body = ("Écho. What remains? Why return?\n"
                "I wonder whether this changes tomorrow.\n"
                "```python\nprint('What?')\n~~~\nStill code?\n```\n"
                "~~~\nI don't understand hidden code.\n~~~~\n"
                "I don’t understand the interruption.\n")
        candidates = candidate_questions(body)
        self.assertEqual([c["text"] for c in candidates], [
            "What remains?", "Why return?", "I wonder whether this changes tomorrow.",
            "I don’t understand the interruption."])
        self.assertEqual([c["kind"] for c in candidates],
                         ["explicit_question"] * 2 + ["implicit_question"] * 2)
        for candidate in candidates:
            self.assertEqual(body[candidate["start_offset"]:candidate["end_offset"]], candidate["text"])
        self.assertEqual(candidate_questions("An ordinary entry.\n"), [])
        self.assertEqual(len(candidate_questions("I wonder: will it return?")), 1)
        wrapped = "Earlier observation.\nWhat becomes\nof this question?\n\nI wonder about silence."
        self.assertEqual([r["text"] for r in candidate_questions(wrapped)],
                         ["What becomes\nof this question?", "I wonder about silence."])

    def test_fts_phrase_is_not_operator_syntax(self):
        self.add("literal", 'The phrase "state" OR body appears.', time=10)
        self.add("separate", "state appears elsewhere in the body", time=20)
        self.add("other", "state OR body", being="minime", time=30)
        self.assertEqual({r["id"] for r in search(self.conn, '"state" OR body')}, {"literal", "other"})
        self.assertEqual([r["id"] for r in search(self.conn, "state OR body", being="astrid", since=10, until=20)], ["literal"])
        self.assertEqual(search(self.conn, "   "), [])
        self.assertEqual(search(self.conn, "***"), [])
        self.assertEqual(search(self.conn, "state", limit=0), [])
        self.assertEqual(len(search(self.conn, "state", limit=1)), 1)

    def test_recurrence_literal_case_and_duplicates_are_separate(self):
        body = "What stays? What stays?"
        self.add("first", body, time=0)
        self.add("copy", body, being="minime", time=2678400)
        self.add("new", "I ask: What stays?", time=2678401, lane="aspiration")
        self.add("lowercase", "what stays?", time=40)
        self.add("wildcards", "The literal %_ marker.", time=50)
        result = recurrence(self.conn, "What stays?")
        self.assertEqual((result["entries"], result["occurrences"], result["distinct_bodies"], result["duplicate_entries"]), (3, 5, 2, 1))
        self.assertEqual([r["id"] for r in result["matches"]], ["first", "copy", "new"])
        self.assertEqual(result["matches"][1]["duplicate_of"], "first")
        self.assertEqual([r["month"] for r in result["by_month"]], ["1970-01", "1970-02"])
        self.assertEqual(recurrence(self.conn, "%_")["entries"], 1)
        self.assertEqual(recurrence(self.conn, "' OR 1=1 --")["entries"], 0)
        self.assertEqual(recurrence(self.conn, "What stays?", since="1970-02-01", until="1970-02-02")["entries"], 2)

    def test_sample_is_reproducible_and_exposes_eligibility_and_overlap(self):
        self.populate()
        manifest = sample(self.conn, per_being=2, since=0, until=60, seed="reading", context=2,
                          curated_ids=["a2", "missing"])
        self.assertEqual(manifest, sample(self.conn, per_being=2, since=0, until=60,
                                         seed="reading", context=2, curated_ids=["a2", "missing"]))
        self.assertEqual(manifest["missing_curated_ids"], ["missing"])
        self.assertEqual(manifest["eligibility"]["total_eligible_dated_prose"], 11)
        self.assertEqual(manifest["eligibility"]["undated_prose_by_being_before_time_filters"], {"astrid": 1})
        self.assertEqual(len(manifest["selected"]), 5)
        ordinary = [r for r in manifest["selected"] if r["selection"] == "ordered_midpoint"]
        self.assertEqual({r["being"] for r in ordinary}, {"astrid", "minime"})
        self.assertNotIn("a2", {r["id"] for r in ordinary})
        self.assertNotIn("operational", {r["id"] for r in ordinary})
        self.assertNotIn("undated", {r["id"] for r in ordinary})
        self.assertTrue(manifest["overlap"]["context_ids_used_by_multiple_selections"])
        self.assertNotIn("operational", {r["id"] for r in manifest["context_entries"]})
        self.assertEqual([(r["id"], r["position"], r["eligible_list_count"]) for r in ordinary],
                         [("a1", 1, 5), ("a4", 3, 5), ("m1", 1, 6), ("m4", 4, 6)])
        by_id = {r["id"]: r for r in manifest["selected"]}
        for neighbor in manifest["context_entries"]:
            for use in neighbor["uses"]:
                self.assertEqual(neighbor["being"], by_id[use["selected_id"]]["being"])
        self.assertEqual(len(manifest["context_entries"]), len({r["id"] for r in manifest["context_entries"]}))
        self.assertEqual(manifest["index_snapshot"]["user_version"], 1)
        self.assertEqual(len(manifest["content_fingerprint"]), 64)

    def test_ordered_midpoints_follow_rank_not_duration_and_seed_is_label_only(self):
        for i, time in enumerate((0, 1, 2, 3, 4, 5, 6, 100000)):
            self.add("a" + str(i), time=time)
        first = sample(self.conn, per_being=4, context=0, seed="first")
        second = sample(self.conn, per_being=4, context=0, seed="second")
        self.assertEqual([r["id"] for r in first["selected"]], ["a1", "a3", "a5", "a7"])
        self.assertEqual(first["selected"], second["selected"])
        self.assertEqual(first["content_fingerprint"], second["content_fingerprint"])
        self.assertNotEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_context_crosses_time_filter_and_records_shortfalls(self):
        self.populate()
        manifest = sample(self.conn, since=20, until=30, per_being=1, context=3)
        focal = next(r for r in manifest["selected"] if r["being"] == "astrid")
        self.assertEqual(focal["id"], "a2")
        self.assertEqual(focal["context_ids"], ["a0", "a1", "a3", "a4", "a5"])
        self.assertEqual(focal["context_coverage"]["missing_before"], 1)
        self.assertEqual(focal["context_coverage"]["missing_after"], 0)

    def test_snapshot_captures_limited_run_scope_without_rechecking_sources(self):
        self.add("a")
        self.conn.executescript("""
            CREATE TABLE sources(id INTEGER, being TEXT, root TEXT, kind TEXT);
            CREATE TABLE runs(id INTEGER, kind TEXT, options_json TEXT, summary_json TEXT, status TEXT);
            INSERT INTO sources VALUES(1,'astrid','/not-mounted/live','journal');
            INSERT INTO runs VALUES(1,'journals','{"limit_per_source":50}',
                                    '{"coverage":"partial"}','complete');
        """)
        snapshot = sample(self.conn)["index_snapshot"]
        self.assertEqual(snapshot["registered_sources"][0]["root"], "/not-mounted/live")
        self.assertEqual(snapshot["applicable_or_latest_runs"][0]["options"]["limit_per_source"], 50)
        self.assertIn("not rechecked", snapshot["source_availability"])

    def test_curated_undated_and_empty_windows_remain_explicit(self):
        self.populate()
        manifest = sample(self.conn, since=100, until=200, curated_ids=["undated"])
        self.assertEqual(manifest["eligibility"]["total_eligible_dated_prose"], 0)
        self.assertEqual(len(manifest["eligibility"]["by_being"]), 2)
        self.assertEqual(len(manifest["selected"]), 1)
        self.assertIn("unavailable", manifest["selected"][0]["context_note"])
        self.assertEqual(sample(self.conn, per_being=0)["selected"], [])
        with self.assertRaises(ValueError):
            sample(self.conn, per_being=-1)
        with self.assertRaises(ValueError):
            sample(self.conn, since=20, until=10)

    def test_sampling_preserves_callers_transaction(self):
        self.populate()
        self.conn.execute("UPDATE catalog SET lane='changed' WHERE id='a0'")
        sample(self.conn, context=0)
        self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()
        self.assertEqual(self.conn.execute("SELECT lane FROM catalog WHERE id='a0'").fetchone()[0], "moment")

    def test_export_uses_cache_and_contains_fence_safe_source_and_blank_notes(self):
        raw = "A raw entry\n````\n# Pretend heading\n````\nNo terminal newline"
        self.add("raw", body="What remains?", raw=raw)
        manifest = sample(self.conn, context=0)
        with tempfile.TemporaryDirectory() as directory:
            paths = export_pack(self.conn, manifest, Path(directory))
            saved = json.loads(Path(paths["manifest"]).read_text())
            pack = Path(paths["reading_pack"]).read_text()
            self.assertEqual(saved, manifest)
            self.assertIn("`````\n" + raw + "\n`````", pack)
            self.assertIn("/not-mounted/live/raw.txt", pack)
            self.assertIn("Our interpretation: [unfilled]", pack)
            if os.name == "posix":
                self.assertEqual(Path(paths["manifest"]).stat().st_mode & 0o777, 0o600)
                self.assertEqual(Path(paths["reading_pack"]).stat().st_mode & 0o777, 0o600)
            Path(paths["reading_pack"]).write_text(pack + "\nReader's independent notes.\n")
            with self.assertRaises(FileExistsError):
                export_pack(self.conn, manifest, Path(directory))
            self.assertTrue(Path(paths["reading_pack"]).read_text().endswith("Reader's independent notes.\n"))

    def test_reexport_from_saved_manifest_is_byte_identical(self):
        self.populate()
        manifest = sample(self.conn, per_being=2, context=1)
        with tempfile.TemporaryDirectory() as directory:
            first = export_pack(self.conn, manifest, Path(directory)/'first')
            saved = json.loads(Path(first['manifest']).read_text())
            second = export_pack(self.conn, saved, Path(directory)/'second')
            for name in ('manifest','reading_pack'):
                self.assertEqual(Path(first[name]).read_bytes(), Path(second[name]).read_bytes())

    def test_export_rejects_manifest_tampering_and_changed_cached_text(self):
        self.add("a", body="What remains?")
        manifest = sample(self.conn, context=0)
        with tempfile.TemporaryDirectory() as directory:
            tampered = json.loads(json.dumps(manifest))
            tampered["selected"][0]["id"] = "different"
            with self.assertRaisesRegex(ValueError, "integrity"):
                export_pack(self.conn, tampered, Path(directory) / "tampered")
            self.conn.execute("UPDATE catalog SET raw_text='changed without updating stored hashes' WHERE id='a'")
            with self.assertRaisesRegex(ValueError, "changed"):
                export_pack(self.conn, manifest, Path(directory) / "drift")
            self.assertFalse((Path(directory) / "drift").exists())


if __name__ == "__main__":
    unittest.main()
