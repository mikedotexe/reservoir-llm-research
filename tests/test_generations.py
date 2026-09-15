"""Fixtures follow inspected legacy jobs and the documented per-attempt v1 schema."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reservoir_research.generations import discover_generation_files, read_generation


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data) if isinstance(data, (dict, list)) else data, encoding="utf-8")
        return path

    def legacy(self, **fields):
        return self.write("jobs/job_minime_1/job.json", dict(job_id="job_minime_1", system="minime",
            created_at="2026-09-06T23:06:00Z", call_kind="journal_pressure", status="completed", **fields))

    def generation(self, **fields):
        record = dict(schema_version=1, generation_id="generation-1", being="minime", lane="moment",
            created_at_unix_ms=1788735960000, backend="ollama", status="ok", attempt_index=0,
            messages_source="adapted", messages=[{"role": "user", "content": "Notice?", "chars": 7}],
            response_text="I notice a distinction.")
        record.update(fields)
        return self.write(f"generations/2026-09-06/gen_1_a{record['attempt_index']}.json", record)

    def test_legacy_prompt_and_response_preserved_without_inferred_backend(self):
        path = self.legacy(summary="moment completed via MLX", prompt_path="/outside/prompt.txt")
        self.write("jobs/job_minime_1/prompt.txt", "Why?")
        self.write("jobs/job_minime_1/result.txt", "A short answer.")
        result = read_generation(path, "minime")
        self.assertEqual(result["id"], "minime:legacy_job:job_minime_1")
        self.assertEqual(result["prompt_text"], "Why?")
        self.assertEqual(result["metadata"]["prompt_status"], "captured_legacy")
        self.assertEqual(result["prompt_available"], 0)
        self.assertEqual(result["response_text"], "A short answer.")
        self.assertIsNone(result["backend"])
        self.assertEqual(result["occurred_at"], 1788735960.0)

    def test_known_action_stub_and_summary_are_not_model_text(self):
        path = self.legacy()
        self.write("jobs/job_minime_1/prompt.txt", "Action-level LLM job. The existing action finalizer owns prompt construction, validation, artifacts, and NEXT extraction.")
        self.write("jobs/job_minime_1/result.txt", "Executed autonomous action `journal_pressure`.")
        result = read_generation(path, "minime")
        self.assertIsNone(result["prompt_text"])
        self.assertEqual(result["metadata"]["prompt_status"], "stub")
        self.assertIsNone(result["response_text"])
        self.assertIsNone(result["response_sha256"])

    def test_generic_stub_does_not_erase_actual_response(self):
        path = self.legacy()
        self.write("jobs/job_minime_1/prompt.txt", "<stub>")
        self.write("jobs/job_minime_1/result.txt", "Still a recorded response.")
        result = read_generation(path, "minime")
        self.assertEqual(result["prompt_available"], 0)
        self.assertEqual(result["response_text"], "Still a recorded response.")

    def test_timeout_retained_without_journal_or_response(self):
        path = self.generation(status="timeout", response_text=None)
        result = read_generation(path, "minime")
        self.assertEqual(result["status"], "timeout")
        self.assertIsNone(result["response_text"])
        self.assertEqual(result["journal_refs"], [])
        self.assertEqual(result["prompt_available"], 1)

    def test_verified_dedup_preserves_roles_and_exactness(self):
        system = "You are Minime.\nUse λ carefully."
        sha = hashlib.sha256(system.encode()).hexdigest()
        self.write(f"generations/system_prompts/{sha}.txt", system)
        path = self.generation(messages=[{"role": "system", "content_sha256": sha, "chars": len(system)},
                                         {"role": "user", "content": "What changed?"}])
        result = read_generation(path, "minime")
        self.assertEqual(result["prompt_available"], 1)
        self.assertEqual(result["prompt_text"], f"[system]\n{system}\n\n[user]\nWhat changed?")
        self.assertTrue(result["metadata"]["exact_prompt"])

    def test_missing_or_corrupt_dedup_leaves_partial_prompt(self):
        for text in (None, "wrong text"):
            with self.subTest(text=text):
                sha = "a" * 64
                if text is not None:
                    self.write(f"generations/system_prompts/{sha}.txt", text)
                path = self.generation(messages=[{"role": "system", "content_sha256": sha}, {"role": "user", "content": "Keep this"}])
                result = read_generation(path, "minime")
                self.assertEqual(result["prompt_available"], 0)
                self.assertEqual(result["metadata"]["missing_message_indices"], [0])
                self.assertEqual(result["prompt_text"], "[user]\nKeep this")
                self.assertTrue(result["warnings"])

    def test_reconstructed_and_astrid_snapshots_not_exact(self):
        for source in ("reconstructed", None):
            with self.subTest(source=source):
                result = read_generation(self.generation(messages_source=source), "minime")
                self.assertEqual(result["prompt_available"], 0)
                self.assertIsNotNone(result["prompt_text"])

    def test_attempts_have_distinct_ids_and_hashes_are_recomputed(self):
        first = read_generation(self.generation(response_sha256="untrusted"), "minime")
        second = read_generation(self.generation(attempt_index=1, status="rejected_quality_gate"), "minime")
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first["response_sha256"], hashlib.sha256(first["response_text"].encode()).hexdigest())
        self.assertIn("response_sha256 mismatch", " ".join(first["warnings"]))

    def test_journal_refs_retained_as_evidence_never_opened(self):
        links = [{"kind": "journal", "path": "/other/private.txt", "match": "recency"},
                 {"kind": "journal", "path_or_uri": "../journal/moment.txt", "match": "content"},
                 {"kind": "context_overflow", "path": "/not-a-journal.txt"}]
        result = read_generation(self.generation(linked_artifacts=links), "minime")
        self.assertEqual(result["journal_refs"], ["/other/private.txt", "../journal/moment.txt"])
        self.assertEqual(result["metadata"]["source_record"]["linked_artifacts"], links)

    def test_symlink_and_hash_traversal_are_not_followed(self):
        path = self.legacy()
        outside = self.write("secret.txt", "SECRET")
        (path.parent / "prompt.txt").symlink_to(outside)
        result = read_generation(path, "minime")
        self.assertIsNone(result["prompt_text"])
        self.assertTrue(result["warnings"])
        gen = self.generation(messages=[{"role": "system", "content_sha256": "../../secret"}])
        self.assertIsNone(read_generation(gen, "minime")["prompt_text"])
        alias = self.root / "alias"
        alias.symlink_to(path.parent, target_is_directory=True)
        self.assertEqual(read_generation(alias / "job.json", "minime")["status"], "unreadable")

    def test_missing_malformed_utf8_and_budget_are_explicit(self):
        absent = read_generation(self.root / "missing/job.json", "minime")
        self.assertEqual(absent["status"], "unreadable")
        for content in ("{", "[]", '{"created_at": NaN}', '{"response_text": "\\ud800"}'):
            path = self.write("bad/job.json", content)
            self.assertEqual(read_generation(path, "minime")["status"], "malformed")
        path.write_bytes(b"\xff")
        self.assertIn("UnicodeDecodeError", " ".join(read_generation(path, "minime")["warnings"]))
        path = self.generation()
        self.assertEqual(read_generation(path, "minime", max_bytes=4)["status"], "unreadable")

    def test_naive_time_is_unknown_and_invalid_schema_never_exact(self):
        path = self.legacy()
        data = json.loads(path.read_text())
        data["created_at"] = "2026-09-06T23:06:00"
        path.write_text(json.dumps(data))
        self.assertIsNone(read_generation(path, "minime")["occurred_at"])
        result = read_generation(self.generation(schema_version=2), "minime")
        self.assertEqual(result["prompt_available"], 0)

    def test_discovery_is_sorted_and_skips_symlink_trees(self):
        a = self.write("jobs/a/job.json", {})
        b = self.write("jobs/b/job.json", {})
        self.write("jobs/b/ignore.json", {})
        (self.root / "jobs/link").symlink_to(a.parent, target_is_directory=True)
        self.assertEqual(list(discover_generation_files(self.root / "jobs")), [a, b])
        self.assertEqual(list(discover_generation_files(a.parent)), [a])
        self.assertEqual(list(discover_generation_files(a)), [a])


if __name__ == "__main__":
    unittest.main()
