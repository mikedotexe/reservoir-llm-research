"""Hash installed dependency files without importing model code or changing assets.

This supplementary receipt has its own observation time; it is not retroactively
part of an earlier frozen protocol. Bytecode caches are excluded because imports
may create them. Verification checks the same installed file identities.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

PACKAGES = ('mlx', 'mlx-metal', 'mlx-lm', 'numpy', 'transformers', 'tokenizers')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def capture():
    packages = {}
    for name in PACKAGES:
        distribution = importlib.metadata.distribution(name)
        files = {}
        for entry in distribution.files or []:
            if '__pycache__' in str(entry) or str(entry).endswith('.pyc'):
                continue
            path = Path(distribution.locate_file(entry)).resolve()
            if path.is_file():
                files[str(path)] = digest(path)
        packages[name] = dict(version=distribution.version, files=files)
    return dict(schema='contextual_dependency_receipt_v1', observed_unix=time.time(),
                scope='Installed distribution files excluding bytecode; observation begins at this receipt, not an earlier protocol freeze.',
                packages=packages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    current = capture()
    if args.verify:
        original = json.loads(args.receipt.read_text())
        unchanged = current['packages'] == original['packages']
        print(json.dumps(dict(dependencies_unchanged=unchanged, verified_unix=current['observed_unix'],
                              since_unix=original['observed_unix'])))
        raise SystemExit(0 if unchanged else 1)
    with args.receipt.open('x') as output:
        output.write(json.dumps(current, indent=2) + '\n')
    print(json.dumps({name:len(row['files']) for name,row in current['packages'].items()}))


if __name__ == '__main__':
    main()
