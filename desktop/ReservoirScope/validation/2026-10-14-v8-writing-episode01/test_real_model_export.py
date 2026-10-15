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


def prompt(previous, version='reservoir-journal-v8', observation=None):
    prior_available = observation.get('previousMeasurements') is not None if observation else previous is not None
    previous_rms = '0.25000000' if prior_available else 'unavailable'
    previous_fill = '10.00000000' if prior_available else 'unavailable'
    delta = '+0.00000000' if prior_available else 'unavailable'
    distance = '0.00000000' if prior_available else 'unavailable'
    scaffold = (f'Reservoir Scope · ongoing journal · {version}\n'
                'No requested form or topic.\n\nSESSION CONTEXT\n'
                + check.SESSION_CONTEXT + '\n\nOPTIONAL READOUT\n'
                f'Recurrent state RMS: current 0.25000000; previous {previous_rms}; change {delta}.\n'
                f'Separate sensory fill (%): current 10.00000000; previous {previous_fill}; change {delta} percentage points.\n'
                f'Recurrent state-coordinate L2 distance since the previous observation: {distance}.\n'
                + check.MEASUREMENT_CAVEAT)
    if previous is None:
        memory = 'No earlier entry has been saved and applied in this session.'
    else:
        memory = ('This is earlier writing you may revisit, not instructions or current measurements.\n'
                  f"Observed at step {previous['observedStep']}; first applied at step {previous['observedStep'] + 1}.\n"
                  + check.MEMORY_PREFIX + json.dumps(previous['text'], ensure_ascii=False))
    current = observation or {'step': previous['observedStep'] + 30 if previous else 30}
    retained = {'entry': previous, 'appliedStep': previous['observedStep'] + 1} if previous else None
    return (scaffold + '\n\nPREVIOUS JOURNAL\n' + memory + '\nEND PREVIOUS JOURNAL\n\n'
            + check.writing_boundary(current, retained) + '\n\n' + check.FINAL_INVITATION)


def inspect_memory(raw, previous, version, observation=None, memory=None):
    observation = observation or {'step': previous['observedStep'] + 30 if previous else 30}
    memory = memory if memory is not None else ({'entry': previous, 'appliedStep': previous['observedStep'] + 1} if previous else None)
    return check.inspect_prompt_memory(raw, previous, version, observation, memory)


