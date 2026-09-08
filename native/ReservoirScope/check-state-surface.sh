#!/usr/bin/env bash
# Pure state-surface checks. Reads synthetic fixtures only, no live data.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-surface.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/StateSurface.swift" \
    "$task_native_dir/Tests/StateSurfaceChecks.swift" > "$task_check_dir/checks.swift"
xcrun swiftc -O -swift-version 6 "$task_check_dir/checks.swift" -o "$task_check_dir/checks"
"$task_check_dir/checks"
