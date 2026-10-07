#!/bin/bash
# Renders synthetic geometry views; screenshots alone do not establish human acceptance.
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_output="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/geometry-bookmark-presentation}"
task_fixtures="$task_dir/Tests/Fixtures/geometry-bookmarks"
mkdir -p "$task_output"
python3 -B "$task_fixtures/generate.py" --check
xcrun swiftc -parse-as-library -swift-version 5 -target "$(uname -m)-apple-macosx14.0" \
  -framework AppKit -framework SwiftUI \
  "$task_dir/Sources/ReservoirScope/ResourceBundle.swift" \
  "$task_dir/Sources/ReservoirScope/GeometryBookmark.swift" \
  "$task_dir/Sources/ReservoirScope/GeometryBookmarkViewModel.swift" \
  "$task_dir/Sources/ReservoirScope/GeometryBookmarkView.swift" \
  "$task_dir/Tests/GeometryBookmarkPresentationChecks.swift" -o "$task_output/checks"
"$task_output/checks" "$task_fixtures/minime-synthetic-geometry.json" "$task_output"