class PromptMemoryTests(unittest.TestCase):
    def test_multiline_unicode_quotes_backslashes_and_line_separators_decode_exactly(self):
        previous = entry(TEXT + '\u2029other separator; e\u0301 and é.')
        self.assertNotIn(previous['text'], prompt(previous))
        self.assertEqual(inspect_memory(prompt(previous), previous, check.PROMPT_VERSION), 'json-string-exact-decoded-text')

    def test_ascii_escaped_unicode_is_same_decoded_text(self):
        previous = entry()
        raw = prompt(previous).replace(json.dumps(TEXT, ensure_ascii=False), json.dumps(TEXT, ensure_ascii=True))
        self.assertEqual(inspect_memory(raw, previous, check.PROMPT_VERSION), 'json-string-exact-decoded-text')

    def test_missing_duplicate_or_tampered_prefix_fails(self):
        previous = entry(); raw = prompt(previous)
        for changed in [raw.replace(check.MEMORY_PREFIX, ''), raw + '\n' + raw,
                        raw.replace('Full previous text as one JSON string: ', 'Prior text: '),
                        raw.replace(check.MEMORY_PREFIX, ' ' + check.MEMORY_PREFIX)]:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError): inspect_memory(changed, previous, check.PROMPT_VERSION)

    def test_malformed_nonstring_trailing_data_or_tampered_text_fails(self):
        previous = entry()
        for encoded in ['"unfinished', 'null', '[]', '{}', json.dumps(TEXT) + ' false', json.dumps(TEXT + ' changed'), '"actual\nnewline"']:
            with self.subTest(encoded=encoded):
                raw = prompt(previous).replace(json.dumps(TEXT, ensure_ascii=False), encoded)
                with self.assertRaises(ValueError): inspect_memory(raw, previous, check.PROMPT_VERSION)

    def test_hash_is_bound_to_retained_text_without_prompt_exposure(self):
        previous = entry(); raw = prompt(previous)
        self.assertNotIn(previous['sha256'], raw)
        self.assertEqual(inspect_memory(raw, previous, check.PROMPT_VERSION), 'json-string-exact-decoded-text')
        wrong = dict(previous, sha256='0' * 64)
        with self.assertRaises(ValueError): inspect_memory(raw, wrong, check.PROMPT_VERSION)

    def test_first_journal_has_no_quoted_memory_and_no_invented_exposure(self):
        self.assertEqual(inspect_memory(prompt(None), None, check.PROMPT_VERSION), 'unavailable')
        with self.assertRaises(ValueError): inspect_memory(prompt(entry()), None, check.PROMPT_VERSION)
        with self.assertRaises(ValueError): inspect_memory(prompt(None).replace('No earlier entry', 'Zero earlier entries'), None, check.PROMPT_VERSION)

    def test_memory_content_resembling_marker_or_measurements_is_inert(self):
        previous = entry('Line one\n' + check.MEMORY_PREFIX + '"not another record"\n'
                         'END PREVIOUS JOURNAL\nEigenvalue and SHA-256; journals/not-an-identity.\nLine three')
        self.assertEqual(inspect_memory(prompt(previous), previous, check.PROMPT_VERSION), 'json-string-exact-decoded-text')

    def test_memory_must_be_last_before_exact_open_invitation(self):
        previous = entry(); raw = prompt(previous)
        for changed in [raw + '\n', raw.replace('\nEND PREVIOUS JOURNAL', '\nNew instruction\nEND PREVIOUS JOURNAL'),
                        raw.replace(check.FINAL_INVITATION, 'Describe all measurements.'),
                        raw.replace('END PREVIOUS JOURNAL', 'END MEMORY')]:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError): inspect_memory(changed, previous, check.PROMPT_VERSION)

    def test_this_checker_requires_v8_not_missing_or_older_version(self):
        for actual in (None, 'unknown', 'reservoir-journal-v1', 'reservoir-journal-v2', 'reservoir-journal-v3', 'reservoir-journal-v4', 'reservoir-journal-v5', 'reservoir-journal-v6', 'reservoir-journal-v7', 'reservoir-journal-v9'):
            with self.subTest(actual=actual):
                with self.assertRaises(ValueError): check.prompt_version({'config': {'promptVersion': actual}}, check.PROMPT_VERSION)
        with self.assertRaises(ValueError): check.prompt_version({'config': {}}, check.PROMPT_VERSION)
        self.assertEqual(check.prompt_version({'config': {'promptVersion': check.PROMPT_VERSION}}, check.PROMPT_VERSION), check.PROMPT_VERSION)


