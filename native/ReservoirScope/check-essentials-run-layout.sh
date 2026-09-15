#!/usr/bin/env bash
# Actual 300-step Run and timer-driven Stop in a native AppKit event loop.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_cache="${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research"
task_core_lib="${1:-$task_cache/ReservoirScope-build/essentials/lib}"
task_output="${2:-$task_cache/ReservoirScope-validation/essentials-run-layout}"
python3 - "$task_native_dir" "$task_core_lib" "$task_output" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys,time
native,lib,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
source=native/'Sources/ReservoirScope'
paths=[source/name for name in ['ResourceBundle.swift','ReplayClock.swift','StateSurface.swift',
    'StateSurfaceScene.swift','EssentialsViewModel.swift','EssentialsExperience.swift']]
paths.append(native/'Tests/EssentialsRunLayoutChecks.swift')
fixture=native.parent.parent/'essentials/examples/essentials-stage-4.json'
assembled=out/'checks.swift'
source_bytes={str(path):path.read_bytes() for path in paths}
assembled.write_bytes(b'\n'.join(source_bytes.values()))
binary=out/'checks'
command=['xcrun','swiftc','-O','-swift-version','5','-I',str(lib),'-L',str(lib),
    '-lEssentialsCore','-framework','Accelerate',str(assembled),'-o',str(binary)]
build=subprocess.run(command,capture_output=True,text=True)
(out/'build.log').write_text(build.stdout+build.stderr)
if build.returncode:
    print(build.stderr); raise SystemExit(build.returncode)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
identity={'sources':{path:hashlib.sha256(data).hexdigest() for path,data in source_bytes.items()},
    'fixture_sha256':sha(fixture),'core_library_sha256':sha(lib/'libEssentialsCore.a'),
    'executable_sha256':sha(binary)}
statuses={}
for mode in ['complete','stop']:
    start=time.monotonic()
    try:
        run=subprocess.run([str(binary),str(fixture),str(out/f'{mode}.json'),mode],
            capture_output=True,text=True,timeout=60)
        log=run.stdout+run.stderr
        status={'exit_code':run.returncode,'timed_out':False,'elapsed_seconds':time.monotonic()-start}
    except subprocess.TimeoutExpired as error:
        log=(error.stdout or b'').decode()+(error.stderr or b'').decode()
        status={'exit_code':124,'timed_out':True,'elapsed_seconds':time.monotonic()-start}
    (out/f'{mode}.log').write_text(log)
    statuses[mode]=status
    (out/'receipt.json').write_text(json.dumps({'identity':identity,'status':statuses},indent=2,sort_keys=True)+'\n')
    print('\n'.join(log.splitlines()[-2:]),flush=True)
    print(json.dumps({mode:status}),flush=True)
    if status['exit_code']: raise SystemExit(status['exit_code'])
print(out)
PY
