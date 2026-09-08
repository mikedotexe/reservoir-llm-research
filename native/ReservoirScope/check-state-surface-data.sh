#!/usr/bin/env bash
# Retained captures and synthetic temporary fixtures only; no live-system reads.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-surface-data.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
mkdir -p "$task_check_dir/fixtures"
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/Evidence.swift" \
    "$task_source_dir/LiveState.swift" \
    "$task_native_dir/Tests/StateSurfaceDataChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" \
    "$task_source_dir/Resources" "$task_check_dir/fixtures"
