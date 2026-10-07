#!/bin/bash
# Small offline state checks and workspace typecheck; no app build or UI launch.
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_root="$(cd -- "$task_dir/../.." && pwd -P)"
task_output="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/research-cases-workspace-checks}"
mkdir -p "$task_output"
task_sources="$task_dir/Sources/ReservoirScope"
xcrun swiftc -parse-as-library -swift-version 5 -target "$(uname -m)-apple-macosx14.0" \
  "$task_sources/ResourceBundle.swift" "$task_sources/ResearchCase.swift" \
  "$task_sources/ResearchCasesViewModel.swift" "$task_dir/Tests/ResearchCasesWorkspaceChecks.swift" \
  -o "$task_output/checks"
"$task_output/checks" "$task_root/research/examples/research-cases-v1.json"
xcrun swiftc -typecheck -parse-as-library -swift-version 5 -target "$(uname -m)-apple-macosx14.0" \
  "$task_sources/ResourceBundle.swift" "$task_sources/ResearchCase.swift" \
  "$task_sources/ResearchCasesViewModel.swift" "$task_sources/ResearchCaseView.swift" \
  "$task_sources/ResearchCasesWorkspace.swift"
