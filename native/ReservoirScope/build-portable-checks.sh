#!/bin/bash
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_lib="$1"
task_out="$2"
mkdir -p "$task_out"
cat "$task_native_dir/Sources/ReservoirScope/ResourceBundle.swift" \
    "$task_native_dir/Sources/ReservoirScope/ExperimentStore.swift" \
    "$task_native_dir/Sources/ReservoirScope/ReplayClock.swift" \
    "$task_native_dir/Sources/ReservoirScope/EssentialsViewModel.swift" \
    "$task_native_dir/Sources/ReservoirScope/ExplorationViewModel.swift" \
    "$task_native_dir/Sources/ReservoirScope/ActionComparisonViewModel.swift" \
    "$task_native_dir/Tests/PortableStoreChecks.swift" > "$task_out/checks.swift"
xcrun swiftc -O -swift-version 6 -I "$task_lib" -L "$task_lib" -lEssentialsCore -framework Accelerate \
    "$task_out/checks.swift" -o "$task_out/portable-store-checks"
