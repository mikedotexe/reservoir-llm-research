#!/usr/bin/env python3
"""Finite research-native rehearsal. Python 3.12+; Cargo/Rust and local Metal.

Only retained esn/GPU/buffer/shader sources are compiled, never Minime's runtime.
Source sibling is read-only. Build products use a new steward temporary folder.
Run --prepare first to freeze the protocol before producing numerical outcomes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/outputs/2026-09-07-native-shaping-rehearsal"
SOURCE = ROOT.parent / "minime/minime"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare(output: Path, source: Path):
    output.mkdir(parents=True, exist_ok=True)
    if (output / "protocol.json").exists():
        raise RuntimeError("Protocol already frozen; choose a new output to prepare again")
    sources = ["src/esn.rs", "src/gpu.rs", "src/buffer_pool.rs", "shaders/esn.metal",
               "shaders/spectral.metal", "shaders/nn.metal", "Cargo.toml", "Cargo.lock"]
    records = []
    for relative in sources:
        original = source / relative
        data = original.read_bytes()
        retained = output / "source" / relative
        retained.parent.mkdir(parents=True, exist_ok=True)
        retained.write_bytes(data)
        records.append({"source": str(original), "retained": str(retained.relative_to(output)),
                        "sha256": sha(data), "bytes": len(data)})
    lock = tomllib.loads((source / "Cargo.lock").read_text())
    names = ["anyhow", "metal", "serde", "serde_json", "fastrand"]
    versions = {v["name"]: v["version"] for v in lock["package"] if v["name"] in names}
    manifest = '[package]\nname = "native-shaping-rehearsal"\nversion = "0.1.0"\nedition = "2021"\n\n[features]\ndivision-rehearsal = []\n\n[dependencies]\n'
    for name in names:
        manifest += (f'{name} = {{ version = "={versions[name]}", features = ["derive"] }}\n'
                     if name == "serde" else f'{name} = "={versions[name]}"\n')
    manifest += '\n[profile.release]\nopt-level = 3\n'
    (output / "harness-Cargo.toml").write_text(manifest)
    save(output / "source-manifest.json", {"captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
         "identity": "observed source bytes; no deployed-process identity or live checkpoint claimed",
         "files": records, "direct_dependency_versions": versions})
    protocol = {
        "schema": "research.native_shaping_rehearsal.protocol.v1",
        "registered_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "subject": "newly constructed 128-state/66-input research instance of exact copied native Minime ESN code on local Metal",
        "not_replayed": ["live Minime checkpoint", "512D sensory field", "sensory bus", "orchestration/stable-core controller", "language model", "triple-reservoir handles"],
        "source_manifest_sha256": sha((output / "source-manifest.json").read_bytes()),
        "native_state_dtype": "f32",
        "constructor_seed": 3517018368,
        "constructor": {"res_size": 128, "in_size": 66, "in_scale": 0.25, "res_density": 0.15,
                        "target_row_sum_radius_bound": 0.95, "leak_base": 0.35, "lambda_base": 0.999},
        "forcing": "input[t,i] = 0.15f32 * sin(((t*7+i*3) as f32)*0.071f32); explicit zero external recurrent drive; exact ordinary native realized noise and effective leak",
        "checkpoint_successful_boundaries": [24, 96, 192],
        "horizon_steps": 100,
        "parity_modes": ["synchronous_profile", "asynchronous_default"],
        "parity": {"state_max_abs_tolerance": 1e-6, "leak_noise_max_abs_tolerance": 0.0,
                   "snapshot_numeric_max_abs_tolerance": 1e-6,
                   "compare": ["ordinary parent vs JSON-restored ordinary checkpoint continuation", "ordinary parent vs step_shadow with captured forcing", "independent step_shadow clones"],
                   "exclude": "spectral.last_profile (wall timings, profiling diagnostics), and RNG equality for forced-noise shadow (draws intentionally bypassed)"},
        "intervention_mode": "synchronous_profile; run only after all synchronous parity gates pass",
        "directions": ["coordinate_0", "seeded_uniform_unit_vector", "checkpoint_spectral_eigenvector_unit"],
        "direction_seed": 20260907,
        "signed_l2_doses": [-0.01, -0.001, -0.0001, 0.0001, 0.001, 0.01],
        "one_shot_runs": 54,
        "sequence_runs": 6,
        "sequence": {"direction": "coordinate_0", "signed_l2_doses": [-0.001, 0.001],
                     "apply_boundaries": [0, 1, 2, 3, 4, 5, 6, 7], "release_boundary": 7,
                     "meaning": "eight finite checkpoint-boundary state edits followed by free continuation; distinct from single nudge"},
        "leak_override_checks": {"scope": "native ESN module only; not orchestration admission or live efficacy",
            "start_boundary": 24, "horizon_steps": 16,
            "cases": [{"id": "low_duration", "leak": 0.2, "duration": 3, "cancel_after": None},
                      {"id": "high_duration", "leak": 0.8, "duration": 3, "cancel_after": None},
                      {"id": "cancel_after_one", "leak": 0.8, "duration": 8, "cancel_after": 1},
                      {"id": "upper_clamps", "leak": 1.5, "duration": 99, "cancel_after": None},
                      {"id": "lower_clamps", "leak": -1.0, "duration": 0, "cancel_after": None}],
            "gates": "effective alpha equals clamped [.20,.90] request for clamped [1,12] duration; cancellation after one step; status remaining ticks; after release same next-step state as freshly cleared same-state checkpoint; ordinary paired RNG/noise equality"},
        "operation": "copy complete checkpoint, add signed f32 unit direction, clamp state to [-1,1], recompute geom_radius in source arithmetic, preserve geom_baseline history and other fields, restore exact source; this is a checkpoint-boundary intervention, not implemented live engine hook",
        "comparison": "paired step_shadow continuations retain native spectral adaptation but force identical realized noise/leak/input; surrounding controller absent",
        "return_threshold_fraction": 0.1,
        "return_dwell_boundaries": 8,
        "return_reference": "one-shot: actual initial displacement; sequence: separation immediately after final edit; search starts after last edit",
        "saturation": "count state coordinates exactly at +/-1 at every boundary; do not assert hidden preclip events",
        "retention": "all checkpoints, actual forcing, full paths, per-boundary spectral/geometry observables, actual edit receipts, failures and gate results",
        "finish_line": "report finite native-source parity and response outcomes; no subjective, live-state, full-controller or live-amplitude claim",
    }
    save(output / "protocol.json", protocol)
    print(json.dumps({"prepared": str(output), "protocol_sha256": sha((output / 'protocol.json').read_bytes())}))


def run(output: Path):
    protocol = output / "protocol.json"
    if not protocol.exists():
        raise RuntimeError("Run --prepare first")
    if (output / "results.json").exists():
        raise RuntimeError("Outcomes already exist; choose a new output for another run")
    provenance = json.loads((output / "source-manifest.json").read_text())
    for record in provenance["files"]:
        if sha((output / record["retained"]).read_bytes()) != record["sha256"]:
            raise RuntimeError("Retained source hash mismatch")
    build = Path(tempfile.mkdtemp(prefix="reservoir-native-shaping-"))
    shutil.copytree(output / "source/src", build / "src")
    shutil.copytree(output / "source/shaders", build / "shaders")
    shutil.copyfile(output / "harness-Cargo.toml", build / "Cargo.toml")
    shutil.copyfile(output / "source/Cargo.lock", build / "Cargo.lock")
    main = ROOT / "probes/native_shaping_rehearsal.rs"
    shutil.copyfile(main, build / "src/main.rs")
    (output / "retained-harness.rs").write_bytes(main.read_bytes())
    commands = [["cargo", "build", "--release", "--features", "division-rehearsal"],
                [str(build / "target/release/native-shaping-rehearsal"), str(protocol), str(output)]]
    receipt = {"build_directory": str(build), "protocol_sha256": sha(protocol.read_bytes()),
               "harness_sha256": sha(main.read_bytes()), "runner_sha256": sha(Path(__file__).read_bytes()),
               "platform": platform.platform(), "steps": []}
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(build / "target")
    for index, command in enumerate(commands):
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            proc = subprocess.run(command, cwd=build, env=environment, capture_output=True, text=True, timeout=300)
            (output / f"execution-{index}.log").write_text(proc.stdout + proc.stderr)
            receipt["steps"].append({"command": command, "started_at_utc": started,
                 "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "returncode": proc.returncode})
            save(output / "execution-receipt.json", receipt)
            print(proc.stdout[-4000:])
            if proc.returncode:
                print(proc.stderr[-5000:])
                raise SystemExit(proc.returncode)
        except subprocess.TimeoutExpired as exc:
            receipt["steps"].append({"command": command, "started_at_utc": started, "timed_out_seconds": 300})
            save(output / "execution-receipt.json", receipt)
            raise SystemExit("Finite execution deadline exceeded") from exc
    shutil.copyfile(build / "Cargo.lock", output / "resolved-Cargo.lock")
    receipt["rustc"] = subprocess.check_output(["rustc", "--version"], text=True).strip()
    receipt["cargo"] = subprocess.check_output(["cargo", "--version"], text=True).strip()
    receipt["binary_sha256"] = sha((build / "target/release/native-shaping-rehearsal").read_bytes())
    receipt["outputs"] = {str(p.relative_to(output)): sha(p.read_bytes()) for p in sorted(output.rglob("*.json")) if p.name != "execution-receipt.json"}
    save(output / "execution-receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT) and not args.output.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        parser.error("Output must be research-local or under steward temp")
    prepare(args.output.resolve(), args.source.resolve()) if args.prepare else run(args.output.resolve())
