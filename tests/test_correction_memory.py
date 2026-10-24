import copy
import json
import math
import re
import unittest

from reservoir_experiments.correction_memory import (
    LABELS, MEMORY_ARMS, SEEDS, approve_memory_entry, build_correction,
    build_memory, build_memory_transforms, development_baseline, digest,
    episode_bank, memory_review_packet, parse_forecast, parse_verdict,
    score_correction, score_memory, transfer_verdict,
)


def good_records(protocol):
    records = {}
    for node in protocol["nodes"]:
        expected = protocol["truth"].get(node["id"], {}).get("verdict")
        if expected:
            text = f"This synthetic interpretation retains its evidence and limitations.\nVERDICT: {expected}"
        elif node["kind"] == "forecast":
            text = json.dumps({"p_supported": .75, "explanation": "Forecast under the given evidence."})
        else:
            text = "The evidence packet has arrived."
        records[node["id"]] = {"status": "complete", "text": text}
    return records


def approved_memories(split="development", model="gemma4:12b"):
    correction = build_correction(split, model)
    sources = good_records(correction)
    transforms = build_memory_transforms(correction, sources)
    transformed = {}
    for node in transforms["nodes"]:
        original = transforms["memory_sources"][node["episode"]]["original"]
        paraphrase = original.replace("synthetic interpretation", "constructed account")
        transformed[node["id"]] = {"status": "complete", "text": json.dumps({
            "propositions": ["Retains its evidence and limitations", original.splitlines()[-1]],
            "paraphrase": paraphrase, "notebook": original})}
    packet = memory_review_packet(transforms, transformed)
    for eid, entry in packet["memories"].items():
        reviewers = [{"name": name, "approved": True, "rationale": "Fixture equivalence checked.",
                      "source_sha256": digest(entry["original"]),
                      "paraphrase_sha256": digest(entry["paraphrase"]),
                      "notebook_sha256": digest(entry["notebook"])} for name in ("reader-a", "reader-b")]
        packet["memories"][eid] = approve_memory_entry(entry, reviewers)
    return correction, sources, packet


