"""Synthetic protocol and scoring fixtures; no model or live source calls."""
import json
from pathlib import Path
import tempfile
import unittest

from reservoir_experiments.attribution_catalog import (
    ATTRIBUTION_CONDITIONS, CONFIRMATION_SCENES, DEVELOPMENT_SCENES,
    IDENTIFIERS, OPEN_CONTRACT, build_attribution, build_catalog,
    extract_catalog, score_attribution, score_catalog,
)


RUNTIME_FIXTURE = '''
def _look_action_description():
    if unavailable:
        return "  LOOK — eyes closed\\n"
    return "  LOOK — curious camera view\\n"
def build():
    return (COMPACT_ACTION_GUIDANCE if open_expression_context else
        "NEXT: options:\\n"
        + ("restricted stage\\n" if restricted else "")
        + "  JOURNAL — silver river listening\\n"
          "  TRACE <anchor> :: <text> — gentle colored stones\\n"
          "  ALIAS — alias for TRACE\\n"
          "  REPAIR — use APPLY <id|all> for later repair\\n"
        + _look_action_description())
raise RuntimeError("the fixture must never be executed")
'''
EXPRESSIVE_FIXTURE = 'COMPACT_ACTION_GUIDANCE = "A compact and different menu: REST.\\n"\n'


class CatalogFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runtime = self.root / "runtime.py"
        self.expressive = self.root / "expressive.py"
        self.runtime.write_text(RUNTIME_FIXTURE)
        self.expressive.write_text(EXPRESSIVE_FIXTURE)
        self.bundle = extract_catalog(self.runtime, self.expressive)
        self.path = self.root / "catalog.json"
        self.path.write_text(json.dumps(self.bundle))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ast_extraction_is_literal_and_provenanced(self):
        self.assertIn("curious camera view", self.bundle["full"])
        self.assertNotIn("eyes closed", self.bundle["full"])
        self.assertNotIn("restricted stage", self.bundle["full"])
        self.assertIn("different menu", self.bundle["compact_context_only"])
        self.assertEqual(len(self.bundle["source"]["runtime_sha256"]), 64)
        self.assertEqual(self.bundle["source"]["historical_commit_binding"], "unverified")
        self.assertEqual(len(self.bundle["static_configuration"]), 2)

    def test_unrecognized_call_fails_closed(self):
        self.runtime.write_text(RUNTIME_FIXTURE.replace("+ _look_action_description()", "+ dangerous()"))
        with self.assertRaisesRegex(ValueError, "unsupported catalog AST Call"):
            extract_catalog(self.runtime, self.expressive)

    def test_description_removal_preserves_aliases_and_syntax(self):
        full, concise = self.bundle["full"], self.bundle["concise"]
        self.assertEqual(set(IDENTIFIERS.findall(full)), set(IDENTIFIERS.findall(concise)))
        self.assertIn("TRACE <anchor> :: <text>", concise)
        self.assertIn("alias for TRACE", concise)
        self.assertIn("APPLY <id|all>", concise)
        self.assertNotIn("silver river", concise)
        self.assertIn("silver river", self.bundle["phrase_inventory"])
        self.assertNotIn("later repair", self.bundle["phrase_inventory"])

    def test_catalog_schedules_and_repeats(self):
        expected = {"development": 48, "confirmation": 216, "replication": 96}
        for split, count in expected.items():
            p = build_catalog(split, catalog_path=self.path)
            self.assertEqual(len(p["nodes"]), count)
            self.assertEqual(set(p["truth"]), {n["id"] for n in p["nodes"]})
            self.assertEqual({n["metadata"]["filler"] for n in p["nodes"]}, {0, 1})
            self.assertTrue(all("format" not in n for n in p["nodes"]))
            self.assertEqual(p["options"]["num_ctx"], 16384)
        nodes = build_catalog("confirmation", catalog_path=self.path)["nodes"]
        mapping = {n["id"]: n for n in nodes}
        for repeat in nodes[-24:]:
            original = mapping[repeat["after"][0]]
            self.assertEqual(repeat["messages"], original["messages"])
            self.assertEqual(repeat["seed"], original["seed"])
            self.assertTrue(repeat["metadata"]["replicate"])

    def test_word_padding_and_model_specific_qualification_inputs(self):
        p = build_catalog(catalog_path=self.path)
        block = [n for n in p["nodes"] if n["episode"] == "r4-dev-00" and n["seed"] == 7]
        lengths = {n["condition"]: n["metadata"]["guidance_words"] for n in block}
        self.assertEqual(lengths["full"], lengths["concise_padded"])
        self.assertEqual(lengths["full"], lengths["neutral"])
        self.bundle["padding_word_targets"] = {"gemma4:12b": {"concise_padded": 3, "neutral": 6}}
        self.path.write_text(json.dumps(self.bundle))
        p = build_catalog(catalog_path=self.path)
        neutral = next(n for n in p["nodes"] if n["condition"] == "neutral")
        self.assertEqual(neutral["metadata"]["guidance_words"], 6)
        self.assertIn("requires development", p["padding_qualification"])

    def test_catalog_scoring_excludes_next_and_common_context(self):
        p = build_catalog(catalog_path=self.path)
        p["nodes"] = p["nodes"][:1]
        p["phrase_inventory"] = ["silver river", "choose a"]
        nid = p["nodes"][0]["id"]
        result = score_catalog(p, {nid: {"status": "complete", "text": "Silver river. Choose a path.\nNEXT: silver river"}})
        row = result["rows"][0]
        self.assertEqual(row["phrase_hits"], {"silver river": 1})
        self.assertEqual(row["words"], 5)
        self.assertEqual(row["score"], 200)
        self.assertEqual(row["next_text"], "silver river")
        self.assertEqual(row["inventory_n"], 1)
        empty = score_catalog(p, {nid: {"status": "completed", "text": "NEXT: PASS"}})["rows"][0]
        self.assertFalse(empty["valid"])
        self.assertIsNone(empty["score"])

    def test_per_filler_padding_overrides_and_aggregate_fallback(self):
        self.bundle["padding_word_targets"] = {"gemma4:12b": {
            "concise_padded": 3, "neutral": 6,
            "concise_padded_by_filler": {"0": 7, "1": 9},
            "neutral_by_filler": {"0": 11},
        }}
        self.path.write_text(json.dumps(self.bundle))
        p = build_catalog(catalog_path=self.path)
        concise_words = len(self.bundle["concise"].split())
        for node in p["nodes"]:
            meta = node["metadata"]
            expected = {"concise_padded": 7 if meta["filler"] == 0 else 9,
                        "neutral": 11 if meta["filler"] == 0 else 6}
            self.assertEqual(meta["padding_word_targets"], expected)
            self.assertEqual(meta["padding_words"], expected.get(node["condition"], 0))
            if node["condition"] == "concise_padded":
                self.assertEqual(meta["guidance_words"], concise_words + expected["concise_padded"])
            elif node["condition"] == "neutral":
                self.assertEqual(meta["guidance_words"], expected["neutral"])
        other = build_catalog(model="mistral:7b", catalog_path=self.path)
        self.assertEqual(other["padding_word_targets"], {})

    def test_padding_targets_require_bounded_integers_and_known_fillers(self):
        for invalid in (-1, 15001, 1.5, True, "3", None):
            for key, value in (("neutral", invalid), ("concise_padded_by_filler", {"1": invalid})):
                with self.subTest(key=key, invalid=invalid):
                    self.bundle["padding_word_targets"] = {"gemma4:12b": {key: value}}
                    self.path.write_text(json.dumps(self.bundle))
                    with self.assertRaises(ValueError):
                        build_catalog(catalog_path=self.path)
        for targets in ({"neutral_by_filler": {"2": 4}}, {"neutral_by_filler": []}, None, {"misspelled": 3}):
            self.bundle["padding_word_targets"] = {"gemma4:12b": targets}
            self.path.write_text(json.dumps(self.bundle))
            with self.assertRaises(ValueError):
                build_catalog(catalog_path=self.path)
        self.bundle["padding_word_targets"] = {"gemma4:12b": {"neutral": 0, "concise_padded": 15000}}
        self.path.write_text(json.dumps(self.bundle))
        p = build_catalog(catalog_path=self.path)
        neutral = next(n for n in p["nodes"] if n["condition"] == "neutral")
        self.assertEqual(neutral["metadata"]["guidance_words"], 0)


