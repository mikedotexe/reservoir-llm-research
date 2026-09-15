#!/usr/bin/env bash
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_check_dir="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/ReservoirScope-validation/shared-camera}"
python3 - "$task_native_dir" "$task_check_dir" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys,time
native,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
paths=[native/'Sources/ReservoirScope'/name for name in ['StateSurface.swift','StateSurfaceScene.swift']]
paths.append(native/'Tests/SharedStateSurfaceCameraChecks.swift')
sources={str(path):path.read_bytes() for path in paths}
assembled=out/'checks.swift'
assembled.write_bytes(b'\n'.join(sources.values()))
binary=out/'checks'
build=subprocess.run(['xcrun','swiftc','-O','-swift-version','5',str(assembled),'-o',str(binary)],capture_output=True,text=True)
(out/'build.log').write_text(build.stdout+build.stderr)
if build.returncode:
    print(build.stderr); raise SystemExit(build.returncode)
start=time.monotonic()
run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
(out/'run.log').write_text(run.stdout+run.stderr)
receipt={'identity':{'sources':{path:hashlib.sha256(data).hexdigest() for path,data in sources.items()},
    'executable_sha256':sha(binary)},'status':{'exit_code':run.returncode,'elapsed_seconds':time.monotonic()-start}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(run.stdout+run.stderr); print(out)
raise SystemExit(run.returncode)
PY
