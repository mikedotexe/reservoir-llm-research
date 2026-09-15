"""Verify selected live helper using isolated research state; no model/delivery."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/outputs/2026-09-09-study-choice-recovery"


def main():
    astrid = Path("/Users/v/other/astrid")
    active = json.loads((astrid / ".runtime/bridge-deployment/active.json").read_text())
    stage = Path(active["stage"])
    assert stage == Path("/Users/v/other/worktrees/study-choice-20260909/bridge-stage-01")
    helper = stage / "helpers/astrid-source-study"
    manifest_raw = (stage / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_raw).hexdigest() == active["manifest_sha256"]
    helper_sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    assert helper_sha == json.loads(manifest_raw)["artifacts"]["source-study-reader"]["sha256"]
    OUT.mkdir(exist_ok=False)
    base = dict(astrid_root=str(astrid), minime_root="/Users/v/other/minime",
                state_directory=str(OUT / "state"), operation="prepare")
    wrong = "astrid/capsules/spectral-bridge/src/runtime/command_dispatch.rs"
    right = "astrid/capsules/spectral-bridge/src/action_continuity/runtime/command_dispatch.rs"
    actions = [f"SELF_STUDY OPEN {wrong} 1", f"SELF_STUDY OPEN {wrong} 1",
               f"SELF_STUDY OPEN {right} 1"]
    rows = []
    for action in actions:
        request = dict(base, action=action)
        run = subprocess.run([str(helper)], input=json.dumps(request), text=True,
                             capture_output=True, check=True, timeout=45)
        rows.append(dict(request=request, output=json.loads(run.stdout)))
    for row in rows[:2]:
        assert row["output"]["page"] is None
        assert f"SELF_STUDY OPEN {right} 1" in row["output"]["text"]
        assert "candidates, not opened" in row["output"]["text"]
    assert rows[2]["output"]["page"]["source"] == right
    result = dict(verified_at=datetime.now(timezone.utc).isoformat(), active=active,
        helper_sha256=helper_sha, repeated_recovery_offers_exact_path=True,
        no_implicit_open=True, explicit_open_succeeds=True, rows=rows,
        scope="Selected helper, isolated prepare-only state. No model call, delivery or Being notebook mutation; no natural uptake inference.")
    (OUT / "recovery.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
