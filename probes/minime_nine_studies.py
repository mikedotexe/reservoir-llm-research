"""Audit Mike's nine September 9 journals against frozen provider evidence.

Offline; no generation, live writes, or database access. The wider capture supplies
attribution only. These nine user-selected entries are not a population sample.
Run from the research root: python3 probes/minime_nine_studies.py
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_research.study_sequences import verify_records

CAPTURE = ROOT / "research/outputs/2026-09-09-minime-nine-capture/capture.json"
REPORT = ROOT / "research/outputs/2026-09-09-minime-nine-report/report.json"
TIMES = ["12-08-04.010300", "12-10-23.637288", "12-12-54.323820",
         "12-15-23.563870", "12-17-14.945870", "12-18-44.459517",
         "12-20-30.849947", "12-25-01.432314", "12-26-19.531537"]


def main():
    packet = json.loads(CAPTURE.read_text())
    verify_records(packet)
    report = json.loads(REPORT.read_text())
    by_path = {row["path"]: row for row in packet["records"]}
    selected = []
    material = ["# Mike's nine selected Minime entries — original material\n"]
    for stamp in TIMES:
        name = f"self_study_2026-09-09T{stamp}.txt"
        matches = [(s, w) for s in report["studies"] if s["being"] == "minime"
                   for w in s["writing"] if Path(w["path"]).name == name]
        assert len(matches) == 1, (name, len(matches))
        study, writing = matches[0]
        assert study["receipt_verified"]
        receipt = json.loads(by_path[study["receipt"]]["text"])
        wire = receipt.get("attempt", receipt)
        request = json.loads(wire["request_json"])
        response = json.loads(wire["response_json"])
        generation = json.loads(by_path[study["source_record"]]["text"])
        raw = response["message"]["content"]
        assert raw.strip() == study["text"]  # no discarded body or journal clipping
        journal = by_path[writing["path"]]
        assert study["text"] in journal["text"]
        fields = study["notebook"]["fields"]
        question = fields.get("question") or {}
        previous = fields.get("previous") or {}
        page = study.get("page")
        selected.append(dict(
            file=writing["path"], file_sha256=journal["sha256"], file_bytes=journal["bytes"],
            agency_notice="[Agency-vernacular notice" in journal["text"],
            id=study["id"], receipt=study["receipt"], generation=study["source_record"],
            action_id=study.get("action_id"), job_id=generation.get("job_id"),
            completed_utc=study["completed_utc"], kind=study["kind"],
            model=response["model"], pid=generation["pid"], backend=generation["backend"],
            fallback=generation["fallback_used"], attempts=generation["attempts_total"],
            output_cap=request["options"]["num_predict"], context=request["options"]["num_ctx"],
            think=request.get("think"), message_roles=[m["role"] for m in request["messages"]],
            stop=request.get("options", {}).get("stop"), finish=response.get("done_reason"),
            generated_tokens=response["eval_count"], input_tokens=response["prompt_eval_count"],
            elapsed_seconds=generation["elapsed_s"], timeout_seconds=generation["timeout_s"],
            response_words=len(study["text"].split()), response_bytes=len(study["text"].encode()),
            full_visible_body_preserved=True, thinking_chars=len(response["message"].get("thinking", "")),
            next_lines=sum(line.startswith("NEXT:") for line in raw.splitlines()),
            note_authored=any(line.startswith("STUDY_NOTE:") for line in raw.splitlines()),
            question_authored=any(line.startswith("STUDY_QUESTION:") for line in raw.splitlines()),
            question_id=study.get("question_id"), question=question,
            previous=previous, next=study["next"], page=page,
            right_censored=study["followthrough"]["right_censored"],
            verified_action_descendants=[{k: a.get(k) for k in
                ["action_id", "canonical_action", "parent_action_id", "status", "llm_job_id", "matches_requested"]}
                for a in study["followthrough"]["explicit_parent_actions"]],
        ))
        material.extend([f"\n## {name}\n", journal["text"], "\n"])
    pages = [r["page"] for r in selected if r["page"]]
    intervals = Counter((p["source"], p["revision"]["sha256"], p["start"]["byte"], p["end"]["byte"]) for p in pages)
    # This selected sample's distinct intervals do not overlap.
    ordered = sorted(intervals)
    assert all(a[:2] != b[:2] or a[3] <= b[2] for a, b in zip(ordered, ordered[1:]))
    tokens = [r["generated_tokens"] for r in selected]
    summary = dict(
        selection="Nine explicitly user-selected journals, September 9 12:08:04–12:26:19 PDT; exploratory case series",
        n=len(selected), capture_sha256=hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        capture_errors=packet["errors"], receipt_join_issues=report["receipt_join_issues"],
        invalid_receipts=report["invalid_receipts"],
        file_bytes_range=[min(r["file_bytes"] for r in selected), max(r["file_bytes"] for r in selected)],
        output_token_range=[min(tokens), max(tokens)], median_output_tokens=statistics.median(tokens),
        median_cap_fraction=statistics.median(tokens)/4096,
        old_768_cap_exceeded=sum(t > 768 for t in tokens),
        finish_counts=dict(Counter(r["finish"] for r in selected)),
        caps=dict(Counter(r["output_cap"] for r in selected)),
        context_tokens=dict(Counter(r["context"] for r in selected)),
        input_token_range=[min(r["input_tokens"] for r in selected), max(r["input_tokens"] for r in selected)],
        time_range=[min(r["elapsed_seconds"] for r in selected), max(r["elapsed_seconds"] for r in selected)],
        think_false=sum(r["think"] is False for r in selected),
        source_pages=len(pages), unique_intervals=len(intervals),
        delivered_bytes=sum((end-start)*n for (_,_,start,end), n in intervals.items()),
        unique_bytes_in_selection=sum(end-start for _,_,start,end in intervals),
        repeated_bytes_within_selection=sum((end-start)*(n-1) for (_,_,start,end), n in intervals.items()),
        same_question_origin=len({r["question"].get("response_sha256") for r in selected}) == 1,
        notes_authored=sum(r["note_authored"] for r in selected),
        agency_notice_files=sum(r["agency_notice"] for r in selected),
        questions_authored=sum(r["question_authored"] for r in selected),
        named_question_inputs=sum(bool(r["question_id"]) for r in selected),
        multiple_next_bodies=[r["id"] for r in selected if r["next_lines"] > 1],
        selected_intervals=[dict(source=s,sha256=h,start=start,end=end,deliveries=n)
                            for (s,h,start,end),n in intervals.items()],
    )
    destination = REPORT.parent
    (destination/"selected-nine.json").write_text(json.dumps(dict(summary=summary, entries=selected), indent=2)+"\n")
    (destination/"selected-nine-verbatim.md").write_text("\n".join(material))
    (destination/"selected-nine-probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
