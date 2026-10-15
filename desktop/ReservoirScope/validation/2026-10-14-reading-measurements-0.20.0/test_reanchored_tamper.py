"""Pure temporary-file tests; production verifier execution is explicitly mocked."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

T = load('tamper', HERE / 'check_reanchored_tamper.py')
F = load('fixture_tests', HERE / 'test_check_fixture_export.py')


def write_json(path, value):
    path.write_bytes(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())


def make_bundle(path):
    """Anchor-consistent miniature, not a valid numerical session/qualification."""
    path.mkdir()
    for directory in ('journals', 'segments', 'checkpoints'):
        (path / directory).mkdir()
    hashes = []
    helper = F.InspectionHelpers()
    for number, text in [(1, None), (2, 'Quoted "data" \\ e\u0301\u2028\u2029\nWRITING BOUNDARY')]:
        pending = helper.pending(text)
        pending['entry'] = {'id': f'entry-{number}', 'attemptId': number}
        journal = path / 'journals' / f'entry-{number}.json'
        write_json(journal, {'pending': pending})
        hashes.append(T.C.sha(journal.read_bytes()))
    checkpoint = b'{"state":{"step":20,"seed":18446744073709551615},"sha256":"typed-state-placeholder"}'
    cp_hash = T.C.sha(checkpoint)
    (path / 'checkpoints' / (cp_hash + '.json')).write_bytes(checkpoint)
    (path / 'checkpoints' / 'previous.json').write_bytes(b'{"prior":true}')
    previous = None
    for number in range(1, 4):
        anchors = {} if number == 3 else {f'entry-{number}': hashes[number - 1]}
        link = {'sequence': number, 'previousSha256': previous,
                'journalSha256s': anchors, 'segment': None}
        raw = json.dumps(link, separators=(',', ':')).encode().replace(
            b'"segment":null',
            b'"segment": {"exactFloat":1.0000000000000002,"signedZero":-0.0,"wide":18446744073709551615,"clock":1e-09}')
        segment = path / 'segments' / f'segment-{number:08}.json'
        segment.write_bytes(raw)
        previous = T.C.sha(raw)
    write_json(path / 'manifest.json', {'config': {'promptVersion': T.C.PROMPT_VERSION},
               'segmentCount': 3, 'lastSegmentSha256': previous, 'checkpointSha256': cp_hash})
    T.check_anchors(path)
    return path


class TamperHelpers(unittest.TestCase):
    def test_all_seven_mutations_reanchor_and_preserve_original_and_core_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = make_bundle(root / 'original')
            before = T.C.inventory(original)
            for case in T.CASES:
                with self.subTest(case=case):
                    target = root / case
                    details = T.mutate_copy(original, target, case)
                    T.check_anchors(target)
                    self.assertTrue(details['allByteAnchorsConsistent'])
                    self.assertEqual(before, T.C.inventory(original))
                    for path in (original / 'checkpoints').iterdir():
                        self.assertEqual(path.read_bytes(), (target / 'checkpoints' / path.name).read_bytes())
                    for path in (original / 'segments').iterdir():
                        self.assertEqual(T.raw_json_field(path.read_bytes(), 'segment'),
                                         T.raw_json_field((target / 'segments' / path.name).read_bytes(), 'segment'))
                    if case == 'manifest-version':
                        self.assertEqual(details['expectedDiagnostic'], T.CHAIN_DIAGNOSTIC)
                        self.assertEqual(T.C.decode((target / 'manifest.json').read_bytes())['config']['promptVersion'], 'reservoir-journal-v7')
                    else:
                        self.assertEqual(details['journalByteAnchorsRecomputed'], 1)
                        self.assertEqual(details['expectedDiagnostic'], T.JOURNAL_DIAGNOSTIC)
                        journal = T.C.decode((target / 'journals' / details['journal']).read_bytes())
                        with self.assertRaises(ValueError):
                            T.C.check_compact_prompt(journal['pending'])

    def test_measurement_caveat_removal_preserves_all_other_prompt_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            original = make_bundle(Path(directory) / 'original')
            target = Path(directory) / 'negative'
            T.mutate_copy(original, target, 'measurement-caveat-removed')
            old = T.C.decode((original / 'journals/entry-1.json').read_bytes())['pending']
            new = T.C.decode((target / 'journals/entry-1.json').read_bytes())['pending']
            self.assertEqual(old['prompt'].replace(T.C.MEASUREMENT_CAVEAT, '', 1), new['prompt'])
            self.assertIn(T.C.writing_boundary(new['observation'], new['memory']), new['prompt'])
            self.assertEqual(old['memory'], new['memory'])
            self.assertEqual(old['observation'], new['observation'])
            self.assertEqual((original / 'journals/entry-2.json').read_bytes(),
                             (target / 'journals/entry-2.json').read_bytes())

    def test_recorded_return_changes_later_saved_receipt_not_prior_prose(self):
        with tempfile.TemporaryDirectory() as directory:
            original = make_bundle(Path(directory) / 'original')
            target = Path(directory) / 'negative'
            T.mutate_copy(original, target, 'recorded-return')
            old = T.C.decode((original / 'journals/entry-2.json').read_bytes())['pending']
            new = T.C.decode((target / 'journals/entry-2.json').read_bytes())['pending']
            self.assertEqual(old['memory'], new['memory'])
            self.assertEqual(old['observation'], new['observation'])
            self.assertEqual(old['prompt'].replace('input at step 11.', 'input at step 12.'), new['prompt'])
            self.assertEqual((original / 'journals/entry-1.json').read_bytes(), (target / 'journals/entry-1.json').read_bytes())

    def test_string_replacement_preserves_unrelated_bytes_and_exact_unicode(self):
        raw = b'{"prompt":"old", "wide":18446744073709551615,"x":-0.0}'
        text = '\n"quoted" \\ e\u0301\u2028\u2029'
        changed = T.replace_json_string(raw, 'prompt', 'old', text)
        self.assertEqual(T.C.decode(changed)['prompt'], text)
        self.assertTrue(changed.endswith(b', "wide":18446744073709551615,"x":-0.0}'))
        for malformed in [b'{"prompt":"a","prompt":"b"}', b'{"other":"old"}', b'{"prompt":"wrong"}']:
            with self.assertRaises(ValueError):
                T.replace_json_string(malformed, 'prompt', 'old', 'new')

    def test_hash_replacement_requires_unique_anchor(self):
        old, new = 'a' * 64, 'b' * 64
        for raw in [b'{}', json.dumps([old, old]).encode()]:
            with self.assertRaises(ValueError):
                T.replace_hash(raw, old, new)

    def test_existing_output_or_linked_bundle_member_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = make_bundle(root / 'original')
            target = root / 'existing'
            target.mkdir()
            with self.assertRaises(ValueError):
                T.mutate_copy(original, target, 'authority')
            (original / 'linked.json').symlink_to(original / 'manifest.json')
            with self.assertRaises(ValueError):
                T.mutate_copy(original, root / 'new', 'authority')
            self.assertFalse((root / 'new').exists())

    def test_wrong_anchor_and_noncontiguous_segment_filename_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            original = make_bundle(Path(directory) / 'original')
            segment = original / 'segments/segment-00000002.json'
            raw = segment.read_bytes()
            segment.write_bytes(raw + b' ')
            with self.assertRaisesRegex(ValueError, 'predecessor'):
                T.check_anchors(original)
            segment.write_bytes(raw)
            segment.rename(segment.with_name('segment-00000009.json'))
            with self.assertRaisesRegex(ValueError, 'contiguous'):
                T.check_anchors(original)

    def test_main_mocked_replay_runs_positive_before_and_after_and_preserves_failure(self):
        for wrong_diagnostic in (False, True):
            with self.subTest(wrong_diagnostic=wrong_diagnostic), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                original = make_bundle(root / 'original')
                here = root / 'validation/episode'
                here.mkdir(parents=True)
                (here / 'check_fixture_export.py').write_bytes(b'# mocked identity only\n')
                cli = root / 'fake-cli'
                cli.write_bytes(b'NOT AN EXECUTABLE: mocked subprocess only')
                output = root / 'target/qa/tamper-01'
                calls = []
                def replay(command, **kwargs):
                    calls.append(command)
                    name = Path(command[-1]).name
                    if name == 'original':
                        return subprocess.CompletedProcess(command, 0, b'{"status":"passed"}', b'')
                    diagnostic = ('wrong cause' if wrong_diagnostic else
                                  T.CHAIN_DIAGNOSTIC if name == 'manifest-version' else T.JOURNAL_DIAGNOSTIC)
                    return subprocess.CompletedProcess(command, 1, json.dumps({'error': diagnostic}).encode(), b'')
                args = ['checker', '--bundle', str(original), '--cli', str(cli),
                        '--expected-cli-sha256', T.C.sha(cli.read_bytes()), '--output-directory', str(output)]
                with patch.object(T, 'HERE', here), patch.object(T.subprocess, 'run', side_effect=replay), patch('sys.argv', args), contextlib.redirect_stdout(io.StringIO()):
                    result = T.main()
                report = json.loads((output / 'receipt.json').read_bytes())
                self.assertEqual(result, int(wrong_diagnostic))
                self.assertEqual(report['status'], 'failed' if wrong_diagnostic else 'passed')
                self.assertTrue(report['originalUnchanged'])
                self.assertTrue(report['executableUnchanged'])
                self.assertEqual(report['positiveAfter']['exitCode'], 0)
                self.assertEqual(Path(calls[0][-1]), original.resolve())
                self.assertEqual(Path(calls[-1][-1]), original.resolve())
                self.assertEqual(len(report['cases']), 1 if wrong_diagnostic else 7)
                if wrong_diagnostic:
                    self.assertIn('wrong cause', report['cases'][0]['stdout'])


if __name__ == '__main__':
    unittest.main()
