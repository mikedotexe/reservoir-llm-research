#!/usr/bin/env bash
# Pure measured-fill and presentation checks; reads no live telemetry or evidence.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-watermark-checks.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/FillWatermarks.swift" \
    "$task_native_dir/Tests/FillWatermarkChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift"
