#!/usr/bin/env bash
# Retained captures and synthetic temporary fixtures only; no live-system reads.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-surface-data.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
task_resource_dir="$task_check_dir/resources"
python3 "$task_native_dir/stage-package.py" resources --repo "$task_native_dir/../.." \
    --destination "$task_resource_dir" --names data.json state-geometry.json state-replay.json state-replay.bin state-response.json
mkdir -p "$task_check_dir/fixtures"
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/Evidence.swift" \
    "$task_source_dir/LiveState.swift" \
    "$task_native_dir/Tests/StateSurfaceDataChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" \
    "$task_resource_dir" "$task_check_dir/fixtures"
