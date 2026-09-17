#!/bin/zsh
# Stage a coherent native + ../../essentials package; never compile or install.
set -euo pipefail
task_source_dir="${1:?Pass the native source directory}"
task_staged_root="${2:?Pass the staged repository root}"
task_repo_dir="${task_source_dir:A:h:h}"
python3 "$task_source_dir/stage-package.py" stage --repo "$task_repo_dir" --destination "$task_staged_root"
