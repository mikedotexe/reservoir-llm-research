"""Verify and describe the fixed startup capture; no live reads or model calls."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "research/outputs"
CAPTURE = ROOT / "2026-09-09-study-context-startup-capture/capture.json"
OUT = ROOT / "2026-09-09-study-context-startup-report"


def main():
    packet = json.loads(CAPTURE.read_text())
    report = json.loads((OUT / "report.json").read_text())
    assert report["capture_sha256"] == hashlib.sha256(CAPTURE.read_bytes()).hexdigest()
    by = {row["path"]: row for row in packet["records"]}
    rows = []
    for study in report["studies"]:
        if not study["receipt_verified"]:
            continue
        receipt = json.loads(by[study["receipt"]]["text"])
        wire = receipt.get("attempt", receipt)
        request, response = json.loads(wire["request_json"]), json.loads(wire["response_json"])
        book = study["notebook"]["fields"]
        system = "\n".join(m["content"] for m in request["messages"] if m["role"] == "system")
        rows.append(dict(
            id=study["id"], being=study["being"], kind=study["kind"], completed=study["completed_utc"],
            new_guidance="recent complete visible responses" in system,
            complete_previous=book["previous"].get("complete") if book["previous"] else None,
            recent_count=len(book.get("recent", [])), origin_receipts=study["notebook"]["origin_receipts"],
            output_limit=request.get("max_tokens", request.get("options", {}).get("num_predict")),
            context_tokens=request.get("options", {}).get("num_ctx"),
            native_token_counter=response.get("eval_count", response.get("usage", {}).get("completion_tokens")),
            finish=study.get("native_finish"), think=request.get("think"), final_chars=len(study["text"]),
            chosen=study["next"], response=study["text"], writing=study["writing"],
            user_text=study["user_text"], followthrough=study["followthrough"]))
    for being in ("astrid", "minime"):
        items = [row for row in rows if row["being"] == being]
        assert len(items) == 2 and items[1]["complete_previous"] is True
        assert any(origin["before_this_attempt"] and origin["verified"] for origin in items[1]["origin_receipts"]["previous"])
    assert all(row["new_guidance"] and row["output_limit"] == 4096 for row in rows)
    assert all(row["context_tokens"] == 32768 and row["think"] is False for row in rows if row["being"] == "minime")
    result = dict(verified=True, completed_studies=4, complete_prior_response_supplied_on_second_study=True,
                  scope="Input/writing and navigation uptake; no causal understanding claim; zero MLX counters are unavailable, not zero output.",
                  capture_sha256=report["capture_sha256"], rows=rows)
    (OUT / "verified-startup.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "startup-probe.py").write_bytes(Path(__file__).read_bytes())
    print({key: value for key, value in result.items() if key != "rows"})


if __name__ == "__main__":
    main()
