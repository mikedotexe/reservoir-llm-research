#!/usr/bin/env bash
# Finite GPU correctness checks. Retained resources; no live files or windows.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-surface-renderer.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
task_resource_dir="$task_check_dir/resources"
python3 "$task_native_dir/stage-package.py" resources --repo "$task_native_dir/../.." \
    --destination "$task_resource_dir" --names data.json state-geometry.json state-replay.json state-replay.bin state-response.json
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/Evidence.swift" \
    "$task_source_dir/StateSurface.swift" \
    "$task_source_dir/StateSurfaceScene.swift" \
    "$task_source_dir/StateSurfaceProfiling.swift" \
    "$task_native_dir/Tests/StateSurfaceRendererChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" "$task_resource_dir"
