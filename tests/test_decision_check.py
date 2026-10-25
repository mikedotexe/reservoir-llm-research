"""S-019 bank, invariants, strict certificates and receipt-chain tests.

All model outputs below are synthetic fixture text through an injected fake
transport. These tests make no provider/network/live-system calls.
"""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import contextlib
import io
import json
import random
import re
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import decision_check as s, provenance_decision as previous, runner
from reservoir_experiments.transport import json_bytes


def answer(form, case, *, action=None, account='The current verified record supports this decision.',
           changes=None, reverse=False):
    data = {'action': action or ('ROUTE_LOW' if case['x'] < case['threshold'] else 'ROUTE_HIGH'),
            'account': account, 'x': case['x'], 'current_threshold': case['threshold'],
            'relation': 'LT' if case['x'] < case['threshold'] else 'GE'}
    data.update(changes or {})
    order = list(s.ORDERS[form])
    if reverse:
        order.reverse()
    return json.dumps({key: data[key] for key in order})


class Fake:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.requests = []

    def identity(self, model):
        return {'SYNTHETIC_FIXTURE_ONLY': True, 'endpoint': 'http://127.0.0.1:11434',
                'runtime': {'version': '0.35.0'},
                'model': {'name': model,
                          'digest': '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d'}}

    def generate(self, request, timeout):
        self.requests.append(json.loads(request))
        output = self.outputs.pop(0)
        text, reason = output if isinstance(output, tuple) else (output, 'stop')
        return json_bytes({'model': 'mistral-small:24b', 'done': True, 'done_reason': reason,
                           'message': {'content': text}, 'eval_count': 640 if reason == 'length' else 25,
                           'prompt_eval_count': 500})


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.design = self.write_design('development')

    def tearDown(self):
        self.temp.cleanup()

    def write_design(self, split):
        path = self.root / (split + '-design.json')
        path.write_bytes(json_bytes(s.make_design(split)))
        return path

    def prepare(self, design=None, *, gate=None, protocol=None, name='run'):
        design = design or self.design
        protocol = protocol or s.build(design, gate_path=gate)[0]
        path = self.root / (name + '-protocol.json')
        path.write_bytes(json_bytes(protocol))
        run = self.root / 'research' / 'outputs' / name
        runner.prepare(path, run, repository=self.root)
        return protocol, run

    def execute(self, output=None, *, split='development', gate=None, name=None, limit=None):
        design = self.write_design(split)
        protocol, run = self.prepare(design, gate=gate, name=name or split)
        outputs = [(output(node, protocol['truth'][node['episode']]) if output else
                    answer(node['condition'], protocol['truth'][node['episode']])) for node in protocol['nodes']]
        client = Fake(outputs)
        runner.run_protocol(run, transport=client, limit=limit)
        self.assertTrue(runner.verify(run)['valid'])
        return design, protocol, run, client

    def discovery_gate(self, output=None, *, limit=None):
        design, protocol, run, client = self.execute(output, split='discovery', limit=limit)
        report = s.score(design, run)
        report_path = self.root / 'discovery-score.json'
        report_path.write_bytes(json_bytes(report))
        gate_path = self.root / 'discovery-gate.json'
        gate_path.write_bytes(json_bytes(s.make_gate(design, run, report_path)))
        return gate_path, design, protocol, run, report_path, report

    def test_exact_banks_counts_and_separation(self):
        expected = {
            'development': ([29, 77], [-5, 5], 'Kite', '2026-07-17', [7], 18),
            'discovery': ([23, 34, 46, 57, 62, 71, 78, 86], [-5, 5, -5, 5, 5, -5, 5, -5], 'Heron', '2026-08-23', [7, 20260909], 144),
            'confirmation': ([26, 35, 44, 59, 66, 74, 83, 88], [5, -5, 5, -5, -5, 5, -5, 5], 'Ibis', '2026-09-19', [7, 20260909], 144),
        }
        gate, *_ = self.discovery_gate(lambda n, c: 'invalid fixture response')
        identifiers = {field: [] for field in ('id', 'focal', 'snapshot', 'x', 'audit_id')}
        for split, (values, offsets, prefix, date, seeds, count) in expected.items():
            design = s.make_design(split)
            self.assertEqual([c['x'] for c in design['cases']], values)
            self.assertEqual([c['current_offset'] for c in design['cases']], offsets)
            self.assertEqual(design['seeds'], seeds)
            self.assertEqual(design['contexts'], list(s.CONTEXTS))
            self.assertEqual(design['formats'], list(s.FORMATS))
            protocol, ledger = s.build(self.write_design(split), gate_path=gate if split == 'confirmation' else None)
            self.assertEqual(len(protocol['nodes']), count)
            self.assertEqual(len(ledger['planned']), count)
            self.assertEqual(len({n['id'] for n in protocol['nodes']}), count)
            self.assertEqual(design['shuffle_seed'], 20261025)
            self.assertEqual(design['reading_shuffle_seed'], 20261025)
            self.assertEqual(design['bootstrap_seed'], 20261024)
            self.assertEqual(design['model_digest'], '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d')
            directions = []
            for index, case in enumerate(design['cases']):
                self.assertEqual(case['focal'], f'{prefix}{index+1:02d}')
                self.assertEqual(case['snapshot'], date + 'T12:00:00Z')
                self.assertEqual(case['decision_clock'], date + 'T14:00:00Z')
                self.assertEqual(case['threshold'], values[index] + offsets[index])
                directions.append(case['x'] < case['threshold'])
            self.assertEqual(sum(directions), len(values) // 2)
            for field in identifiers:
                current = {c[field] for c in design['cases']}
                self.assertTrue(all(not (current & seen) for seen in identifiers[field]))
                identifiers[field].append(current)

    def test_requested_only_order_and_context_reflection_all_worlds(self):
        for split in ('development', 'discovery', 'confirmation'):
            design = s.make_design(split)
            for case in design['cases']:
                expected_fact = json.dumps(s.factual_record(case), sort_keys=True)
                history = {context: s.historical_threshold(case, context) for context in s.CONTEXTS}
                self.assertIsNone(history['none'])
                self.assertEqual(history['aligned'] + history['conflict'], 2 * case['x'])
                self.assertEqual(abs(history['aligned'] - case['x']), 10)
                self.assertEqual(case['x'] < history['aligned'], case['x'] < case['threshold'])
                self.assertNotEqual(case['x'] < history['conflict'], case['x'] < case['threshold'])
                for value in (history['aligned'], history['conflict']):
                    self.assertEqual(len(str(value)), 2)
                    self.assertNotEqual(value, case['threshold'])
                for form in s.FORMATS:
                    prompts = {context: s.messages(case, context, form) for context in s.CONTEXTS}
                    for context in ('aligned', 'conflict'):
                        altered = deepcopy(prompts[context])
                        line = '\n' + s.HISTORY_PREFIX + str(history[context]) + '.'
                        self.assertEqual(altered[1]['content'].count(line), 1)
                        altered[1]['content'] = altered[1]['content'].replace(line, '')
                        self.assertEqual(altered, prompts['none'])
                    for prompt in prompts.values():
                        self.assertEqual(prompt[0]['content'], previous.CONTRACT)
                        self.assertIn(previous.DISTRACTORS, prompt[1]['content'])
                        self.assertIn(expected_fact, prompt[1]['content'])
                        self.assertIn('sufficient to choose a direct route', prompt[1]['content'])
                        self.assertIn('researcher-authored background, not the current rule or a record of executed action', prompt[1]['content'])
                        for hidden in ('aligned', 'conflict', 'action_first', 'check_first', 'proposed_action'):
                            self.assertNotIn(hidden, prompt[1]['content'])
                for context in s.CONTEXTS:
                    a = s.messages(case, context, 'action_first')
                    b = s.messages(case, context, 'check_first')
                    a[1]['content'] = a[1]['content'].replace(', '.join(s.ORDERS['action_first']), 'ORDER')
                    b[1]['content'] = b[1]['content'].replace(', '.join(s.ORDERS['check_first']), 'ORDER')
                    self.assertEqual(a, b)

    def test_render_settings_schedule_and_unchanged_dependencies(self):
        protocol, ledger = s.build(self.design)
        shuffled = [slot['node_id'] for slot in ledger['planned']]
        random.Random(20261025).shuffle(shuffled)
        self.assertEqual(shuffled, [n['id'] for n in protocol['nodes']])
        for node in protocol['nodes']:
            request = json.loads(runner.render_request(protocol, node, {}))
            self.assertEqual(request['options'], {'temperature': .7, 'num_ctx': 16384, 'seed': 7, 'num_predict': 640})
            self.assertEqual(request['format'], 'json')
            self.assertEqual(node['inputs'], [])
            self.assertEqual(node['after'], [])
        for name in ('simulate', 'route', 'CONTRACT', 'DISTRACTORS'):
            self.assertIs(getattr(s, name), getattr(previous, name))
        hashes = s.code_hashes()
        expected = {'reservoir_experiments/decision_check.py', 'probes/decision_check.py',
                    'reservoir_experiments/provenance_decision.py', 'reservoir_experiments/statistics.py',
                    *('reservoir_experiments/' + name for name in runner.CORE_FILES)}
        self.assertEqual(set(hashes), expected)
        self.assertEqual(s.build(self.design)[0], protocol)

    def test_strict_json_types_actions_and_whole_response(self):
        case = s.make_design('development')['cases'][0]
        for form in s.FORMATS:
            valid = answer(form, case)
            examples = ['```json\n' + valid + '\n```', valid + ' suffix',
                        valid[:-1] + ',"extra":true}', valid.replace('"account":', '"action":"MEASURE","account":'),
                        valid.replace('"account": "The current verified record supports this decision."', '"account":NaN'),
                        valid.replace('"account": "The current verified record supports this decision."', '"account":1e999'),
                        answer(form, case, account='  '), answer(form, case, action='UNKNOWN'),
                        'null', '[]', '{}', '"object"', answer(form, case, changes={'account': True}),
                        answer(form, case, changes={'action': False})]
            if form != 'direct':
                examples += [answer(form, case, changes=changes) for changes in (
                    {'x': True}, {'current_threshold': False}, {'x': 29.0}, {'current_threshold': '24'},
                    {'relation': 'LE'}, {'relation': True}, {'x': None})]
            for text in examples:
                with self.subTest(form=form, text=text):
                    parsed = s.parse_action({'status': 'complete', 'text': text}, form)
                    self.assertFalse(parsed['action_valid'])
                    self.assertFalse(parsed['schema_valid'])
                    self.assertIsNone(parsed['requested_order_compliant'])
                    self.assertTrue(all(v is None for v in s.check_diagnostics(case, parsed, form).values()))
                    self.assertIsNone(s.simulate(case, parsed)['utility'])
            incomplete = s.parse_action({'status': 'incomplete', 'text': valid}, form)
            self.assertFalse(incomplete['action_valid'])
            self.assertIsNone(incomplete['actual_key_order'])
        for nonfinite in ('NaN', 'Infinity', '-Infinity', '1e999'):
            with self.assertRaises(ValueError):
                s.strict_json('{"nested":{"value":' + nonfinite + '}}')
        with self.assertRaises(ValueError):
            s.strict_json('{"nested":{"k":1,"k":2}}')

    def test_wrong_certificates_valid_and_order_retained(self):
        case = s.make_design('development')['cases'][0]
        wrong = 'ROUTE_LOW'  # x=29, t=24 requires HIGH.
        for form in ('action_first', 'check_first'):
            parsed = s.parse_action({'status': 'complete', 'text': answer(form, case, action=wrong, reverse=True)}, form)
            self.assertTrue(parsed['schema_valid'])
            self.assertFalse(parsed['requested_order_compliant'])
            self.assertEqual(parsed['actual_key_order'], list(reversed(s.ORDERS[form])))
            diag = s.check_diagnostics(case, parsed, form)
            self.assertTrue(diag['correct_check'])
            self.assertTrue(diag['correct_check_wrong_direct'])
            self.assertFalse(diag['action_matches_reported_relation'])
            self.assertEqual(s.simulate(case, parsed)['utility'], -4)
            parsed = s.parse_action({'status': 'complete', 'text': answer(form, case, changes={'x': 2, 'current_threshold': 9, 'relation': 'LT'})}, form)
            self.assertTrue(parsed['schema_valid'])
            diag = s.check_diagnostics(case, parsed, form)
            self.assertFalse(diag['x_fidelity'])
            self.assertFalse(diag['current_threshold_fidelity'])
            self.assertFalse(diag['relation_correct'])
            self.assertTrue(diag['relation_consistent_with_reported_inputs'])
            self.assertTrue(diag['incorrect_check_correct_direct'])
            self.assertEqual(s.simulate(case, parsed)['utility'], 0)
            parsed = s.parse_action({'status': 'complete', 'text': answer(form, case, action='MEASURE')}, form)
            diag = s.check_diagnostics(case, parsed, form)
            self.assertTrue(diag['correct_check_measure'])
            self.assertFalse(diag['action_matches_reported_relation'])
            self.assertEqual(s.simulate(case, parsed)['utility'], -1)
        text = '{"account":"a","action":"MEASURE","extra":true}'
        parsed = s.parse_action({'status': 'complete', 'text': text}, 'direct')
        self.assertEqual(parsed['actual_key_order'], ['account', 'action', 'extra'])
        self.assertIsNone(parsed['requested_order_compliant'])

    def test_simulator_oracle_lengths_and_equality(self):
        for case in s.make_design('discovery')['cases'] + [dict(s.make_design()['cases'][0], x=50, threshold=50)]:
            correct = 'ROUTE_LOW' if case['x'] < case['threshold'] else 'ROUTE_HIGH'
            for form in s.FORMATS:
                for action in s.ACTIONS:
                    parsed = s.parse_action({'status': 'complete', 'text': answer(form, case, action=action, account='word ' * 101)}, form)
                    self.assertTrue(parsed['action_valid'])
                    self.assertFalse(parsed['within_requested_account_length'])
                    sim = s.simulate(case, parsed)
                    cost = 1 if action == 'MEASURE' else 0 if action == correct else 4
                    self.assertEqual(sim['cost'], cost)
                    self.assertEqual(sim['utility'], -cost)
                    self.assertEqual(sim['after']['ticket'], correct if action == 'MEASURE' else action)
                    self.assertEqual(sim['observed_measurement'] is not None, action == 'MEASURE')
                    self.assertEqual(sim['simulator_sha256'], s.digest(Path(previous.__file__)))

    def synthetic_rows(self, design, values):
        return [{'case_id': case['id'], 'context': context, 'seed': seed, 'condition': form,
                 'valid': True, 'score': values(case['base_index'], context, seed, form)}
                for case in design['cases'] for context in s.CONTEXTS for seed in design['seeds'] for form in s.FORMATS]

    def test_all_13_contrasts_pair_by_world_and_seed_and_fixed_bootstrap(self):
        design = s.make_design('discovery')
        offsets = {'none': 0, 'aligned': 1, 'conflict': 2}
        forms = {'direct': 0, 'action_first': 1, 'check_first': 3}
        values = lambda world, context, seed, form: world + offsets[context] * forms[form] + (seed != 7)
        rows = self.synthetic_rows(design, values)
        for name, (first, second) in s.CONTRASTS.items():
            result = s.paired_contrast(rows, design, name)
            expected = offsets[first[0]] * forms[first[1]] - offsets[second[0]] * forms[second[1]]
            self.assertEqual(result['difference'], expected, name)
            self.assertEqual(result['valid_pairs'], 16)
            self.assertEqual(result['candidate_pairs'], 16)
            self.assertEqual(result['paired_episodes'], 8)
            self.assertEqual(result['ci95'], [expected, expected])
            self.assertEqual(len(result['seed_differences']), 16)
        result = s.interaction(rows, design)
        self.assertEqual(result['difference'], 2)
        self.assertEqual(result['valid_quadruples'], 16)
        self.assertEqual(len(s.CONTRASTS) + 1, 13)
        gains = [-4, -1, 0, 1, 2, 3, 4, 4]
        rows = self.synthetic_rows(design, lambda world, context, seed, form: gains[world] if form == 'check_first' else 0)
        result = s.paired_contrast(rows, design, 'order_conflict')
        rng = random.Random(20261024)
        boot = sorted(sum(rng.choices(gains, k=8)) / 8 for _ in range(10000))
        self.assertEqual(result['difference'], sum(gains) / 8)
        self.assertEqual(result['ci95'], [boot[int(.025 * 9999)], boot[int(.975 * 9999)]])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            s.paired_contrast(rows + [rows[0]], design, 'order_conflict')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            s.interaction(rows + [rows[0]], design)

    def test_interaction_uses_only_complete_same_seed_quadruples(self):
        design = s.make_design('discovery')
        rows = []
        for case in design['cases']:
            for seed in design['seeds']:
                for context in ('conflict', 'aligned'):
                    for form in ('check_first', 'action_first'):
                        world = case['base_index']
                        valid = world < 2
                        if world == 0 and seed == 7 and context == 'aligned' and form == 'action_first':
                            valid = False
                        if world == 1 and seed != 7:
                            valid = False
                        score = 0 if form == 'action_first' else (-4 if seed == 7 else -1) if context == 'conflict' else -1
                        if world == 1:
                            score = (0 if form == 'check_first' else -1) if context == 'conflict' else (-1 if form == 'check_first' else 0)
                        rows.append({'case_id': case['id'], 'context': context, 'seed': seed,
                                     'condition': form, 'valid': valid, 'score': score if valid else None})
        result = s.interaction(rows, design)
        self.assertEqual(result['candidate_quadruples'], 16)
        self.assertEqual(result['valid_quadruples'], 2)
        self.assertEqual(result['world_differences'], {design['cases'][0]['id']: 0, design['cases'][1]['id']: 2})
        self.assertEqual(result['difference'], 1)
        self.assertEqual(result['ci95'], [0, 2])
        self.assertEqual(len(result['partial_worlds']), 2)
        self.assertEqual(len(result['unavailable_worlds']), 6)
        separately = s.paired_contrast(rows, design, 'order_conflict')['difference'] - s.paired_contrast(rows, design, 'order_aligned')['difference']
        self.assertNotEqual(result['difference'], separately)
        empty = s.interaction([], design)
        self.assertEqual(empty['candidate_quadruples'], 16)
        self.assertIsNone(empty['difference'])
        self.assertIsNone(empty['ci95'])

    def test_gate_coverage_thresholds_priority_and_fallback(self):
        design = s.make_design('discovery')
        def comparison(gains, seed_override=None):
            rows = self.synthetic_rows(design, lambda world, context, seed, form:
                                       (seed_override(seed) if seed_override else gains[world]) if form == 'check_first' else 0)
            return s.paired_contrast(rows, design, 'order_conflict')
        qualified = comparison([4, 3, 1, 0, 0, 0, 0, 0])  # Exactly1.0, exactly3positiveworlds.
        self.assertTrue(s.practical_gate(qualified, design)['qualified'])
        below = comparison([4, 2, 1, 0, 0, 0, 0, 0])
        self.assertFalse(s.practical_gate(below, design)['qualified'])
        two_worlds = comparison([4, 4, 0, 0, 0, 0, 0, 0])
        self.assertFalse(s.practical_gate(two_worlds, design)['qualified'])
        seed_zero = comparison([], lambda seed: 0 if seed == 7 else 2)
        self.assertFalse(s.practical_gate(seed_zero, design)['qualified'])
        rows = self.synthetic_rows(design, lambda w, c, seed, f: 2 if f == 'check_first' else 0)
        next(r for r in rows if r['context'] == 'conflict' and r['condition'] == 'check_first').update(valid=False, score=None)
        partial = s.paired_contrast(rows, design, 'order_conflict')
        self.assertEqual(partial['valid_pairs'], 15)
        self.assertFalse(s.practical_gate(partial, design)['qualified'])
        selected = s.select_candidate({name: qualified for name in s.CANDIDATES}, design)
        self.assertEqual(selected['selected_candidate'], 'order_conflict')
        selected = s.select_candidate(dict(zip(s.CANDIDATES, [below, qualified, qualified])), design)
        self.assertEqual(selected['selected_candidate'], 'bundle_conflict')
        selected = s.select_candidate(dict(zip(s.CANDIDATES, [below, below, qualified])), design)
        self.assertEqual(selected['selected_candidate'], 'history_direct')
        selected = s.select_candidate({name: below for name in s.CANDIDATES}, design)
        self.assertEqual(selected['selected_candidate'], 'order_conflict')
        self.assertEqual(selected['selection_status'], 'no discovery candidate')
        self.assertFalse(selected['selected_qualified_in_discovery'])
        with self.assertRaises(ValueError):
            s.practical_gate(qualified, s.make_design('development'))

    def test_pairing_never_matches_different_seeds_or_worlds(self):
        design = s.make_design('discovery')
        rows = self.synthetic_rows(design, lambda w, c, seed, f: 0)
        for row in rows:
            row['valid'] = False
            row['score'] = None
            if row['context'] == 'conflict' and row['case_id'] == design['cases'][0]['id']:
                if (row['seed'], row['condition']) in ((7, 'check_first'), (20260909, 'action_first')):
                    row.update(valid=True, score=0)
            if row['context'] == 'conflict' and row['case_id'] == design['cases'][1]['id']:
                if (row['seed'], row['condition']) == (7, 'action_first'):
                    row.update(valid=True, score=-4)
        result = s.paired_contrast(rows, design, 'order_conflict')
        self.assertEqual(result['valid_pairs'], 0)
        self.assertIsNone(result['difference'])
        self.assertEqual(len(result['seed_differences']), 16)
        self.assertEqual(len(result['unavailable_worlds']), 8)

    def test_gate_refuses_pending_or_ambiguous_discovery_slots(self):
        design, protocol, run, _ = self.execute(split='discovery', limit=1)
        report_path = self.root / 'partial-score.json'
        report_path.write_bytes(json_bytes(s.score(design, run)))
        with self.assertRaisesRegex(ValueError, '144.*terminal'):
            s.make_gate(design, run, report_path)
        # All remaining outputs may be terminal schema failures; they retain
        # null utility and do not block an honest no-candidate gate.
        runner.run_protocol(run, transport=Fake(['invalid fixture'] * 143))
        report_path.write_bytes(json_bytes(s.score(design, run)))
        gate = s.make_gate(design, run, report_path)
        self.assertEqual(gate['selection_status'], 'no discovery candidate')
        self.assertFalse(gate['selected_qualified_in_discovery'])
        _, ambiguous_run = self.prepare(design, name='ambiguous-discovery')
        runner.run_protocol(ambiguous_run, transport=Fake(['invalid fixture'] * 143), limit=143)
        class Interrupted(BaseException):
            pass
        class InterruptTransport(Fake):
            def generate(self, request, timeout):
                raise Interrupted()
        with self.assertRaises(Interrupted):
            runner.run_protocol(ambiguous_run, transport=InterruptTransport([]))
        report_path.write_bytes(json_bytes(s.score(design, ambiguous_run)))
        with self.assertRaisesRegex(ValueError, '144.*terminal'):
            s.make_gate(design, ambiguous_run, report_path)

    def test_actual_model_digest_runtime_and_endpoint_are_bound(self):
        protocol, pending_run = self.prepare(name='undispatched')
        self.assertFalse((pending_run / 'identity.json').exists())
        s.frozen_run(self.design, pending_run)
        mutations = [lambda i: i['model'].update(digest='changed'),
                     lambda i: i['runtime'].update(version='changed'),
                     lambda i: i['model'].update(name='different:tag'),
                     lambda i: i.update(endpoint='http://localhost:11434')]
        for index, mutate in enumerate(mutations):
            class WrongIdentity(Fake):
                def identity(self, model):
                    value = super().identity(model)
                    mutate(value)
                    return value
            protocol, run = self.prepare(name=f'wrong-identity-{index}')
            runner.run_protocol(run, transport=WrongIdentity(['invalid fixture']), limit=1)
            self.assertTrue(runner.verify(run)['valid'])
            with self.assertRaisesRegex(ValueError, 'Provider identity differs'):
                s.score(self.design, run)

    def test_scoring_nine_groups_diagnostics_missing_and_order_outcomes(self):
        def output(node, case):
            form, context = node['condition'], node['kind']
            if context == 'none':
                return answer(form, case, reverse=True, account='word ' * 101)
            if context == 'aligned':
                return answer(form, case, action='MEASURE')
            return 'invalid' if form == 'direct' else answer(form, case, action='ROUTE_HIGH' if case['x'] < case['threshold'] else 'ROUTE_LOW')
        design, _, run, _ = self.execute(output)
        report = s.score(design, run)
        self.assertEqual(len(report['rows']), 18)
        self.assertEqual(len(report['groups']), 9)
        self.assertEqual(len(report['contrasts']), 13)
        for group in report['groups']:
            self.assertEqual(group['planned'], 2)
            self.assertEqual(sum(group['statuses'].values()), 2)
            diagnostic = group['diagnostics']
            if group['context'] == 'none':
                self.assertEqual(group['correct_direct_per_planned'], 1)
                self.assertEqual(diagnostic['requested_order_compliant']['false'], 2)
                self.assertEqual(diagnostic['within_requested_account_length']['false'], 2)
            elif group['context'] == 'aligned':
                self.assertEqual(group['measure'], 2)
                self.assertEqual(group['total_cost'], 2)
            elif group['condition'] == 'direct':
                self.assertEqual(group['malformed_complete'], 2)
                self.assertEqual(group['nonexecuted'], 2)
                self.assertIsNone(group['mean_utility_valid'])
            else:
                self.assertEqual(group['wrong_direct_routes'], 2)
                self.assertEqual(group['total_cost'], 8)
                self.assertEqual(diagnostic['correct_check_wrong_direct']['true'], 2)
            if group['condition'] == 'direct':
                self.assertEqual(diagnostic['correct_check']['scorable'], 0)
                self.assertFalse(diagnostic['correct_check']['applicable'])
        self.assertIsNone(report['contrasts']['bundle_conflict']['difference'])
        self.assertEqual(report['contrasts']['bundle_conflict']['valid_pairs'], 0)

    def test_partial_schedule_and_incomplete_are_null_not_zero(self):
        design, protocol, run, _ = self.execute(lambda n, c: (answer(n['condition'], c), 'length'), limit=3)
        report = s.score(design, run)
        self.assertEqual(len(report['rows']), 18)
        self.assertEqual(sum(r['status'] == 'pending' for r in report['rows']), 15)
        self.assertEqual(sum(r['status'] == 'incomplete' for r in report['rows']), 3)
        self.assertTrue(all(r['score'] is None and not r['valid'] for r in report['rows']))
        self.assertTrue(all(r['requested_order_compliant'] is None and r['correct_check'] is None for r in report['rows']))
        self.assertIsNone(report['contrasts']['order_conflict']['difference'])

    def test_ambiguous_attempt_is_retained_without_retry(self):
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

    def test_confirmation_requires_gate_and_selected_failure_cannot_be_replaced(self):
        confirmation = self.write_design('confirmation')
        with self.assertRaisesRegex(ValueError, 'requires a frozen'):
            s.build(confirmation)
        def discovery_output(node, case):
            action = 'MEASURE' if node['condition'] == 'action_first' and node['kind'] == 'conflict' else None
            return answer(node['condition'], case, action=action)
        gate, _, _, _, _, _ = self.discovery_gate(discovery_output)
        selected = s.read_gate(gate)
        self.assertEqual(selected['selected_candidate'], 'order_conflict')
        self.assertTrue(selected['selected_qualified_in_discovery'])
        def confirmation_output(node, case):
            # Selected order contrast is null; secondary bundle is favorable.
            return answer(node['condition'], case, action='MEASURE' if node['condition'] == 'direct' else None)
        design, protocol, run, client = self.execute(confirmation_output, split='confirmation', gate=gate)
        report = s.score(design, run)
        self.assertEqual(len(client.requests), 144)
        self.assertEqual(len(report['rows']), 144)
        self.assertEqual(report['confirmation']['primary_name'], 'order_conflict')
        self.assertFalse(report['confirmation']['practical_replicated_improvement'])
        self.assertFalse(report['confirmation']['primary_gate']['qualified'])
        self.assertEqual(report['contrasts']['bundle_conflict']['difference'], 1)
        self.assertEqual(protocol['discovery_gate']['sha256'], s.digest(gate))
        self.assertIn(s.source(gate), protocol['sources'])
        self.assertEqual(report['run']['evidence_sha256'], s.run_binding(run)['evidence_sha256'])
        with self.assertRaisesRegex(ValueError, 'Only confirmation'):
            s.build(self.design, gate_path=gate)

    def test_no_candidate_fallback_cannot_be_claimed_replication(self):
        gate, *_ = self.discovery_gate()
        def output(node, case):
            return answer(node['condition'], case, action='MEASURE' if node['condition'] == 'action_first' else None)
        design, _, run, _ = self.execute(output, split='confirmation', gate=gate)
        report = s.score(design, run)
        self.assertEqual(report['confirmation']['selection_status'], 'no discovery candidate')
        self.assertTrue(report['confirmation']['primary_gate']['qualified'])
        self.assertFalse(report['confirmation']['practical_replicated_improvement'])

    def test_selected_candidate_can_replicate_with_all_cells_retained(self):
        def output(node, case):
            return answer(node['condition'], case, action='MEASURE' if node['condition'] == 'action_first' else None)
        gate, *_ = self.discovery_gate(output)
        design, _, run, _ = self.execute(output, split='confirmation', gate=gate)
        report = s.score(design, run)
        self.assertTrue(report['confirmation']['practical_replicated_improvement'])
        self.assertEqual(report['confirmation']['primary_gate']['valid_pairs'], 16)
        self.assertEqual(len(report['rows']), 144)

    def test_gate_tampering_and_raw_evidence_binding(self):
        gate, design, protocol, run, report_path, report = self.discovery_gate()
        original = gate.read_bytes()
        changed = json.loads(original)
        changed['selected_candidate'] = 'history_direct'
        gate.write_bytes(json_bytes(changed))
        with self.assertRaisesRegex(ValueError, 'immutable inputs|selection rule'):
            s.build(self.write_design('confirmation'), gate_path=gate)
        gate.write_bytes(original)
        changed_report = deepcopy(report)
        changed_report['groups'][0]['total_cost'] += 1
        report_path.write_bytes(json_bytes(changed_report))
        with self.assertRaisesRegex(ValueError, 'source binding'):
            s.read_gate(gate)
        report_path.write_bytes(json_bytes(report))
        # A coordinated whitespace-only raw/result change still preserves parsed
        # behavior; the gate must reject its different physical evidence bytes.
        directory = run / 'nodes' / protocol['nodes'][0]['id']
        raw = directory / 'response.raw'
        raw.write_bytes(raw.read_bytes() + b'\n')
        result_path = directory / 'result.json'
        result = json.loads(result_path.read_text())
        result['files']['response.raw'] = s.digest(raw)
        result_path.write_bytes(json_bytes(result))
        self.assertTrue(runner.verify(run)['valid'])
        with self.assertRaisesRegex(ValueError, 'score differs'):
            s.read_gate(gate)

    def test_confirmation_scoring_revalidates_gate_binding(self):
        gate, *_ = self.discovery_gate(lambda n, c: 'invalid fixture response')
        confirmation = self.write_design('confirmation')
        _, run = self.prepare(confirmation, gate=gate)
        gate.write_bytes(gate.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            s.score(confirmation, run)

    def test_design_protocol_source_and_result_tampering(self):
        protocol = s.build(self.design)[0]
        mutations = [lambda p: p['nodes'][0]['messages'][1].update(content='changed authority'),
                     lambda p: p['planned_slots'][0].update(condition='direct'),
                     lambda p: p['truth'][next(iter(p['truth']))].update(x=99),
                     lambda p: p['sources'].pop(1)]
        # First planned format is direct: change it to a distinct allocation.
        mutations[1] = lambda p: p['planned_slots'][0].update(condition='check_first')
        for index, mutation in enumerate(mutations):
            altered = deepcopy(protocol)
            mutation(altered)
            _, run = self.prepare(protocol=altered, name=f'altered-{index}')
            with self.assertRaisesRegex(ValueError, 'frozen design|immutable construction'):
                s.score(self.design, run)
        changed = json.loads(self.design.read_text())
        changed['schema_version'] = True
        self.design.write_bytes(json_bytes(changed))
        with self.assertRaisesRegex(ValueError, 'Design differs'):
            s.build(self.design)
        self.design = self.write_design('development')
        design, protocol, run, _ = self.execute()
        result_path = run / 'nodes' / protocol['nodes'][0]['id'] / 'result.json'
        result = json.loads(result_path.read_text())
        result['text'] = 'tampered'
        result_path.write_bytes(json_bytes(result))
        with self.assertRaises(runner.ExperimentError):
            s.score(design, run)

    def test_fixed_reading_36_all_cells_and_unavailable_exact_requests(self):
        gate, *_ = self.discovery_gate(lambda n, c: 'invalid fixture response')
        design, protocol, run, _ = self.execute(lambda n, c: answer(n['condition'], c, account='opaque ``` sentinel'),
                                                split='confirmation', gate=gate, limit=40)
        out = self.root / 'reading'
        with patch.object(s, 'guard_output', side_effect=lambda p: Path(p)):
            receipt = s.reading(design, run, out)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                s.reading(design, run, out)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertEqual(receipt['packets'], 36)
        self.assertEqual(len(key), 36)
        self.assertEqual({r['base_index'] for r in key}, {0, 1, 6, 7})
        self.assertEqual({r['seed'] for r in key}, {7})
        expected = [slot['node_id'] for slot in protocol['planned_slots'] if slot['seed'] == 7 and slot['base_index'] in (0, 1, 6, 7)]
        random.Random(20261025).shuffle(expected)
        self.assertEqual([r['node_id'] for r in key], expected)
        for index in (0, 1, 6, 7):
            self.assertEqual({(r['context'], r['condition']) for r in key if r['base_index'] == index},
                             {(c, f) for c in s.CONTEXTS for f in s.FORMATS})
        self.assertTrue(any(r['status'] == 'pending' for r in key))
        output_only = (out / 'reading.md').read_text()
        evidence = (out / 'evidence.md').read_text()
        for hidden in ('Ibis', 'base_id', 'condition', 'Historical threshold', 'conflict', 'aligned', 'action_first'):
            self.assertNotIn(hidden, output_only)
        self.assertIn('````text', output_only)
        for row in key:
            request = run / 'nodes' / row['node_id'] / 'request.json'
            if request.exists():
                self.assertIn(json.loads(request.read_text())['messages'][1]['content'], evidence)
                self.assertEqual(row['files']['request.json'], s.digest(request))
            else:
                self.assertIsNone(row['files']['request.json'])
        for name, digest in receipt['files'].items():
            self.assertEqual(s.digest(out / name), digest)

    def test_cli_build_ledger_binding_and_write_once_outputs(self):
        spec = spec_from_file_location('decision_check_probe', s.ROOT / 'probes/decision_check.py')
        probe = module_from_spec(spec)
        spec.loader.exec_module(probe)
        out, ledger = self.root / 'built.json', self.root / 'ledger.json'
        review = self.root / 'review.txt'
        review.write_text('Synthetic preflight fixture.')
        args = ['decision_check.py', 'build', str(self.design), '--out', str(out),
                '--ledger-out', str(ledger), '--source', str(review)]
        with patch.object(s, 'guard_output', side_effect=lambda p: Path(p)), patch('sys.argv', args):
            with contextlib.redirect_stdout(io.StringIO()):
                probe.main()
            with self.assertRaisesRegex(ValueError, 'existing output'):
                probe.main()
        protocol = json.loads(out.read_text())
        self.assertEqual(json.loads(ledger.read_text())['planned'], protocol['planned_slots'])
        self.assertEqual(protocol['sources'][-1], s.source(ledger))
        self.assertIn(s.source(review), protocol['sources'])
        _, run = self.prepare(protocol=protocol)
        s.frozen_run(self.design, run)
        with self.assertRaises(runner.ExperimentError):
            s.guard_output(self.root / 'outside.json')
        with self.assertRaisesRegex(ValueError, 'closed'):
            s.guard_output(s.ROOT / 'research/outputs/retained-action-20261024/new.json')


if __name__ == '__main__':
    unittest.main()