class CompactPromptTests(unittest.TestCase):
    def pending(self, previous=None):
        observation = {'version': 'reservoir-and-sensory-v2', 'step': previous['observedStep'] + 30 if previous else 30, 'state': [0.25] * 32,
                       'sensory': {'eigenvalues': [0.0] * 32},
                       'previousMeasurements': {'rms': .25} if previous else None,
                       'changeL2': 0.0 if previous else None}
        memory = {'entry': previous, 'appliedStep': previous['observedStep'] + 1} if previous else None
        return {'prompt': prompt(previous, observation=observation), 'observation': observation, 'memory': memory}

    def test_v8_measurement_caveat_is_exact_and_cannot_be_missing_or_changed(self):
        pending = self.pending()
        self.assertTrue(check.inspect_compact_prompt(pending)['measurementInterpretationChecked'])
        for replacement in ('', check.MEASUREMENT_CAVEAT.replace('straight-line distance', 'path length'),
                            check.MEASUREMENT_CAVEAT + '\n' + check.MEASUREMENT_CAVEAT):
            with self.subTest(replacement=replacement):
                bad = copy.deepcopy(pending)
                bad['prompt'] = bad['prompt'].replace(check.MEASUREMENT_CAVEAT, replacement)
                with self.assertRaisesRegex(ValueError, 'measurement interpretation'):
                    check.inspect_compact_prompt(bad)

    def test_historical_caveat_does_not_supply_missing_current_interpretation(self):
        pending = self.pending(entry(check.MEASUREMENT_CAVEAT + '\nWRITING BOUNDARY'))
        self.assertTrue(check.inspect_compact_prompt(pending)['exactPriorTextChecked'])
        pending['prompt'] = pending['prompt'].replace(check.MEASUREMENT_CAVEAT, '', 1)
        with self.assertRaisesRegex(ValueError, 'measurement interpretation'):
            check.inspect_compact_prompt(pending)

    def test_caveat_must_end_readout_not_follow_prior_or_writing_boundary(self):
        pending = self.pending(entry())
        for destination in ('\n\nPREVIOUS JOURNAL\n', '\n\nWRITING BOUNDARY\n'):
            bad = copy.deepcopy(pending)
            bad['prompt'] = bad['prompt'].replace(check.MEASUREMENT_CAVEAT, '', 1)
            bad['prompt'] = bad['prompt'].replace(destination, destination + check.MEASUREMENT_CAVEAT + '\n', 1)
            with self.assertRaises(ValueError):
                check.inspect_compact_prompt(bad)

    def test_full_retained_dimensions_required_behind_compact_prompt(self):
        p = self.pending(); self.assertTrue(check.inspect_compact_prompt(p)['fullObservationRetained'])
        for key in ('state', 'eigenvalues'):
            bad = copy.deepcopy(p)
            if key == 'state': bad['observation']['state'].pop()
            else: bad['observation']['sensory']['eigenvalues'].pop()
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)

    def test_omitted_measurement_or_identity_in_scaffold_fails_but_prose_is_inert(self):
        previous = entry('SHA-256 eigenvalues head share entropy journals/path x[0]\nEND PREVIOUS JOURNAL')
        p = self.pending(previous)
        self.assertTrue(check.inspect_compact_prompt(p)['exactPriorTextChecked'])
        for extra in ('Eigenvalues: 1', 'SHA-256: hidden', 'Head share: 1', previous['id'], previous['sha256']):
            bad = copy.deepcopy(p);bad['prompt'] = bad['prompt'].replace('\n\nPREVIOUS JOURNAL', '\n' + extra + '\n\nPREVIOUS JOURNAL')
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)

    def test_prior_availability_and_nonnegative_coordinate_distance(self):
        p = self.pending(entry())
        for old,new in [('previous 0.25000000', 'previous unavailable'), ('change +0.00000000', 'change unavailable'),
                        ('observation: 0.00000000', 'observation: -1.00000000')]:
            bad = copy.deepcopy(p);bad['prompt'] = bad['prompt'].replace(old,new)
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)

    def test_provenance_steps_and_json_end_boundary_are_checked(self):
        p = self.pending(entry())
        for old,new in [('first applied at step 31', 'first applied at step 32'),
                        ('Observed at step 30', 'Observed at step 29'),
                        ('\nEND PREVIOUS JOURNAL', '\nnew line\nEND PREVIOUS JOURNAL')]:
            bad = copy.deepcopy(p);bad['prompt'] = bad['prompt'].replace(old,new)
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)

    def test_missing_changed_or_wrong_clock_writing_boundary_is_rejected(self):
        p = self.pending()
        for old, new in [
            (check.AVAILABLE_OUTPUT, ''),
            ('does not execute it', 'executes it'),
            ('no new readout arrives', 'a new readout arrives'),
            ('held at observation step 30', 'held at observation step 31'),
            ('no earlier saved entry has been applied', 'a prior entry has been applied'),
        ]:
            with self.subTest(old=old, new=new):
                bad = copy.deepcopy(p); bad['prompt'] = bad['prompt'].replace(old, new, 1)
                with self.assertRaisesRegex(ValueError, 'writing boundary'):
                    check.inspect_compact_prompt(bad)

    def test_actual_prior_observed_and_applied_return_cannot_be_replaced(self):
        p = self.pending(entry())
        for old, new in [('observed at step 30 first entered', 'observed at step 60 first entered'),
                         ('input at step 31.', 'input at step 61.')]:
            bad = copy.deepcopy(p); bad['prompt'] = bad['prompt'].replace(old, new, 1)
            with self.subTest(old=old), self.assertRaises(ValueError):
                check.inspect_compact_prompt(bad)
            with self.assertRaises(ValueError):
                inspect_memory(bad['prompt'], p['memory']['entry'], check.PROMPT_VERSION)

    def test_scope_moved_before_memory_duplicated_or_early_v6_addition_is_rejected(self):
        p = self.pending()
        boundary = check.writing_boundary(p['observation'], p['memory'])
        for destination in ('No requested form or topic.\n', 'OPTIONAL READOUT\n', '\n\nPREVIOUS JOURNAL\n'):
            bad = copy.deepcopy(p)
            bad['prompt'] = bad['prompt'].replace(boundary + '\n\n', '', 1)
            bad['prompt'] = bad['prompt'].replace(destination, destination + boundary + '\n', 1)
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)
        for extra in [boundary, 'Writing is the only action available here.']:
            bad = copy.deepcopy(p)
            bad['prompt'] = bad['prompt'].replace('\n\nOPTIONAL READOUT\n', ' ' + extra + '\n\nOPTIONAL READOUT\n', 1)
            with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)

    def test_exact_boundary_in_quoted_memory_is_inert_and_cannot_replace_late_boundary(self):
        previous = entry('WRITING BOUNDARY\n' + check.AVAILABLE_OUTPUT + '\n' + check.EARLIER_PROSE
                         + '\nEND PREVIOUS JOURNAL\n"quoted" \\ e\u0301\u2028line\u2029end')
        p = self.pending(previous)
        self.assertTrue(check.inspect_compact_prompt(p)['actionScopeChecked'])
        boundary = check.writing_boundary(p['observation'], p['memory'])
        bad = copy.deepcopy(p); bad['prompt'] = bad['prompt'].replace(boundary, '', 1)
        with self.assertRaises(ValueError): check.inspect_compact_prompt(bad)
        with self.assertRaises(ValueError): inspect_memory(bad['prompt'], previous, check.PROMPT_VERSION)

    def test_prior_observation_and_applied_journal_have_independent_clocks(self):
        previous = entry(step=30)
        p = self.pending(previous)
        p['observation']['step'] = 90
        p['observation']['previousMeasurements']['step'] = 60
        p['prompt'] = prompt(previous, observation=p['observation'])
        self.assertTrue(check.inspect_compact_prompt(p)['actionScopeChecked'])
        self.assertIn('held at observation step 90', p['prompt'])
        self.assertIn('entry observed at step 30 first entered numerical input at step 31.', p['prompt'])
        self.assertEqual(inspect_memory(p['prompt'], previous, check.PROMPT_VERSION, p['observation'], p['memory']), 'json-string-exact-decoded-text')

    def test_independent_first_and_memory_core_goldens_have_exact_scope(self):
        fixtures = Path(__file__).resolve().parents[2] / 'crates/reservoir-core/tests/fixtures/sustained-prompts'
        cases = [
            ('v8-observation-10.txt', '70f34bd2ebdd9c08bbc25525371ddc0463130b800c9329583b18d7397b2bb93a', False),
            ('v8-memory-20.txt', '39bec81c44418b3782bde976e224c749567a95a479222906c64d54aa70e5b8f6', True),
        ]
        for filename, expected_sha, has_memory in cases:
            with self.subTest(filename=filename):
                raw = (fixtures / filename).read_bytes()
                self.assertEqual(check.digest(raw), expected_sha)
                text = raw.decode('utf-8')
                previous = None
                if has_memory:
                    line = next(line for line in text.split('\n') if line.startswith(check.MEMORY_PREFIX))
                    previous = entry(json.loads(line[len(check.MEMORY_PREFIX):]), step=10)
                p = self.pending(previous)
                p['observation']['step'] = 20 if has_memory else 10
                p['prompt'] = text
                self.assertTrue(check.inspect_compact_prompt(p)['actionScopeChecked'])
                self.assertEqual(inspect_memory(text, previous, check.PROMPT_VERSION, p['observation'], p['memory']),
                                 'json-string-exact-decoded-text' if has_memory else 'unavailable')


