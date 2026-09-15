"""Exercise the selected reader with isolated research state; no model or live state.

Reads the live source catalog and immutable helper. Writes only below --out.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out = args.out.resolve()
    root = Path(__file__).resolve().parents[1]
    assert args.out.is_relative_to(root / "research/outputs")
    args.out.mkdir(parents=True, exist_ok=False)
    astrid = Path("/Users/v/other/astrid")
    active = json.loads((astrid / ".runtime/bridge-deployment/active.json").read_text())
    stage = Path(active["stage"])
    manifest_bytes = (stage / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == active["manifest_sha256"]
    helper = stage / "helpers/astrid-source-study"
    helper_sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    assert helper_sha == json.loads(manifest_bytes)["artifacts"]["source-study-reader"]["sha256"]
    base = dict(astrid_root=str(astrid), minime_root="/Users/v/other/minime",
                state_directory=str(args.out / "state"))
    wrong = "astrid/capsules/spectral-bridge/src/runtime/command_dispatch.rs"
    right = "astrid/capsules/spectral-bridge/src/action_continuity/runtime/command_dispatch.rs"
    actions = [f"SELF_STUDY OPEN {wrong} 1", "SELF_STUDY FIND command_dispatch", f"SELF_STUDY OPEN {right} 1"]
    rows = []
    for action in actions:
        request = dict(base, operation="prepare", action=action)
        result = subprocess.run([str(helper)], input=json.dumps(request), text=True, capture_output=True, check=True, timeout=45)
        rows.append(dict(request=request, output=json.loads(result.stdout)))
    assert rows[0]["output"]["page"] is None and right not in rows[0]["output"]["text"]
    assert right in rows[1]["output"]["text"]
    assert rows[2]["output"]["page"]["source"] == right
    result = dict(recorded_at=datetime.now(timezone.utc).isoformat(), helper_sha256=helper_sha,
        active=active, scope="Isolated prepare-only replay against current catalog. No delivery, model, or Being state write.",
        recovery_omits_existing_exact_candidate=True, find_returns_exact_candidate=True,
        exact_open_succeeds=True, rows=rows)
    (args.out / "recovery.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / "probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
