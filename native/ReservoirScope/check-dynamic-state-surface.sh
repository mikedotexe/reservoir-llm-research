#!/usr/bin/env bash
# Synthetic CPU/GPU correctness and retained offscreen images. No live inputs.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-dynamic-surface.XXXXXX")"
task_output="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/ReservoirScope-validation/dynamic-nodes}"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/StateSurface.swift" \
    "$task_native_dir/Sources/ReservoirScope/StateSurfaceScene.swift" \
    "$task_native_dir/Tests/DynamicStateSurfaceChecks.swift" > "$task_check_dir/checks.swift"
xcrun swiftc -O -swift-version 6 "$task_check_dir/checks.swift" -o "$task_check_dir/checks"
"$task_check_dir/checks" "$task_output"