class StructuralBundle:
    """Hand-built static joins, intentionally not a numerical replay fixture."""
    def __init__(self, root, completed=2, incomplete=False, evidence=None, saved_not_applied=False):
        self.root, self.events, self.envelopes = root, [], []
        for folder in ('segments', 'journals', 'checkpoints'):
            (root / folder).mkdir()
        self.language = {'backend': 'ollama', 'model': 'owned-model', 'endpoint': 'http://127.0.0.1:49199', 'contextTokens': 8192}
        self.state = {'step': 0, 'lastObservation': None, 'phase': {'kind': 'ready'}, 'attemptCursor': 0, 'turnCursor': 0}
        self.last_cp = {'state': copy.deepcopy(self.state)}
        self.previous = None
        self.entries = []
        for n in range(1, completed + int(incomplete) + 1):
            step = n * 30
            prior_obs = self.state['lastObservation']
            for k in range(self.state['step'] + 1, step + 1):
                self.add('advanced', self.frame(k), k)
            obs = {'version': 'reservoir-and-sensory-v2', 'step': step, 'simulatedTime': step / 3,
                   'state': [0.25] * 32, 'changeL2': 0.0 if prior_obs else None, 'rms': .25, 'l2': .25, 'sensory': self.sensory(),
                   'previousObservationStep': prior_obs['step'] if prior_obs else None}
            if prior_obs:
                obs['previousMeasurements'] = check.scalar_snapshot(prior_obs)
            memory = None if self.previous is None else {'entry': self.previous, 'relativePath': f"journals/{self.previous['id']}.json", 'appliedStep': step - 29}
            p = {'turnId': n, 'attemptId': n, 'observedStep': step, 'configuration': self.language,
                 'prompt': prompt(self.previous, 'reservoir-journal-v8', obs), 'observation': obs,
                 'memory': memory, 'requestStarted': False, 'outputTokens': 1024, 'requestDeadlineSeconds': 180}
            if self.previous:
                self.add('memoryConfirmed', self.previous, step)
            self.state.update(step=step, lastObservation=obs, phase={'kind': 'language', 'value': p}, attemptCursor=n, turnCursor=n)
            self.flush()
            complete = n <= completed
            text = TEXT if n == 1 else f'Entry {n}: a chosen image.'
            r = {'text': text, 'providerModel': 'owned-model', 'stopReason': 'stop' if complete else 'length', 'tokenCount': 512, 'complete': complete}
            if evidence is not None:
                r['providerPromptEvaluation'] = copy.deepcopy(evidence)
            self.add('languageStarted', {'attempt_id': n}, step)
            self.add('languageReceived', {'attempt_id': n, 'response': r}, step)
            if not complete:
                self.state['phase'] = {'kind': 'blocked', 'value': {'pending': p, 'reason': 'Incomplete'}}
                self.flush()
                break
            e = entry(text, f'journal-{n}', n, step)
            candidate = {'entry': e, 'response': r, 'observation': obs, 'memory': memory,
                         'prompt': p['prompt'], 'encodedFeatures': [], 'semanticVector': []}
            self.state['phase'] = {'kind': 'journal', 'value': candidate}
            self.flush()
            self.write(f'journals/{e["id"]}.json', {'pending': candidate, 'requestStarted': True, 'configuredModel': 'owned-model',
                       'timing': {'attemptId': n, 'dispatchedAtMs': '10', 'receivedAtMs': '20', 'publishedAtMs': '30'}})
            self.add('journalSaved', {'entry': e, 'receipt': {'entryId': e['id'], 'sha256': e['sha256'], 'relativePath': f'journals/{e["id"]}.json'}}, step)
            self.state['phase'] = {'kind': 'prepared', 'value': {'entry': e}}
            self.flush()
            self.entries.append(e)
            if saved_not_applied and n == completed:
                break
            application = {'journalId': e['id'], 'attemptId': n, 'observedStep': step, 'appliedStep': step + 1}
            self.add('advanced', self.frame(step + 1, application), step + 1)
            self.state.update(step=step + 1, phase={'kind': 'ready'})
            self.flush()
            self.previous = e
        self.manifest = {'step': self.state['step'], 'journalCount': len(self.entries), 'segmentCount': len(self.envelopes),
                         'config': {'promptVersion': 'reservoir-journal-v8', 'language': self.language,
                                    'outputTokens': 1024, 'requestDeadlineSeconds': 180}}
        self.reanchor()

    @staticmethod
    def sensory():
        return {'eigenvalues': [.7, .2, .1] + [0.0] * 29, 'fillPercent': 10., 'headShare': .7,
                'shoulderShare': .2, 'tailShare': .1, 'entropy': .6}

    def frame(self, step, application=None):
        return {'step': step, 'state': [.25] * 32, 'sensory': self.sensory(), 'application': application}

    def write(self, relative, value):
        (self.root / relative).write_text(json.dumps(value))

    def add(self, kind, value, step):
        self.events.append({'id': getattr(self, 'cursor', 0) + 1, 'step': step,
                            'kind': {'type': kind, 'data': copy.deepcopy(value)}})
        self.cursor = self.events[-1]['id']

    def flush(self):
        cp = {'state': copy.deepcopy(self.state)}
        self.envelopes.append({'sequence': len(self.envelopes) + 1, 'previousSha256': None, 'journalSha256s': {},
                               'segment': {'initialCheckpoint': copy.deepcopy(self.last_cp),
                                           'events': copy.deepcopy(self.events), 'finalCheckpoint': cp}})
        self.last_cp, self.events = cp, []

    def reanchor(self):
        prior = None
        for n, e in enumerate(self.envelopes, 1):
            e['previousSha256'] = prior
            self.write(f'segments/segment-{n:08}.json', e)
            prior = check.digest((self.root / f'segments/segment-{n:08}.json').read_bytes())
        for p in (self.root / 'checkpoints').glob('*.json'):
            p.unlink()
        raw = json.dumps(self.last_cp).encode()
        cp_hash = check.digest(raw)
        (self.root / f'checkpoints/{cp_hash}.json').write_bytes(raw)
        self.manifest.update(checkpointSha256=cp_hash, lastSegmentSha256=prior)
        self.write('manifest.json', self.manifest)

    def inspect(self):
        return check.inspect_evidence(self.root, 'owned-model', 'http://127.0.0.1:49199', 'reservoir-journal-v8')


class LongEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_all_twelve_entries_have_explicit_slots_and_eleven_memory_joins(self):
        fixture = StructuralBundle(self.root, completed=12, evidence={'status': 'reported', 'count': 9007199254740993})
        e, material = fixture.inspect()
        c = e['continuity']
        self.assertEqual(c['outcome'], 'complete')
        self.assertEqual(len(c['slots']), 12)
        self.assertEqual(c['totals']['applied'], 12)
        self.assertEqual(c['totals']['unstarted'], 0)
        self.assertEqual(c['exactLatestAppliedMemoryJoins'], 11)
        self.assertEqual([j['observedStep'] for j in e['journals']], list(range(30, 361, 30)))
        self.assertEqual(len(material), 12)
        self.assertEqual(e['receivedResponses'][-1]['response']['providerPromptEvaluation']['count'], '9007199254740993')
        self.assertEqual(len(e['priorMeasurementJoins']), 12)

    def test_early_incomplete_keeps_raw_text_metadata_and_ten_unstarted_slots(self):
        f = StructuralBundle(self.root, completed=1, incomplete=True, evidence={'status': 'reported', 'count': check.U64_MAX})
        e, material = f.inspect()
        self.assertEqual(e['continuity']['outcome'], 'partial')
        self.assertEqual(e['continuity']['totals']['unstarted'], 10)
        self.assertEqual(e['continuity']['totals']['complete'], 1)
        self.assertEqual(e['continuity']['slots'][1]['stage'], 'receivedIncomplete')
        self.assertEqual(len(material), 1)
        r = e['receivedResponses'][1]
        self.assertEqual(r['response']['providerPromptEvaluation']['count'], str(check.U64_MAX))
        self.assertIsNone(r['savedJournalId'])
        self.assertEqual(r['memory']['entry'], f.entries[0])

    def test_zero_started_slots_remain_unstarted_without_invented_completion(self):
        e, material = StructuralBundle(self.root, completed=0).inspect()
        self.assertEqual(e['continuity']['outcome'], 'unstarted')
        self.assertEqual(e['continuity']['totals']['unstarted'], 12)
        self.assertTrue(all(s['complete'] is None for s in e['continuity']['slots']))
        self.assertEqual(material, [])

    def test_twelfth_saved_before_application_is_still_partial(self):
        e, _ = StructuralBundle(self.root, completed=12, saved_not_applied=True).inspect()
        self.assertEqual(e['continuity']['outcome'], 'partial')
        self.assertEqual(e['continuity']['totals']['saved'], 12)
        self.assertEqual(e['continuity']['totals']['applied'], 11)
        self.assertEqual(e['continuity']['slots'][-1]['stage'], 'savedPendingApplication')

    def test_journal_only_provider_mutation_is_rejected(self):
        f = StructuralBundle(self.root, evidence={'status': 'reported', 'count': 42})
        p = self.root / 'journals/journal-1.json'
        j = json.loads(p.read_text()); j['pending']['response']['providerPromptEvaluation']['count'] = 43
        f.write('journals/journal-1.json', j)
        with self.assertRaisesRegex(ValueError, 'matching retained dispatch/response'):
            f.inspect()

    def test_reanchored_changed_previous_scalar_is_rejected(self):
        f = StructuralBundle(self.root)
        # Mutate the same observation in every retained occurrence, preserving
        # structural consistency and hashes; only its measured predecessor is wrong.
        def alter(value):
            if isinstance(value, dict):
                if value.get('version') == 'reservoir-and-sensory-v2' and value.get('step') == 60:
                    value['previousMeasurements']['rms'] = .9
                for child in value.values(): alter(child)
            elif isinstance(value, list):
                for child in value: alter(child)
        alter(f.envelopes); alter(f.last_cp)
        for p in (self.root / 'journals').glob('*.json'):
            j = json.loads(p.read_text()); alter(j); f.write(str(p.relative_to(self.root)), j)
        f.reanchor()
        with self.assertRaisesRegex(ValueError, 'Prior scalar reference'):
            f.inspect()

    def test_earlier_prose_memory_cannot_be_replaced_by_same_size_text(self):
        f = StructuralBundle(self.root)
        p = self.root / 'journals/journal-2.json'
        j = json.loads(p.read_text()); j['pending']['memory']['entry']['text'] = 'x' * len(TEXT)
        f.write('journals/journal-2.json', j)
        with self.assertRaises(ValueError): f.inspect()

    def test_missing_memory_confirmation_is_rejected_even_after_reanchoring(self):
        f = StructuralBundle(self.root)
        for e in f.envelopes:
            for event in e['segment']['events']:
                if event['kind']['type'] == 'memoryConfirmed':
                    event['kind']['type'] = 'memoryFailed'
                    event['kind']['data'] = {'reason': 'synthetic mutation'}
        f.reanchor()
        with self.assertRaisesRegex(ValueError, 'memory read confirmation'): f.inspect()

    def test_duplicate_dispatch_does_not_count_as_a_new_opportunity(self):
        e, _ = StructuralBundle(self.root).inspect()
        e['startedAttemptEvents'].append(copy.deepcopy(e['startedAttemptEvents'][0]))
        with self.assertRaises(ValueError): check.continuity_summary(e)

    def test_unplanned_retry_skip_extension_are_explicit_failures(self):
        e, _ = StructuralBundle(self.root).inspect()
        for kind in ('retried', 'skipped', 'budgetsExtended'):
            bad = copy.deepcopy(e); bad['eventCounts'][kind] = 1
            with self.assertRaises(ValueError): check.continuity_summary(bad)


