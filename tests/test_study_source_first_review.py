"""Source-first integrity and missingness tests with explicit synthetic responses."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "research/outputs/2026-09-10-question-framing-v1"
spec = importlib.util.spec_from_file_location("source_first_review", ROOT / "probes/study_source_first_review.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def write(path, value):
    if path.exists():
        path.chmod(0o600)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fixture(temp):
    root = Path(temp) / "study"
    protocol = probe.plan.freeze(root, PREVIOUS)
    return root, protocol


def generated(root, protocol, trial, *, finish="stop", text="The shown branch sets pending fields.", outcome="returned", terminal=106):
    prepared = probe.plan.prepare_trial(root, protocol, trial)
    if "outcome" in prepared:
        row = {"spec": trial, **prepared}
        write(root / (trial["id"] + ".json"), row)
        return row
    system, user = [m["content"].strip() for m in prepared["messages"]]
    rendered = "<bos><|turn>system\n" + system + "<turn|>\n<|turn>user\n" + user + "<turn|>\n<|turn>model\n<|channel>thought\n<channel|>"
    prompt_tokens = [2, 3, 4]
    write(root / f"rendered-{trial['id']}.json", {"arm": trial["arm"], "id": trial["id"], "rendered_text": rendered,
          "rendered_sha256": sha(rendered), "token_ids": prompt_tokens, "token_count": len(prompt_tokens)})
    tokens = [42, terminal] if finish == "stop" else [42] * (protocol["settings"]["max_tokens"] if finish == "length" else 1)
    termination = ({"kind": "model_eos", "model_eos_reached": True, "stop_token_id": terminal, "stop_special": "<turn|>"}
                   if finish == "stop" else {"kind": "output_allowance", "model_eos_reached": False, "stop_token_id": None, "stop_special": None})
    result = {"text": text, "raw_text": text, "response_sha256": sha(text), "tokens": tokens, "completion_tokens": len(tokens),
              "prompt_tokens": len(prompt_tokens), "prompt_sha256": sha(rendered), "filtered_tokens": 0,
              "terminal_tokens": int(finish == "stop"), "finish": finish, "termination": None if finish == "error" else termination,
              "controls": {"temperature": protocol["settings"]["temperature"], "top_p": protocol["settings"]["top_p"]},
              "initial_cache_positions": [0, 0], "final_cache_positions": [len(prompt_tokens) + len(tokens)] * 2,
              "seconds": .2, "admission_seconds": .1}
    row = {"spec": trial, "outcome": outcome, "error": "synthetic failure" if finish == "error" else None, "result": result}
    write(root / (trial["id"] + ".json"), row)
    return row


@unittest.skipUnless(PREVIOUS.exists(), "frozen predecessor not available")
class SourceFirstReviewTests(unittest.TestCase):
    def test_prerun_is_read_only_and_separates_two_first_reads_from_eight_finals(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = fixture(temp)
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            report = probe.review(root)
            after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(report["planned"], 10)
            self.assertEqual(report["first"]["planned"], 2)
            self.assertEqual(report["finals"]["planned"], 8)
            self.assertEqual(report["outcomes"], {"missing": 10})
            self.assertEqual(len(report["within_account_pairs"]), 4)
            self.assertEqual(len(report["dependency_blocks"]), 2)
            self.assertEqual(report["complete_eligible_pairs"], 0)
            self.assertTrue(all(set(c["assessment"].values()) == {"unassessed"} for c in report["cells"]))

    def test_complete_block_keeps_distinct_pair_and_prerequisite_denominators(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = fixture(temp)
            for trial in protocol["trials"][:5]:
                generated(root, protocol, trial)
            report = probe.review(root)
            self.assertEqual(report["first"]["eligible"], 1)
            self.assertEqual(report["finals"]["eligible"], 4)
            self.assertEqual(report["complete_eligible_pairs"], 2)
            self.assertEqual(report["outcomes"], {"returned": 5, "missing": 5})
            self.assertTrue(report["dependency_blocks"][0]["first_eligible"])
            self.assertFalse(report["dependency_blocks"][1]["first_eligible"])

    def test_ineligible_first_blocks_only_carried_finals_and_preserves_nonempty(self):
        for kind in ("length", "error", "empty", "admission"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(temp)
                first = protocol["trials"][0]
                if kind == "admission":
                    probe.plan.prepare_trial(root, protocol, first)
                    write(root / (first["id"] + ".json"), {"spec": first, "outcome": "admission_unavailable", "result": None, "error": "busy"})
                else:
                    generated(root, protocol, first, finish=kind if kind in ("length", "error") else "stop",
                              text="" if kind == "empty" else "Partial or complete visible prose.",
                              outcome="generation_error" if kind == "error" else "returned")
                for trial in protocol["trials"][1:5]:
                    generated(root, protocol, trial)
                report = probe.review(root)
                self.assertEqual(report["first"]["eligible"], 0)
                self.assertEqual(report["finals"]["eligible"], 2)
                self.assertEqual(report["finals"]["outcomes"], {"returned": 2, "dependency_unavailable": 2, "missing": 4})
                self.assertEqual(report["complete_eligible_pairs"], 0)
                self.assertEqual(report["first"]["nonempty"], int(kind in ("length", "error")))

    def test_error_empty_and_length_finals_do_not_form_eligible_pairs(self):
        for kind in ("length", "error", "empty"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(temp)
                generated(root, protocol, protocol["trials"][0])
                generated(root, protocol, protocol["trials"][1])
                generated(root, protocol, protocol["trials"][2], finish=kind if kind != "empty" else "stop",
                          outcome="generation_error" if kind == "error" else "returned", text="" if kind == "empty" else "Partial text.")
                report = probe.review(root)
                self.assertEqual(report["complete_eligible_pairs"], 0)
                self.assertEqual(report["within_account_pairs"][0]["complete_nonempty"], kind != "empty")

    def test_changed_frozen_fields_source_template_predecessor_and_manifest_rejected(self):
        for kind in ("plan", "question", "account", "source", "template", "predecessor", "manifest", "settings"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(temp)
                if kind == "plan": protocol["trials"].reverse()
                elif kind == "question": protocol["question"] = "Find the proxy."
                elif kind == "account": protocol["accounts"]["retained"]["note"] = "Changed memory"
                elif kind == "settings": protocol["settings"]["top_p"] = .5
                elif kind == "source":
                    path = root / "source-snapshot/context.rs"; path.chmod(0o600); path.write_text("different source")
                elif kind == "template":
                    path = root / "block-runtime-source.txt"; path.chmod(0o600); path.write_text("different runtime")
                elif kind == "predecessor": protocol["previous"]["sha256"] = "false"
                else: write(root / "manifest.json", {"protocol_sha256": "false"})
                write(root / "protocol.json", protocol)
                with self.assertRaises(ValueError): probe.review(root)

    def test_complete_dependency_hashes_and_exact_prompt_content_are_checked(self):
        for kind in ("dependency_hash", "response_hash", "text_excerpt", "first_leak", "direct_leak", "result_spec"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(temp)
                for trial in protocol["trials"][:3]: generated(root, protocol, trial)
                first, direct, carried = protocol["trials"][:3]
                selected = first if kind == "first_leak" else direct if kind == "direct_leak" else carried
                path = root / f"input-{selected['id']}.json"
                row = json.loads(path.read_text())
                if kind in ("dependency_hash", "response_hash"):
                    row["dependency"]["result_file_sha256" if kind == "dependency_hash" else "response_sha256"] = "false"
                elif kind == "text_excerpt": row["messages"][1]["content"] = row["messages"][1]["content"].replace("The shown branch sets pending fields.", "The shown branch")
                elif kind == "result_spec":
                    path = root / f"{selected['id']}.json"; row = json.loads(path.read_text()); row["spec"]["seed"] += 1
                else: row["messages"][1]["content"] += "\nISOLATED FIRST-READ RESPONSE — leaked memory"
                write(path, row)
                with self.assertRaises(ValueError): probe.review(root)

    def test_native_eos_cache_render_and_response_receipts_are_independently_checked(self):
        for kind in ("native_eos", "stop_flag", "stop_token", "response_hash", "cache", "render", "filter", "returned_error"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(temp)
                first = protocol["trials"][0]
                row = generated(root, protocol, first)
                value = row["result"]
                if kind == "native_eos": value["tokens"][-1] = value["termination"]["stop_token_id"] = 999999
                elif kind == "stop_flag": value["termination"]["model_eos_reached"] = False
                elif kind == "stop_token": value["termination"]["stop_token_id"] = 1
                elif kind == "response_hash": value["response_sha256"] = "false"
                elif kind == "cache": value["initial_cache_positions"] = [1, 0]
                elif kind == "filter": value["filtered_tokens"] = 2
                elif kind == "returned_error": row["error"] = "hidden error"
                else:
                    path = root / f"rendered-{first['id']}.json"; rendered = json.loads(path.read_text())
                    rendered["rendered_text"] += "HIDDEN RECALL"; rendered["rendered_sha256"] = sha(rendered["rendered_text"])
                    write(path, rendered); value["prompt_sha256"] = rendered["rendered_sha256"]
                write(root / f"{first['id']}.json", row)
                with self.assertRaises(ValueError): probe.review(root)

    def test_absent_null_and_hash_linked_annotations_are_not_automatic_scores(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = fixture(temp)
            first = protocol["trials"][0]
            row = generated(root, protocol, first)
            write(root / "annotations.json", None)
            self.assertEqual(probe.review(root)["annotated"], 0)
            annotation = {"id": first["id"], "response_sha256": row["result"]["response_sha256"], "proxy_status": None,
                          "fixture_role": "unassessed", "shown_call_path": "partially_supported", "saved_note": "omitted",
                          "claims": [{"quote": "sets pending fields", "verdict": "supported"}], "choices": []}
            write(root / "annotations.json", [annotation])
            report = probe.review(root)
            self.assertEqual(report["first"]["annotated"], 1)
            self.assertEqual(report["cells"][0]["assessment"]["proxy_status"], "unassessed")
            self.assertNotIn("score", report)
            annotation["ambiguity_review"] = {"context_quote": "The shown branch sets pending fields.", "alternative_coding": "unassessed"}
            write(root / "annotations.json", [annotation])
            self.assertEqual(probe.review(root)["annotated"], 1)
            annotation["ambiguity_review"]["context_quote"] = "Context that never appeared"
            write(root / "annotations.json", [annotation])
            with self.assertRaises(ValueError): probe.review(root)
            del annotation["ambiguity_review"]
            annotation["claims"][0]["quote"] = "invented quote"
            write(root / "annotations.json", [annotation])
            with self.assertRaises(ValueError): probe.review(root)

    def test_completion_cannot_hide_missing_trials_or_claim_unverified_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = fixture(temp)
            write(root / "completed.json", {"cells": 10, "live_writes": False, "sources_unchanged": True, "model_assets_unchanged": True})
            with self.assertRaises(ValueError): probe.review(root)


if __name__ == "__main__":
    unittest.main()
