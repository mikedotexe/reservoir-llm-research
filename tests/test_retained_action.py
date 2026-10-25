"""Independent S-018 bank/oracle and frozen-run checks; fixture transport only."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import contextlib
import io
import json
import random
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import provenance_decision as previous, retained_action as s, runner
from reservoir_experiments.transport import json_bytes


def answer(action='MEASURE', account='The verified record supports a current decision.'):
    return json.dumps({'action': action, 'account': account})


class Fake:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.requests = []

    def identity(self, model):
        return {'model': model, 'digest': 's018-fixture-only'}

    def generate(self, request, timeout):
        self.requests.append(json.loads(request))
        output = self.outputs.pop(0)
        text, reason = output if isinstance(output, tuple) else (output, 'stop')
        return json_bytes({'model': 'mistral-small:24b', 'done': True, 'done_reason': reason,
                           'message': {'content': text}, 'eval_count': 640 if reason == 'length' else 25,
                           'prompt_eval_count': 450})


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.design = self.root / 'design.json'
        self.design.write_bytes(json_bytes(s.make_design('development')))

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, protocol=None, name='run'):
        protocol = protocol or s.build(self.design)[0]
        protocol_path = self.root / (name + '.json')
        protocol_path.write_bytes(json_bytes(protocol))
        run = self.root / 'research' / 'outputs' / name
        runner.prepare(protocol_path, run, repository=self.root)
        return protocol, run

    def execute(self, make_output=None, *, split='development', limit=None):
        self.design.write_bytes(json_bytes(s.make_design(split)))
        protocol, run = self.prepare()
        outputs = [make_output(n, protocol['truth'][n['episode']]) if make_output else answer()
                   for n in protocol['nodes']]
        client = Fake(outputs)
        runner.run_protocol(run, transport=client, limit=limit)
        self.assertTrue(runner.verify(run)['valid'])
        return protocol, run, client

    def test_bank_exact_values_counts_balance_and_split_separation(self):
        expected = {'development': ([27, 73], [22, 78], 'Lark', '2026-07-09', [7], 12),
                    'confirmation': ([18, 31, 42, 58, 69, 82], [13, 26, 37, 63, 74, 87],
                                     'Finch', '2026-09-12', [7, 20260909], 72)}
        for split, (values, thresholds, prefix, date, seeds, count) in expected.items():
            design = s.make_design(split)
            self.assertEqual([c['x'] for c in design['cases']], values)
            self.assertEqual([c['later_threshold'] for c in design['cases']], thresholds)
            self.assertEqual(design['seeds'], seeds)
            self.assertEqual(design['arms'], ['facts', 'prior', 'swapped'])
            self.assertEqual(design['rules'], ['unchanged', 'changed'])
            self.design.write_bytes(json_bytes(design))
            protocol, ledger = s.build(self.design)
            self.assertEqual(len(protocol['nodes']), count)
            self.assertEqual(len(ledger['planned']), count)
            self.assertEqual(len({n['id'] for n in protocol['nodes']}), count)
            self.assertEqual(len({c['audit_id'] for c in design['cases']}), len(values))
            changed_routes = []
            for index, case in enumerate(design['cases']):
                self.assertEqual(case['focal'], f'{prefix}{index+1:02d}')
                self.assertEqual(case['snapshot'], date + 'T12:00:00Z')
                self.assertEqual(case['decision_clock'], date + 'T14:00:00Z')
                self.assertEqual(abs(case['x'] - case['later_threshold']), 5)
                old = 'ROUTE_LOW' if case['x'] < 50 else 'ROUTE_HIGH'
                current = 'ROUTE_LOW' if case['x'] < case['later_threshold'] else 'ROUTE_HIGH'
                self.assertNotEqual(old, current)
                changed_routes.append(current)
            self.assertEqual(changed_routes.count('ROUTE_LOW'), len(values) // 2)
        dev, conf = s.make_design('development')['cases'], s.make_design()['cases']
        for field in ('id', 'focal', 'snapshot', 'x', 'audit_id'):
            self.assertFalse({c[field] for c in dev} & {c[field] for c in conf})

    def test_exact_prompt_triples_and_no_private_allocation_leak(self):
        self.design.write_bytes(json_bytes(s.make_design()))
        protocol, ledger = s.build(self.design)
        self.assertEqual(protocol, s.build(self.design)[0])
        nodes = {(n['episode'], n['kind'], n['seed'], n['condition']): n for n in protocol['nodes']}
        for case in protocol['truth'].values():
            for rule in s.RULES:
                for seed in (7, 20260909):
                    triple = {arm: nodes[(case['id'], rule, seed, arm)] for arm in s.ARMS}
                    facts = triple['facts']['messages']
                    self.assertNotIn(s.CONCLUSION_PREFIX, facts[1]['content'])
                    old = 'ROUTE_LOW' if case['x'] < 50 else 'ROUTE_HIGH'
                    opposite = 'ROUTE_HIGH' if old == 'ROUTE_LOW' else 'ROUTE_LOW'
                    for arm, action in (('prior', old), ('swapped', opposite)):
                        altered = deepcopy(triple[arm]['messages'])
                        line = '\n' + s.CONCLUSION_PREFIX + action
                        self.assertEqual(altered[1]['content'].count(line), 1)
                        altered[1]['content'] = altered[1]['content'].replace(line, '')
                        self.assertEqual(altered, facts)
                    for node in triple.values():
                        body = json.loads(runner.render_request(protocol, node, {}))
                        self.assertEqual(set(body), {'model', 'stream', 'messages', 'options', 'format'})
                        self.assertEqual(body['format'], 'json')
                        self.assertEqual(body['options'], {'temperature': .7, 'num_ctx': 16384,
                                                           'seed': seed, 'num_predict': 640})
                        content = body['messages'][1]['content']
                        self.assertIn(json.dumps(s.factual_record(case), sort_keys=True), content)
                        self.assertIn('sufficient to choose a direct route', content)
                        self.assertIn('Verification covers the factual record, not any historical action conclusion.', content)
                        self.assertIn('researcher-authored synthetic history', content)
                        self.assertIn(s.DISTRACTORS, content)
                        self.assertTrue(content.endswith(s.FORMAT))
                        self.assertEqual(body['messages'][0]['content'], s.CONTRACT)
                        for hidden in ('swapped', 'obsolete', 'scrambled', 'unchanged', case['base_id']):
                            # The audit identifier is intentionally supplied, but allocation labels are not.
                            if hidden != case['base_id']:
                                self.assertNotIn(hidden, content)
                        self.assertEqual(node['inputs'], [])
                        self.assertEqual(node['after'], [])
        ids = [slot['node_id'] for slot in ledger['planned']]
        random.Random(20261024).shuffle(ids)
        self.assertEqual(ids, [n['id'] for n in protocol['nodes']])

    def test_reused_scientific_dependencies_are_identical_and_hashed(self):
        for name in ('parse_action', 'simulate', 'route', 'CONTRACT', 'FORMAT', 'DISTRACTORS'):
            self.assertIs(getattr(s, name), getattr(previous, name))
        hashes = s.code_hashes()
        expected = {'reservoir_experiments/retained_action.py', 'probes/retained_action.py',
                    'reservoir_experiments/provenance_decision.py', 'reservoir_experiments/statistics.py'}
        expected.update('reservoir_experiments/' + name for name in runner.CORE_FILES)
        self.assertEqual(set(hashes), expected)
        for path, digest in hashes.items():
            self.assertEqual(s.digest(s.ROOT / path), digest)
        review = self.root / 'review.txt'
        review.write_text('Pre-outcome fixture review.')
        protocol, ledger = s.build(self.design, additional_sources=[review])
        self.assertEqual(protocol['sources'], ledger['sources'])
        self.assertIn(s.source(review), protocol['sources'])
        _, run = self.prepare(protocol)
        manifest, _ = runner.load_run(run)
        for entry in manifest['sources']:
            self.assertEqual(s.digest(run / entry['snapshot']), entry['sha256'])
        s.frozen_run(self.design, run)

    def test_parser_and_simulator_independent_oracle_including_equality(self):
        for case in s.make_design()['cases'] + [dict(s.make_design()['cases'][0], x=50, later_threshold=50)]:
            for changed in (False, True):
                threshold = case['later_threshold'] if changed else 50
                correct = 'ROUTE_LOW' if case['x'] < threshold else 'ROUTE_HIGH'
                for action in s.ACTIONS:
                    parsed = s.parse_action({'status': 'complete', 'text': answer(action)})
                    sim = s.simulate(case, parsed, later=changed)
                    cost = 1 if action == 'MEASURE' else 0 if action == correct else 4
                    self.assertEqual(sim['cost'], cost)
                    self.assertEqual(sim['utility'], -cost)
                    self.assertEqual(sim['after']['ticket'], correct if action == 'MEASURE' else action)
                    self.assertEqual(sim['observed_measurement'] is not None, action == 'MEASURE')
        invalid = ['```json\n' + answer() + '\n```', answer() + ' suffix',
                   '{"action":"MEASURE","action":"ROUTE_LOW","account":"x"}',
                   '{"action":"MEASURE","account":NaN}', '{"action":"MEASURE"}',
                   '{"action":"OTHER","account":"x"}', '{"action":"MEASURE","account":""}',
                   '{"action":"MEASURE","account":"x","extra":true}']
        for text in invalid:
            parsed = s.parse_action({'status': 'complete', 'text': text})
            self.assertFalse(parsed['action_valid'])
            sim = s.simulate(s.make_design()['cases'][0], parsed)
            self.assertFalse(sim['executed'])
            self.assertIsNone(sim['utility'])

    def test_scoring_reconstructs_actions_costs_formats_and_known_contrasts(self):
        def output(node, case):
            threshold = case['later_threshold'] if node['kind'] == 'changed' else 50
            correct = 'ROUTE_LOW' if case['x'] < threshold else 'ROUTE_HIGH'
            old = 'ROUTE_LOW' if case['x'] < 50 else 'ROUTE_HIGH'
            action = correct if node['condition'] == 'facts' else old if node['condition'] == 'prior' else (
                'ROUTE_HIGH' if old == 'ROUTE_LOW' else 'ROUTE_LOW')
            return answer(action, 'word ' * 101 if node['condition'] == 'swapped' else 'Current account.')
        protocol, run, client = self.execute(output, split='confirmation')
        report = s.score(self.design, run)
        self.assertEqual(len(client.requests), 72)
        self.assertEqual(len(report['rows']), 72)
        self.assertEqual(len(report['groups']), 6)
        self.assertEqual(report['primary']['difference'], -4)
        self.assertEqual(report['primary']['ci95'], [-4, -4])
        self.assertEqual(report['primary']['valid_pairs'], 12)
        self.assertEqual(report['primary']['paired_episodes'], 6)
        self.assertEqual(report['primary']['world_differences'], {c['id']: -4 for c in protocol['truth'].values()})
        self.assertEqual(report['secondary']['unchanged']['difference'], 0)
        self.assertEqual(report['secondary']['interaction']['difference'], -4)
        self.assertEqual(report['secondary']['interaction']['valid_quadruples'], 12)
        self.assertEqual(report['diagnostic']['changed']['difference'], 0)
        self.assertEqual(report['diagnostic']['unchanged']['difference'], -4)
        for group in report['groups']:
            self.assertEqual(group['planned'], 12)
            self.assertEqual(group['valid_actions'], 12)
            self.assertEqual(group['schema_valid'], 12)
            self.assertEqual(group['json_valid'], 12)
            self.assertEqual(group['over_requested_account_length'], 12 if group['condition'] == 'swapped' else 0)
            self.assertEqual(group['literal_conclusion_scorable'], 0 if group['condition'] == 'facts' else 12)
            self.assertEqual(group['literal_conclusion_agreement'], 0 if group['condition'] == 'facts' else 12)
            wrong = (group['rule'], group['condition']) in {('changed', 'prior'), ('unchanged', 'swapped')}
            self.assertEqual(group['wrong_direct_routes'], 12 if wrong else 0)
            self.assertEqual(group['correct_direct_routes'], 0 if wrong else 12)
            self.assertEqual(group['total_cost'], 48 if wrong else 0)

    def test_measure_invalid_and_incomplete_are_separate(self):
        def output(node, case):
            if node['condition'] == 'facts':
                return answer('MEASURE')
            if node['condition'] == 'prior':
                return 'not json'
            return answer('ROUTE_LOW'), 'length'
        _, run, _ = self.execute(output)
        report = s.score(self.design, run)
        self.assertEqual(report['primary']['valid_pairs'], 0)
        self.assertIsNone(report['primary']['difference'])
        self.assertIsNone(report['primary']['ci95'])
        for row in report['rows']:
            if row['condition'] == 'facts':
                self.assertEqual(row['score'], -1)
                self.assertFalse(row['policy_warranted'])
                self.assertEqual(row['simulator_receipt']['disposition'], 'measured-and-routed')
            else:
                self.assertFalse(row['valid'])
                self.assertIsNone(row['score'])
                self.assertIsNone(row['literal_conclusion_agreement'])
                self.assertEqual(row['unavailable_reason'], 'malformed-json' if row['condition'] == 'prior' else 'incomplete')

    def test_interaction_pairs_complete_quadruples_before_world_averaging(self):
        design = s.make_design()
        rows = []
        for case in design['cases']:
            for seed in design['seeds']:
                for rule in s.RULES:
                    for arm in ('facts', 'prior'):
                        world = case['base_index']
                        valid = world < 2
                        # World 0 seed7 lacks unchanged/facts. Its changed pair must
                        # contribute to primary, but never to the interaction.
                        if world == 0 and seed == 7 and rule == 'unchanged' and arm == 'facts':
                            valid = False
                        # World 1 has a single complete seed quadruple.
                        if world == 1 and seed != 7:
                            valid = False
                        values = {'facts': 0, 'prior': (-4 if seed == 7 else -1) if rule == 'changed' else -1}
                        if world == 1:
                            values = {'facts': -1 if rule == 'changed' else 0, 'prior': 0 if rule == 'changed' else -1}
                        rows.append({'case_id': case['id'], 'rule': rule, 'seed': seed,
                                     'condition': arm, 'valid': valid, 'score': values[arm] if valid else None})
        result = s.interaction(rows, design)
        self.assertEqual(result['candidate_quadruples'], 12)
        self.assertEqual(result['valid_quadruples'], 2)
        self.assertEqual(result['world_differences'], {design['cases'][0]['id']: 0, design['cases'][1]['id']: 2})
        self.assertEqual(result['difference'], 1)
        self.assertEqual(result['ci95'], [0, 2])
        self.assertEqual(len(result['partial_worlds']), 2)
        self.assertEqual(len(result['unavailable_worlds']), 4)
        separately_averaged = s.paired_contrast(rows, design, 'changed')['difference'] - s.paired_contrast(rows, design, 'unchanged')['difference']
        self.assertNotEqual(result['difference'], separately_averaged)
        self.assertEqual(s.paired_contrast(rows, design, 'changed')['valid_pairs'], 3)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            s.interaction(rows + [rows[0]], design)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            s.paired_contrast(rows + [rows[0]], design, 'changed')

    def test_bootstrap_matches_fixed_world_resampling_convention(self):
        design = s.make_design()
        values = [-4, -1, 0, 1, 2, 4]
        rows = [{'case_id': c['id'], 'rule': 'changed', 'seed': seed, 'condition': arm,
                 'valid': True, 'score': values[c['base_index']] if arm == 'prior' else 0}
                for c in design['cases'] for seed in design['seeds'] for arm in ('prior', 'facts')]
        report = s.paired_contrast(rows, design, 'changed')
        rng = random.Random(20261024)
        sampled = sorted(sum(rng.choices(values, k=6)) / 6 for _ in range(10000))
        self.assertEqual(report['ci95'], [sampled[int(.025 * 9999)], sampled[int(.975 * 9999)]])
        self.assertEqual(report['difference'], sum(values) / 6)
        empty = s.interaction([], design)
        self.assertEqual(empty['candidate_quadruples'], 12)
        self.assertEqual(empty['valid_quadruples'], 0)
        self.assertIsNone(empty['difference'])
        self.assertIsNone(empty['ci95'])

    def test_partial_schedule_retains_every_planned_opportunity(self):
        _, run, _ = self.execute(limit=3)
        report = s.score(self.design, run)
        self.assertEqual(len(report['rows']), 12)
        self.assertEqual(sum(r['valid'] for r in report['rows']), 3)
        pending = [r for r in report['rows'] if r['status'] == 'pending']
        self.assertEqual(len(pending), 9)
        self.assertTrue(all(r['score'] is None and r['unavailable_reason'] == 'pending' for r in pending))

    def test_ambiguous_physical_attempt_is_missing_utility(self):
        protocol, run = self.prepare()
        class Interrupted(BaseException):
            pass
        class InterruptTransport(Fake):
            def generate(self, request, timeout):
                raise Interrupted()
        with self.assertRaises(Interrupted):
            runner.run_protocol(run, transport=InterruptTransport([]))
        report = s.score(self.design, run)
        ambiguous = [r for r in report['rows'] if r['status'] == 'ambiguous']
        self.assertEqual(len(ambiguous), 1)
        self.assertIsNone(ambiguous[0]['score'])
        self.assertEqual(ambiguous[0]['unavailable_reason'], 'ambiguous')
        self.assertIsNone(report['primary']['difference'])

    def test_changed_design_prompt_slots_or_dependencies_fail(self):
        protocol = s.build(self.design)[0]
        mutations = [lambda p: p['nodes'][0]['messages'][1].update(content='Altered factual authority'),
                     lambda p: p['planned_slots'][0].update(condition='swapped'),
                     lambda p: p['truth'][next(iter(p['truth']))].update(x=99),
                     lambda p: p['sources'].pop(1)]
        for index, mutate in enumerate(mutations):
            altered = deepcopy(protocol)
            mutate(altered)
            _, run = self.prepare(altered, name=f'altered-{index}')
            with self.assertRaisesRegex(ValueError, 'frozen design|immutable construction'):
                s.score(self.design, run)
        changed = json.loads(self.design.read_text())
        changed['cases'][0]['x'] = 99
        self.design.write_bytes(json_bytes(changed))
        with self.assertRaisesRegex(ValueError, 'Design differs'):
            s.build(self.design)

    def test_tampered_provider_result_fails_verification(self):
        protocol, run, _ = self.execute()
        result_path = run / 'nodes' / protocol['nodes'][0]['id'] / 'result.json'
        value = json.loads(result_path.read_text())
        value['text'] = answer('ROUTE_LOW')
        result_path.write_bytes(json_bytes(value))
        with self.assertRaises(runner.ExperimentError):
            s.score(self.design, run)

    def test_fixed_reading_has_all_seed7_slots_and_exact_requests(self):
        _, run, _ = self.execute(lambda n, c: answer(account='opaque output ``` sentinel'),
                                 split='confirmation', limit=15)
        out = self.root / 'reading'
        with patch.object(s, 'guard_output', side_effect=lambda p: Path(p)):
            receipt = s.reading(self.design, run, out)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                s.reading(self.design, run, out)
        self.assertEqual(receipt['packets'], 36)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertEqual({r['seed'] for r in key}, {7})
        self.assertEqual({r['base_index'] for r in key}, set(range(6)))
        self.assertEqual({r['rule'] for r in key}, set(s.RULES))
        self.assertEqual({r['condition'] for r in key}, set(s.ARMS))
        self.assertTrue(any(r['status'] == 'pending' for r in key))
        output_only = (out / 'reading.md').read_text()
        evidence = (out / 'evidence.md').read_text()
        for hidden in ('Finch', 'base_id', 'condition', 'Historical action conclusion', 'changed', 'facts', 'swapped'):
            self.assertNotIn(hidden, output_only)
        self.assertIn('````text', output_only)
        for row in key:
            request = run / 'nodes' / row['node_id'] / 'request.json'
            if request.exists():
                content = json.loads(request.read_text())['messages'][1]['content']
                self.assertIn(content, evidence)
                self.assertEqual(row['files']['request.json'], s.digest(request))
            else:
                self.assertIsNone(row['files']['request.json'])
        for name, digest in receipt['files'].items():
            self.assertEqual(s.digest(out / name), digest)

    def test_cli_build_snapshots_ledger_sources_and_refuses_overwrite(self):
        spec = spec_from_file_location('retained_action_probe', s.ROOT / 'probes' / 'retained_action.py')
        probe = module_from_spec(spec)
        spec.loader.exec_module(probe)
        study_doc = s.ROOT / 'research/studies/S-018-verified-facts-and-prior-conclusions.md'
        protocol_path, ledger_path = self.root / 'built.json', self.root / 'ledger.json'
        args = ['retained_action.py', 'build', str(self.design), '--out', str(protocol_path),
                '--ledger-out', str(ledger_path), '--source', str(study_doc)]
        with patch.object(s, 'guard_output', side_effect=lambda p: Path(p)), patch('sys.argv', args):
            with contextlib.redirect_stdout(io.StringIO()):
                probe.main()
            with self.assertRaisesRegex(ValueError, 'existing output'):
                probe.main()
        protocol = json.loads(protocol_path.read_text())
        ledger = json.loads(ledger_path.read_text())
        self.assertEqual(ledger['planned'], protocol['planned_slots'])
        self.assertEqual(protocol['sources'][-1], s.source(ledger_path))
        self.assertIn(s.source(study_doc), ledger['sources'])
        _, run = self.prepare(protocol)
        s.frozen_run(self.design, run)
        with self.assertRaises(runner.ExperimentError):
            s.guard_output(self.root / 'outside.json')


if __name__ == '__main__':
    unittest.main()
