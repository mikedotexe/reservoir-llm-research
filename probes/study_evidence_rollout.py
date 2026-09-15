"""Retain or verify this owning rollout's fixed evidence; no live writes or model calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT.parent / "worktrees/study-evidence-20260908"
OUT = ROOT / "research/outputs/2026-09-08-study-evidence-live"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify():
    manifest = json.loads((OUT / "manifest.json").read_text())
    for row in manifest["records"]:
        raw = (OUT / row["retained"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], row["retained"]
    for row in manifest["references"]:
        assert sha((ROOT / row["path"]).read_bytes()) == row["sha256"]
    replay = json.loads((OUT / "historical-replay.json").read_text())
    assert replay["all_report_content_fields_identical"]
    live_row = next(r for r in manifest["records"] if r["retained"].endswith("live-rollout.json"))
    live = json.loads((OUT / live_row["retained"]).read_text())
    for being, key, hashkey in (("bridge", "activation_receipt", "activation_receipt_sha256"),
                                ("minime", "receipt", "receipt_sha256")):
        receipt = next(r for r in manifest["records"] if r["source"] == live[being][key])
        assert receipt["sha256"] == live[being][hashkey]
    return dict(verified=True, records=len(manifest["records"]),
                manifest_sha256=sha((OUT / "manifest.json").read_bytes()))


def capture():
    assert not (OUT / "manifest.json").exists(), "Preserve the existing packet"
    live_path = ROOT.parent / "astrid/docs/steward-notes/study-evidence-validation/live-rollout.json"
    live = json.loads(live_path.read_text())
    paths = [live_path, live_path.with_name("validation.json"),
             ROOT.parent / "astrid/docs/steward-notes/2026-09-08-study-evidence-and-readable-overflow.md",
             Path(live["bridge"]["activation_receipt"]), Path(live["minime"]["receipt"]),
             TASK / "bridge-stage-01/manifest.json", TASK / "bridge-stage-01/source-inputs.json",
             TASK / "bridge-stage-01/build.log"]
    paths += [TASK / "evidence" / name for name in (
        "final-checks.json", "main-integration.json", "minime-pending-next-continuity.json",
        "minime-restored-next.log", "reader-smoke.json", "before-activation.json", "after-reloads.json",
        "minime-reload-refused-actor.jsonl", "controller-reload-hold.json", "verify_live.py",
        "research-final-tests.log", "minime-full-tests.log", "bridge-suite.log",
        "retained-overflow-final.log", "telemetry.jsonl")]
    paths += [ROOT / p for p in ("reservoir_research/study_capture.py", "reservoir_research/study_sequences.py",
                                "tests/test_study_sequences.py", "probes/study_evidence_rollout.py")]
    records = []

    def retain(source, raw, name):
        target = OUT / "retained" / name
        target.parent.mkdir(mode=0o700, exist_ok=True)
        with target.open("xb") as f:
            os.chmod(target, 0o600)
            f.write(raw)
        records.append(dict(source=str(source), retained=str(target.relative_to(OUT)),
                            bytes=len(raw), sha256=sha(raw)))

    for index, path in enumerate(paths):
        a = path.stat()
        assert a.st_size < 32 * 1024 * 1024 and not path.is_symlink()
        raw = path.read_bytes()
        b = path.stat()
        assert (a.st_size, a.st_mtime_ns, a.st_ino) == (b.st_size, b.st_mtime_ns, b.st_ino)
        retain(path, raw, f"{index:02d}-{path.name}")
    for name, commit in (("astrid", live["astrid_commit"]), ("minime", live["minime_commit"])):
        raw = subprocess.check_output(["git", "show", "--format=fuller", "--stat", "--patch", commit], cwd=ROOT.parent/name)
        retain(f"{name}:git:{commit}", raw, f"{name}-implementation.patch")
    for path in sorted(OUT.glob("*.json")):
        retain(path, path.read_bytes(), f"result-{path.name}")
    references = [ROOT / "research/outputs" / name for name in (
        "2026-09-08-study-evidence-first-capture/capture.json",
        "2026-09-08-study-evidence-first-report/report.json",
        "2026-09-08-study-after-follow-through/capture.json",
        "2026-09-08-study-after-follow-through-report/report.json")]
    value = dict(schema="study_evidence_rollout_retention_v1", captured_at=datetime.now(timezone.utc).isoformat(),
                 authority="research evidence only; no live control", records=records,
                 references=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p.read_bytes())) for p in references])
    (OUT / "manifest.json").write_text(json.dumps(value, indent=2)+"\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["capture"]:
        capture()
    elif sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: study_evidence_rollout.py capture|verify")
    print(json.dumps(verify(), indent=2))
