"""Evidence errors that would falsely imply learning or successful follow-through."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reservoir_research.study_capture import Collector, SCHEMA, encoded, epoch, new_output, sha
from reservoir_research.study_sequences import (
    NOTEBOOK, RECALLED_NOTEBOOK, authored_fields, build_report, command, era_for, followthrough,
    matching_generations, merge_ranges, notebook_exposure, receipt_records,
    source_progress, text_sha, verify_records,
    writing_match,
)


def record(kind, value, being="minime", path="/fixture"):
    raw = encoded(value)
    return dict(path=path, kind=kind, being=being, text=raw.decode(),
                sha256=sha(raw), bytes=len(raw), filename_time=120)


def delivery(start=0, end=10, when=100, revision="a", being="minime"):
    return dict(path=f"/{being}/{when}", being=being, completed=when, verified=True,
        page=dict(source="astrid/file.rs", revision={"sha256": revision, "bytes": 20},
                  start={"byte": start}, end={"byte": end}))


def wire_record(navigation=False, supplied="SOURCE file", actual=None, finish="stop"):
    page = dict(id="page", text=supplied)
    request = dict(model="model", messages=[dict(role="system", content="system"),
                                           dict(role="user", content=actual or supplied)])
    response = dict(message=dict(content="NEXT: SELF_STUDY CONTINUE"), done=True,
                    done_reason=finish, created_at="2026-09-08T22:20:00Z")
    value = dict(schema="source_study_navigation_delivery_v1" if navigation else "source_study_delivery_v1",
                 request_json=json.dumps(request), response_json=json.dumps(response))
    if navigation:
        value["output"] = dict(text=supplied, page=None, navigation_id="navigation")
    else:
        value["page"] = page
    result = record("navigation" if navigation else "delivery", value)
    result["path"] = f"/fixture/{'navigation' if navigation else 'page'}/{result['sha256']}.json"
    return result


class SequenceTests(unittest.TestCase):
    def test_receipt_repeats_do_not_double_count_coverage(self):
        rows = [delivery(0, 10, 90), delivery(5, 15, 100), delivery(0, 10, 110), delivery(15, 20, 120)]
        progress = source_progress(rows, 100, 130)
        self.assertEqual([p["new_bytes"] for p in progress], [5, 0, 5])
        self.assertEqual([p["repeated_bytes"] for p in progress], [5, 10, 0])
        self.assertTrue(progress[-1]["full_revision_delivered"])

    def test_revisions_and_beings_keep_separate_coverage(self):
        rows = [delivery(0, 10, 90), delivery(0, 10, 100, revision="b"),
                delivery(0, 10, 110, being="astrid")]
        self.assertEqual([p["new_bytes"] for p in source_progress(rows, 100, 120)], [10, 10])

    def test_cutoff_and_failed_receipt_do_not_advance_source(self):
        bad = delivery(0, 10, 100); bad["verified"] = False
        self.assertEqual(source_progress([bad, delivery(0, 10, 110)], 90, 110), [])

    def test_disjoint_source_does_not_claim_complete_file(self):
        p = source_progress([delivery(0, 5, 100), delivery(10, 20, 110)], 90, 120)[-1]
        self.assertEqual(p["union_bytes_after"], 15)
        self.assertFalse(p["full_revision_delivered"])

    def test_bad_ranges_rejected(self):
        with self.assertRaises(ValueError): merge_ranges([[8, 2]])

    def test_read_more_is_not_continue(self):
        self.assertEqual(command("NEXT: READ_MORE", "astrid")["category"], "READ_MORE")
        self.assertEqual(command("NEXT: SELF_STUDY CONTINUE", "minime")["category"], "SELF_STUDY:CONTINUE")

    def test_terminal_source_choices_are_explicitly_versioned(self):
        choice = "SELF_STUDY OPEN astrid/crates/astrid-kernel/src/lib.rs 1"
        for being in ("astrid", "minime"):
            self.assertIsNone(command(choice, being)["raw"])
            self.assertEqual(command(choice, being, terminal_source_choice=True)["raw"], choice)
            for example in ("> " + choice, "```\n" + choice, "```\n" + choice + "\n```",
                            choice + "\nAn example.", "RUN example"):
                self.assertIsNone(command(example, being, terminal_source_choice=True)["raw"])
            self.assertEqual(command("NEXT: REST\n" + choice, being,
                                     terminal_source_choice=True)["verb"], "REST")

    def test_new_choice_parser_requires_verified_new_process_era(self):
        response = "My next step.\nSELF_STUDY CONTINUE"
        gen = dict(generation_id="120000-x", created_at_unix_ms=130000, lane="self_study",
                   status="ok", pid=2, response_text=response, response_sha256=text_sha(response),
                   messages=[dict(role="user", content="Shared system map")])
        eras = {b: dict(boundary=100, old_pid=1, new_pid=2) for b in ("minime", "astrid")}
        for profile, pid, expected in (("evidence-views", 2, None), ("journal-room", 3, None),
                                       ("journal-room", 2, "SELF_STUDY CONTINUE"),
                                       ("study-choice", 2, "SELF_STUDY CONTINUE")):
            gen["pid"] = pid
            packet = dict(schema=SCHEMA, records=[record("generation", gen)], errors=[],
                          selection=dict(since="1970-01-01T00:01:50Z", until_exclusive="1970-01-01T00:05:00Z",
                                         release_profile=profile))
            with patch("reservoir_research.study_sequences.release_eras", return_value=eras):
                study = build_report(packet)["studies"][0]
            self.assertEqual(study["next"]["raw"], expected)
            self.assertEqual(study["text"], response)

    def test_last_next_outside_fences_and_markdown(self):
        text = "NEXT: REST\n```\nNEXT: READ_MORE\n```\nNEXT: **SELF_STUDY** RESUME astrid/file.rs<end_of_turn>"
        self.assertEqual(command(text, "minime")["comparison_key"], "SELF_STUDY RESUME astrid/file.rs")

    def test_quoted_markers_are_not_authored_fields(self):
        value = authored_fields("```\nSTUDY_NOTE: example\n```\nSTUDY_NOTE: kept\nSTUDY_QUESTION: -")
        self.assertEqual([x["text"] for x in value["STUDY_NOTE"]], ["kept"])
        self.assertEqual(value["STUDY_QUESTION"][0]["text"], "-")

    def test_notebook_requires_complete_delivered_shape(self):
        fields = dict(note=None, question=dict(origin="page", response_sha256="a", text="why?"), previous=None)
        rendered = "SOURCE file\n\n" + NOTEBOOK + " Missing fields.\n" + json.dumps(fields) + "\nEnd of study notebook.\n"
        result = notebook_exposure(rendered)
        self.assertEqual(result["fields"]["question"]["text"], "why?")
        self.assertEqual(notebook_exposure("SOURCE file")["status"], "absent")
        self.assertEqual(notebook_exposure(rendered[:-30])["status"], "malformed")

    def test_navigation_requires_notebook_not_just_map(self):
        rec = wire_record(True, "Shared system map\nnotebook", "Shared system map")
        self.assertFalse(receipt_records([rec])[0]["verified"])

    def test_recent_notebook_accounts_preserve_completeness_without_inventing_legacy_fields(self):
        legacy = dict(origin="page:1", response_sha256="a", text="opening excerpt")
        complete = dict(origin="page:2", response_sha256="b", text="whole answer", complete=True, prose_bytes=12)
        fields = dict(note=None, question=None, previous=complete, recent=[legacy])
        def rendered():
            return "SOURCE file\n\n" + RECALLED_NOTEBOOK + " — recalled prose.\n" + json.dumps(fields) + "\nEnd of study notebook.\n"
        exposure = notebook_exposure(rendered())
        self.assertEqual(exposure["fields"], fields)
        self.assertNotIn("complete", exposure["fields"]["recent"][0])
        fields["recent"] = "not a list"
        self.assertEqual(notebook_exposure(rendered())["status"], "malformed")
        fields["recent"] = [dict(complete, complete="true")]
        self.assertEqual(notebook_exposure(rendered())["status"], "malformed")

    def test_report_retains_separate_origins_for_recent_accounts_without_inventing_receipts(self):
        entry = dict(origin="page:1", response_sha256="not-captured", text="earlier conclusion", complete=True)
        fields = dict(note=None, question=None, previous=None, recent=[entry])
        supplied = "SOURCE file\n\n" + RECALLED_NOTEBOOK + " — recalled prose.\n" + json.dumps(fields) + "\nEnd of study notebook.\n"
        text = "I can compare the earlier conclusion.\nNEXT: SELF_STUDY CONTINUE"
        gen = dict(generation_id="120000-x", created_at_unix_ms=130000, lane="self_study",
                   status="ok", pid=2, response_text=text, response_sha256=text_sha(text),
                   messages=[dict(role="user", content=supplied)])
        eras = {b: dict(boundary=100, old_pid=1, new_pid=2) for b in ("minime", "astrid")}
        packet = dict(schema=SCHEMA, records=[record("generation", gen)], errors=[],
                      selection=dict(since="1970-01-01T00:01:50Z", until_exclusive="1970-01-01T00:05:00Z", release_profile="study-context"))
        with patch("reservoir_research.study_sequences.release_eras", return_value=eras):
            study = build_report(packet)["studies"][0]
        self.assertEqual(study["notebook"]["origin_receipts"], {"recent[0]": []})
        self.assertEqual(study["notebook"]["fields"]["recent"], [entry])

    def test_recalled_notebook_preserves_origin_and_source_commands(self):
        previous = dict(origin="page:1", response_sha256="abc", text="No matches for the exact literal query",
                        reopen="SELF_STUDY OPEN astrid/file.rs", resume="SELF_STUDY RESUME astrid/file.rs")
        fields = dict(note=None, question=None, previous=previous)
        current = "THIS TURN — system map\nShared system map"
        rendered = current + "\n\n" + RECALLED_NOTEBOOK + " — claims are not verified.\n" + json.dumps(fields) + "\nEnd of study notebook.\n"
        result = notebook_exposure(rendered)
        self.assertEqual(result["status"], "included_in_submitted_user_text")
        self.assertEqual(result["fields"]["previous"], previous)
        self.assertEqual(rendered[:result["start"]], current)
        self.assertEqual(notebook_exposure(rendered[:-30])["status"], "malformed")

    def test_length_completion_not_verified_delivery(self):
        self.assertFalse(receipt_records([wire_record(finish="length")])[0]["verified"])

    def test_source_page_can_have_additional_notebook_exposure(self):
        row = receipt_records([wire_record(actual="SOURCE file\nnotebook")])[0]
        self.assertTrue(row["verified"])
        self.assertEqual(row["user_text"], "SOURCE file\nnotebook")

    def test_protected_navigation_uses_utf8_byte_offsets(self):
        source = "Shared system map — fixture"
        prefix = "λ header\n"
        content = prefix + source + "\nwrapper"
        admission = dict(kind="source_study", content_id="source-navigation:fixture", message_index=0,
                         content_start_byte=len(prefix.encode()), content_end_byte=len((prefix+source).encode()),
                         source_start_byte=0, admitted_end_byte=len(source.encode()),
                         offered_bytes=len(source.encode()), admitted_text_sha256=text_sha(source))
        value = dict(schema="accepted_prompt_delivery_v1", accepted_completion="NEXT: READ_MORE",
                     attempt=dict(admission=admission,
                         request_json=json.dumps(dict(messages=[dict(role="user", content=content)])),
                         response_json=json.dumps(dict(created=120, choices=[dict(finish_reason="stop",
                             message=dict(content="NEXT: READ_MORE"))]))))
        row = record("accepted_delivery", value, "astrid")
        row["path"] = f"/fixture/{row['sha256']}.json"
        receipt = receipt_records([row])[0]
        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["text"], "NEXT: READ_MORE")
        value["attempt"]["admission"]["offered_bytes"] += 1
        row = record("accepted_delivery", value, "astrid")
        row["path"] = f"/fixture/{row['sha256']}.json"
        self.assertFalse(receipt_records([row])[0]["verified"])

    def test_two_stores_do_not_duplicate_one_delivery(self):
        row = wire_record()
        d = json.loads(row["text"])
        value = dict(schema="accepted_prompt_delivery_v1", accepted_completion="NEXT: SELF_STUDY CONTINUE",
            attempt=dict(request_json=d["request_json"], response_json=d["response_json"],
                         admission=dict(kind="source_study")))
        other = record("accepted_delivery", value, path="/duplicate-store")
        self.assertEqual(len(receipt_records([other, row])), 1)

    def test_repeated_exact_generations_remain_ambiguous(self):
        rec = receipt_records([wire_record()])[0]
        gen = dict(model="model", response_text=rec["text"], messages=[
            dict(role="system", content_sha256=text_sha("system")), dict(role="user", content="SOURCE file")])
        a, b = record("generation", gen, path="/a"), record("generation", gen, path="/b")
        self.assertEqual(len(matching_generations(rec, [(a, gen), (b, gen)])), 2)
        b["being"] = "astrid"
        self.assertEqual(len(matching_generations(rec, [(a, gen), (b, gen)])), 1)

    def test_system_prompt_mismatch_prevents_join(self):
        rec = receipt_records([wire_record()])[0]
        gen = dict(model="model", response_text=rec["text"], messages=[
            dict(role="system", content_sha256="wrong"), dict(role="user", content="SOURCE file")])
        self.assertEqual(matching_generations(rec, [(record("generation", gen), gen)]), [])

    def test_parentage_and_temporal_neighbor_are_distinct(self):
        study = dict(id="s", being="minime", completed=100, started=90, action_id="owner",
                     next=command("NEXT: SELF_STUDY CONTINUE", "minime"))
        base = dict(being="minime", started=105, action_id="a", raw_next="SELF_STUDY CONTINUE")
        foreign = {**base, "being": "astrid", "parent_action_id": "owner"}
        neighbor = {**base, "parent_action_id": "elsewhere"}
        child = {**base, "parent_action_id": "owner", "raw_next": "READ_MORE", "status": "blocked"}
        result = followthrough(study, [foreign, neighbor, child], [], 200)
        self.assertEqual(len(result["explicit_parent_actions"]), 1)
        self.assertFalse(result["explicit_parent_actions"][0]["matches_requested"])
        self.assertEqual(result["temporal_action_count"], 2)
        self.assertTrue(result["right_censored"])
        self.assertEqual(result["observed_seconds"], 100)

    def test_horizon_end_excluded(self):
        study = dict(id="s", being="astrid", completed=100, started=90, next=command("NEXT: READ_MORE", "astrid"))
        late = dict(being="astrid", started=1900, raw_next="READ_MORE")
        result = followthrough(study, [late], [], 2000)
        self.assertEqual(result["temporal_action_count"], 0)
        self.assertFalse(result["right_censored"])

    def test_transition_unknown_pid_and_manifest(self):
        eras = {"astrid": dict(boundary=100, old_pid=1, new_pid=2,
                              old_manifest_sha256="old", manifest_sha256="new")}
        self.assertEqual(era_for("astrid", 99, 101, 1, eras), "transition")
        self.assertEqual(era_for("astrid", 101, 110, 3, eras), "after_unverified")
        self.assertEqual(era_for("astrid", 101, 110, 2, eras, {"manifest_sha256": "old"}), "after_unverified")
        self.assertEqual(era_for("astrid", 101, 110, 2, eras, {"manifest_sha256": "new"}), "after")

    def test_shared_helper_activation_precedes_minime_reload(self):
        eras = {"astrid": dict(boundary=95), "minime": dict(boundary=100, old_pid=1, new_pid=2)}
        self.assertEqual(era_for("minime", 96, 99, 1, eras), "transition_shared_helper")

    def test_tampering_and_duplicate_paths_fail(self):
        row = record("journal", "hello")
        packet = dict(schema=SCHEMA, records=[row])
        verify_records(packet)
        packet["records"].append(row)
        with self.assertRaises(ValueError): verify_records(packet)
        packet["records"] = [{**row, "text": "changed"}]
        with self.assertRaises(ValueError): verify_records(packet)

    def test_runtime_action_separator_keeps_exact_authored_spans(self):
        response = "My question.\n\nNEXT: INTROSPECT file 0"
        text = "Header\n\nMy question.\n\n--- ACTION TAIL ---\nNEXT: INTROSPECT file 0\n"
        row = dict(text=text, path="/moment.txt", sha256=text_sha(text))
        match = writing_match(response, row)
        self.assertEqual(len(match["source_spans"]), 2)
        self.assertEqual("".join(text[a:b] for a,b in match["source_spans"]), response)
        self.assertIsNone(writing_match(response.replace("question", "answer"), row))

    def test_separator_inside_quoted_code_is_not_removed(self):
        text = "```\na\n--- ACTION TAIL ---\nb\n```"
        row = dict(text=text, path="/quoted.txt", sha256=text_sha(text))
        self.assertIsNone(writing_match("a\nb", row))

    def test_output_and_time_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): new_output(Path(tmp) / "live")
        with self.assertRaises(ValueError): epoch("2026-09-08T12:00:00")
        with self.assertRaises(ValueError): Collector(1, 100000)

    def test_failed_study_wire_is_linked_once_and_never_an_accepted_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            folder = workspace / "diagnostics/source_study_attempts"
            folder.mkdir(parents=True)
            path = folder / ("attempt_" + "a" * 32 + ".json")
            path.write_text('{"failure":"output_limit"}')
            capture = Collector(1, 2)
            for _ in range(2):
                capture.linked_study_failure(workspace, str(path), "minime")
            self.assertEqual(len(capture.records), 1)
            self.assertEqual(capture.records[0]["kind"], "source_study_failure")
            self.assertFalse(capture.errors)

    def test_failed_study_links_cannot_read_outside_diagnostics_or_through_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            outside = workspace / "outside.json"
            outside.write_text("private")
            folder = workspace / "diagnostics/source_study_attempts"
            folder.mkdir(parents=True)
            link = folder / ("attempt_" + "a" * 32 + ".json")
            link.symlink_to(outside)
            capture = Collector(1, 2)
            for path in (outside, link, folder / "unrelated.json"):
                capture.linked_study_failure(workspace, str(path), "minime")
            self.assertFalse(capture.records)
            self.assertEqual(len(capture.errors), 3)

    def test_absent_navigation_receipt_does_not_discard_generation(self):
        gen = dict(generation_id="120000-x", created_at_unix_ms=130000, lane="self_study",
                   status="ok", pid=2, response_text="NEXT: SELF_STUDY MAP", response_sha256=text_sha("NEXT: SELF_STUDY MAP"),
                   messages=[dict(role="user", content="Shared system map")])
        packet = dict(schema=SCHEMA, records=[record("generation", gen)], errors=[],
                      selection=dict(since="1970-01-01T00:01:50Z", until_exclusive="1970-01-01T00:05:00Z"))
        eras = {b: dict(boundary=100, old_pid=1, new_pid=2) for b in ("minime", "astrid")}
        with patch("reservoir_research.study_sequences.release_eras", return_value=eras):
            result = build_report(packet)
        self.assertEqual(result["summary"]["minime"]["after"]["attempts"], 1)
        self.assertFalse(result["studies"][0]["receipt_verified"])
        self.assertEqual(result["studies"][0]["writing"], [])

    def test_late_provider_completion_is_not_available_at_cutoff(self):
        event = dict(stage="dispatch_started", attempt_id="test", label="self_study", pid=2,
                     created_at_unix_ms=120000, provider="mlx", release_before={"manifest_sha256": "new"})
        terminal = {**event, "stage": "provider_outcome", "elapsed_ms": 300000, "outcome": "provider_returned"}
        packet = dict(schema=SCHEMA, errors=[], records=[record("provider_event", event, "astrid", "/dispatch"),
                      record("provider_event", terminal, "astrid", "/terminal")],
                      selection=dict(since="1970-01-01T00:01:50Z", until_exclusive="1970-01-01T00:05:00Z"))
        eras = {b: dict(boundary=100, old_pid=1, new_pid=2, manifest_sha256="new") for b in ("astrid", "minime")}
        with patch("reservoir_research.study_sequences.release_eras", return_value=eras):
            result = build_report(packet)
        self.assertEqual(result["studies"][0]["status"], "no_completion_by_cutoff")
        self.assertFalse(result["studies"][0]["receipt_verified"])

    def test_recalled_search_wording_does_not_become_current_navigation_signal(self):
        fields = dict(note=None, question=None, previous=dict(origin="page", response_sha256="abc",
                      text="No matches for the exact literal query"))
        supplied = "THIS TURN — Map: navigation only.\nShared system map\n\n" + RECALLED_NOTEBOOK + "\n" + json.dumps(fields) + "\nEnd of study notebook."
        gen = dict(generation_id="120000-x", created_at_unix_ms=130000, lane="self_study", status="ok", pid=2,
                   response_text="NEXT: SELF_STUDY CONTINUE", response_sha256=text_sha("NEXT: SELF_STUDY CONTINUE"),
                   messages=[dict(role="user", content=supplied)])
        packet = dict(schema=SCHEMA, records=[record("generation", gen)], errors=[],
                      selection=dict(since="1970-01-01T00:01:50Z", until_exclusive="1970-01-01T00:05:00Z"))
        eras = {b: dict(boundary=100, old_pid=1, new_pid=2) for b in ("minime", "astrid")}
        with patch("reservoir_research.study_sequences.release_eras", return_value=eras):
            study = build_report(packet)["studies"][0]
        self.assertEqual(study["notebook"]["status"], "included_in_submitted_user_text")
        self.assertFalse(study["navigation"]["explicit_no_matches"])


if __name__ == "__main__":
    unittest.main()
