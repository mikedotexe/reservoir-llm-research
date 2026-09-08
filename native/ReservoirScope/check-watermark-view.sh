#!/usr/bin/env bash
# Finite offscreen SwiftUI render checks. No windows, live telemetry, or preferences.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-watermark-view.XXXXXX")"
task_output_dir="${1:-$task_native_dir/validation/0.7.1/watermark-view}"
trap 'rm -rf -- "$task_check_dir"' EXIT
mkdir -p "$task_output_dir"
python3 - "$task_native_dir" "$task_check_dir" "$task_output_dir" <<'PY'
import hashlib
import json
import pathlib
import sys

native_dir, check_dir, output_dir = map(pathlib.Path, sys.argv[1:])
scene_path = native_dir / "Sources/ReservoirScope/ReservoirScene.swift"
scene = scene_path.read_bytes()
start = scene.index(b"enum ReferenceLens {")
end = scene.index(b"\n/// Native Metal view.", start)
lens = scene[start:end]
assert lens.rstrip().endswith(b"}"), "ReferenceLens extraction no longer ends at its declaration"
paths = [native_dir / "Sources/ReservoirScope/FillWatermarks.swift",
         native_dir / "Sources/ReservoirScope/FillWatermarkMemory.swift",
         native_dir / "Sources/ReservoirScope/ReferenceWatermarksView.swift",
         native_dir / "Tests/WatermarkViewChecks.swift"]
captured = {path: path.read_bytes() for path in paths}
captured[scene_path] = scene
parts = [captured[paths[0]], captured[paths[1]], lens, captured[paths[2]], captured[paths[3]]]
combined = b"\n".join(parts)
(check_dir / "checks.swift").write_bytes(combined)
source_hashes = {str(path.relative_to(native_dir)): hashlib.sha256(captured[path]).hexdigest()
                 for path in paths + [scene_path]}
source_hashes["ReferenceLens exact extracted bytes"] = hashlib.sha256(lens).hexdigest()
source_hashes["Staged combined Swift source"] = hashlib.sha256(combined).hexdigest()
(output_dir / "sources.json").write_text(json.dumps({
    "scope": "Synthetic measured fills; exact production aging model, watermark view and lens geometry; offscreen only",
    "source_hashes": source_hashes,
}, indent=2) + "\n")
PY
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" "$task_output_dir"