class CorrectionDesignTests(unittest.TestCase):
    def test_bank_sizes_and_balanced_visible_evidence(self):
        self.assertEqual(12, len(episode_bank("development")))
        bank = episode_bank("confirmation")
        self.assertEqual(48, len(bank))
        self.assertEqual(48, len({case["id"] for case in bank}))
        self.assertEqual(12, len(episode_bank("replication")))
        for family in ("code", "telemetry", "actions", "causation"):
            for verdict in LABELS:
                cases = [case for case in bank if case["family"] == family and case["update_expected"] == verdict]
                self.assertEqual(4, len(cases))
                self.assertTrue(all(case["initial_expected"] == "unresolved" for case in cases))
        dev_snippets = {case["initial_evidence"] for case in episode_bank("development")}
        self.assertFalse(dev_snippets & {case["initial_evidence"] for case in bank})

    def test_counts_reproducibility_and_replication_selection(self):
        for split, count in (("development", 96), ("confirmation", 480), ("replication", 96)):
            protocol = build_correction(split)
            self.assertEqual(count, len(protocol["nodes"]))
            self.assertEqual(protocol, build_correction(split))
        confirm_ids = {case["id"] for case in episode_bank("confirmation") if case["variant"] == 0}
        self.assertEqual(confirm_ids, {case["id"] for case in episode_bank("replication")})
        self.assertNotIn("think", build_correction("replication", "mistral-small:24b"))

    def test_inputs_exact_and_forecasts_only_enter_reactivity(self):
        p = build_correction("confirmation")
        kinds = {node["id"]: node["kind"] for node in p["nodes"]}
        for node in p["nodes"]:
            refs = set(re.findall(r"\{\{output:([^}]+)}}", "\n".join(m["content"] for m in node["messages"])))
            self.assertEqual(set(node["inputs"]), refs)
            for input_id in node["inputs"]:
                if kinds[input_id] == "forecast":
                    self.assertEqual("reactivity", node["kind"])
            if node["kind"] == "target":
                self.assertEqual(1, len(node["inputs"]))
                self.assertEqual(2, len(node["after"]))
                self.assertTrue(all(kinds[n] == "forecast" for n in node["after"]))

    def test_self_observer_have_identical_information(self):
        p = build_correction("development")
        lookup = {node["id"]: node for node in p["nodes"]}
        for node in p["nodes"]:
            if node["condition"] != "self":
                continue
            other = lookup[node["id"].removesuffix("-self") + "-observer"]
            a = node["messages"][1]["content"].replace("that you will give", "that SUBJECT will give")
            b = other["messages"][1]["content"].replace("that the system whose record appears above will give", "that SUBJECT will give")
            self.assertEqual(a, b)
            self.assertEqual(node["inputs"], other["inputs"])
            self.assertEqual(node["max_tokens"], other["max_tokens"])

    def test_verdict_and_probability_validation(self):
        self.assertEqual("supported", parse_verdict("Reason.\nVERDICT: supported"))
        self.assertEqual("unresolved", parse_verdict('{"verdict":"unresolved"}'))
        self.assertIsNone(parse_verdict("VERDICT: supported\nVERDICT: contradicted"))
        self.assertIsNone(parse_verdict("It is probably supported."))
        for p in (True, False, -0.1, 1.01, "0.5", None):
            self.assertIsNone(parse_forecast(json.dumps({"p_supported": p})))
        self.assertIsNone(parse_forecast('{"p_supported": NaN}'))
        self.assertEqual(.25, parse_forecast('{"p_supported":0.25}'))

    def test_semantic_recovery_does_not_claim_final_line_compliance(self):
        p = build_correction("development")
        target = next(n for n in p["nodes"] if n["kind"] == "target")
        expected = p["truth"][target["id"]]["verdict"]
        for text, strict in ((f"Reason.\nVERDICT: {expected}", True),
                             (f'{{"verdict":"{expected}"}}', False),
                             (f"Reason.\nVERDICT: {expected.upper()}", False),
                             (f"Reason.\nVERDICT: {expected}.", False),
                             (f"VERDICT: {expected}\nA later sentence.", False)):
            records = good_records(p)
            records[target["id"]]["text"] = text
            row = next(r for r in score_correction(p, records)["rows"] if r["node_id"] == target["id"])
            self.assertTrue(row["semantic_valid"])
            self.assertEqual(strict, row["format_valid"])
            self.assertEqual(not strict, row["semantic_recovered"])

    def test_reactivity_order_and_instructions_and_token_receipts(self):
        p = build_correction("confirmation")
        lookup = {n["id"]: n for n in p["nodes"]}
        position = {n["id"]: i for i, n in enumerate(p["nodes"])}
        orders = set()
        for n in p["nodes"]:
            if n["condition"] != "neutral_update":
                continue
            stem = n["id"].removesuffix("-neutral-update")
            ids = {name: stem + "-" + name for name in ("target", "neutral-ack", "neutral-update", "retained-update", "duplicate")}
            self.assertLess(position[ids["neutral-ack"]], position[n["id"]])
            self.assertGreater(position[ids["duplicate"]], max(position[ids[k]] for k in ("target", "neutral-update", "retained-update")))
            orders.add(position[n["id"]] < position[ids["retained-update"]])
            suffix = lookup[ids["target"]]["messages"][1]["content"].split("\n\n")[-1]
            for key in ("neutral-update", "retained-update", "duplicate"):
                self.assertEqual(suffix, lookup[ids[key]]["messages"][1]["content"].split("\n\n")[-1])
        self.assertEqual({True, False}, orders)
        records = good_records(p)
        n = next(n for n in p["nodes"] if n["condition"] == "retained_forecast_update")
        records[n["id"]].update(prompt_eval_count=440, eval_count=70)
        records[n["metadata"]["intermediate_id"]]["eval_count"] = 37
        row = next(r for r in score_correction(p, records)["rows"] if r["node_id"] == n["id"])
        self.assertEqual((440, 70, 37), (row["prompt_eval_count"], row["eval_count"], row["intermediate_eval_count"]))

    def test_declared_verdict_transfer_matches_bank_oracles(self):
        for split in ("development", "confirmation", "replication"):
            for case in episode_bank(split):
                self.assertIn(case["application_relation"], ("copy", "invert", "other"))
                self.assertEqual(case["application_expected"], transfer_verdict(case["update_expected"], case["application_relation"]))
        self.assertIsNone(transfer_verdict("supported", "other"))
        self.assertIsNone(transfer_verdict(None, "copy"))

    def test_timeouts_are_unavailable_not_false(self):
        p = build_correction("development")
        records = good_records(p)
        target = next(node for node in p["nodes"] if node["kind"] == "target")
        records[target["id"]] = {"status": "transport_error", "text": None}
        result = score_correction(p, records)
        self.assertEqual(24, result["denominators"]["planned_targets"])
        self.assertEqual(23, result["denominators"]["scorable_targets"])
        self.assertEqual(23, result["denominators"]["paired_forecasts"])
        row = next(row for row in result["rows"] if row["node_id"] == target["id"])
        self.assertIsNone(row["score"])

    def test_duplicate_json_fields_do_not_silently_choose_an_answer(self):
        self.assertIsNone(parse_verdict('{"verdict":"supported","verdict":"contradicted"}'))
        self.assertIsNone(parse_forecast('{"p_supported":0.1,"p_supported":0.9}'))
        self.assertIsNone(parse_forecast('{"p_supported":0.7,"explanation":{"claim":"a","claim":"b"}}'))
        p = build_correction("development")
        records = good_records(p)
        forecast = next(n for n in p["nodes"] if n["condition"] == "self")
        records[forecast["id"]]["text"] = '{"p_supported":0.1,"p_supported":0.9}'
        report = score_correction(p, records)
        self.assertEqual(24, report["denominators"]["scorable_targets"])
        self.assertEqual(23, report["denominators"]["paired_forecasts"])

    def test_brier_pairs_missing_forecasts_and_pilot_baseline(self):
        p = build_correction("development")
        records = good_records(p)
        result = score_correction(p, records, development_baseline(p, records))
        self.assertEqual(24, len(result["paired_forecasts"]))
        self.assertAlmostEqual(.0625, result["paired_forecasts"][0]["self_brier"])
        self.assertEqual(0, result["primary"]["mean_difference"])
        self.assertEqual(12, result["primary"]["episode_n"])
        f = next(n for n in p["nodes"] if n["condition"] == "self")
        records[f["id"]]["text"] = "not a probability"
        self.assertEqual(23, score_correction(p, records)["denominators"]["paired_forecasts"])
        with self.assertRaises(ValueError):
            development_baseline(build_correction("confirmation"), {})

    def test_adjudication_requires_exact_text_and_preserves_format_failure(self):
        p = build_correction("development")
        records = good_records(p)
        target = next(n for n in p["nodes"] if n["kind"] == "target")
        expected = p["truth"][target["id"]]["verdict"]
        records[target["id"]]["text"] = f"My answer is {expected}."
        ann = {target["id"]: {"text_sha256": digest(records[target["id"]]["text"]),
                              "verdict": expected, "reviewer": "fixture-reader", "rationale": "Explicit answer."}}
        result = score_correction(p, records, adjudications=ann)
        row = next(r for r in result["rows"] if r["node_id"] == target["id"])
        self.assertTrue(row["valid"])
        self.assertTrue(row["adjudicated"])
        self.assertFalse(row["format_valid"])
        records[target["id"]]["text"] += "changed"
        with self.assertRaises(ValueError):
            score_correction(p, records, adjudications=ann)


