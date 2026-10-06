"""Synthetic shared-reader + real Minime adapter interoperability, never live workspaces.

Usage: --reader <candidate helper> --minime-adapter <candidate repo> --out <new dir>
The Astrid lane uses the same helper protocol, not the full bridge scheduler.
"""
import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--minime-adapter", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.minime_adapter))
    StudyClient = importlib.import_module("minime_autonomy.source_study").StudyClient
    for owner in ("astrid", "minime"):
        with tempfile.TemporaryDirectory(prefix="geometry-fixture-") as directory:
            root = Path(directory)
            astrid, minime = root / "astrid", root / "minime"
            workspace = root / "owner-workspace"
            (astrid / "crates/example/src").mkdir(parents=True)
            (astrid / "crates/example/src/lib.rs").write_text("fn unrelated() {}\n")
            (minime / "workspace/runtime").mkdir(parents=True)
            workspace.mkdir()
            state = workspace / "diagnostics/source_first_v3/shared_reader"
            client = StudyClient(minime, workspace, astrid_root=astrid, executable=args.reader)

            def call(**operation):
                if owner == "minime":
                    return client.call(**operation)
                request = dict(astrid_root=str(astrid), minime_root=str(minime), state_directory=str(state),
                               runtime_workspace=str(workspace), being=owner, **operation)
                result = subprocess.run([str(args.reader)], input=json.dumps(request), text=True,
                                        capture_output=True, timeout=30, check=True)
                return json.loads(result.stdout)

            def prepare(action):
                return client.prepare(action).output if owner == "minime" else call(operation="prepare", action=action)

            def history():
                return json.loads((state / "reader-v1.json").read_text())["questions"]["entries"]["q1"]["geometry"]

            def geometry(operation, identifier=""):
                records = history()["records"]
                head = records[-1]["id"] if records else "empty"
                return prepare("SELF_STUDY GEOMETRY " + json.dumps(dict(question="q1", request_id=identifier,
                               expected_head=head, operation=operation)))

            def capture(second):
                now = int(time.time() * 1000)
                values = [math.sin(i * 0.23) * 0.4 + (0.1 if second else 0) for i in range(128)]
                offsets = [0, 1000, 3000]  # Explicit gap, not interpolated.
                frames = [dict(t_ms=(20000 if second else 10000) + dt,
                               wall_clock_unix_ms=now - (3000 if second else 11000) + dt,
                               activations=values, summary=dict(finite_fraction=1.0)) for dt in offsets]
                trace = dict(policy="esn_activation_trace_v1", reservoir_dim=128, sample_interval_ms=1000,
                             retained_secs=180, updated_at_unix_ms=frames[-1]["wall_clock_unix_ms"], frames=frames)
                (minime / "workspace/runtime/esn_activation_trace_v1.json").write_text(json.dumps(trace))
                return geometry(dict(kind="capture", seconds=10, note="Synthetic chosen interval B." if second else "Synthetic chosen interval A."), "b" if second else "a")

            prepare("SELF_STUDY QUESTION NEW Synthetic question: will the mean state remain nearby?")
            capture(False); a = history()["records"][-1]["id"]
            geometry(dict(kind="predict", baseline=a, maximum_rms_distance=0.05,
                          expectation="Synthetic expectation: mean-state RMS distance at most 0.05."), "prediction")
            prediction = history()["records"][-1]["id"]
            capture(True); b = history()["records"][-1]["id"]
            output = geometry(dict(kind="compare", prediction=prediction, observation=b), "comparison")
            entry = json.loads(history()["records"][-1]["body_json"])
            assert abs(entry["rms_distance"] - 0.1) < 1e-12 and not entry["threshold_met"]
            comparison = history()["records"][-1]["id"]
            geometry(dict(kind="revise", target=comparison,
                          text="Synthetic revision: the numerical threshold was not met; mechanism and experience remain unknown."), "revision")
            revision = history()["records"][-1]["id"]
            prepare("SELF_STUDY QUESTION PARK q1")
            unrelated = prepare("SELF_STUDY OPEN astrid/crates/example/src/lib.rs 1")
            assert "Synthetic revision:" not in unrelated["text"]
            prepare("SELF_STUDY QUESTION q1")
            output = geometry(dict(kind="show", id=revision))
            assert "Synthetic revision:" in output["text"] and output["input_kind"] == "geometry"
            request = json.dumps(dict(messages=[dict(role="user", content=output["text"])]))
            response = json.dumps(dict(message=dict(content="Synthetic response: still open."), done=True, done_reason="stop"))
            receipt = call(operation="navigation_delivered", navigation_id=output["navigation_id"], request_json=request, response_json=response)
            assert receipt["request_sha256"] == hashlib.sha256(request.encode()).hexdigest()
            geometry(dict(kind="export"))
            exported = next((state / "geometry-exports").glob("*.json")).read_bytes()
            (args.out / f"{owner}-synthetic-geometry.json").write_bytes(exported)
            print(f"{owner}: capture -> prediction -> capture -> comparison -> revision -> park -> unrelated page -> return -> verified delivery -> export PASS")


if __name__ == "__main__":
    main()
