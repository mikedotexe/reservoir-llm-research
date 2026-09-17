#!/bin/bash
# Offline tests: mocked inventory transport and self-contained case verification.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_lib="$1"
task_output="$2"
mkdir -p "$task_output"
cat "$task_native_dir/Sources/ReservoirScope/ExperimentStore.swift" \
    "$task_native_dir/Sources/ReservoirScope/LocalModelReadiness.swift" \
    "$task_native_dir/Sources/ReservoirScope/ResearchCase.swift" \
    "$task_native_dir/Tests/ReadinessAndResearchCaseChecks.swift" > "$task_output/checks.swift"
xcrun swiftc -parse-as-library -O -swift-version 6 -I "$task_lib" -L "$task_lib" -lEssentialsCore -framework Accelerate "$task_output/checks.swift" -o "$task_output/checks"
if [[ $# -gt 2 ]]; then "$task_output/checks" "$3"; else "$task_output/checks"; fi
