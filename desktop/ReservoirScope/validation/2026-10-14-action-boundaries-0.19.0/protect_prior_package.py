#!/usr/bin/env python3
"""Prospective pre-build preservation of 0.18 artifacts; never build or launch.

Run before replacing the current package path. This verifies the existing app,
exclusive historical archive and pinned CLI against the 0.18 receipt, then copies
the full app into an exclusive QA directory. It never changes the originals,
re-signs, deletes or invokes an application.
"""
import hashlib
import json
from pathlib import Path
import stat
import shutil
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
sys.path.insert(0, str(DESKTOP / 'scripts'))
from qualification_receipt import package_inventory


def sha(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Expected ordinary immutable artifact: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as stream:
        before = stream.seek(0, 2)
        stream.seek(0)
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    if path.stat().st_size != before:
        raise ValueError('Artifact size changed during read')
    return h.hexdigest()


def main():
    basis = HERE.parent / '2026-10-14-writing-scope-0.18.0/archive-check-01.json'
    value = json.loads(basis.read_text())
    report = {'schema': 'reservoir-prior-package-preservation-v1',
              'capturedAtUtc': datetime.now(timezone.utc).isoformat(),
              'basis': str(basis), 'basisSha256': sha(basis),
              'scope': 'Verify original app/archive/pin and create one exclusive full app copy; no process or application calls.'}
    with (HERE / 'prior-package-preserved-01.json').open('x') as stream:
        try:
            app = Path(value['app'])
            archive = Path(value['archive'])
            pin = Path(value['pinnedExecutable'])
            assert app == DESKTOP / 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app'
            assert archive.name == 'ReservoirScopeTauriPreview-0.18.0-macos-arm64.tar.gz'
            assert pin == DESKTOP / 'target/qa/0.18-pinned/reservoir-scope-desktop'
            observed = package_inventory(app)
            assert observed == value['package'], 'Installed old package differs'
            assert sha(archive) == value['archiveSha256'], 'Old archive differs'
            assert sha(pin) == value['executableSha256'], 'Old pin differs'
            preserved = DESKTOP / 'target/qa/0.18-preserved'
            preserved.mkdir(mode=0o700)  # Exclusive; partial copies remain evidence.
            preserved_app = preserved / app.name
            shutil.copytree(app, preserved_app, symlinks=True)
            assert package_inventory(preserved_app) == observed, 'Full preserved app differs'
            assert package_inventory(app) == observed, 'Original app changed during copy'
            assert sha(archive) == value['archiveSha256'], 'Old archive changed during copy'
            assert sha(pin) == value['executableSha256'], 'Old pin changed during copy'
            report.update(passed=True, package=observed, archive=str(archive),
                          archiveSha256=value['archiveSha256'], pinnedExecutable=str(pin),
                          executableSha256=value['executableSha256'],
                          preservedApp=str(preserved_app), fullAppCopyIdentical=True)
        except Exception as error:
            report.update(passed=False, error=f'{type(error).__name__}: {error}')
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': report['passed']}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
