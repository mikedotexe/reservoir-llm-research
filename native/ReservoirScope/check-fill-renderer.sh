#!/usr/bin/env bash
# Finite GPU correctness checks; no windows, live files, remote hosts or benchmarks.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-renderer-checks.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/FillTransition.swift" \
    "$task_native_dir/Sources/ReservoirScope/ReservoirScene.swift" \
    "$task_native_dir/Tests/FillRendererChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift"
