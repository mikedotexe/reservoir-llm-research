"""Literal source trails over synthetic cached originals, with no live source files."""
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.store import connect
from reservoir_research.trails import collect_trail, export_trail


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class TrailTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.db = self.base / "cache.sqlite3"
        self.conn = connect(self.db, writable=True)
        self.addCleanup(self.conn.close)
        self.conn.execute("INSERT INTO sources(being,root,kind) VALUES ('minime','/unmounted/journals','journal')")
        self.conn.commit()

    def journal(self, entry_id, raw, time=10, being="minime", body="Cleaned ordinary prose.", next_raw=None):
        record = dict(id=entry_id, being=being, canonical_name=entry_id + ".txt", occurred_at=time,
                      time_source="fixture", lane="fixture_lane", entry_type="moment", content_kind="prose",
                      header_text="", body_text=body, raw_text=raw, raw_sha256=sha(raw), body_sha256=sha(body),
                      next_raw=next_raw, next_verb=None, contract=None, metadata_json="{}", warnings_json="[]",
                      parser_version=2)
        self.conn.execute("INSERT INTO entries (" + ",".join(record) + ") VALUES (" +
                          ",".join("?" for _ in record) + ")", list(record.values()))
        self.conn.execute("INSERT INTO files(source_id,relative_path,entry_id,size_bytes,mtime_ns,ctime_ns,mike_flag,present) VALUES (1,?,?,?,0,0,0,1)",
                          (entry_id + ".txt", entry_id, len(raw.encode())))
        self.conn.commit()

    def generation(self, generation_id, time=10, being="minime", prompt=None, response=None, metadata=None):
        encoded = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
        values = (generation_id, being, time, "fixture_lane", None, "recorded_status", prompt, 0, response,
                  sha(response) if response is not None else None, "[]", encoded, "[]",
                  "/unmounted/generations/" + generation_id + ".json", sha(encoded))
        self.conn.execute("INSERT INTO generations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        self.conn.commit()
        return encoded

    def collect(self, terms=None, **kwargs):
        return collect_trail(self.conn, terms or ["lead"], kwargs.pop("being", "minime"),
                             kwargs.pop("since", 0), kwargs.pop("until", 40), **kwargs)

    def test_header_and_next_only_terms_are_recovered_from_originals(self):
        raw = "=== JOURNAL ===\nPrompt contract: header_lead\n\nAn ordinary passage.\nNEXT: HOLD action_lead\n"
        self.journal("journal", raw, next_raw="HOLD action_lead")
        result = self.collect(["header_lead", "action_lead"])
        self.assertEqual(result["total_matching"], 1)
        record = result["records"][0]
        self.assertEqual(record["kind"], "journal")
        self.assertEqual(record["next_raw"], "HOLD action_lead")
        self.assertEqual(record["raw_sha256"], sha(raw))
        self.assertEqual(record["field_sha256"]["raw_text"], sha(raw))
        self.assertEqual([span["text"] for span in record["matched_spans"]], ["header_lead", "action_lead"])
        for span in record["matched_spans"]:
            self.assertEqual(raw[span["start_offset"]:span["end_offset"]], span["text"])
            self.assertEqual(raw[span["context_start_offset"]:span["context_end_offset"]], span["context_text"])
        self.assertNotIn("body_text", record)

    def test_generation_prompt_response_and_serialized_metadata_stay_separate(self):
        prompt, response = "An input_lead before generation.", "An output_lead in the response."
        metadata = self.generation("generation", prompt=prompt, response=response, metadata={"declared_action": "metadata_lead"})
        result = self.collect(["input_lead", "output_lead", "metadata_lead"])
        record = result["records"][0]
        self.assertEqual(record["kind"], "generation")
        self.assertEqual(record["source_sha256"], sha(metadata))
        expected = {"prompt_text": prompt, "response_text": response, "metadata_json": metadata}
        self.assertEqual([span["field"] for span in record["matched_spans"]], list(expected))
        for span in record["matched_spans"]:
            self.assertEqual(expected[span["field"]][span["start_offset"]:span["end_offset"]], span["text"])
            self.assertIsNone(span["channel"])
        self.assertEqual(record["prompt_available"], 0)
        self.assertNotIn("execution", record)

    def test_bounds_being_and_undated_denominators_include_nonmatches(self):
        self.journal("start", "lead at start", time=10)
        self.journal("ordinary", "unrelated material", time=15)
        self.journal("end", "lead at exclusive end", time=20)
        self.journal("before", "lead before window", time=9)
        self.journal("unknown", "lead without time", time=None)
        self.journal("other-being", "lead from Astrid", time=12, being="astrid")
        self.generation("g-start", time=10, response="lead")
        self.generation("g-ordinary", time=18, response="unrelated")
        self.generation("g-unknown", time=None, response="lead")
        result = self.collect(since=10, until=20)
        self.assertEqual([record["id"] for record in result["records"]], ["g-start", "start"])
        denominators = {row["kind"]: row for row in result["denominators"]}
        self.assertEqual(denominators["journal"]["total_indexed"], 5)
        for kind in ("journal", "generation"):
            self.assertEqual(denominators[kind]["being"], "minime")
            self.assertEqual(denominators[kind]["dated_in_window"], 2)
            self.assertEqual(denominators[kind]["undated_before_time_filter"], 1)
            self.assertEqual(denominators[kind]["undated_matching_excluded"], 1)

    def test_sql_and_fts_characters_are_case_sensitive_literals(self):
        literal = "%' OR 1=1 -- [x]_*"
        self.journal("literal", "Context " + literal + " closing.")
        self.journal("near", "Context OR 1=1 x closing.")
        self.journal("case", "Lead with uppercase.")
        result = self.collect([literal])
        self.assertEqual([row["id"] for row in result["records"]], ["literal"])
        self.assertEqual(result["records"][0]["matched_spans"][0]["text"], literal)
        self.assertEqual(self.collect(["lead"])["records"], [])
        self.assertEqual([row["id"] for row in self.collect(["Lead"])["records"]], ["case"])

    def test_caps_are_deterministic_and_total_matching_is_not_returned_count(self):
        self.journal("later", "lead", time=20)
        self.journal("same-time", "lead", time=10)
        self.generation("earliest", time=10, response="lead")
        result = self.collect(limit=1)
        self.assertEqual(result["total_matching"], 3)
        self.assertEqual(result["returned"], 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["records"][0]["id"], "earliest")
        self.assertEqual(result, self.collect(limit=1))
        self.assertEqual(self.collect(limit=5)["returned"], 3)
        self.assertFalse(self.collect(limit=5)["truncated"])

    def test_span_cap_preserves_total_occurrences_and_earliest_offsets(self):
        raw = "early " + "lead " * 80 + "late"
        self.journal("repeated", raw)
        result = self.collect(["late", "lead", "early"])
        record = result["records"][0]
        self.assertEqual(record["match_occurrences"], 82)
        self.assertEqual(record["returned_spans"], 40)
        self.assertTrue(record["spans_truncated"])
        self.assertEqual(record["matched_spans"][0]["text"], "early")
        offsets = [span["start_offset"] for span in record["matched_spans"]]
        self.assertEqual(offsets, sorted(offsets))
        self.assertFalse(result["truncated"])

    def test_raw_reply_markers_add_only_structural_channel_hints(self):
        raw = "Header lead.\n\nINBOX_REPLY literal_target\n\nA reply lead."
        self.journal("mixed", raw)
        spans = self.collect()["records"][0]["matched_spans"]
        self.assertEqual([span["channel"] for span in spans], ["pre_reply_context", "inbox_reply"])
        self.assertEqual([span["reply_target"] for span in spans], [None, "literal_target"])

    def test_collection_is_read_only_and_does_not_open_sources(self):
        self.journal("cached", "lead in cached text")
        self.generation("cached-generation", prompt="lead in cached prompt")
        before = self.db.read_bytes()
        self.conn.execute("PRAGMA query_only=ON")
        with patch("pathlib.Path.open", side_effect=AssertionError("No source reads")), \
                patch("builtins.open", side_effect=AssertionError("No source reads")):
            result = self.collect()
        self.assertEqual(result["returned"], 2)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(result["index_snapshot"]["registered_sources"][0]["root"], "/unmounted/journals")

    def test_content_fingerprint_tracks_cached_field_changes(self):
        self.journal("cached", "lead before")
        before = self.collect()
        self.conn.execute("UPDATE entries SET raw_text='lead after' WHERE id='cached'")
        self.conn.commit()
        after = self.collect()
        self.assertNotEqual(before["content_fingerprint"], after["content_fingerprint"])
        self.assertNotEqual(before["result_sha256"], after["result_sha256"])

    def test_missing_generation_table_is_unavailable_not_an_inferred_zero(self):
        self.journal("cached", "lead")
        self.conn.execute("DROP VIEW catalog")
        self.conn.execute("DROP TABLE generation_links")
        self.conn.execute("DROP TABLE generations")
        self.conn.execute("CREATE VIEW catalog AS SELECT e.*, '/unmounted/source.txt' AS source_path, NULL AS backend, 0 AS prompt_available FROM entries e")
        self.conn.commit()
        result = self.collect()
        self.assertEqual(result["missing_kinds"], ["generation"])
        generation = next(row for row in result["denominators"] if row["kind"] == "generation")
        self.assertFalse(generation["available"])
        self.assertIsNone(generation["dated_in_window"])
        self.assertEqual(result["returned"], 1)

    def test_export_is_byte_deterministic_private_and_never_overwrites(self):
        self.journal("fenced", "lead\n`````\n# Quoted source heading\n`````\n")
        result = self.collect()
        first = export_trail(result, self.base / "first")
        second = export_trail(result, self.base / "second")
        for kind in ("json", "markdown"):
            a, b = Path(first[kind]), Path(second[kind])
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(stat.S_IMODE(a.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.base / "first").stat().st_mode), 0o700)
        self.assertEqual(json.loads(Path(first["json"]).read_text()), result)
        self.assertIn("\n``````\nlead\n`````", Path(first["markdown"]).read_text())
        before = Path(first["markdown"]).read_bytes()
        with self.assertRaises(FileExistsError):
            export_trail(result, self.base / "first")
        self.assertEqual(Path(first["markdown"]).read_bytes(), before)
        empty = self.base / "existing-empty"
        empty.mkdir()
        with self.assertRaises(FileExistsError):
            export_trail(result, empty)
        altered = dict(result, total_matching=999)
        with self.assertRaisesRegex(ValueError, "integrity"):
            export_trail(altered, self.base / "altered")
        self.assertFalse((self.base / "altered").exists())

    def test_required_scope_and_literal_terms_are_validated(self):
        invalid = [([], "minime", 0, 40, 1), ([""], "minime", 0, 40, 1),
                   (["   "], "minime", 0, 40, 1), ("lead", "minime", 0, 40, 1),
                   (["lead"], "other", 0, 40, 1), (["lead"], "minime", None, 40, 1),
                   (["lead"], "minime", 40, 40, 1), (["lead"], "minime", 41, 40, 1),
                   (["lead"], "minime", float("nan"), 40, 1), (["lead"], "minime", True, 40, 1),
                   (["lead"], "minime", 0, 40, 0), (["lead"], "minime", 0, 40, True)]
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    collect_trail(self.conn, *arguments)


if __name__ == "__main__":
    unittest.main()
