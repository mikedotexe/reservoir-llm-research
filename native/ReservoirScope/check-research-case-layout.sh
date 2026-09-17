#!/bin/bash
set -euo pipefail
task_dir="$(cd "$(dirname "$0")" && pwd)"
task_root="$(cd "$task_dir/../.." && pwd)"
task_core="${CORE_LIB:-${ESSENTIALS_BUILD_DIR:-$HOME/.cache/reservoir-research/ReservoirScope-build/essentials}/lib}"
task_output="${OUTPUT_DIR:-${1:-$HOME/.cache/reservoir-research/research-case-layout}}"
mkdir -p "$task_output"
xcrun swiftc -parse-as-library -swift-version 5 -target arm64-apple-macosx14.0 -I "$task_core" -L "$task_core" -lEssentialsCore -framework Accelerate -framework AppKit -framework SwiftUI "$task_dir/Sources/ReservoirScope/ResearchCase.swift" "$task_dir/Sources/ReservoirScope/ResearchCaseView.swift" "$task_dir/Sources/ReservoirScope/LocalModelReadiness.swift" "$task_dir/Tests/ResearchCasePresentationChecks.swift" -o "$task_output/checks"
"$task_output/checks" "$task_root/research/examples/research-cases-v1.json" "$task_output"