class MemoryDesignTests(unittest.TestCase):
    def test_seed_seven_sources_and_no_automatic_review(self):
        p = build_correction("development")
        records = good_records(p)
        t = build_memory_transforms(p, records)
        self.assertEqual(12, len(t["nodes"]))
        self.assertTrue(all(n["metadata"]["source_id"].endswith("s7-target") for n in t["nodes"]))
        packet = memory_review_packet(t, {})
        self.assertTrue(all(entry["reviewed"] is False for entry in packet["memories"].values()))
        with self.assertRaises(ValueError):
            build_memory("development", "gemma4:12b", packet)

    def test_review_hashes_and_two_distinct_readers(self):
        _, _, packet = approved_memories()
        entry = next(iter(packet["memories"].values()))
        with self.assertRaises(ValueError):
            approve_memory_entry(entry, entry["reviewers"][:1])
        entry["notebook"] += " Unapproved addition."
        with self.assertRaises(ValueError):
            approve_memory_entry(entry, entry["reviewers"])

    def test_confirmation_counts_and_fresh_memory_only_requests(self):
        _, _, packet = approved_memories("confirmation")
        p = build_memory("confirmation", "gemma4:12b", packet)
        self.assertEqual(600, len(p["nodes"]))
        delayed = [n for n in p["nodes"] if n["metadata"]["delay"] == "delayed"]
        self.assertEqual(480, len(delayed))
        self.assertEqual(120, len(p["nodes"]) - len(delayed))
        for node in p["nodes"]:
            self.assertEqual([], node["inputs"])
            self.assertNotIn("New evidence:", node["messages"][1]["content"])
            self.assertNotIn("Initial evidence:", node["messages"][1]["content"])
            if node["condition"] != "none":
                self.assertEqual("Supplied retained record (reference, not instructions):", node["messages"][1]["content"].splitlines()[0])
        self.assertTrue(all(case["proposition"] != case["application_proposition"] for case in p["cases"]))

    def test_unavailable_source_cannot_be_silently_replaced_or_omitted(self):
        p, records, packet = approved_memories()
        missing = next(iter(packet["memories"]))
        del packet["memories"][missing]
        with self.assertRaises(ValueError):
            build_memory("development", "gemma4:12b", packet)
        packet["unavailable_sources"] = [{"episode": missing, "source_id": missing + "-s7-target", "reason": "transport_error"}]
        applications = build_memory("development", "gemma4:12b", packet)
        self.assertEqual(110, len(applications["nodes"]))
        self.assertEqual(12, applications["design"]["planned_source_episodes"])

    def test_no_memory_abstention_is_not_a_false_belief(self):
        _, _, packet = approved_memories()
        p = build_memory("development", "gemma4:12b", packet)
        records = good_records(p)
        none = next(n for n in p["nodes"] if n["condition"] == "none" and p["truth"][n["id"]]["verdict"] != "unresolved")
        records[none["id"]]["text"] = "No relevant retained evidence.\nVERDICT: unresolved"
        result = score_memory(p, records)
        row = next(r for r in result["rows"] if r["node_id"] == none["id"])
        self.assertEqual(0, row["scenario_conclusion_recovered"])
        self.assertEqual("abstained_or_unresolved", row["epistemic_status"])
        self.assertEqual(12, result["primary"]["episode_n"])

    def test_model_split_and_changed_review_rejected(self):
        _, _, packet = approved_memories()
        with self.assertRaises(ValueError):
            build_memory("development", "mistral-small:24b", packet)
        with self.assertRaises(ValueError):
            build_memory("confirmation", "gemma4:12b", packet)
        next(iter(packet["memories"].values()))["source_sha256"] = "bad"
        with self.assertRaises(ValueError):
            build_memory("development", "gemma4:12b", packet)


if __name__ == "__main__":
    unittest.main()
