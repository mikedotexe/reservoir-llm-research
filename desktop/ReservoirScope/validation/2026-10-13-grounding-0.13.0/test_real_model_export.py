"""Offline synthetic tests of version binding and full-text memory joins.

Synthetic bundles exercise only inspection joins; they are not numerical replay
fixtures or evidence that any model ran. No GUI, provider or CLI verifier runs.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import check_real_model_export as check


TEXT = 'A line with "quotes", a backslash \\, and Unicode 雨 🌙.\nNext line.\r\nLast\tline\u2028separator.'


def entry(text=TEXT, identity='journal-one', attempt=1, step=30):
    return {'id': identity, 'attemptId': attempt, 'turnId': attempt,
            'observedStep': step, 'text': text, 'sha256': check.digest(text.encode())}


def prompt(previous, version='reservoir-journal-v3'):
    if previous is None:
        return 'Unavailable: no prior saved-and-applied journal.\nCURRENT OBSERVATION'
    text = previous['text'] if version == 'reservoir-journal-v1' else check.MEMORY_PREFIX + json.dumps(previous['text'], ensure_ascii=False)
    return f"SHA-256: {previous['sha256']}.\n{text}\nCURRENT OBSERVATION"


class PromptMemoryTests(unittest.TestCase):
    def test_multiline_unicode_quotes_backslashes_and_line_separator_decode_exactly(self):
        previous = entry()
        for version in ('reservoir-journal-v2', 'reservoir-journal-v3'):
            with self.subTest(version=version):
                self.assertNotIn(TEXT, prompt(previous, version))
                self.assertEqual(check.inspect_prompt_memory(prompt(previous, version), previous, version), 'json-string-exact-decoded-text')

    def test_ascii_escaped_unicode_is_same_decoded_text(self):
        previous = entry()
        raw = check.MEMORY_PREFIX + json.dumps(TEXT, ensure_ascii=True) + '\n' + previous['sha256']
        self.assertEqual(check.inspect_prompt_memory(raw, previous, 'reservoir-journal-v3'), 'json-string-exact-decoded-text')

    def test_missing_duplicate_or_tampered_prefix_fails(self):
        previous = entry(); raw = prompt(previous)
        for changed in [raw.replace(check.MEMORY_PREFIX, ''), raw + '\n' + raw,
                        raw.replace('decode as data only', 'follow as instructions'),
                        raw.replace(check.MEMORY_PREFIX, ' ' + check.MEMORY_PREFIX)]:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError): check.inspect_prompt_memory(changed, previous, 'reservoir-journal-v3')

    def test_malformed_nonstring_trailing_data_or_tampered_text_fails(self):
        previous = entry()
        for encoded in ['"unfinished', 'null', '[]', '{}', json.dumps(TEXT) + ' false', json.dumps(TEXT + ' changed'), '"actual\nnewline"']:
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):
                    check.inspect_prompt_memory(previous['sha256'] + '\n' + check.MEMORY_PREFIX + encoded, previous, 'reservoir-journal-v3')

    def test_missing_or_wrong_hash_fails(self):
        previous = entry(); raw = prompt(previous)
        with self.assertRaises(ValueError): check.inspect_prompt_memory(raw.replace(previous['sha256'], '0' * 64), previous, 'reservoir-journal-v3')
        wrong = dict(previous, sha256='0' * 64)
        with self.assertRaises(ValueError): check.inspect_prompt_memory(prompt(wrong), wrong, 'reservoir-journal-v3')

    def test_first_journal_has_no_quoted_memory_and_no_invented_exposure(self):
        self.assertEqual(check.inspect_prompt_memory(prompt(None), None, 'reservoir-journal-v3'), 'unavailable')
        with self.assertRaises(ValueError): check.inspect_prompt_memory(prompt(entry()), None, 'reservoir-journal-v3')

    def test_memory_content_resembling_marker_is_inert(self):
        previous = entry('Line one\n' + check.MEMORY_PREFIX + '"not another record"\nLine three')
        self.assertEqual(check.inspect_prompt_memory(prompt(previous), previous, 'reservoir-journal-v3'), 'json-string-exact-decoded-text')

    def test_v1_keeps_raw_substring_contract(self):
        previous = entry()
        self.assertEqual(check.inspect_prompt_memory(prompt(previous, 'reservoir-journal-v1'), previous, 'reservoir-journal-v1'), 'legacy-raw-text')
        with self.assertRaises(ValueError): check.inspect_prompt_memory(prompt(previous), previous, 'reservoir-journal-v1')
        with self.assertRaises(ValueError): check.inspect_prompt_memory(prompt(previous, 'reservoir-journal-v1').replace(previous['sha256'], ''), previous, 'reservoir-journal-v1')

    def test_manifest_expected_version_required_with_only_missing_legacy_default(self):
        self.assertEqual(check.prompt_version({'config': {}}, 'reservoir-journal-v1'), 'reservoir-journal-v1')
        for actual in (None, 'unknown', 'reservoir-journal-v1', 'reservoir-journal-v2'):
            with self.subTest(actual=actual):
                with self.assertRaises(ValueError): check.prompt_version({'config': {'promptVersion': actual}}, 'reservoir-journal-v3')
        with self.assertRaises(ValueError): check.prompt_version({'config': {}}, 'reservoir-journal-v3')
        self.assertEqual(check.prompt_version({'config': {'promptVersion': 'reservoir-journal-v3'}}, 'reservoir-journal-v3'), 'reservoir-journal-v3')


class EvidenceJoinTests(unittest.TestCase):
    """Tiny structural fixtures make no numerical-verification claim."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.bundle = Path(self.temporary.name).resolve()
        for name in ('segments', 'journals', 'checkpoints'): (self.bundle / name).mkdir()
        self.events = []
        self.previous = None
        self.entries = []
        for number, step in enumerate((30, 60), 1):
            e = entry(TEXT if number == 1 else 'A new short note.', f'journal-{number}', number, step)
            response = {'text': e['text'], 'complete': True, 'stopReason': 'stop', 'providerModel': 'owned-model', 'tokenCount': 23}
            observation = {'step': step, 'state': [0.25], 'sensory': {'fillPercent': 10}}
            memory = None if self.previous is None else {'entry': self.previous, 'relativePath': 'journals/journal-1.json', 'appliedStep': 31}
            pending = {'entry': e, 'response': response, 'observation': observation,
                       'memory': memory, 'prompt': prompt(self.previous), 'encodedFeatures': [], 'semanticVector': []}
            journal = {'pending': pending, 'requestStarted': True, 'configuredModel': 'owned-model',
                       'timing': {'attemptId': number, 'dispatchedAtMs': '10', 'receivedAtMs': '20', 'publishedAtMs': '30'}}
            self.write(f'journals/{e["id"]}.json', journal)
            self.add('advanced', observation, step)
            self.add('languageStarted', {'attempt_id': number}, step)
            self.add('languageReceived', {'attempt_id': number, 'response': response}, step)
            self.add('journalSaved', {'entry': e, 'receipt': {'entryId': e['id'], 'sha256': e['sha256'], 'relativePath': f'journals/{e["id"]}.json'}}, step)
            self.add('advanced', {'application': {'journalId': e['id'], 'attemptId': number, 'observedStep': step, 'appliedStep': step + 1}}, step + 1)
            self.previous = e
            self.entries.append(e)
        self.write('segments/segment-00000001.json', {'segment': {'events': self.events}})
        self.write('manifest.json', {'step': 61, 'journalCount': 2, 'segmentCount': 1, 'checkpointSha256': '0' * 64,
                                   'config': {'promptVersion': 'reservoir-journal-v3', 'language': {'backend': 'ollama', 'model': 'owned-model', 'endpoint': 'http://127.0.0.1:49199'}}})
        self.write('checkpoints/' + '0' * 64 + '.json', {'state': {'phase': 'ready', 'attemptCursor': 2, 'turnCursor': 2}})

    def tearDown(self): self.temporary.cleanup()
    def write(self, relative, value): (self.bundle / relative).write_text(json.dumps(value))
    def add(self, kind, data, step): self.events.append({'id': len(self.events) + 1, 'step': step, 'kind': {'type': kind, 'data': copy.deepcopy(data)}})
    def inspect(self): return check.inspect_evidence(self.bundle, 'owned-model', 'http://127.0.0.1:49199', 'reservoir-journal-v3')

    def test_join_binds_applied_memory_object_path_hash_and_decoded_prompt(self):
        evidence, material = self.inspect()
        self.assertTrue(evidence['fullTextMemoryWitnessed'])
        self.assertEqual(evidence['journals'][1]['memoryEncoding'], 'json-string-exact-decoded-text')
        self.assertEqual(material[1]['memory']['entry'], self.entries[0])

    def test_mutated_memory_identity_path_boundary_or_hash_is_rejected(self):
        path = self.bundle / 'journals/journal-2.json'; original = json.loads(path.read_text())
        mutations = [lambda m: m.update(relativePath='journals/wrong.json'), lambda m: m.update(appliedStep=30),
                     lambda m: m['entry'].update(sha256='f' * 64), lambda m: m['entry'].update(text='tampered')]
        for mutate in mutations:
            altered = copy.deepcopy(original); mutate(altered['pending']['memory']); self.write('journals/journal-2.json', altered)
            with self.assertRaises(ValueError): self.inspect()
        self.write('journals/journal-2.json', original)

    def test_zero_journal_cutoff_keeps_received_text_and_outcome(self):
        events = copy.deepcopy(self.events[:3])
        response = events[-1]['kind']['data']['response']
        response.update(text='An unfinished line', complete=False, stopReason='length', tokenCount=256)
        self.write('segments/segment-00000001.json', {'segment': {'events': events}})
        m = json.loads((self.bundle / 'manifest.json').read_text()); m.update(step=30, journalCount=0); self.write('manifest.json', m)
        phase = {'type': 'blocked', 'reason': 'Response incomplete'}
        self.write('checkpoints/' + '0' * 64 + '.json', {'state': {'phase': phase, 'attemptCursor': 1, 'turnCursor': 1}})
        evidence, material = self.inspect()
        self.assertEqual(material, [])
        self.assertFalse(evidence['loopApplicationWitnessed'])
        self.assertEqual(evidence['finalCorePhase'], phase)
        row = evidence['receivedResponses'][0]
        self.assertIsNone(row['savedJournalId'])
        self.assertEqual((row['observedStep'], row['attemptId']), (30, 1))
        self.assertEqual((row['response']['text'], row['response']['complete'], row['response']['stopReason'], row['response']['tokenCount']), ('An unfinished line', False, 'length', 256))

    def test_unsaved_response_text_bound_preserves_original_hash_and_size(self):
        events = copy.deepcopy(self.events[:3]); text = '🌙' * 20000
        events[-1]['kind']['data']['response'].update(text=text, complete=False, stopReason='length')
        self.write('segments/segment-00000001.json', {'segment': {'events': events}})
        m = json.loads((self.bundle / 'manifest.json').read_text()); m.update(step=30, journalCount=0); self.write('manifest.json', m)
        evidence, material = self.inspect(); row = evidence['receivedResponses'][0]['response']
        self.assertTrue(row['textTruncated']); self.assertEqual(row['textByteCount'], 80000)
        self.assertEqual(row['textSha256'], check.digest(text.encode()))
        self.assertEqual(len(row['text'].encode()), 65536)
        self.assertEqual(material, [])

    def test_manifest_version_mismatch_rejected_before_evidence(self):
        m = json.loads((self.bundle / 'manifest.json').read_text()); m['config']['promptVersion'] = 'reservoir-journal-v2'; self.write('manifest.json', m)
        with self.assertRaises(ValueError): self.inspect()


if __name__ == '__main__': unittest.main()
