#!/bin/zsh
# Build the shared research core and headless runner on local storage.
set -euo pipefail
task_dir="${0:A:h}"
task_cache="${ESSENTIALS_BUILD_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/Essentials-build}"
task_sources="$task_cache/sources"
mkdir -p "$task_sources" "$task_cache/lib" "$task_cache/bin"
for component in reservoir spectral_bridge llm regulation stages actions runner; do
  mkdir -p "$task_sources/$component"
  rsync -a --delete --include='*.swift' --exclude='*' "$task_dir/$component/" "$task_sources/$component/"
done
task_core_sources=("$task_sources"/{reservoir,spectral_bridge,llm,regulation,stages,actions}/*.swift)
swiftc -parse-as-library -swift-version 5 -O -module-name EssentialsCore \
  -target "$(uname -m)-apple-macosx14.0" -emit-library -static -emit-module \
  -emit-module-path "$task_cache/lib/EssentialsCore.swiftmodule" \
  "${task_core_sources[@]}" -framework Accelerate -o "$task_cache/lib/libEssentialsCore.a"
swiftc -parse-as-library -swift-version 5 -O -target "$(uname -m)-apple-macosx14.0" \
  -I "$task_cache/lib" -L "$task_cache/lib" -lEssentialsCore -framework Accelerate \
  "$task_sources"/runner/*.swift -o "$task_cache/bin/essentials-run"
print -r -- "$task_cache/bin/essentials-run"
