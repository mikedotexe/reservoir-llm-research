#!/bin/zsh
# Steward-side, finite offscreen rendering only. The optional --app bundle may
# be copied unchanged to another Mac to compare an identical executable/data.
set -euo pipefail
task_dir="${0:A:h}"
profile_app=""
profile_output="${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/profiles/$(date -u +%Y%m%dT%H%M%SZ)-reservoir-scope.json"
profile_extra=()
while (( $# > 0 )); do
  case "$1" in
    --app)
      (( $# >= 2 )) || { print -u2 -- 'Missing --app path'; exit 2; }
      profile_app="$2"; shift 2 ;;
    --output)
      (( $# >= 2 )) || { print -u2 -- 'Missing --output path'; exit 2; }
      profile_output="$2"; shift 2 ;;
    --width|--height|--warmups|--frames)
      (( $# >= 2 )) || { print -u2 -- "Missing $1 value"; exit 2; }
      profile_extra+=("--profile-${1#--}" "$2"); shift 2 ;;
    --help|-h)
      print -r -- 'Usage: profile-app.sh [--app "/path/Reservoir Scope.app"] [--output report.json] [--width 1280] [--height 800] [--warmups 8] [--frames 30]'
      print -r -- 'Without --app, builds the current viewer locally. With --app, uses that unchanged bundle. JSON is written to --output and stdout.'
      exit 0 ;;
    *) print -u2 -- "Unknown option: $1"; exit 2 ;;
  esac
done
if [[ -z "$profile_app" ]]; then
  profile_app="$(/bin/zsh "$task_dir/build-app.sh")"
fi
profile_executable="$profile_app/Contents/MacOS/ReservoirScope"
[[ -x "$profile_executable" ]] || { print -u2 -- "No executable at $profile_executable"; exit 2; }
# The app itself hashes the executable and both bundled evidence files. Source
# hashes are optional context, not proof that an arbitrary --app used this tree.
profile_source_args=()
if [[ -d "$task_dir/Sources/ReservoirScope" ]]; then
  profile_source_args=(--profile-source-directory "$task_dir/Sources/ReservoirScope")
fi
exec "$profile_executable" --profile --profile-output "$profile_output" "${profile_source_args[@]}" "${profile_extra[@]}"
