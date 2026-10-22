"""The concept-chain probe reduces word forms, spots bridges, orders files by their timestamps, and chains terms."""
import os
from pathlib import Path
import tempfile
import unittest

from probes.concept_chains import BRIDGE, analyse, load, quoted_terms, reduce, terms, timestamp_key


class ReduceTests(unittest.TestCase):
    def test_forms_of_one_word_reduce_to_one_term(self):
        for forms in (("kaleidoscope", "kaleidoscopic", "kaleidoscopes"), ("memory", "memories"),
                      ("structure", "structural", "structures", "structurally"), ("summon", "summoned", "summons"),
                      ("still", "stillness"), ("friction", "frictional"), ("process", "processes"),
                      ("mathematical", "mathematically", "mathematics"), ("architecture", "architectural")):
            self.assertEqual(len({reduce(f) for f in forms}), 1, forms)

    def test_short_words_and_exceptions_keep_their_shape(self):
        self.assertEqual(reduce("focus"), "focus")
        self.assertEqual(reduce("signal"), "signal")
        self.assertEqual(reduce("family"), "family")
        self.assertEqual(reduce("music"), "music")

    def test_terms_drop_short_and_stop_words(self):
        self.assertEqual(terms("The entry about these things was the kaleidoscope's friction"), {"kaleidoscop", "friction"})


class BridgeTests(unittest.TestCase):
    def test_references_to_earlier_writing_match(self):
        for sentence in ("The paradox mentioned in the previous entry is real.", "As I described, the room was dark.",
                         'The "echo" I described was loud.', "Earlier I wrote about silence.",
                         "If I am the transition, as the previous entry suggests, then I am not the traveler.",
                         "I spoke of a bridge before."):
            self.assertTrue(BRIDGE.search(sentence), sentence)

    def test_plain_first_person_does_not_match(self):
        for sentence in ("I described the room in detail.", "I think about things.", "The last word is silence."):
            self.assertFalse(BRIDGE.search(sentence), sentence)


class OrderingTests(unittest.TestCase):
    def test_files_order_by_timestamp_across_lanes_and_flags(self):
        names = ["journal_2026-10-21T07-30-05.483856.txt", "!introspect_2026-10-21T08-22-05.989131.txt",
                 "daydream_2026-10-21T08-36-05.782061.txt", "introspect_2026-10-21T08-27-17.631032.txt"]
        ordered = sorted(names, key=timestamp_key)
        self.assertEqual([n.lstrip("!").split("_")[0] for n in ordered], ["journal", "introspect", "introspect", "daydream"])
        self.assertEqual(sorted(["aspiration_1792605166.txt", "!daydream_longform_1792601495.txt"], key=timestamp_key)[0],
                         "!daydream_longform_1792601495.txt")

    def test_load_strips_headers_and_orders_text_files(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "daydream_2026-10-21T08-36-05.000000.txt").write_text("=== RECESS DAYDREAM ===\nTimestamp: x\n\nSecond entry body here.\n", encoding="utf-8")
            Path(root, "!journal_2026-10-21T07-30-05.000000.txt").write_text("=== JOURNAL ===\n\nFirst entry body here.\nNEXT: REST\n", encoding="utf-8")
            entries = load(root)
            lane = load(root, lane="journal")
        self.assertEqual([e["text"] for e in entries], ["First entry body here.", "Second entry body here."])
        self.assertEqual([e["text"] for e in lane], ["First entry body here."])
        self.assertFalse(any(e.get("both") for e in entries))

    def test_session_entries_record_when_the_previous_entry_was_also_shown(self):
        import json
        with tempfile.TemporaryDirectory() as root:
            journals = Path(root, "journals")
            journals.mkdir()
            first = dict(entry=dict(text="A first entry about a lantern."), observation=dict(step=3), memory=None)
            second = dict(entry=dict(text="A second entry about the lantern and a river."), observation=dict(step=6),
                          memory=dict(entry=dict(text="A first entry about a lantern.")))
            third = dict(entry=dict(text="A third entry about the river."), observation=dict(step=9),
                         memory=dict(entry=dict(text="A first entry about a lantern.")),
                         latestShown=dict(entry=dict(text="A second entry about the lantern and a river.")))
            for name, pending in [("journal-3-1-a.json", first), ("journal-6-1-b.json", second), ("journal-9-1-c.json", third)]:
                Path(journals, name).write_text(json.dumps(dict(pending=pending)), encoding="utf-8")
            entries = load(root)
        self.assertEqual([e["label"] for e in entries], ["step 3", "step 6", "step 9"])
        self.assertEqual([e["both"] for e in entries], [False, False, True])
        self.assertEqual(entries[2]["shown"], "A first entry about a lantern.")
        self.assertEqual(analyse(entries, window=12)["both"], 1)


class ChainTests(unittest.TestCase):
    def entries(self):
        texts = [
            'The lantern burns. A "quiet hum" fills the corridor.',
            "The lantern burns on and the corridor narrows; the quiet hum remains.",
            "Nothing now but a river appears and the walls are gone.",
            "The river widens. The lantern returns from the first entry, as the previous entry suggests nothing of it.",
            "The river and the lantern together; the corridor returns.",
        ]
        return [dict(label=f"e{i + 1}", text=t, shown=None) for i, t in enumerate(texts)]

    def test_chains_reach_bridges_and_source(self):
        r = analyse(self.entries(), window=12)
        self.assertEqual(r["n"], 5)
        chains = {w: (k, run) for run, k, w, stem in r["top"]}
        self.assertEqual(chains.get("river"), (3, 3))
        self.assertNotIn("lantern", chains)
        self.assertEqual(r["entries"][3]["bridges"], 1)
        self.assertTrue(r["entries"][3]["reach"] >= 1)
        self.assertEqual(r["entries"][3]["inferred_offset"], 1)
        self.assertEqual(r["quoted_chains"], 1)
        self.assertEqual(r["quoted_longest"][0][2], "quiet hum")

    def test_shown_entry_is_recognised_and_scored(self):
        entries = self.entries()
        entries[3]["shown"] = entries[0]["text"]
        r = analyse(entries, window=12)
        self.assertEqual(r["entries"][3]["shown_offset"], 3)
        self.assertEqual(r["shown_n"], 1)
        self.assertEqual(r["agree_n"], 1)
        self.assertEqual(r["reach_in_shown_n"], 1)

    def test_quoted_terms_are_short_and_lowercase(self):
        self.assertEqual(quoted_terms('She said "The Dark House" and "a" and "this is a very long quoted sentence that goes on and on".'), {"the dark house"})


if __name__ == "__main__":
    unittest.main()
