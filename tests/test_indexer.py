"""Integration checks for the local cache, using temporary synthetic source trees."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.explore import search
from reservoir_research.indexer import ingest_generations, ingest_journals, reparse_cached
from reservoir_research.parsing import parse_journal
from reservoir_research.store import connect


class IndexerIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # On macOS /var can be a symlink; source readers require canonical paths.
        self.base = Path(temporary.name).resolve()
        self.source = self.base / "journal"
        self.source.mkdir()
        self.generations = self.base / "generations"
        self.generations.mkdir()
        self.db_path = self.base / "cache" / "index.sqlite3"
        self.conn = connect(self.db_path, writable=True,
                            source_roots=[self.source, self.generations])
        self.addCleanup(self.conn.close)

    def journal(self, name, body="Could this question change later?", stamp="2026-09-06T23:00:00+00:00"):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        header = "=== MOMENT CAPTURE ===\n"
        if stamp is not None:
            header += f"Timestamp: {stamp}\n"
        path.write_text(header + "Fill %: 68.0%\n\n" + body, encoding="utf-8")
        return path

    def ingest(self, **options):
        return ingest_journals(self.conn, [("minime", self.source)], **options)

    def count(self, table):
        self.assertIn(table, {"entries", "catalog", "files", "entry_fts", "candidates", "generation_links"})
        return self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def generation(self, name, response, references=()):
        path = self.generations / "2026-09-06" / f"gen_{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": 1, "generation_id": name, "attempt_index": 0,
            "being": "minime", "lane": "moment", "backend": "recorded-backend",
            "created_at_unix_ms": 1788735600000, "status": "ok",
            "messages_source": "adapted",
            "messages": [{"role": "user", "content": "What might change?"}],
            "response_text": response,
            "linked_artifacts": [{"kind": "journal", "path": str(ref), "match": "recency"}
                                 for ref in references],
        }
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_source_files_are_unchanged_and_symlinks_are_not_ingested(self):
        path = self.journal("moment_2026-09-06T16-00-00.txt", "Could a read remain only a read?")
        path.chmod(0o444)
        outside = self.base / "outside.txt"
        outside.write_text("A secret outside the selected source tree.", encoding="utf-8")
        (self.source / "linked.txt").symlink_to(outside)
        before = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode,
                  sorted(p.name for p in self.source.iterdir()))
        self.ingest()
        after = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode,
                 sorted(p.name for p in self.source.iterdir()))
        self.assertEqual(before, after)
        self.assertEqual(self.count("catalog"), 1)
        row = self.conn.execute("SELECT raw_sha256,raw_text FROM catalog").fetchone()
        self.assertEqual(row["raw_sha256"], hashlib.sha256(before[0]).hexdigest())
        self.assertEqual(row["raw_text"], before[0].decode())
        self.assertEqual(search(self.conn, "secret"), [])

    def test_repeat_and_rehash_are_idempotent_in_catalog_search_and_candidates(self):
        self.journal("moment_2026-09-06T16-00-00.txt", "Could a lantern help us remember?")
        self.ingest()
        initial = {name: self.count(name) for name in ("entries", "files", "entry_fts", "candidates")}
        self.assertGreater(initial["candidates"], 0)
        again = self.ingest()
        self.assertEqual(again["counts"].get("unchanged"), 1)
        self.ingest(rehash=True)
        self.assertEqual(initial, {name: self.count(name) for name in initial})
        self.assertEqual(self.count("catalog"), 1)
        self.assertEqual(len(search(self.conn, "lantern")), 1)

    def test_archive_and_flag_aliases_share_one_entry_and_flag_tracks_present_copy(self):
        name = "moment_2026-09-06T16-00-00.txt"
        flagged = self.journal("!" + name, "Could this shared passage have two paths?")
        archived = self.source / "archive" / "saved" / name
        archived.parent.mkdir(parents=True)
        archived.write_bytes(flagged.read_bytes())
        self.ingest()
        self.assertEqual(self.count("entries"), 1)
        self.assertEqual(self.count("files"), 2)
        self.assertEqual(self.count("entry_fts"), 1)
        self.assertEqual(self.conn.execute("SELECT mike_flag FROM catalog").fetchone()[0], 1)
        flagged.unlink()
        self.ingest()
        self.assertEqual(self.count("catalog"), 1)
        row = self.conn.execute("SELECT mike_flag,source_path FROM catalog").fetchone()
        self.assertEqual(row["mike_flag"], 0)
        self.assertEqual(row["source_path"], str(archived))

    def test_edited_source_preserves_history_but_search_uses_current_version(self):
        path = self.journal("moment_2026-09-06T16-00-00.txt", "An obsoleteword marks the earlier version.")
        self.ingest()
        old_id = self.conn.execute("SELECT id FROM catalog").fetchone()[0]
        path.write_text(path.read_text().replace("obsoleteword", "replacementword"), encoding="utf-8")
        self.ingest(rehash=True)
        self.assertEqual(self.count("entries"), 2)
        self.assertEqual(self.count("catalog"), 1)
        self.assertNotEqual(self.conn.execute("SELECT id FROM catalog").fetchone()[0], old_id)
        self.assertEqual(search(self.conn, "obsoleteword"), [])
        self.assertEqual(len(search(self.conn, "replacementword")), 1)

    def test_date_window_is_start_inclusive_end_exclusive_and_unknown_is_explicit(self):
        self.journal("at_start.txt", stamp="2026-09-06T23:00:00Z")
        self.journal("at_end.txt", stamp="2026-09-07T00:00:00Z")
        self.journal("before.txt", stamp="2026-09-06T22:59:59Z")
        unknown = self.journal("unknown.txt", stamp=None)
        since = datetime(2026, 9, 6, 23, tzinfo=timezone.utc).timestamp()
        summary = self.ingest(since=since, until=since + 3600)
        self.assertEqual([r[0] for r in self.conn.execute("SELECT canonical_name FROM catalog")], ["at_start.txt"])
        self.assertEqual(summary["counts"].get("outside_window"), 2)
        self.assertEqual(summary["counts"].get("unknown_time_excluded"), 1)
        issue = self.conn.execute("SELECT path,error FROM ingest_issues").fetchone()
        self.assertEqual(issue["path"], str(unknown))
        self.assertIn("Unknown time", issue["error"])

    def test_changed_outside_window_source_retires_old_mapping_until_imported(self):
        path = self.journal("entry.txt", "The obsoleteword belongs to the first version.")
        self.ingest()
        original = path.read_text()
        path.write_text(original.replace("2026-09-06", "2026-09-08").replace("obsoleteword", "replacementword"))
        since = datetime(2026, 9, 6, 23, tzinfo=timezone.utc).timestamp()
        summary = self.ingest(since=since, until=since + 3600)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated"), 1)
        self.assertEqual(self.count("catalog"), 0)
        self.assertEqual(self.count("entries"), 1)
        self.assertEqual(search(self.conn, "obsoleteword"), [])
        self.assertEqual(self.conn.execute("SELECT present FROM files").fetchone()[0], 0)
        self.ingest()
        self.assertEqual(self.count("entries"), 2)
        self.assertEqual(self.count("catalog"), 1)
        self.assertEqual(len(search(self.conn, "replacementword")), 1)

    def test_changed_unknown_time_source_retires_old_mapping(self):
        path = self.journal("entry.txt", "An obsoleteword from a dated entry.")
        self.ingest()
        path.write_text("=== BOREDOM ===\nFill %: 68.0%\n\nA replacement without recorded time.")
        since = datetime(2026, 9, 6, 23, tzinfo=timezone.utc).timestamp()
        summary = self.ingest(since=since, until=since + 3600)
        self.assertEqual(summary["counts"].get("unknown_time_excluded"), 1)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated"), 1)
        self.assertEqual(self.count("catalog"), 0)
        self.assertEqual(self.count("entries"), 1)
        self.assertEqual(search(self.conn, "obsoleteword"), [])
        self.assertIn("Unknown time", self.conn.execute("SELECT error FROM ingest_issues").fetchone()[0])

    def test_failed_read_retires_changed_mapping_but_preserves_unverified_unchanged_source(self):
        changed = self.journal("changed.txt", "An obsoleteword before a change.")
        self.journal("unchanged.txt", "A preservedword in an unchanged source.")
        self.ingest()
        changed.write_text(changed.read_text() + "\nA change that is not yet readable.")
        with patch("reservoir_research.indexer.read_stable", side_effect=PermissionError("temporarily unavailable")):
            summary = self.ingest(rehash=True)
        self.assertEqual(summary["counts"].get("errors"), 2)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated"), 1)
        self.assertEqual(self.count("entries"), 2)
        self.assertEqual(self.count("catalog"), 1)
        self.assertEqual(search(self.conn, "obsoleteword"), [])
        self.assertEqual(len(search(self.conn, "preservedword")), 1)

    def test_parser_failure_after_same_metadata_edit_cannot_resurrect_stale_mapping(self):
        path = self.journal("entry.txt", "An obsoleteword in this passage.")
        self.ingest()
        before = path.stat()
        changed = path.read_text().replace("obsoleteword", "replacedword")
        path.write_text(changed)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        with patch("reservoir_research.parsing.parse_journal", side_effect=ValueError("unsupported format")):
            summary = self.ingest(rehash=True)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated"), 1)
        self.assertEqual(self.count("catalog"), 0)
        # Without rehash, an invalidated mapping still needs a fresh read even if
        # a replacement happened to preserve the previous size and timestamp.
        self.ingest()
        self.assertEqual(search(self.conn, "obsoleteword"), [])
        self.assertEqual(len(search(self.conn, "replacedword")), 1)

    def test_change_during_failed_read_invalidates_prior_mapping(self):
        path = self.journal("entry.txt", "An obsoleteword before the attempted read.")
        self.ingest()

        def changed_during_read(source):
            source.write_text(source.read_text() + "\nA concurrent change.")
            raise ValueError("Source changed during read; retry on next index run")

        with patch("reservoir_research.indexer.read_stable", side_effect=changed_during_read):
            summary = self.ingest(rehash=True)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated"), 1)
        self.assertEqual(self.count("catalog"), 0)
        self.assertEqual(self.count("entries"), 1)

    def test_touch_without_content_change_does_not_invalidate_excluded_mapping(self):
        path = self.journal("entry.txt", "An unchangedword with a new modification time.")
        self.ingest()
        before = path.stat()
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        later = datetime(2026, 9, 8, tzinfo=timezone.utc).timestamp()
        summary = self.ingest(since=later)
        self.assertEqual(summary["counts"].get("outside_window"), 1)
        self.assertEqual(summary["counts"].get("stale_mappings_invalidated", 0), 0)
        self.assertEqual(len(search(self.conn, "unchangedword")), 1)

    def test_limited_scan_cannot_mark_unvisited_or_removed_paths_absent(self):
        self.journal("a.txt")
        removed = self.journal("b.txt")
        self.journal("c.txt")
        self.ingest()
        removed.unlink()
        summary = self.ingest(limit=1)
        self.assertEqual(summary["counts"].get("limited"), 1)
        self.assertEqual(self.count("catalog"), 3)
        self.assertEqual(self.conn.execute("SELECT SUM(present) FROM files").fetchone()[0], 3)

    def test_complete_scan_marks_missing_paths_absent_without_erasing_history(self):
        self.journal("a.txt")
        removed = self.journal("b.txt")
        self.ingest()
        removed.unlink()
        summary = self.ingest()
        self.assertEqual(summary["counts"].get("paths_no_longer_seen"), 1)
        self.assertEqual(self.count("catalog"), 1)
        self.assertEqual(self.count("entries"), 2)
        self.assertEqual(self.conn.execute("SELECT present FROM files WHERE relative_path='b.txt'").fetchone()[0], 0)

    def test_read_error_is_recorded_and_prevents_absence_claim(self):
        self.journal("a.txt")
        removed = self.journal("b.txt")
        self.ingest()
        removed.unlink()
        oversized = self.source / "oversized.txt"
        # A sparse file exercises the public read limit without allocating its body.
        with oversized.open("wb") as stream:
            stream.truncate(5 * 1024 * 1024)
        summary = self.ingest()
        self.assertEqual(summary["counts"].get("errors"), 1)
        self.assertEqual(self.count("catalog"), 2)
        issue = self.conn.execute("SELECT path,error FROM ingest_issues ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(issue["path"], str(oversized))
        self.assertIn("file limit", issue["error"])

    def test_missing_source_fails_and_records_failed_run(self):
        missing = self.base / "missing"
        with self.assertRaisesRegex(ValueError, "directory not found"):
            ingest_journals(self.conn, [("minime", missing)])
        self.assertFalse(missing.exists())
        run = self.conn.execute("SELECT status,finished_at FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(run["status"], "failed")
        self.assertIsNotNone(run["finished_at"])
        self.assertEqual(self.count("catalog"), 0)

    def test_database_destinations_inside_custom_protected_and_symlink_roots_are_refused(self):
        with self.assertRaisesRegex(ValueError, "source tree"):
            connect(self.source / "forbidden.sqlite3", writable=True, source_roots=[self.source])
        protected = self.base / "protected-being"
        protected.mkdir()
        alias = self.base / "output-alias"
        alias.symlink_to(protected, target_is_directory=True)
        with patch("reservoir_research.store.protected_roots", return_value=[protected]):
            for destination in (protected / "cache.sqlite3", alias / "cache.sqlite3"):
                with self.subTest(destination=destination):
                    with self.assertRaisesRegex(ValueError, "source tree"):
                        connect(destination, writable=True)
        self.assertFalse((self.source / "forbidden.sqlite3").exists())
        self.assertEqual(list(protected.iterdir()), [])

    def test_unrelated_sqlite_is_refused_without_modification(self):
        unrelated = self.base / "unrelated.sqlite3"
        with closing(sqlite3.connect(unrelated)) as conn, conn:
            conn.execute("CREATE TABLE personal_notes(body TEXT)")
            conn.execute("INSERT INTO personal_notes VALUES ('Retain this record')")
        before = unrelated.read_bytes()
        with self.assertRaisesRegex(ValueError, "not a reservoir-research index"):
            connect(unrelated, writable=True)
        self.assertEqual(unrelated.read_bytes(), before)
        with closing(sqlite3.connect(unrelated)) as conn:
            self.assertEqual(conn.execute("SELECT body FROM personal_notes").fetchone()[0], "Retain this record")

    def test_cache_relocated_inside_its_registered_source_is_refused(self):
        self.journal("entry.txt")
        self.ingest()
        relocated = self.source / "relocated.sqlite3"
        relocated.write_bytes(self.db_path.read_bytes())
        before = relocated.read_bytes()
        with self.assertRaisesRegex(ValueError, "source tree"):
            connect(relocated, writable=True)
        self.assertEqual(relocated.read_bytes(), before)

    def test_generations_link_only_after_exact_response_becomes_unambiguous(self):
        body = "Could the same sentence have two different histories?"
        self.journal("first.txt", body)
        second = self.journal("second.txt", body, stamp="2026-09-06T23:01:00Z")
        self.ingest()
        self.generation("shared", body)
        ingest_generations(self.conn, [("minime", self.generations)])
        self.assertEqual(self.count("generation_links"), 0)
        self.assertEqual(self.conn.execute("SELECT SUM(prompt_available) FROM catalog").fetchone()[0], 0)
        second.unlink()
        self.ingest()
        self.assertEqual(self.count("generation_links"), 1)
        row = self.conn.execute("SELECT backend,prompt_available FROM catalog").fetchone()
        self.assertEqual(row["backend"], "recorded-backend")
        self.assertEqual(row["prompt_available"], 1)

    def test_recency_reference_and_nearby_time_do_not_supply_unverified_generation_link(self):
        source = self.journal("moment_2026-09-06T16-00-00.txt", "A journal with independently retained text.")
        self.ingest()
        self.generation("different-response", "A different generated response.", references=[source])
        self.generation("no-response", None, references=[source])
        ingest_generations(self.conn, [("minime", self.generations)])
        self.assertEqual(self.count("generation_links"), 0)
        row = self.conn.execute("SELECT backend,prompt_available FROM catalog").fetchone()
        self.assertIsNone(row["backend"])
        self.assertEqual(row["prompt_available"], 0)

    def test_cached_reparse_updates_current_and_historical_text_without_source_reads(self):
        path = self.source / "resonance.txt"
        header = "=== RESERVOIR RESONANCE ===\nTimestamp: 2026-09-06T19:29:13\nFill %: 69.1%\n\nMinime <-> Astrid resonance:\n  divergence: 1.1\n  correlation: -0.8\n  trajectory RMSD: 2.5\n\n"
        first, second = "Could a former question return?", "Could a current question develop?"

        def legacy_parse(raw, being, filename):
            result = parse_journal(raw, being, filename)
            # Reproduce the earlier stored interpretation: an unknown wrapper
            # whose telemetry was left inside candidate body text.
            result.update(header_text="", body_text=raw.strip(), entry_type="unknown",
                          content_kind="unknown", lane=None)
            result["metadata"]["parser_version"] = "journal-v1"
            return result

        with patch("reservoir_research.parsing.parse_journal", side_effect=legacy_parse), \
                patch("reservoir_research.indexer.PARSER_VERSION", 1):
            path.write_text(header + first)
            self.ingest()
            path.write_text(header + second)
            self.ingest(rehash=True)
        generation = self.generation("current", second)
        ingest_generations(self.conn, [("minime", self.generations)])
        self.assertEqual(self.count("generation_links"), 0)
        self.assertEqual(self.count("candidates"), 0)
        retained = [tuple(row) for row in self.conn.execute(
            "SELECT id,being,canonical_name,raw_text,raw_sha256 FROM entries ORDER BY id")]
        files = [tuple(row) for row in self.conn.execute("SELECT * FROM files ORDER BY id")]
        generations = [tuple(row) for row in self.conn.execute("SELECT * FROM generations ORDER BY id")]
        path.unlink()
        generation.unlink()
        with patch("reservoir_research.indexer.read_stable", side_effect=AssertionError("source read forbidden")), \
                patch("reservoir_research.indexer.discover_journals", side_effect=AssertionError("source scan forbidden")):
            summary = reparse_cached(self.conn)
        self.assertEqual(summary["parser_version"], 2)
        self.assertEqual(summary["counts"]["reparsed"], 2)
        self.assertEqual(summary["counts"]["historical_entries"], 1)
        self.assertEqual(summary["counts"]["current_entries"], 1)
        self.assertEqual(summary["counts"]["generation_links"], 1)
        self.assertEqual(retained, [tuple(row) for row in self.conn.execute(
            "SELECT id,being,canonical_name,raw_text,raw_sha256 FROM entries ORDER BY id")])
        self.assertEqual(files, [tuple(row) for row in self.conn.execute("SELECT * FROM files ORDER BY id")])
        self.assertEqual(generations, [tuple(row) for row in self.conn.execute("SELECT * FROM generations ORDER BY id")])
        self.assertEqual({row[0] for row in self.conn.execute("SELECT body_text FROM entries")}, {first, second})
        self.assertEqual({row[0] for row in self.conn.execute("SELECT parser_version FROM entries")}, {2})
        self.assertEqual(self.count("candidates"), 2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM entry_fts WHERE entry_fts MATCH 'divergence'").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT body_text FROM catalog").fetchone()[0], second)
        self.assertEqual(self.conn.execute("SELECT kind,status FROM runs ORDER BY id DESC LIMIT 1").fetchone()[:], ("reparse", "complete"))
        reparse_cached(self.conn)
        self.assertEqual(self.count("entry_fts"), 2)
        self.assertEqual(self.count("candidates"), 2)
        self.assertEqual(self.count("generation_links"), 1)

    def test_cached_reparse_preserves_decode_warning_and_original_byte_hash(self):
        path = self.journal("invalid_utf8.txt", "Could this decoded text be retained?")
        path.write_bytes(path.read_bytes() + b"\n\xff")
        self.ingest()
        before = self.conn.execute("SELECT id,raw_text,raw_sha256 FROM entries").fetchone()
        self.assertNotEqual(before["raw_sha256"], hashlib.sha256(before["raw_text"].encode()).hexdigest())
        path.unlink()
        reparse_cached(self.conn)
        after = self.conn.execute("SELECT id,raw_text,raw_sha256,warnings_json FROM entries").fetchone()
        self.assertEqual(after[:3], before[:])
        self.assertIn("Invalid UTF-8 replaced for display; raw byte hash retained.", json.loads(after["warnings_json"]))

    def test_cached_reparse_failure_rolls_back_all_derived_data_but_records_failure(self):
        self.journal("one.txt", "Could this first question remain?")
        self.journal("two.txt", "Could this second question remain?")
        self.ingest()
        snapshots = {table: [tuple(row) for row in self.conn.execute(f"SELECT * FROM {table} ORDER BY 1,2")]
                     for table in ("entries", "files", "entry_fts", "candidates", "generation_links")}
        calls = 0

        def fail_after_one(raw, being, filename):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ValueError("fixture parser failure")
            result = parse_journal(raw, being, filename)
            result["body_text"] = "Could an uncommitted change leak into search?"
            return result

        with patch("reservoir_research.parsing.parse_journal", side_effect=fail_after_one):
            with self.assertRaisesRegex(ValueError, "fixture parser failure"):
                reparse_cached(self.conn)
        self.assertEqual(calls, 2)
        for table, before in snapshots.items():
            self.assertEqual(before, [tuple(row) for row in self.conn.execute(f"SELECT * FROM {table} ORDER BY 1,2")], table)
        run = self.conn.execute("SELECT kind,status,summary_json FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual((run["kind"], run["status"]), ("reparse", "failed"))
        self.assertTrue(json.loads(run["summary_json"])["rolled_back"])
        self.assertEqual(search(self.conn, "uncommitted"), [])

    def test_empty_cache_reparse_records_a_completed_run(self):
        summary = reparse_cached(self.conn)
        self.assertEqual(summary["counts"]["entries"], 0)
        self.assertEqual(summary["counts"]["reparsed"], 0)
        self.assertEqual(summary["counts"]["generation_links"], 0)
        self.assertEqual(self.conn.execute("SELECT status FROM runs").fetchone()[0], "complete")


if __name__ == "__main__":
    unittest.main()
