"""Classify this prior diagnostic freeze; unknown input scopes fail closed."""
from pathlib import Path


def partition_prior_refs(refs, desktop):
    desktop = Path(desktop)
    repository = desktop.parents[1]
    core = desktop / 'crates/reservoir-core'
    # The four core validation receipts are historical evidence, not mutable code.
    evidence_roots = (desktop / 'validation', core / 'validation', desktop / 'target/qa')
    product_roots = (desktop / 'src', desktop / 'src-tauri', core,
                     repository / 'shared/reservoir-scope')
    product_files = {desktop / name for name in ('Cargo.lock', 'Cargo.toml', 'package-lock.json', 'package.json')}
    retained, historical = [], []
    seen = set()
    for ref in refs:
        path = Path(ref['path'])
        if not path.is_absolute() or '..' in path.parts or path in seen:
            raise ValueError(f'Noncanonical or duplicate historical reference: {path}')
        seen.add(path)
        if any(path.is_relative_to(root) for root in evidence_roots):
            retained.append(ref)
        elif path in product_files or any(path.is_relative_to(root) for root in product_roots):
            historical.append(ref)
        else:
            raise ValueError(f'Unclassified historical dependency: {path}')
    return retained, historical