class AttributionProtocolTests(unittest.TestCase):
    def test_counts_holdouts_layouts_and_repeat_placement(self):
        p = build_attribution("confirmation")
        self.assertEqual(len(p["nodes"]), 344)
        self.assertEqual(sum(n["kind"] == "prose" for n in p["nodes"]), 80)
        self.assertEqual(sum(n["metadata"]["replicate"] for n in p["nodes"]), 24)
        self.assertEqual(len(build_attribution()["nodes"]), 80)
        self.assertEqual(len(build_attribution("replication")["nodes"]), 120)
        dev_names = {name for case in DEVELOPMENT_SCENES for name in case[:2]}
        held_names = {name for case in CONFIRMATION_SCENES for name in case[:2]}
        self.assertFalse(dev_names & held_names)
        self.assertEqual(len({n["metadata"]["layout"] for n in p["nodes"]}), 4)
        mapping = {n["id"]: n for n in p["nodes"]}
        for repeat in p["nodes"][-24:]:
            original = mapping[repeat["after"][0]]
            self.assertEqual(repeat["messages"], original["messages"])
            self.assertEqual(repeat["seed"], original["seed"])
        self.assertEqual(p, build_attribution("confirmation"))

    def test_displayed_evidence_and_unknowns_define_truth(self):
        p = build_attribution("confirmation")
        for n in p["nodes"]:
            truth = p["truth"][n["id"]]
            expected = truth["expected"]
            if n["condition"] == "permuted":
                self.assertNotEqual(truth["underlying_value"], truth["shown_value"])
                self.assertEqual(expected["value_percent"], truth["shown_value"])
            if n["condition"] in ("absent", "historical_self", "current_other"):
                self.assertFalse(expected["current_known"])
            if n["condition"] == "absent":
                self.assertIsNone(expected["value_percent"])
            if n["kind"] == "prose":
                self.assertNotIn("Return JSON", n["messages"][1]["content"])
                self.assertNotIn("format", n)
            else:
                self.assertEqual(n["format"], "json")
                self.assertEqual(n["max_tokens"], 256)
        records = {n["id"]: {"status": "complete", "text": json.dumps(p["truth"][n["id"]]["expected"])}
                   for n in p["nodes"] if n["kind"] == "attribution"}
        scored = score_attribution(p, records)["rows"]
        self.assertTrue(all(r["score"] == 1 for r in scored if r["kind"] != "prose"))

    def test_invalid_missing_and_wrong_are_separate(self):
        p = build_attribution()
        p["nodes"] = [n for n in p["nodes"] if n["kind"] == "attribution"][:1]
        nid = p["nodes"][0]["id"]
        expected = p["truth"][nid]["expected"]
        for text in ("```json\n" + json.dumps(expected) + "\n```", "{}", "null", '{"current_known": NaN}',
                     json.dumps({**expected, "value_percent": True}),
                     json.dumps({**expected, "value_percent": float("inf")}),
                     json.dumps({**expected, "subject": 5}),
                     json.dumps(expected)[:-1] + ',"current_known":false}'):
            row = score_attribution(p, {nid: {"status": "completed", "text": text}})["rows"][0]
            self.assertFalse(row["valid"], text)
            self.assertEqual(row["errors"], ["invalid_format"])
            self.assertIsNone(row["score"])
        missing = score_attribution(p, {})["rows"][0]
        self.assertEqual(missing["errors"], ["unavailable"])
        wrong = {**expected, "current_known": not expected["current_known"]}
        row = score_attribution(p, {nid: {"status": "complete", "text": json.dumps(wrong)}})["rows"][0]
        self.assertTrue(row["valid"])
        self.assertEqual(row["score"], 0)
        self.assertEqual(row["errors"], ["current_known"])

    def test_large_json_integer_is_wrong_without_float_overflow(self):
        p = build_attribution()
        p["nodes"] = [n for n in p["nodes"] if n["kind"] == "attribution"][:1]
        nid = p["nodes"][0]["id"]
        answer = {**p["truth"][nid]["expected"], "value_percent": 10 ** 400}
        row = score_attribution(p, {nid: {"status": "complete", "text": json.dumps(answer)}})["rows"][0]
        self.assertTrue(row["valid"])
        self.assertEqual(row["score"], 0)
        self.assertEqual(row["errors"], ["value_percent"])

    def test_model_thinking_and_system_contract(self):
        gemma, mistral = build_attribution(), build_attribution(model="mistral:7b")
        self.assertIs(gemma["think"], False)
        self.assertNotIn("think", mistral)
        self.assertTrue(all(n["messages"][0]["content"] == OPEN_CONTRACT for n in gemma["nodes"]))


if __name__ == "__main__":
    unittest.main()
