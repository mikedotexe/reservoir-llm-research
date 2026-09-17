#!/bin/bash
# Synthetic package identity qualification; existing core library required.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
python3 "$task_native_dir/Tests/PackageIdentityChecks.py"
