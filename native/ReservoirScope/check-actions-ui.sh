#!/usr/bin/env bash
# Production MainActor lifecycle with controlled clocks and memory-only I/O.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_repo_dir="$(cd -- "$task_native_dir/../.." && pwd -P)"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-actions-ui.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT
if [[ $# -gt 0 ]]; then
  task_core_lib="$1"
else
  ESSENTIALS_BUILD_DIR="$task_check_dir/core" zsh "$task_repo_dir/essentials/build.sh" >/dev/null
  task_core_lib="$task_check_dir/core/lib"
fi
cat "$task_native_dir/Sources/ReservoirScope/ResourceBundle.swift" \
    "$task_native_dir/Sources/ReservoirScope/ExperimentStore.swift" \
    "$task_native_dir/Sources/ReservoirScope/ActionComparisonViewModel.swift" \
    "$task_native_dir/Tests/ActionComparisonViewModelChecks.swift" > "$task_check_dir/checks.swift"
xcrun swiftc -O -swift-version 6 -I "$task_core_lib" -L "$task_core_lib" -lEssentialsCore -framework Accelerate \
    "$task_check_dir/checks.swift" -o "$task_check_dir/checks"
"$task_check_dir/checks"
