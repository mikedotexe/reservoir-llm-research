#!/usr/bin/env bash
# Pure source-clock memory checks; reads no live telemetry or evidence.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-watermark-memory-checks.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/FillWatermarks.swift" \
    "$task_native_dir/Sources/ReservoirScope/FillWatermarkMemory.swift" \
    "$task_native_dir/Tests/FillWatermarkMemoryChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift"
