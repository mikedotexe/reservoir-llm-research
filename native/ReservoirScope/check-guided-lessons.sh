#!/bin/bash
# Pure cursor evidence checks against explicitly selected bundled fixtures.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_lib="$1"
task_examples="$2"
task_output="$3"
mkdir -p "$task_output"
cat "$task_native_dir/Sources/ReservoirScope/GuidedLessons.swift" "$task_native_dir/Tests/GuidedLessonChecks.swift" > "$task_output/checks.swift"
xcrun swiftc -parse-as-library -O -swift-version 6 -I "$task_lib" -L "$task_lib" -lEssentialsCore -framework Accelerate "$task_output/checks.swift" -o "$task_output/checks"
"$task_output/checks" "$task_examples" "$task_examples/guided-lessons.json"
