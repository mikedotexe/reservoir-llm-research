"""Four authorized, uncoupled Ollama replays; never imports a Being runtime.

Saved inputs from the nine-entry study. No journals, actions, notebooks, live
configuration or reservoir handles are written. Results stay in research outputs.
One request at a time, no retries. Stop on an error or incomplete/empty answer.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/outputs/2026-09-09-study-thinking-comparison-v2"
CAPTURE = ROOT / "research/outputs/2026-09-09-minime-nine-capture/capture.json"
REPORT = ROOT / "research/outputs/2026-09-09-minime-nine-report/report.json"


def main():
    OUT.mkdir(exist_ok=False)
    packet = json.loads(CAPTURE.read_text())
    report = json.loads(REPORT.read_text())
    by = {r["path"]: r for r in packet["records"]}
    cases = ["12-20-30.849947", "12-25-01.432314"]
    plan = []
    for i, case in enumerate(cases):
        study = next(s for s in report["studies"] if s["being"] == "minime" and case in str(s["writing"]))
        receipt = json.loads(by[study["receipt"]]["text"])
        request = json.loads(receipt.get("attempt", receipt)["request_json"])
        for enabled in ([False, True] if i == 0 else [True, False]):
            request_copy = json.loads(json.dumps(request))
            request_copy["think"] = enabled
            request_copy["options"].update(num_predict=8192, num_ctx=32768, seed=37+i)
            plan.append(dict(case=case, study_id=study["id"], think=enabled, request=request_copy))
    protocol = dict(
        frozen_at=datetime.now(timezone.utc).isoformat(),
        design="Two fixed cases, one off/on pair each, reversed condition order; exploratory qualification, not a statistical efficacy trial.",
        route="http://localhost:11434/api/chat",
        route_scope="Standalone Ollama; never coupled Astrid :8090. Initial preparation attempt stopped before HTTP on an invalid URL; retained separately.",
        controls="Identical saved messages/model/seed/temperature/top_p/output allowance/context/deadline within each pair. New memory/synthesis prompt is not introduced here.",
        cap=8192, context=32768, request_deadline_seconds=480,
        outcomes=["normal nonempty final answer", "source-supported task-lifecycle comparison", "new relevant unresolved question or test", "unsupported claims", "within-answer duplication", "final answer length", "reasoning presence/length", "total generated tokens", "wall and provider duration"],
        limitations="Four completions; shared hardware/live Ollama contention makes latency descriptive. Reasoning text is retained privately, never fed to Being memory. No causal natural-behavior or Astrid-model claim.",
        promotion="A gain must be visible in final answers without worse unsupported claims, repeated text or completion failures. Mixed/insufficient results retain current production thinking-off; expanded trials require a new declared plan.",
        plan=plan,
    )
    (OUT/"protocol.json").write_text(json.dumps(protocol, indent=2)+"\n")
    (OUT/"probe.py").write_bytes(Path(__file__).read_bytes())
    for i, item in enumerate(plan):
        raw = json.dumps(item["request"], ensure_ascii=False, separators=(",", ":")).encode()
        request = urllib.request.Request(protocol["route"], data=raw, headers={"Content-Type":"application/json"})
        print(json.dumps(dict(event="started", index=i, case=item["case"], think=item["think"])), flush=True)
        start = time.monotonic()
        result = dict(index=i, case=item["case"], think=item["think"], request_json=raw.decode(), request_sha256=hashlib.sha256(raw).hexdigest(), started_utc=datetime.now(timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(request, timeout=480) as response:
                body = response.read().decode()
            parsed = json.loads(body)
            result.update(response_json=body, response_sha256=hashlib.sha256(body.encode()).hexdigest(), finish=parsed.get("done_reason"), generated_tokens=parsed.get("eval_count"), final_chars=len(parsed.get("message",{}).get("content","")), thinking_chars=len(parsed.get("message",{}).get("thinking","")))
            result["complete"] = bool(parsed.get("done") and parsed.get("done_reason") == "stop" and parsed.get("message",{}).get("content", "").strip())
        except Exception as error:
            result.update(complete=False, error=f"{type(error).__name__}: {error}")
        result["wall_seconds"] = time.monotonic()-start
        (OUT/f"attempt-{i}.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({k:v for k,v in result.items() if k not in ["request_json","response_json"]}), flush=True)
        if not result["complete"]:
            print("Stopped per protocol; later planned calls were not run.", flush=True)
            break


if __name__ == "__main__":
    main()