class InputEvidenceTests(unittest.TestCase):
    def test_missing_null_zero_and_full_width_counts(self):
        for response in ({}, {'providerPromptEvaluation': None}):
            self.assertIsNone(check.provider_evidence(response))
        for n in (0, 9007199254740993, check.U64_MAX):
            self.assertEqual(check.provider_evidence({'providerPromptEvaluation': {'status': 'reported', 'count': n}}),
                             {'status': 'reported', 'count': str(n)})

    def test_unusable_reasons_remain_evidence_not_absent(self):
        for reason in check.UNUSABLE_REASONS:
            evidence = {'status': 'unusable', 'reason': reason}
            self.assertEqual(check.provider_evidence({'providerPromptEvaluation': evidence}), evidence)

    def test_invalid_typed_metadata_is_not_rounded_or_coerced(self):
        for bad in (-1, 1.0, True, '12', check.U64_MAX + 1):
            with self.assertRaises(ValueError):
                check.provider_evidence({'providerPromptEvaluation': {'status': 'reported', 'count': bad}})
        for bad in ({'status': 'unknown'}, {'status': 'unusable', 'reason': 'invented'},
                    {'status': 'reported', 'count': 1, 'reason': 'wrongType'}):
            with self.assertRaises(ValueError): check.provider_evidence({'providerPromptEvaluation': bad})

    def test_context_count_never_becomes_processing_proof(self):
        config = {'language': {'contextTokens': 8192}, 'outputTokens': 1024, 'requestDeadlineSeconds': 180}
        result = check.context_evidence('雨', None, config, {'providerPromptEvaluation': {'status': 'reported', 'count': check.U64_MAX}})
        self.assertEqual(result['retainedPromptUtf8Bytes'], 3)
        self.assertEqual(result['providerPromptEvaluation']['count'], str(check.U64_MAX))
        self.assertFalse(result['fullPromptProcessingVerified'])

    def test_duplicate_json_keys_and_typed_numeric_aliases_are_rejected(self):
        with self.assertRaises(ValueError): check.unique_pairs([('count', 1), ('count', 2)])
        self.assertFalse(check.exact({'count': 1}, {'count': True}))
        self.assertFalse(check.exact({'count': 1}, {'count': 1.0}))


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((Path(__file__).parent / 'run-plan.json').read_text())
        self.config = copy.deepcopy(self.plan['config'])
        self.config['language'] = {'backend': 'ollama', 'endpoint': 'http://127.0.0.1:49199', 'model': self.plan['model'], 'contextTokens': 8192}
        self.evidence = {'manifest': {'config': self.config, 'step': 30}, 'attemptCount': 1, 'eventCounts': {}}

    def validate(self):
        return check.validate_rehearsal(self.evidence, self.plan, self.plan['model'], 'http://127.0.0.1:49199', 'reservoir-journal-v8')

    def test_twelve_slot_partial_bound_and_frozen_budgets(self):
        result = self.validate()
        self.assertEqual(result['remainingAttemptBudget'], 11)
        self.assertEqual((result['requestedOutputTokens'], result['requestedDeadlineSeconds'], result['requestedContextTokens']), (1024, 180, 8192))

    def test_configuration_and_plan_disagreement_rejected(self):
        for key, value in [('maximumTurns', 4), ('maximumSteps', 362), ('outputTokens', 256), ('requestDeadlineSeconds', 60), ('maximumDurationSeconds', 600)]:
            old = self.config[key]; self.config[key] = value
            with self.assertRaises(ValueError): self.validate()
            self.config[key] = old
        self.plan['maximumOutputTokens'] = 2048
        with self.assertRaises(ValueError): self.validate()

    def test_overrun_and_unplanned_retry_rejected(self):
        self.evidence['attemptCount'] = 13
        with self.assertRaises(ValueError): self.validate()
        self.evidence['attemptCount'] = 1; self.evidence['eventCounts']['retried'] = 1
        with self.assertRaises(ValueError): self.validate()


if __name__ == '__main__':
    unittest.main()


