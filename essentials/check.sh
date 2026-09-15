#!/bin/zsh
# Test only fresh, isolated research fixtures. No live services are contacted.
set -euo pipefail
task_dir="${0:A:h}"
task_cache="${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/Essentials-tests"
swift test --package-path "$task_dir" --scratch-path "$task_cache" "$@"
