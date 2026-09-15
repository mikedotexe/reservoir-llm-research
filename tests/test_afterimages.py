"""Synthetic Afterimage chains; no source files, runtime imports or model calls."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.afterimages import build_afterimage_trace, export_afterimage_trace


AFTERIMAGE = "ai_2026-09-07_fixture_1788813600000_000001"
AT = "2026-09-07T20:42:00Z"
AT_MS = int(datetime.fromisoformat(AT.replace("Z", "+00:00")).timestamp() * 1000)
JOURNAL = "/not-opened/minime/journal/daydream_2026-09-07T13-42-00.txt"
CUE = f"Past {AFTERIMAGE} | 2026-09-07 | incomplete physical trace"
RESPONSE = f"The saved trace {AFTERIMAGE} has a missing interval.\nNEXT: AFTERIMAGE_OPEN {AFTERIMAGE}"
MESSAGES = [{"role":"system", "content":"A synthetic fixture: Ω."},
            {"role":"user", "content":CUE}]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def source(kind, value, source_id=None, being="minime", path=None, **changes):
    content = value if isinstance(value, str) else encoded(value)
    source_id = source_id or kind + "-fixture"
    item = {"source_id":source_id, "kind":kind, "being":being,
            "path":path or f"/not-opened/{being}/{source_id}.json",
            "sha256":digest(content), "content":content, "complete_file":True,
            "byte_offset":0, "bytes_read":len(content.encode("utf-8")), "stable":True}
    item.update(changes)
    return item


def exposure(**changes):
    item = {"afterimage_id":AFTERIMAGE, "opportunity_id":"opportunity_fixture",
            "receiver":"minime", "attempt_id":"exposure_fixture",
            "backend":"ollama", "model":"fixture-model", "included":True,
            "content_fingerprint":digest(CUE),
            "final_messages_fingerprint":digest(encoded(MESSAGES)),
            "outcome":"final_request_prepared", "reason":None,
            "recorded_at_unix_ms":AT_MS}
    item.update(changes)
    return item


def generation(**changes):
    item = {"schema_version":1, "being":"minime", "generation_id":"gen_fixture",
            "attempt_index":0, "lane":"daydream", "backend":"ollama",
            "model":"fixture-model", "status":"accepted", "messages_source":"adapted",
            "messages":deepcopy(MESSAGES), "response_text":RESPONSE,
            "response_sha256":digest(RESPONSE), "created_at_unix_ms":AT_MS + 2000,
            "job_id":"job_fixture", "action_id":"action_fixture", "thread_id":"thread_fixture",
            "linked_artifacts":[{"kind":"journal", "path":JOURNAL}]}
    item.update(changes)
    return item


def capture(*extra_sources):
    physical = {"schema_version":1, "policy":"transition_afterimage_v1", "id":AFTERIMAGE,
                "origin":"automatic_event", "anchor_unix_ms":AT_MS - 120000,
                "session_id":"session_fixture", "status":"incomplete",
                "reasons":["producer_cadence_gap"], "coverage":{"complete":False},
                "samples":[], "events":[], "measurements":{}}
    selection = {"id":AFTERIMAGE, "opportunity_id":"opportunity_fixture", "receiver":"minime",
                 "anchor_unix_ms":AT_MS - 120000, "text":CUE,
                 "fingerprint":digest(CUE), "protected":False}
    cue = {"enabled":True, "eligible_count":3, "opportunities":{
        "opportunity_fixture":{"created_at_unix_ms":AT_MS, "selection":selection}}}
    return {"schema":"afterimage_capture_v1", "afterimage_id":AFTERIMAGE,
            "since":"2026-09-07T20:39:00Z", "until":"2026-09-07T21:18:38Z",
            "captured_at_utc":"2026-09-07T21:20:00Z",
            "sources":[source("physical_trace", physical), source("cue_state", cue), *extra_sources],
            "coverage":[{"kind":"fixture", "status":"bounded_fixture_only",
                         "notes":["No claim about uncaptured sources or live delivery."]}], "issues":[]}


class AfterimageTraceTests(unittest.TestCase):
    def report(self, *sources):
        return build_afterimage_trace(capture(*sources))

    def test_capture_only_and_exact_source_bytes_are_preserved_without_source_reads(self):
        value = capture(source("exposure", exposure()))
        original = deepcopy(value)
        with patch("builtins.open", side_effect=AssertionError("source path opened")), \
             patch.object(Path, "open", side_effect=AssertionError("source path opened")), \
             patch.object(Path, "read_text", side_effect=AssertionError("source path opened")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("source path opened")):
            report = build_afterimage_trace(value)
        self.assertEqual(value, original)
        self.assertEqual(report["schema"], "afterimage_trace_v1")
        self.assertEqual(report["afterimage_id"], AFTERIMAGE)
        self.assertEqual(report["window"], {"since":value["since"], "until":value["until"]})
        by_id = {row["source_id"]:row for row in report["sources"]}
        self.assertEqual(set(by_id), {row["source_id"] for row in value["sources"]})
        for supplied in value["sources"]:
            retained = by_id[supplied["source_id"]]
            self.assertTrue(retained["verified"])
            for key in supplied:
                self.assertEqual(retained[key], supplied[key])
        self.assertIn(CUE, encoded(report))
        self.assertRegex(report["result_sha256"], r"^[a-f0-9]{64}$")

    def test_selected_cue_omitted_from_request_is_never_accepted(self):
        report = self.report(source("exposure", exposure(included=False,
            generation_id="gen_fixture", attempt_index=0)), source("generation", generation()))
        row = report["exposures"][0]
        self.assertFalse(row["included"])
        self.assertNotEqual(row["acceptance_status"], "explicit_accepted")
        self.assertTrue(report["opportunities"])
        self.assertIn(CUE, encoded(report))

    def test_prepared_included_and_backend_ok_are_not_acceptance(self):
        for with_generation in (False, True):
            with self.subTest(with_generation=with_generation):
                exp = exposure(generation_id="gen_fixture", attempt_index=0)
                sources = [source("exposure", exp)]
                if with_generation:
                    sources.append(source("generation", generation(status="ok")))
                report = self.report(*sources)
                row = report["exposures"][0]
                self.assertTrue(row["included"])
                self.assertEqual(row["outcome"], "final_request_prepared")
                self.assertEqual(row["acceptance_status"], "unresolved")

    def test_explicit_accepted_attempt_needs_matching_final_messages_and_attempt_identity(self):
        for changes in ({}, {"final_messages_fingerprint":"0" * 64}, {"attempt_index":1}):
            with self.subTest(changes=changes):
                exp = exposure(generation_id="gen_fixture", attempt_index=0)
                exp.update(changes)
                report = self.report(source("exposure", exp), source("generation", generation()))
                status = report["exposures"][0]["acceptance_status"]
                if not changes:
                    self.assertEqual(status, "explicit_accepted")
                else:
                    self.assertNotEqual(status, "explicit_accepted")

    def test_accepted_generation_without_final_message_hash_does_not_close_gap(self):
        exp = exposure(generation_id="gen_fixture", attempt_index=0)
        del exp["final_messages_fingerprint"]
        report = self.report(source("exposure", exp), source("generation", generation()))
        self.assertEqual(report["exposures"][0]["acceptance_status"], "unresolved")

    def test_matching_accepted_request_without_the_cue_is_not_accepted_cue_exposure(self):
        no_cue = [{"role":"user", "content":"An unrelated ordinary question."}]
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=0,
            final_messages_fingerprint=digest(encoded(no_cue)))),
            source("generation", generation(messages=no_cue)))
        self.assertNotEqual(report["exposures"][0]["acceptance_status"], "explicit_accepted")
        self.assertTrue(report["gaps"])

    def test_cue_text_fingerprint_mismatch_cannot_verify_accepted_exposure(self):
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=0,
            content_fingerprint="0" * 64)), source("generation", generation()))
        self.assertNotEqual(report["exposures"][0]["acceptance_status"], "explicit_accepted")

    def test_unknown_generation_schema_stays_inspectable_but_cannot_verify_acceptance(self):
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=0)),
            source("generation", generation(schema_version=999)))
        self.assertNotEqual(report["exposures"][0]["acceptance_status"], "explicit_accepted")
        retained = [row for row in report["records"] if row["kind"] == "generation"]
        self.assertEqual(retained[0]["payload"]["schema_version"], 999)
        self.assertTrue(report["issues"] or report["gaps"])

    def test_boolean_provider_attempt_is_not_integer_attempt_zero(self):
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=False)),
            source("generation", generation()))
        self.assertNotEqual(report["exposures"][0]["acceptance_status"], "explicit_accepted")
        self.assertEqual(report["exposures"][0]["generation_ids"], [])

    def test_conflicting_same_generation_attempt_is_not_arbitrarily_accepted(self):
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=0)),
            source("generation", generation(), source_id="generation-accepted"),
            source("generation", generation(status="rejected"), source_id="generation-rejected"))
        self.assertNotEqual(report["exposures"][0]["acceptance_status"], "explicit_accepted")
        self.assertTrue(report["gaps"] or report["issues"])

    def test_generation_response_artifact_and_action_ids_remain_inspectable(self):
        journal = f"=== RECESS DAYDREAM ===\nTimestamp: {AT}\n\n{RESPONSE}\n"
        action = {"action_id":"action_fixture", "job_id":"job_fixture", "thread_id":"thread_fixture",
                  "started_at":AT, "raw_next":f"AFTERIMAGE_OPEN {AFTERIMAGE}",
                  "effective_action":"AFTERIMAGE_OPEN", "status":"blocked", "reason":"fixture budget"}
        report = self.report(source("exposure", exposure(generation_id="gen_fixture", attempt_index=0)),
            source("generation", generation()), source("journal", journal, path=JOURNAL), source("action", action))
        text = encoded(report)
        self.assertIn(RESPONSE.replace("\n", "\\n"), text)
        self.assertIn("action_fixture", text)
        self.assertIn("fixture budget", text)
        self.assertIn(JOURNAL, text)
        self.assertTrue(report["links"])
        gen = next(row for row in report["records"] if row["kind"] == "generation")
        entry = next(row for row in report["records"] if row["kind"] == "journal")
        declared = [edge for edge in report["links"] if edge["source"] == gen["id"]
                    and edge["target"] == entry["id"] and edge["basis"] == "source_declared"]
        self.assertEqual(len(declared), 1)
        # Every link must identify its evidentiary basis, not just name neighbors.
        for link in report["links"]:
            for key in ("source", "target", "basis", "status", "meaning"):
                self.assertTrue(link[key])

    def test_journal_artifact_reference_requires_exact_path_not_prefix(self):
        journal = f"=== RECESS DAYDREAM ===\nTimestamp: {AT}\n\n{RESPONSE}\n"
        report = self.report(source("generation", generation(linked_artifacts=[
            {"kind":"journal", "path":JOURNAL + "_other"}])), source("journal", journal, path=JOURNAL))
        gen = next(row for row in report["records"] if row["kind"] == "generation")
        entry = next(row for row in report["records"] if row["kind"] == "journal")
        self.assertFalse(any(edge["source"] == gen["id"] and edge["target"] == entry["id"]
                             for edge in report["links"]))

    def test_nearby_text_and_similar_ids_do_not_establish_generation_exposure(self):
        nearby = generation(generation_id="unrelated_generation", response_text=RESPONSE,
                            response_sha256=digest(RESPONSE))
        wrong_attempt = exposure(generation_id="gen_fixture_suffix", attempt_index=0)
        report = self.report(source("exposure", wrong_attempt), source("generation", nearby))
        self.assertEqual(report["exposures"][0]["acceptance_status"], "unresolved")
        self.assertEqual(report["exposures"][0]["generation_ids"], [])

    def test_tampered_source_hash_refuses_build(self):
        value = capture(source("generation", generation()))
        value["sources"][-1]["content"] += " "
        with self.assertRaises(ValueError):
            build_afterimage_trace(value)

    def test_partial_jsonl_keeps_valid_record_and_reports_malformed_line(self):
        content = encoded(exposure()) + "\n{invalid partial line\n"
        item = source("exposure", content, complete_file=False, byte_offset=4096, stable=False)
        report = self.report(item)
        self.assertEqual(len(report["exposures"]), 1)
        retained = next(row for row in report["sources"] if row["source_id"] == item["source_id"])
        self.assertFalse(retained["complete_file"])
        self.assertFalse(retained["stable"])
        self.assertEqual(retained["byte_offset"], 4096)
        self.assertTrue(report["issues"] or report["gaps"])
        detail = encoded([report["issues"], report["gaps"]]).lower()
        self.assertTrue(any(word in detail for word in ("malformed", "invalid", "parse", "json")))

    def test_malformed_cue_opportunity_container_is_reported_without_crashing(self):
        for malformed in (None, [], "not a mapping", 12):
            with self.subTest(malformed=malformed):
                value = capture()
                value["sources"][1] = source("cue_state", {"enabled":True, "opportunities":malformed})
                report = build_afterimage_trace(value)
                self.assertTrue(report["issues"])
                self.assertEqual(report["opportunities"], [])

    def test_invalid_json_array_members_remain_visible_as_ingestion_issues(self):
        report = self.report(source("exposure", [exposure(), None, "unexpected scalar"]))
        self.assertEqual(len(report["exposures"]), 1)
        self.assertTrue(report["issues"])

    def test_private_export_refuses_existing_output_and_preserves_notes(self):
        report = self.report(source("exposure", exposure()))
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary).resolve() / "report"
            export_afterimage_trace(report, out)
            self.assertEqual(out.stat().st_mode & 0o777, 0o700)
            outputs = [path for path in out.iterdir() if path.is_file()]
            self.assertTrue(outputs)
            for path in outputs:
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            note = out / "reader-notes.md"
            note.write_text("Keep this reader's interpretation.")
            with self.assertRaises((ValueError, FileExistsError)):
                export_afterimage_trace(report, out)
            self.assertEqual(note.read_text(), "Keep this reader's interpretation.")

    def test_export_rejects_changed_report_and_existing_symlink(self):
        report = self.report(source("exposure", exposure()))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            changed = deepcopy(report)
            changed["afterimage_id"] += "_tampered"
            with self.assertRaises(ValueError):
                export_afterimage_trace(changed, root / "changed")
            self.assertFalse((root / "changed").exists())
            target = root / "real"
            target.mkdir()
            link = root / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises((ValueError, FileExistsError)):
                export_afterimage_trace(report, link)
            self.assertEqual(list(target.iterdir()), [])

    def test_export_protects_captured_source_directories_and_known_live_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            captured = root / "captured"
            captured.mkdir()
            report = self.report(source("exposure", exposure(), path=str(captured / "receipt.jsonl")))
            with self.assertRaises(ValueError):
                export_afterimage_trace(report, captured / "report")
            self.assertFalse((captured / "report").exists())
            live = root / "live"
            live.mkdir()
            with patch("reservoir_research.store.protected_roots", return_value=[live]):
                with self.assertRaises(ValueError):
                    export_afterimage_trace(report, live / "report")
            self.assertFalse((live / "report").exists())


if __name__ == "__main__":
    unittest.main()
