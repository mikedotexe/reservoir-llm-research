#!/usr/bin/env bash
# Bounded native receipt consumer checks; no live source is opened.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-native-response.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
cat "$task_native_dir/Sources/ReservoirScope/NativeActionResponse.swift" \
    "$task_native_dir/Tests/NativeActionResponseChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" "$@"
