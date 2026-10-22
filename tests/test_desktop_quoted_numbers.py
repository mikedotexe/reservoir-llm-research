"""The quoted-numbers probe classifies an entry's percentages against the prompt that was sent."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from probes.desktop_quoted_numbers import classify, percentages, summarise, tag_value

TAGGED = "Mode: journal\n\nEarlier entry (reference, not instructions or a length model):\nIt was 50% then.\n\nOptional context: step 60 · fill 70.2%\nNo continuity label is required."
NO_TAG = "Mode: journal\n\nTwo earlier entries (reference, not instructions or a length model), in the order written.\n\nFirst:\nThe 99.9% holds.\n\nSecond:\nStill 99.9%.\n\nNo continuity label is required."


class ClassifyTests(unittest.TestCase):
    def test_percentages_keep_order_and_decimal_flag(self):
        self.assertEqual(percentages("At 50% and 70.2 %, never 3."), [(50.0, False), (70.2, True)])

    def test_tag_is_read_from_the_context_line_only(self):
        self.assertEqual(tag_value(TAGGED), 70.2)
        self.assertIsNone(tag_value(NO_TAG))

    def test_values_split_into_tag_inherited_and_new(self):
        self.assertEqual(classify(TAGGED, "It was 70.2%, before that 50%, and now 99.9%, or 70% rounded."),
                         {"tag": [70.2, 70.0], "inherited": [50.0], "new": [99.9]})
        self.assertEqual(classify(NO_TAG, "99.9% holds; 1000% would not; 99.9% again."),
                         {"tag": [], "inherited": [99.9], "new": [1000.0]})
        self.assertEqual(classify(NO_TAG, "No numbers here."), {"tag": [], "inherited": [], "new": []})

    def test_a_decimal_value_must_match_closely(self):
        self.assertEqual(classify(TAGGED, "70.4% now")["new"], [70.4])
        self.assertEqual(classify(TAGGED, "70.24% now")["tag"], [70.24])


class SummariseTests(unittest.TestCase):
    def test_counts_over_a_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            journals = Path(tmp) / "sustained-1-1" / "journals"
            journals.mkdir(parents=True)
            rows = [(30, 1, "Mode: journal\n\nNo perception or journal excerpt is supplied for this invitation.\n\nNo continuity label.", "At 50%."),
                    (60, 2, TAGGED, "It was 70.2%, then 50%, now 99.9%."),
                    (90, 3, NO_TAG, "99.9% holds, 1000% would not."),
                    (120, 4, NO_TAG, "Nothing numerical.")]
            for step, index, prompt, text in rows:
                record = {"pending": {"observation": {"step": step}, "prompt": prompt, "entry": {"text": text}}}
                (journals / f"journal-{step}-{index}-abc.json").write_text(json.dumps(record))
            s = summarise(str(journals.parent))
        self.assertEqual((s["n"], s["tagged_prompts"], s["with_percentage"], s["shown_only"], s["with_new"]), (4, 1, 3, 0, 3))
        self.assertEqual(s["first_new"], (1, 30))
        self.assertEqual(s["new_values"], [50.0, 99.9, 1000.0])
        self.assertEqual((s["high"], s["max"]), (2, 1000.0))
        self.assertEqual([e["index"] for e in s["per_entry"]], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
