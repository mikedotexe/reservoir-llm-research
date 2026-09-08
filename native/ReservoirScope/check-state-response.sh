#!/usr/bin/env bash
# Research-local simulation resource and synthetic mutations only; no live reads.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-state-response.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/StateResponseExperience.swift" \
    "$task_native_dir/Tests/StateResponseChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 -D STATE_RESPONSE_DATA_CHECKS "$task_check_dir/checks.swift" \
    "$task_source_dir/Resources/state-response.json"
