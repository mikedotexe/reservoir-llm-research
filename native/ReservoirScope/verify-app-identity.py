#!/usr/bin/env python3
"""Compatibility entry point for the authoritative packaged-identity verifier.

No build-cache layout or source Resources mirror is inferred. Pass --stage only
to additionally compare an explicitly selected frozen staged repository.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import sys

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    native=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app",type=Path,default=Path.home()/".cache/reservoir-research/ReservoirScope-build/current/Reservoir Scope.app")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--stage",type=Path)
    args=parser.parse_args()
    plist=plistlib.loads((args.app/"Contents/Info.plist").read_bytes())
    output=args.output or native/"validation"/plist["CFBundleShortVersionString"]/"artifact-identity.json"
    command=[sys.executable,str(native/"package-identity.py"),"verify","--app",str(args.app)]
    if args.stage:command+=["--stage",str(args.stage)]
    result=subprocess.run(command,capture_output=True,text=True)
    receipt={"verified_at_utc":datetime.now(timezone.utc).isoformat(),
        "version":plist["CFBundleShortVersionString"],"build":plist["CFBundleVersion"],
        "app_path":str(args.app),"binary_sha256":sha(args.app/"Contents/MacOS/ReservoirScope"),
        "essentials_runner_sha256":sha(args.app/"Contents/MacOS/essentials-run"),
        "packaged_identity_sha256":sha(args.app/"Contents/Resources/release-identity.json"),
        "verifier_sha256":sha(native/"package-identity.py"),
        "verification_exit_code":result.returncode,"verification_output":result.stdout+result.stderr,
        "explicit_staged_repository":str(args.stage) if args.stage else None,
        "scope":"Delegated package resource, runner and signature verification. Staged source comparison occurs only when --stage is explicitly supplied; no current checkout equivalence is inferred."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    if result.returncode:raise SystemExit(result.returncode)
if __name__=="__main__":main()
