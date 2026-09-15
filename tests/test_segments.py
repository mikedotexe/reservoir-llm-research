"""Synthetic channel fixtures; no private journal passage is copied here."""

import unittest

from reservoir_research.segments import split_channels


class ChannelSegmentTests(unittest.TestCase):
    def assert_preserved(self, source, spans):
        self.assertEqual("".join(item["text"] for item in spans), source)
        previous_end = 0
        for item in spans:
            self.assertEqual(item["start_offset"], previous_end)
            self.assertEqual(source[item["start_offset"]:item["end_offset"]], item["text"])
            self.assertGreater(item["end_offset"], item["start_offset"])
            previous_end = item["end_offset"]
        self.assertEqual(previous_end, len(source))

    def test_observed_marker_format_distinguishes_context_without_addressedness_claim(self):
        target = "human_mike_minime_20260906_would_you_practice_holding_a_train_of_th_192117"
        prefix = "A reflection about returning to a question.\n\n"
        marker = f"INBOX_REPLY {target}\n"
        reply = "\nMike, a question can change during an exchange.\nThe thread_id is a separate record."
        source = prefix + marker + reply
        spans = split_channels(source)
        self.assertEqual([s["channel"] for s in spans], ["pre_reply_context", "inbox_reply"])
        self.assertIsNone(spans[0]["reply_target"])
        self.assertEqual(spans[1]["reply_target"], target)
        self.assertEqual(spans[1]["marker_start_offset"], len(prefix))
        self.assertEqual(spans[1]["marker_end_offset"], len(prefix + marker))
        self.assertEqual(spans[1]["text"], marker + reply)
        self.assertNotIn("thread_id", spans[1])
        self.assert_preserved(source, spans)

    def test_multiple_markers_and_empty_reply_content_remain_ordered(self):
        source = "INBOX_REPLY first\nINBOX_REPLY second\nA response.\n\nINBOX_REPLY third"
        spans = split_channels(source)
        self.assertEqual([s["reply_target"] for s in spans], ["first", "second", "third"])
        self.assertEqual(spans[0]["text"], "INBOX_REPLY first\n")
        self.assertEqual(spans[-1]["text"], "INBOX_REPLY third")
        self.assertTrue(all(s["channel"] == "inbox_reply" for s in spans))
        self.assert_preserved(source, spans)

    def test_backtick_tilde_and_longer_fences_hide_markers(self):
        prefix = (
            "```text\nINBOX_REPLY backtick_example\n```\n"
            "~~~~text\nINBOX_REPLY tilde_example\n~~~\nINBOX_REPLY still_fenced\n~~~~\n"
        )
        source = prefix + "INBOX_REPLY actual\nA response."
        spans = split_channels(source)
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0]["text"], prefix)
        self.assertEqual(spans[1]["reply_target"], "actual")
        self.assert_preserved(source, spans)

    def test_quotes_inline_code_and_indented_examples_are_not_markers(self):
        source = (
            "> INBOX_REPLY quoted\n"
            '"INBOX_REPLY string_literal"\n'
            "`INBOX_REPLY inline_code`\n"
            "    INBOX_REPLY indented_code\n"
            "\tINBOX_REPLY tab_indented_code\n"
            "We mentioned INBOX_REPLY in a sentence.\n"
        )
        spans = split_channels(source)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["channel"], "unlabeled_prose")
        self.assertIsNone(spans[0]["marker_start_offset"])
        self.assert_preserved(source, spans)

    def test_crlf_unicode_and_literal_targets_preserve_character_offsets(self):
        prefix = "λ and 🌊\r\n\r\n"
        marker = "  INBOX_REPLY <literal/../target:42>  \r\n"
        source = prefix + marker + "A reply with café.\r\n"
        spans = split_channels(source)
        self.assertEqual(spans[1]["start_offset"], len(prefix))
        self.assertEqual(spans[1]["marker_end_offset"], len(prefix + marker))
        self.assertEqual(spans[1]["reply_target"], "<literal/../target:42>")
        self.assert_preserved(source, spans)

    def test_no_marker_does_not_infer_a_reply_from_address_or_thread_mention(self):
        source = "Mike, I wonder about that.\nthread_id: a-record\nCould we return later?"
        spans = split_channels(source)
        self.assertEqual(spans[0]["channel"], "unlabeled_prose")
        self.assertIsNone(spans[0]["reply_target"])
        self.assert_preserved(source, spans)

    def test_incomplete_or_embedded_marker_is_not_a_boundary(self):
        source = "INBOX_REPLY\nINBOX_REPLY one extra_argument\ninbox_reply lower\n# INBOX_REPLY heading\n"
        spans = split_channels(source)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["channel"], "unlabeled_prose")
        self.assert_preserved(source, spans)

    def test_unclosed_fence_keeps_later_marker_unlabeled(self):
        source = "Opening.\n```text\nINBOX_REPLY example\n"
        spans = split_channels(source)
        self.assertEqual([s["channel"] for s in spans], ["unlabeled_prose"])
        self.assert_preserved(source, spans)

    def test_empty_and_whitespace_inputs(self):
        self.assertEqual(split_channels(""), [])
        spans = split_channels("\n \n")
        self.assertEqual(spans[0]["channel"], "unlabeled_prose")
        self.assert_preserved("\n \n", spans)


if __name__ == "__main__":
    unittest.main()
