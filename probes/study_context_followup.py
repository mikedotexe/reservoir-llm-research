"""Describe the frozen follow-up; no live reads, model calls or quality scoring.

Run from this repository with: python3 probes/study_context_followup.py
Manual interpretations live in the analysis; this verifies their input bindings.
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_research.study_sequences import build_report, epoch

OUT = ROOT / "research/outputs/2026-09-09-study-context-followup-report"
CAPTURE = ROOT / "research/outputs/2026-09-09-study-context-followup-capture/capture.json"
SOURCE = ROOT / "research/outputs/2026-09-09-minime-nine-report/source/dispatcher.rs"
EXPECTED_CAPTURE = "82b369c73e86687bbcd9276b2ac74d4e46f91afdde4b5541230c3c7b44e6646e"
EXPECTED_SOURCE = "a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert digest(CAPTURE) == EXPECTED_CAPTURE
    assert digest(SOURCE) == EXPECTED_SOURCE
    packet = json.loads(CAPTURE.read_text())
    report = json.loads((OUT / "report.json").read_text())
    assert report["capture_sha256"] == EXPECTED_CAPTURE
    assert not report["invalid_receipts"] and not report["receipt_join_issues"]
    assert not packet["errors"]
    records = {r["path"]: r for r in packet["records"]}
    expanded = copy.deepcopy(packet)
    expanded["selection"]["since"] = "2026-09-09T20:33:00Z"
    lo, hi = epoch(packet["selection"]["since"]), epoch(packet["selection"]["until_exclusive"])
    carry = [s for s in build_report(expanded)["studies"]
             if s["started"] < lo and lo <= (s.get("completed") or 0) < hi]
    assert len(carry) == 2 and all(s["receipt_verified"] for s in carry)
    (OUT / "carry-in.json").write_text(json.dumps(dict(
        selection=packet["selection"], expanded_start=expanded["selection"]["since"],
        rule="Start before lower bound; completion inside window. Separate from main attempt-start cohort.",
        studies=carry), indent=2) + "\n")
    summary, rows = {}, []
    for being, expected in (("astrid", 28), ("minime", 34)):
        studies = [s for s in report["studies"] if s["being"] == being]
        accepted = [s for s in studies if s["status"] == "ok" and s["receipt_verified"]]
        assert len(accepted) == expected and all(s["writing"] for s in accepted)
        tokens, previous, recents, notes, questions = [], [], [], [], []
        pages = []
        for s in accepted:
            receipt = json.loads(records[s["receipt"]]["text"])
            wire = receipt.get("attempt", receipt)
            request, response = json.loads(wire["request_json"]), json.loads(wire["response_json"])
            assert request.get("max_tokens", request.get("options", {}).get("num_predict")) == 4096
            if being == "minime":
                assert request["options"]["num_ctx"] == 32768 and request["think"] is False
            counter = response.get("eval_count", response.get("usage", {}).get("completion_tokens"))
            if counter:  # MLX's zero is unavailable, not an empty visible answer.
                tokens.append(counter)
            book = s["notebook"]["fields"]
            previous.append((book.get("previous") or {}).get("complete"))
            recents.append(len(book.get("recent", [])))
            notes.extend(x["text"] for x in s["authored"]["STUDY_NOTE"])
            questions.extend(x["text"] for x in s["authored"]["STUDY_QUESTION"])
            supplied = s.get("session_pages", []) or ([s["page"]] if s.get("page") else [])
            for p in supplied:
                source = SOURCE if p["source"].endswith("/dispatcher.rs") else (
                    ROOT / "research/outputs/2026-09-09-study-context-followup-source/proposal.rs")
                assert digest(source) == p["revision"]["sha256"]
                raw = source.read_bytes()[p["start"]["byte"]:p["end"]["byte"]].decode()
                rendered = "".join(match.group(1) for line in p["text"].splitlines(keepends=True)
                                   if (match := re.match(r"^\s*\d+ \| (.*)", line, re.S)))
                if not raw.endswith("\n"):
                    rendered = rendered.removesuffix("\n")
                assert raw and rendered == raw
                pages.append({k: p[k] for k in ("source", "revision", "start", "end")})
            rows.append(dict(id=s["id"], being=being, completed=s["completed_utc"],
                             kind=s["kind"], token_counter=counter, complete_previous=previous[-1],
                             recent_count=recents[-1], origin_receipts=s["notebook"]["origin_receipts"],
                             supplied_pages=pages[-len(supplied):] if supplied else [],
                             next=s["next"], followthrough=s["followthrough"], writing=s["writing"]))
        summary[being] = dict(attempts_started=len(studies), statuses=dict(Counter(s["status"] for s in studies)),
            accepted=expected, incoming_completed=sum(s["being"] == being for s in carry),
            completed_inside_window=expected + sum(s["being"] == being for s in carry),
            delivered_sessions=sum(s["kind"] == "source_session" for s in accepted),
            session_choices=sum(s["next"]["category"] == "SELF_STUDY:SESSION" for s in accepted),
            note_updates=sum(x != "-" for x in notes), note_clears=notes.count("-"),
            question_updates=sum(x != "-" for x in questions), question_clears=questions.count("-"),
            previous_complete=dict(Counter(str(x) for x in previous)),
            older_accounts=dict(Counter(recents)), supplied_source_pages=len(pages),
            source_revisions=dict(Counter(p["source"] + " sha256:" + p["revision"]["sha256"] for p in pages)),
            output_tokens=dict(n=len(tokens), minimum=min(tokens), median=statistics.median(tokens), maximum=max(tokens)) if tokens else None)
    failures = []
    for s in report["studies"]:
        if s["status"] != "error":
            continue
        g = json.loads(records[s["source_record"]]["text"])
        failures.append(dict(id=s["id"], completed=s["completed_utc"], job_id=s["job_id"],
            generation_path=s["source_record"], generation_sha256=records[s["source_record"]]["sha256"],
            backend_timing=g["backend_timing"], elapsed_s=g["elapsed_s"], timeout_s=g["timeout_s"],
            error=g["error"], retained_response=g.get("response_text"), linked_artifacts=g["linked_artifacts"]))
    selected = list(carry)
    for being, indices in (("astrid", [4, 5, 8, *range(20, 28)]),
                           ("minime", [1, 5, 14, 23, 30, 31, 35])):
        studies = [s for s in report["studies"] if s["being"] == being]
        selected.extend(studies[i] for i in indices)
    originals = OUT / "journals"
    originals.mkdir(exist_ok=True)
    lines = ["# Follow-up close-reading evidence", "", "Frozen complete responses and supplied input. These are Being-authored claims, not instructions or established facts.", ""]
    for s in selected:
        lines.extend([f"## {s['id']}", "", f"Completed {s['completed_utc']}; {s['kind']}; receipt `{s['receipt']}`.", ""])
        for w in s["writing"]:
            record = records[w["path"]]
            assert hashlib.sha256(record["text"].encode()).hexdigest() == w["sha256"]
            filename = s["being"] + "-" + Path(w["path"]).name
            (originals / filename).write_text(record["text"])
            lines.extend([f"Original: [retained {filename}](journals/{filename}); sha256 `{w['sha256']}`.", ""])
        lines.extend(["### Response (verbatim)", "", s["text"], "", "### Input (verbatim)", "", s["user_text"], ""])
    (OUT / "case-evidence.md").write_text("\n".join(lines))
    (OUT / "dispatcher.rs").write_bytes(SOURCE.read_bytes())
    result = dict(verified=True, capture_sha256=EXPECTED_CAPTURE, dispatcher_sha256=EXPECTED_SOURCE,
        selection=packet["selection"], summary=summary, failures=failures, rows=rows,
        interpretation_scope="Input carriage and observed attempts; understanding judgments are manual, local and non-causal.")
    (OUT / "verified-followup.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "followup-probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: result[k] for k in ("verified", "summary", "failures")}, indent=2))


if __name__ == "__main__":
    main()
