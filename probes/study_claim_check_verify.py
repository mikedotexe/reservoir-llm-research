"""Read-only verification and declared-case reporting; no additional model calls."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/outputs/2026-09-09-study-claim-check"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    protocol = json.loads((OUT / "protocol.json").read_text())
    manual = json.loads((OUT / "evaluation.json").read_text())
    rows = []
    for i, plan in enumerate(protocol["plan"]):
        path = OUT / f"attempt-{i}.json"
        attempt = json.loads(path.read_text())
        for kind in ["request", "response"]:
            assert sha(attempt[kind + "_json"].encode()) == attempt[kind + "_sha256"]
        request = json.loads(attempt["request_json"])
        assert request == plan["request"]
        response = json.loads(attempt["response_json"])
        body = response["message"]["content"]
        assert len(body) == attempt["final_chars"]
        assert response["done"] is True and response["done_reason"] == "stop"
        assert response["eval_count"] == attempt["generated_tokens"]
        evaluation = manual["attempts"][i]
        assert evaluation["index"] == i
        for quote in evaluation["quotes"]:
            assert quote in body
        row = {k: attempt[k] for k in ["index", "case", "candidate", "finish",
            "generated_tokens", "final_chars", "wall_seconds", "request_sha256", "response_sha256"]}
        row.update(evaluation=evaluation, artifact_sha256=sha(path.read_bytes()))
        rows.append(row)
    for left, right in [(0, 1), (2, 3), (4, 5)]:
        requests = [json.loads((OUT / f"attempt-{i}.json").read_text())["request_json"] for i in [left, right]]
        requests = [json.loads(raw) for raw in requests]
        for request in requests:
            request["messages"][0]["content"] = request["messages"][0]["content"].removesuffix("\n" + protocol["invitation"])
        assert requests[0] == requests[1]
    result = dict(protocol_sha256=sha((OUT / "protocol.json").read_bytes()),
        evaluation_sha256=sha((OUT / "evaluation.json").read_bytes()), attempts=rows,
        n=len(rows), normal_stops=len(rows), production_invitation_promoted=False,
        conclusion="No observed correction benefit in the two erroneous-account pairs. Correct control's host filter preserved in both, with unsupported mediation elaboration. No population, learning or agency score.")
    (OUT / "verified.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "attempts"}, indent=2))


if __name__ == "__main__":
    main()
