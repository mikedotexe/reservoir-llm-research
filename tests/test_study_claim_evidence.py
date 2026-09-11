"""Claim/source layout conservation tests; frozen inputs only, no generations."""
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = ROOT / "research/outputs/2026-09-10-source-first-v1"
PREPARATION = ROOT / "research/outputs/2026-09-10-claim-evidence-preparation"
SELECTIONS = PREPARATION / "selected-quotes.json"
RUBRIC = PREPARATION / "rubric.md"
spec = importlib.util.spec_from_file_location("claim_evidence_test_plan", ROOT / "probes/study_claim_evidence.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def read(path):
    return json.loads(path.read_text())


def rewrite(path, value):
    path.chmod(0o600)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def frozen(temp):
    root = Path(temp) / "packet"
    protocol = probe.freeze(root, PREDECESSOR, SELECTIONS, RUBRIC)
    return root, protocol


def account_block(message, wrapper):
    if message.count(wrapper) != 1 or message.count("\nEND COMPARISON ACCOUNT\n\n") != 1:
        raise AssertionError("account wrapper is absent, repeated or incomplete")
    return message.split(wrapper, 1)[1].split("\nEND COMPARISON ACCOUNT\n\n", 1)[0]


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@unittest.skipUnless(PREDECESSOR.exists() and SELECTIONS.exists() and RUBRIC.exists(), "retained study materials unavailable")
class ClaimEvidenceProtocolTests(unittest.TestCase):
    def test_eight_trials_four_within_account_pairs_and_reversed_second_block(self):
        trials = probe.trial_specs()
        self.assertEqual(len(trials), 8)
        self.assertEqual(len({t["id"] for t in trials}), 8)
        self.assertEqual([t["seed"] for t in trials], [3301] * 4 + [4409] * 4)
        self.assertEqual([t["arm"] for t in trials[:4]], ["retained_grouped", "retained_adjacent", "supported_grouped", "supported_adjacent"])
        self.assertEqual([t["arm"] for t in trials[4:]], [t["arm"] for t in reversed(trials[:4])])
        self.assertEqual(Counter(t["arm"] for t in trials), {arm: 2 for arm in ("retained_grouped", "retained_adjacent", "supported_grouped", "supported_adjacent")})
        self.assertTrue(all(t["id"] == f"claim-evidence-{t['seed']}-{t['arm']}" for t in trials))

    def test_full_account_is_the_exact_prior_rendered_account_in_all_eight_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            prior = read(PREDECESSOR / "protocol.json")
            self.assertEqual(protocol["accounts"], prior["accounts"])
            self.assertEqual(protocol["original_provenance"], prior["original_provenance"])
            for trial in protocol["trials"]:
                with self.subTest(trial=trial["id"]):
                    account = trial["arm"].split("_")[0]
                    before = read(PREDECESSOR / f"input-source-first-1103-{account}_direct.json")["messages"][1]["content"]
                    record = read(root / f"input-{trial['id']}.json")
                    now = record["messages"][1]["content"]
                    self.assertEqual(account_block(now, protocol["account_wrapper"]), account_block(before, prior["account_wrapper"]))
                    self.assertIsNone(record["dependency"])
                    self.assertNotIn("ISOLATED FIRST-READ RESPONSE —", now)
                    self.assertNotIn('"response_sha256":', account_block(now, protocol["account_wrapper"]))

    def test_all_original_source_bytes_and_source_snapshots_are_conserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            original = (PREDECESSOR / "block-evidence.txt").read_text()
            pieces = protocol["evidence_parts"]
            self.assertEqual(set(pieces), {"E1", "E2", "E3"})
            self.assertEqual(pieces["E2"] + pieces["E1"] + pieces["E3"], original)
            self.assertIn("navigation_question_names_exact_sibling_source_before_recycling_old_pages", pieces["E1"])
            self.assertIn("772 Git-tracked .rs files", pieces["E2"])
            self.assertIn('modes::handle_action(conv, base_action.as_str(), &original, &mut ctx)', pieces["E3"])
            self.assertNotIn("NUMBERED SOURCE —", pieces["E2"])
            self.assertEqual((root / "block-evidence.txt").read_bytes(), (PREDECESSOR / "block-evidence.txt").read_bytes())
            for name, receipt in protocol["source_map"].items():
                self.assertEqual((root / "source-snapshot" / name).read_bytes(), (PREDECESSOR / "source-snapshot" / name).read_bytes())
                self.assertEqual(probe.digest(root / "source-snapshot" / name), receipt["sha256"])
            for account in ("retained", "supported"):
                cards = probe.cards(protocol, account)
                for label, source in pieces.items():
                    self.assertEqual(cards[label].count(source), 1)
                    self.assertIn("matching numbers do not certify support", cards[label])

    def test_layouts_change_only_order_of_identical_complete_cards(self):
        with tempfile.TemporaryDirectory() as temp:
            _, protocol = frozen(temp)
            expected_orders = {"grouped": ["C1", "C2", "C3", "E1", "E2", "E3"],
                               "adjacent": ["C1", "E1", "C2", "E2", "C3", "E3"]}
            for account in ("retained", "supported"):
                cards = probe.cards(protocol, account)
                messages = {}
                for layout in ("grouped", "adjacent"):
                    trial = next(t for t in protocol["trials"] if t["arm"] == account + "_" + layout)
                    messages[layout] = probe.build_messages(protocol, trial)
                    suffix = messages[layout][1]["content"].split("\nEND COMPARISON ACCOUNT\n\n", 1)[1]
                    for payload in cards.values():
                        self.assertEqual(suffix.count(payload), 1)
                    observed = sorted(cards, key=lambda label: suffix.index(cards[label]))
                    self.assertEqual(observed, expected_orders[layout])
                    self.assertEqual(suffix, "\n".join(cards[label] for label in observed))
                    self.assertTrue(suffix.endswith(cards["E3"]))
                self.assertEqual(messages["grouped"][0], messages["adjacent"][0])
                self.assertEqual(messages["grouped"][1]["content"].split("\nEND COMPARISON ACCOUNT\n\n", 1)[0],
                                 messages["adjacent"][1]["content"].split("\nEND COMPARISON ACCOUNT\n\n", 1)[0])

    def test_selections_keep_exact_origins_and_unicode_character_offsets(self):
        prior = read(PREDECESSOR / "protocol.json")
        selections = read(SELECTIONS)
        probe.validate_selections(prior["accounts"], selections)
        for account, rows in selections.items():
            self.assertEqual(len(rows), 3)
            for row in rows:
                slot = row["slot"]
                text = prior["accounts"][account]["recent"][int(slot[7:-1])] if slot.startswith("recent[") else prior["accounts"][account][slot]
                self.assertEqual(text[row["start"]:row["end"]], row["text"])
        # The retained action-handling passage includes an em dash. Character
        # offsets are intentionally distinct from UTF-8 byte positions.
        selected = selections["retained"][2]
        self.assertIn("—", selected["text"])
        self.assertGreater(len(selected["text"].encode()), selected["end"] - selected["start"])
        with tempfile.TemporaryDirectory() as temp:
            _, protocol = frozen(temp)
            for account in ("retained", "supported"):
                cards = probe.cards(protocol, account)
                for index, row in enumerate(selections[account], 1):
                    self.assertIn(f"comparison account {row['slot']}; recalled text", cards[f"C{index}"])
                    self.assertIn("\n" + row["text"] + f"\nEND STATEMENT {index}\n", cards[f"C{index}"])

    def test_altered_selection_offsets_text_types_slots_or_inventory_are_rejected(self):
        accounts = read(PREDECESSOR / "protocol.json")["accounts"]
        base = read(SELECTIONS)
        for kind in ("start", "end", "text", "bool_index", "negative", "overrun", "slot", "extra_field", "short", "extra_account"):
            with self.subTest(kind=kind):
                value = copy.deepcopy(base)
                row = value["retained"][0]
                if kind == "start": row["start"] += 1
                elif kind == "end": row["end"] -= 1
                elif kind == "text": row["text"] += " Altered claim."
                elif kind == "bool_index": row["start"] = True
                elif kind == "negative": row["start"] = -1
                elif kind == "overrun": row["end"] = 1000000
                elif kind == "slot": row["slot"] = "recent[3]"
                elif kind == "extra_field": row["origin"] = "invented response"
                elif kind == "short": value["supported"].pop()
                else: value["other"] = []
                with self.assertRaises(ValueError): probe.validate_selections(accounts, value)

    def test_bad_selection_freeze_leaves_no_partial_trial_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            selections = read(SELECTIONS)
            selections["retained"][0]["start"] += 1
            altered = temp / "selections.json"
            altered.write_text(json.dumps(selections))
            target = temp / "invalid"
            with self.assertRaises(ValueError): probe.freeze(target, PREDECESSOR, altered, RUBRIC)
            self.assertFalse(target.exists())

    def test_inputs_are_fixed_immutable_idempotent_and_reject_existing_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            paths = sorted(root.glob("input-*.json"))
            self.assertEqual(len(paths), 8)
            before = snapshot(root)
            for trial in protocol["trials"]:
                path = root / f"input-{trial['id']}.json"
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
                self.assertEqual(probe.prepare_trial(root, protocol, trial), read(path))
            self.assertEqual(snapshot(root), before)
            first = protocol["trials"][0]
            path = root / f"input-{first['id']}.json"
            wrong = read(path); wrong["messages"][1]["content"] += "Changed prompt"
            rewrite(path, wrong)
            damaged = path.read_bytes()
            with self.assertRaises(ValueError): probe.prepare_trial(root, protocol, first)
            self.assertEqual(path.read_bytes(), damaged)
            with self.assertRaises(FileExistsError): probe.freeze(root, PREDECESSOR, SELECTIONS, RUBRIC)

    def test_declared_adapter_source_tamper_blocks_preparation_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            adapter = Path(temp) / "test-only-adapter.py"
            adapter.write_text("# test adapter, outside any source repository\n")
            fixture_protocol = copy.deepcopy(protocol)
            fixture_protocol["adapter_sources"][str(adapter)] = probe.digest(adapter)
            probe.verify_adapter(fixture_protocol)
            adapter.write_text("# changed adapter bytes\n")
            before = snapshot(root)
            with self.assertRaisesRegex(ValueError, "adapter source changed"):
                probe.prepare_trial(root, fixture_protocol, protocol["trials"][0])
            self.assertEqual(snapshot(root), before)

    def test_shared_question_system_and_voluntary_fields_have_no_treatment_only_cues(self):
        with tempfile.TemporaryDirectory() as temp:
            _, protocol = frozen(temp)
            prior = read(PREDECESSOR / "protocol.json")
            self.assertEqual(protocol["question"], prior["question"])
            self.assertEqual(protocol["system"], prior["system"])
            self.assertIn("You may retain, revise, qualify or leave open any statement", protocol["intro"])
            self.assertIn("No format, length, citation or note update is required", protocol["intro"])
            self.assertIn("Omission is valid", protocol["system"])
            self.assertIn("not proof of agreement or a verdict", protocol["intro"])
            for trial in protocol["trials"]:
                messages = probe.build_messages(protocol, trial)
                self.assertEqual(messages[0], {"role": "system", "content": prior["system"]})
                self.assertTrue(messages[1]["content"].startswith(protocol["intro"] + "\nQUESTION — " + prior["question"]))
                self.assertNotIn("source-first-1103-first_read", messages[1]["content"])
                self.assertNotIn("source-first-2207-first_read", messages[1]["content"])

    def test_unplanned_arms_seeds_and_trials_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            for change in ({"arm": "retained_other"}, {"seed": 9}, {"id": "unplanned"}):
                with self.subTest(change=change):
                    trial = {**protocol["trials"][0], **change}
                    before = snapshot(root)
                    with self.assertRaises(ValueError): probe.build_messages(protocol, trial)
                    with self.assertRaises(ValueError): probe.prepare_trial(root, protocol, trial)
                    self.assertEqual(snapshot(root), before)
            for slot in ("recent[10]", "recent[-1]", "question", "unknown"):
                with self.assertRaises(ValueError): probe.slot_text(protocol["accounts"]["retained"], slot)


review_spec = importlib.util.spec_from_file_location("claim_evidence_test_review", ROOT / "probes/study_claim_evidence_review.py")
reviewer = importlib.util.module_from_spec(review_spec)
review_spec.loader.exec_module(reviewer)


def write_artifact(path, value):
    if path.exists():
        path.chmod(0o600)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def generated(root, protocol, trial, *, finish="stop", text="The shown branch sets pending fields.", native=True):
    """Invented model receipts for tests; never calls a generator or tokenizer."""
    messages = read(root / f"input-{trial['id']}.json")["messages"]
    system, user = [m["content"].strip() for m in messages]
    rendered = "<bos><|turn>system\n" + system + "<turn|>\n<|turn>user\n" + user + "<turn|>\n<|turn>model\n<|channel>thought\n<channel|>"
    rendered_hash = hashlib.sha256(rendered.encode()).hexdigest()
    write_artifact(root / f"rendered-{trial['id']}.json", {"arm": trial["arm"], "id": trial["id"],
                   "rendered_text": rendered, "rendered_sha256": rendered_hash, "token_ids": [2, 3, 4], "token_count": 3})
    terminal = 106 if native else 42
    tokens = [43, terminal] if finish == "stop" else [43] * (protocol["settings"]["max_tokens"] if finish == "length" else 1)
    termination = ({"kind": "model_eos" if native else "channel_boundary", "model_eos_reached": native,
                    "stop_token_id": terminal, "stop_special": "<turn|>" if native else "<channel|>"}
                   if finish == "stop" else {"kind": "output_allowance", "model_eos_reached": False, "stop_token_id": None, "stop_special": None})
    result = {"text": text, "raw_text": text, "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "tokens": tokens, "completion_tokens": len(tokens), "filtered_tokens": 0, "terminal_tokens": int(finish == "stop"),
              "finish": finish, "termination": None if finish == "error" else termination,
              "prompt_tokens": 3, "prompt_sha256": rendered_hash, "controls": {"temperature": protocol["settings"]["temperature"], "top_p": protocol["settings"]["top_p"]},
              "initial_cache_positions": [0, 0], "final_cache_positions": [3 + len(tokens)] * 2, "seconds": .2, "admission_seconds": .1}
    row = {"spec": trial, "outcome": "generation_error" if finish == "error" else "returned",
           "error": "invented fixture error" if finish == "error" else None, "result": result}
    write_artifact(root / f"{trial['id']}.json", row)
    return row


@unittest.skipUnless(PREDECESSOR.exists() and SELECTIONS.exists() and RUBRIC.exists(), "retained study materials unavailable")
class ClaimEvidenceReviewTests(unittest.TestCase):
    def test_missing_prerun_is_read_only_with_four_uncompleted_pairs_and_real_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            for receipt in protocol["source_map"].values():
                self.assertEqual(str(Path(receipt["copy"]).resolve()), receipt["copy"])
                self.assertEqual(Path(receipt["copy"]).parent, root.resolve() / "source-snapshot")
            before = snapshot(root)
            report = reviewer.review(root)
            self.assertEqual(snapshot(root), before)
            self.assertEqual(report["planned"], 8)
            self.assertEqual(report["outcomes"], {"missing": 8})
            self.assertEqual(report["eligible"], 0)
            self.assertEqual(len(report["pairs"]), 4)
            self.assertEqual(len(report["seed_blocks"]), 2)
            self.assertEqual(report["complete_eligible_pairs"], 0)
            self.assertTrue(all(set(c["assessment"].values()) == {"unassessed"} for c in report["cells"]))

    def test_complete_pair_denominator_is_distinct_from_all_four_condition_seed_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            for trial in protocol["trials"][:4]: generated(root, protocol, trial)
            report = reviewer.review(root)
            self.assertEqual(report["eligible"], 4)
            self.assertEqual(report["complete_eligible_pairs"], 2)
            self.assertEqual([b["eligible"] for b in report["seed_blocks"]], [4, 0])
            self.assertEqual(report["outcomes"], {"returned": 4, "missing": 4})
            # A nonempty allowance result is a receipt, not a completed pair.
            generated(root, protocol, protocol["trials"][0], finish="length")
            report = reviewer.review(root)
            self.assertEqual(report["nonempty"], 4)
            self.assertEqual(report["eligible"], 3)
            self.assertEqual(report["complete_eligible_pairs"], 1)

    def test_empty_error_length_and_channel_outputs_remain_available_but_ineligible(self):
        for kind in ("empty", "error", "length", "channel"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = frozen(temp)
                generated(root, protocol, protocol["trials"][0], finish=kind if kind in ("length", "error") else "stop",
                          text="" if kind == "empty" else "Visible text.", native=kind != "channel")
                generated(root, protocol, protocol["trials"][1])
                report = reviewer.review(root)
                self.assertEqual(report["eligible"], 1)
                self.assertEqual(report["nonempty"], 1 if kind == "empty" else 2)
                self.assertEqual(report["complete_eligible_pairs"], 0)
                self.assertEqual(report["cells"][0]["outcome"], "generation_error" if kind == "error" else "returned")
                self.assertFalse(report["cells"][0]["eligible"])

    def test_admission_and_resource_outcomes_are_not_substantive_responses(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            for trial, outcome in zip(protocol["trials"][:2], ("admission_unavailable", "cell_wall_resource_limit")):
                write_artifact(root / f"{trial['id']}.json", {"spec": trial, "outcome": outcome, "result": None})
            report = reviewer.review(root)
            self.assertEqual(report["outcomes"], {"admission_unavailable": 1, "cell_wall_resource_limit": 1, "missing": 6})
            self.assertEqual(report["nonempty"], 0)
            self.assertEqual(report["complete_eligible_pairs"], 0)
            write_artifact(root / f"{protocol['trials'][0]['id']}.json", {})
            with self.assertRaises(ValueError): reviewer.review(root)

    def test_result_count_cache_native_eos_hash_and_render_forgery_are_rejected(self):
        for kind in ("count", "cache", "eos", "terminal", "response_hash", "render", "spec", "hidden_error", "filtered"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = frozen(temp)
                trial = protocol["trials"][0]
                row = generated(root, protocol, trial)
                result = row["result"]
                if kind == "count": result["completion_tokens"] += 1
                elif kind == "cache": result["initial_cache_positions"] = [1, 0]
                elif kind == "eos": result["tokens"][-1] = result["termination"]["stop_token_id"] = 999999
                elif kind == "terminal": result["termination"]["model_eos_reached"] = False
                elif kind == "response_hash": result["response_sha256"] = "false"
                elif kind == "spec": row["spec"] = {**trial, "seed": 1}
                elif kind == "hidden_error": row["error"] = "unreported error"
                elif kind == "filtered": result["filtered_tokens"] = 2
                else:
                    path = root / f"rendered-{trial['id']}.json"; rendered = read(path)
                    rendered["rendered_text"] += "EXTRA MEMORY"
                    rendered["rendered_sha256"] = hashlib.sha256(rendered["rendered_text"].encode()).hexdigest()
                    write_artifact(path, rendered); result["prompt_sha256"] = rendered["rendered_sha256"]
                write_artifact(root / f"{trial['id']}.json", row)
                with self.assertRaises(ValueError): reviewer.review(root)

    def test_null_annotations_stay_unassessed_and_all_quote_origins_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = frozen(temp)
            trial = protocol["trials"][0]
            row = generated(root, protocol, trial)
            write_artifact(root / "annotations.json", None)
            self.assertEqual(reviewer.review(root)["annotated"], 0)
            annotation = {"id": trial["id"], "response_sha256": row["result"]["response_sha256"],
                          "proxy_status": None, "fixture_role": "unassessed", "shown_call_path": "partially_supported", "saved_note": "omitted",
                          "claims": [{"quote": "sets pending fields", "classification": "supported"}], "choices": [],
                          "scope_ambiguity": [{"quote": "The shown branch sets pending fields.", "alternative": "unassessed"}],
                          "origin_claims": [{"quote": "sets pending fields", "source_quote": "conv.wants_introspect = true;", "assessment": "supported"}]}
            write_artifact(root / "annotations.json", [annotation])
            report = reviewer.review(root)
            self.assertEqual(report["annotated"], 1)
            self.assertEqual(report["cells"][0]["assessment"]["proxy_status"], "unassessed")
            self.assertNotIn("score", report)
            for kind in ("quote", "context", "source", "hash"):
                bad = copy.deepcopy(annotation)
                if kind == "quote": bad["claims"][0]["quote"] = "invented response quotation"
                elif kind == "context": bad["scope_ambiguity"][0]["quote"] = "invented surrounding context"
                elif kind == "source": bad["origin_claims"][0]["source_quote"] = "invented source excerpt"
                else: bad["response_sha256"] = "false"
                write_artifact(root / "annotations.json", [bad])
                with self.subTest(kind=kind), self.assertRaises(ValueError): reviewer.review(root)

    def test_frozen_input_selection_source_and_false_completion_are_rejected(self):
        for kind in ("input", "selection", "source", "completion", "manifest"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = frozen(temp)
                if kind == "input":
                    path = root / f"input-{protocol['trials'][0]['id']}.json"; value = read(path)
                    value["messages"][1]["content"] += "treatment-only explanation"; rewrite(path, value)
                elif kind == "selection":
                    saved = read(root / "protocol.json"); saved["selections"]["retained"][0]["start"] += 1
                    rewrite(root / "protocol.json", saved)
                elif kind == "source":
                    path = root / "source-snapshot/context.rs"; path.chmod(0o600); path.write_text("changed source")
                elif kind == "completion":
                    write_artifact(root / "completed.json", {"cells": 8, "live_writes": False, "sources_unchanged": True, "model_assets_unchanged": True})
                else: write_artifact(root / "manifest.json", {"protocol_sha256": "false"})
                with self.assertRaises(ValueError): reviewer.review(root)


if __name__ == "__main__":
    unittest.main()
