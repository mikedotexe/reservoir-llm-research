#!/usr/bin/env bash
# Finite GPU correctness checks. Retained resources; no live files or windows.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-surface-renderer.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/Evidence.swift" \
    "$task_source_dir/StateSurface.swift" \
    "$task_source_dir/StateSurfaceScene.swift" \
    "$task_source_dir/StateSurfaceProfiling.swift" \
    "$task_native_dir/Tests/StateSurfaceRendererChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" "$task_source_dir/Resources"
