#!/usr/bin/env python3
"""Verify the research viewer's staged sources, packaged evidence and signature.

Reads the viewer package only. It never opens a live producer or writes outside
an explicitly selected validation output directory.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    native = Path(__file__).resolve().parent
    root = native.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path.home()/'.cache/reservoir-research/ReservoirScope-build/current/Reservoir Scope.app')
    parser.add_argument('--output', type=Path, help='Defaults to validation/<packaged version>/artifact-identity.json')
    args = parser.parse_args()
    app = args.app
    staged = app.parents[1]/'package/Sources/ReservoirScope'
    plist = plistlib.loads((app/'Contents/Info.plist').read_bytes())
    output = args.output or native/'validation'/plist['CFBundleShortVersionString']/'artifact-identity.json'
    sources = {str(p.relative_to(root)): sha(p) for p in sorted((native/'Sources/ReservoirScope').glob('*.swift'))}
    resources = {p.name: sha(p) for p in sorted((native/'Sources/ReservoirScope/Resources').iterdir()) if p.is_file()}
    source_matches = all((staged/Path(p).name).exists() and sha(staged/Path(p).name) == h for p,h in sources.items())
    resource_matches = all((app/'Contents/Resources'/p).exists() and sha(app/'Contents/Resources'/p) == h for p,h in resources.items())
    sig = subprocess.run(['codesign','--verify','--deep','--strict',str(app)], text=True, capture_output=True)
    receipt = {
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'version': plist['CFBundleShortVersionString'], 'build': plist['CFBundleVersion'],
        'app_path': str(app), 'binary_sha256': sha(app/'Contents/MacOS/ReservoirScope'),
        'source_sha256': sources, 'resource_sha256': resources,
        'staged_source_count': len(sources), 'resource_count': len(resources),
        'staged_sources_match': source_matches, 'packaged_resources_match': resource_matches,
        'signature_verify_exit_code': sig.returncode, 'signature_verify_output': sig.stdout + sig.stderr,
        'verifier_sha256': sha(Path(__file__)),
        'qualification_status': 'final packaged-source identity check',
        'scope': 'Viewer packaging identity and signature only; consumer and runtime checks have separate receipts',
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2)+'\n')
    if not (source_matches and resource_matches and sig.returncode == 0):
        raise SystemExit('Viewer identity verification failed; inspect the retained receipt.')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['source_sha256','resource_sha256']}, indent=2))


if __name__ == '__main__':
    main()
