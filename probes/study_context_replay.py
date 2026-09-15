"""Replay saved visible answers into an isolated reader; never generate or write live state."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_sequences import notebook_exposure

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    report_root = ROOT / "research/outputs/2026-09-09-minime-nine-report"
    report = json.loads((report_root / "report.json").read_text())
    source = (report_root / "source/dispatcher.rs").read_bytes()
    path = args.out / "astrid/crates/astrid-capsule/src/dispatcher.rs"
    path.parent.mkdir(parents=True)
    path.write_bytes(source)
    source_sha = hashlib.sha256(source).hexdigest()
    studies = [s for s in report["studies"] if s["being"] == "minime" and any(
        "self_study_2026-09-09T" + stamp in str(s["writing"]) for stamp in (
            "12-08-04", "12-10-23", "12-12-54", "12-15-23", "12-17-14",
            "12-18-44", "12-20-30", "12-25-01", "12-26-19"))]
    studies.sort(key=lambda s: str(s["writing"]))
    assert len(studies) == 9
    base = dict(roots={"astrid": str(args.out / "astrid")}, state_directory=str(args.out / "state"))
    def call(**operation):
        return json.loads(subprocess.check_output([str(args.reader)], input=json.dumps(dict(base, **operation)).encode()))
    rows = []
    for index, study in enumerate(studies):
        page = study.get("page")
        if page:
            assert page["revision"]["sha256"] == source_sha
        action = f'SELF_STUDY OPEN {page["source"]} {page["start"]["line"]}' if page else "SELF_STUDY MAP"
        output = call(operation="prepare", action=action)
        # Seed only the historical authored question, with its original provenance.
        # This is a controlled memory replay, not a recreation of intervening Actions.
        if index == 0:
            old = notebook_exposure(study["user_text"])
            state_path = args.out / "state/reader-v1.json"
            state = json.loads(state_path.read_text())
            state["notebook"]["question"] = old["fields"]["question"]
            state_path.write_text(json.dumps(state))
            output = call(operation="prepare", action=action)
        request = json.dumps(dict(messages=[dict(role="system", content=output["system_prompt"]), dict(role="user", content=output["text"])]))
        response = json.dumps(dict(message=dict(content=study["text"]), done=True, done_reason="stop"))
        args_key = dict(page_id=output["page"]["id"]) if output["page"] else dict(navigation_id=output["navigation_id"])
        call(operation="delivered" if output["page"] else "navigation_delivered", request_json=request, response_json=response, **args_key)
        rows.append(dict(study_id=study["id"], historical_receipt=study["receipt"], output=output))
    next_after_comparison = next(row for row in rows if "12-25-01" in str(next(s["writing"] for s in studies if s["id"] == row["study_id"])))
    book = notebook_exposure(next_after_comparison["output"]["text"])["fields"]
    comparison = next(s for s in studies if "12-20-30" in str(s["writing"]))["text"].split("\nNEXT:")[0].strip()
    assert book["previous"]["complete"] is True
    assert book["previous"]["text"] == comparison
    assert "lifecycle of the task performing that call differs" in book["previous"]["text"]
    assert "SELF_STUDY RELATE dispatch_single" in next_after_comparison["output"]["text"]
    assert "SELF_STUDY SESSION OPEN" in next_after_comparison["output"]["text"]
    result = dict(recorded_at=datetime.now(timezone.utc).isoformat(), reader_sha256=hashlib.sha256(args.reader.read_bytes()).hexdigest(),
                  source_sha256=source_sha, scope="Saved visible prose replay; no model generation or causal behavior comparison",
                  comparison_preserved_complete=True, recent_accounts_before_next_page=len(book["recent"]), rows=rows)
    (args.out / "replay.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / "probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}))


if __name__ == "__main__":
    main()
