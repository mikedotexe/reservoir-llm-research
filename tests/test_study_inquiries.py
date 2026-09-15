"""One shared session is one generation with every supplied source interval."""
import json
import unittest
from reservoir_research.study_capture import encoded, sha
from reservoir_research.study_sequences import receipt_records, source_progress, command


def record(value, kind, identity):
    raw = encoded(value)
    return dict(path=f"/fixture/{identity}/{sha(raw)}.json", kind=kind, being="minime",
                text=raw.decode(), sha256=sha(raw), bytes=len(raw), filename_time=120)


def fixture():
    pages = [dict(id=f"p{i}", text=f"SOURCE file{i}", source=f"minime/file{i}.py",
                  revision=dict(sha256=f"sha{i}", bytes=20), start=dict(byte=0), end=dict(byte=10))
             for i in range(3)]
    text = "\n".join(p["text"] for p in pages)
    wire = dict(request_json=json.dumps(dict(messages=[dict(role="user", content=text)])),
                response_json=json.dumps(dict(message=dict(content="NEXT: SELF_STUDY CONTINUE"),
                   done=True, done_reason="stop", created_at="2026-09-09T18:00:00Z")))
    session = record(dict(schema="source_study_navigation_delivery_v1", **wire,
        output=dict(text=text, page=None, session_pages=pages, navigation_id="session", question_id="q1",
                    input_kind="source_session")), "navigation", "session")
    children = [record(dict(schema="source_study_delivery_v1", **wire, page=p, session_id="session"),
                       "delivery", p["id"]) for p in pages]
    return session, children


class StudyInquiryTests(unittest.TestCase):
    def test_complete_session_prefers_whole_offer_and_counts_all_pages_once(self):
        session, pages = fixture()
        records = receipt_records([*pages, session, session])
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["verified"])
        self.assertEqual(len(records[0]["session_pages"]), 3)
        self.assertEqual(records[0]["question_id"], "q1")
        progress = source_progress(records, 0, 2_000_000_000)
        self.assertEqual(len(progress), 3)
        self.assertEqual(sum(row["new_bytes"] for row in progress), 30)


    def test_partial_session_capture_does_not_claim_complete_delivery(self):
        _, pages = fixture()
        records = receipt_records(pages)
        self.assertFalse(records[0]["verified"])
        self.assertIn("completeness unknown", records[0]["errors"][0])
        self.assertEqual(source_progress(records, 0, 2_000_000_000), [])


    def test_new_choices_are_era_scoped_and_preserve_page_separators(self):
        text = "SELF_STUDY SESSION OPEN astrid/Cargo.toml 1 | OPEN minime/pyproject.toml 1"
        self.assertIsNone(command(text, "minime", terminal_source_choice=True)["raw"])
        actual = command(text, "minime", terminal_source_choice=True, inquiry_navigation=True)
        self.assertEqual(actual["raw"], text)
        self.assertEqual(actual["category"], "SELF_STUDY:SESSION")
        self.assertIsNone(command("SELF_STUDY QUESTION NEW why?", "minime", terminal_source_choice=True,
                                  inquiry_navigation=True)["raw"])
        self.assertEqual(command("NEXT: SELF_STUDY QUESTION NEW why?", "minime", inquiry_navigation=True)["category"],
                         "SELF_STUDY:QUESTION")


if __name__ == "__main__":
    unittest.main()
