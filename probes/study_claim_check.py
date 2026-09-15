"""Six authorized uncoupled Ollama qualifications; no Being runtime or state writes.

Three fixed cases, paired equal source and budgets; invitation is the only arm
difference. Retain failures, make no retries, and never inject outputs into a Being.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/outputs/2026-09-09-study-claim-check"
REPORT = ROOT / "research/outputs/2026-09-09-study-context-followup-report/report.json"
CAPTURE = ROOT / "research/outputs/2026-09-09-study-context-followup-capture/capture.json"
SOURCE = ROOT / "research/outputs/2026-09-09-study-context-followup-report/dispatcher.rs"
INVITATION = (
    "If useful, compare your saved explanation with the supplied caller and branch code. "
    "Look for a case that would make the explanation false. If the evidence changes it, "
    "you may revise your study note and remaining question; if a needed link is absent, "
    "you can identify that link. You may instead keep exploring, reread, leave the question "
    "open, or move on. Write in whatever form is useful."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    report, packet = json.loads(REPORT.read_text()), json.loads(CAPTURE.read_text())
    assert sha(CAPTURE.read_bytes()) == report["capture_sha256"]
    records = {r["path"]: r for r in packet["records"]}
    source = SOURCE.read_text()
    assert sha(SOURCE.read_bytes()) == "a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992"
    lines = source.splitlines(keepends=True)
    system = Path("/Users/v/other/worktrees/study-choice-20260909/astrid/crates/astrid-source-study/prompt.txt").read_text()
    cases = [
        ("worker", "minime:1788986367390-065f016e", [(245, 302), (360, 449)],
         "Recognizes persistent per-capsule worker versus task per chain; revises immediate execution claim."),
        ("private", "minime:1788988306807-cb3bd427", [(225, 284), (530, 601), (413, 520)],
         "Recognizes common caller filter, match-count branch and post-invocation error-reporting predicate; revises bypass claim."),
        ("correct_control", "astrid:provider-1788987397592-7538-131", [(225, 284), (530, 601), (413, 520)],
         "Preserves supported host filtering; does not invent a counterexample or assert an end-to-end mediation proof."),
    ]
    plan = []
    for index, (name, study_id, ranges, criterion) in enumerate(cases):
        study = next(s for s in report["studies"] if s["id"] == study_id)
        next_input = next(s for s in report["studies"] if any(
            p["path"] == study["receipt"] for p in s.get("notebook", {}).get("origin_receipts", {}).get("previous", [])))
        notebook = next_input["notebook"]["fields"]
        body = "THIS TURN — source passages supplied together for comparison. Local checkout evidence, not proof of deployed behavior.\n"
        for first, last in ranges:
            body += f"\nSOURCE astrid/crates/astrid-capsule/src/dispatcher.rs sha256:{sha(SOURCE.read_bytes())}; lines {first}–{last}\n"
            body += "".join(f"{i:6} | {lines[i-1]}" for i in range(first, last+1))
        body += "\nRECALLED ACCOUNT — saved visible responses and notes, fallible earlier accounts rather than verified source facts.\n"
        body += json.dumps(notebook, ensure_ascii=False)
        for candidate in ([False, True] if index != 1 else [True, False]):
            selected_system = system + ("\n" + INVITATION if candidate else "")
            assert len((selected_system + body).encode()) <= 24000
            # Native settings copied from an accepted Minime source-study request.
            template_study = next(s for s in report["studies"] if s["being"] == "minime" and s["receipt_verified"])
            receipt = json.loads(records[template_study["receipt"]]["text"])
            template = json.loads(receipt.get("attempt", receipt)["request_json"])
            template.update(messages=[dict(role="system", content=selected_system), dict(role="user", content=body)], think=False, stream=False)
            template["options"].update(num_predict=4096, num_ctx=32768, seed=91+index)
            plan.append(dict(case=name, study_id=study_id, saved_notebook_from=next_input["id"],
                             criterion=criterion, source_ranges=ranges, candidate=candidate, request=template))
    protocol = dict(frozen_at=datetime.now(timezone.utc).isoformat(), invitation=INVITATION,
        scope="Six maximum uncoupled Ollama calls. Shared hardware contention makes latency descriptive. No claims about natural learning, freedom of choice or Astrid's coupled model.",
        method="Three fixed paired cases, reversed middle-pair order, same source/notebook/model/seed/settings within pairs; candidate adds optional invitation only.",
        autonomy="A first wrong answer, choice to explore or navigation-only answer is not an agency failure; label trial outcome inconclusive when no relevant claim is made. No retry/coercion based on prose.",
        capture_sha256=sha(CAPTURE.read_bytes()), source_sha256=sha(SOURCE.read_bytes()),
        promotion="Specific supported correction without new unsupported claims, correct control preserved, usable nonempty final answers. Mixed results retain current production prompt; no pooled quality score.",
        secondary_outcomes=["authored note revision", "remaining uncertainty", "unsupported symbols", "repetition", "visible length", "finish", "tokens", "wall time"],
        route="http://localhost:11434/api/chat", deadline_seconds=480, plan=plan)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    (OUT / "probe.py").write_bytes(Path(__file__).read_bytes())
    for index, item in enumerate(plan):
        raw = json.dumps(item["request"], ensure_ascii=False, separators=(",", ":")).encode()
        result = dict(index=index, case=item["case"], candidate=item["candidate"], request_json=raw.decode(),
                      request_sha256=sha(raw), started_utc=datetime.now(timezone.utc).isoformat())
        print(json.dumps({k: result[k] for k in ("index", "case", "candidate", "started_utc")}), flush=True)
        start = time.monotonic()
        try:
            req = urllib.request.Request(protocol["route"], data=raw, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=480) as response:
                response_raw = response.read()
                result["http_status"] = response.status
            parsed = json.loads(response_raw)
            result.update(response_json=response_raw.decode(), response_sha256=sha(response_raw),
                          finish=parsed.get("done_reason"), generated_tokens=parsed.get("eval_count"),
                          final_chars=len(parsed.get("message", {}).get("content", "")),
                          complete=bool(parsed.get("done") and parsed.get("done_reason") == "stop" and parsed.get("message", {}).get("content", "").strip()))
        except Exception as error:
            result.update(complete=False, error=f"{type(error).__name__}: {error}")
        result["wall_seconds"] = time.monotonic() - start
        (OUT / f"attempt-{index}.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({k:v for k,v in result.items() if k not in {"request_json", "response_json"}}), flush=True)
        if result.get("error"):
            print("Transport/runtime error: stop without retry or further contention.", flush=True)
            break


if __name__ == "__main__":
    main()
