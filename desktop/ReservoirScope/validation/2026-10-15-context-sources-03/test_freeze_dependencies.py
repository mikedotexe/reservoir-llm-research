"""File-only regression for explicit evidence/product dependency classification."""
import json
from pathlib import Path
import unittest
from dependency_partition import partition_prior_refs
from prepare_window import identity

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]


class DependencyPartitionTests(unittest.TestCase):
    def test_actual_four_core_validation_receipts_are_retained_and_exact(self):
        reuse = json.loads((HERE / 'runtime-copy-01.json').read_text())
        prior = json.loads(Path(reuse['priorFreeze']['path']).read_text())
        retained, historical = partition_prior_refs(prior['files'], DESKTOP)
        expected = {'2026-10-11-exploration-oracles.json', '2026-10-11-swift-stage-roundtrip.json',
                    '2026-10-11-unicode-actions-v1.json', '2026-10-11-unicode-actions-v2.json'}
        core_evidence = [r for r in retained if Path(r['path']).parent == DESKTOP / 'crates/reservoir-core/validation']
        self.assertEqual({Path(r['path']).name for r in core_evidence}, expected)
        for ref in retained: self.assertEqual(ref, identity(ref['path']))
        self.assertEqual(len(retained) + len(historical), len(prior['files']))
        self.assertTrue(all('/validation/' not in r['path'] and '/target/' not in r['path'] for r in historical))

    def test_qa_runtime_and_cache_references_are_never_historical_product(self):
        refs = [dict(path=str(DESKTOP / 'target/qa' / name), bytes=1, sha256='test')
                for name in ('owned-run/launch-intent.json', 'models/stage-receipt.json', 'pinned/verifier')]
        retained, historical = partition_prior_refs(refs, DESKTOP)
        self.assertEqual(retained, refs); self.assertEqual(historical, [])

    def test_explicit_source_and_contract_roots_are_historical(self):
        paths = (DESKTOP / 'src/App.tsx', DESKTOP / 'src-tauri/src/sustained.rs',
                 DESKTOP / 'crates/reservoir-core/src/sustained.rs', DESKTOP / 'Cargo.lock',
                 DESKTOP.parents[1] / 'shared/reservoir-scope/continuing-writing.md')
        refs = [dict(path=str(p), bytes=1, sha256='test') for p in paths]
        retained, historical = partition_prior_refs(refs, DESKTOP)
        self.assertEqual(retained, []); self.assertEqual(historical, refs)

    def test_unknown_and_duplicate_paths_are_not_silently_excluded(self):
        for path in (Path('/tmp/unclassified-runtime.json'), DESKTOP / 'target/release/unknown-runtime'):
            with self.assertRaisesRegex(ValueError, 'Unclassified'):
                partition_prior_refs([dict(path=str(path))], DESKTOP)
        ref = dict(path=str(DESKTOP / 'src/App.tsx'))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            partition_prior_refs([ref, ref], DESKTOP)


if __name__ == '__main__':
    unittest.main()
