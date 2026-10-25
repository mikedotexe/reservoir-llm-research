"""S-020 synthetic qualification. No network/provider/live-system requests."""
from copy import deepcopy
from pathlib import Path
import json
import random
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import reproduced_check as s, retained_action as old, runner
from reservoir_experiments.transport import json_bytes


def answer(form, case, *, action=None, changes=None, reverse=False, account='Verified evidence supports this route.'):
    data = {'action': action or s.route(case['x'], case['threshold']), 'account': account,
            'x': case['x'], 'current_threshold': case['threshold'],
            'relation': 'LT' if case['x'] < case['threshold'] else 'GE'}
    data.update(changes or {})
    order = list(s.ORDERS[form])
    if reverse:
        order.reverse()
    return json.dumps({k: data[k] for k in order})


class Fake:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []

    def identity(self, model):
        return {'SYNTHETIC_FIXTURE_ONLY': True, 'endpoint': 'http://127.0.0.1:11434',
                'runtime': {'version': '0.35.0'},
                'model': {'name': model, 'digest': '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d'}}

    def generate(self, request, timeout):
        self.requests.append(json.loads(request))
        return json_bytes({'model': 'mistral-small:24b', 'done': True, 'done_reason': 'stop',
                           'message': {'content': next(self.outputs)}, 'eval_count': 40, 'prompt_eval_count': 700})


def fixture_rows(split='matched', callback=None):
    design = s.make_design(split)
    nodes, slots = s.planned_nodes(design)
    cases = {c['id']: c for c in design['cases']}
    records = {}
    for node in nodes:
        case = s.current_case(cases[node['episode']], node['kind'])
        text = callback(node, case) if callback else answer(node['condition'], case)
        records[node['id']] = {'status': 'complete', 'text': text}
    return design, slots, records


def reproduced_errors(node, case):
    action = s.route(case['x'], 50) if node['kind'] == 'changed' and case['base_index'] < 2 else None
    return answer(node['condition'], case, action=action)


class ConstructionTests(unittest.TestCase):
    def test_banks_counts_orders_and_separation(self):
        for split, count in (('reproduction', 24), ('matched', 72), ('confirmation', 72)):
            design = s.make_design(split)
            nodes, slots = s.planned_nodes(design)
            self.assertEqual(len(nodes), count)
            self.assertEqual(len({n['id'] for n in nodes}), count)
            self.assertEqual(len(slots), count)
            self.assertEqual(design['seeds'], [7, 20260909])
            self.assertIsNone(design['requested_orders']['direct'])
            self.assertEqual([c['x'] < 50 for c in design['cases']], [True]*3 + [False]*3)
            for c in design['cases']:
                self.assertEqual(abs(c['x'] - c['later_threshold']), 5)
                self.assertNotEqual(s.route(c['x'], 50), s.route(c['x'], c['later_threshold']))
            self.assertEqual([n['id'] for n in nodes], [n['id'] for n in s.planned_nodes(design)[0]])
        self.assertEqual(s.make_design('reproduction')['cases'], old.make_design('confirmation')['cases'])
        self.assertEqual(s.make_design('matched')['cases'], old.make_design('confirmation')['cases'])
        fresh = s.make_design('confirmation')['cases']
        self.assertEqual([c['x'] for c in fresh], [21, 33, 43, 56, 67, 79])
        self.assertEqual([c['later_threshold'] for c in fresh], [16, 28, 38, 61, 72, 84])
        self.assertEqual(fresh[0]['focal'], 'Wren01')
        self.assertEqual(fresh[-1]['audit_id'], 's020-confirmation-base-05-audit')

    def test_request_identity_and_format_only_change(self):
        design = s.make_design('reproduction')
        for c in design['cases']:
            for rule in s.RULES:
                direct = s.messages(c, rule, 'direct')
                self.assertEqual(direct, old.messages(c, rule, 'facts'))
                self.assertTrue(direct[1]['content'].endswith(old.FORMAT))
                prefix = direct[1]['content'][:-len(old.FORMAT)]
                a, b = [s.messages(c, rule, f) for f in ('action_first', 'check_first')]
                self.assertEqual(a[0], direct[0])
                self.assertEqual(b[0], direct[0])
                for form, messages in (('action_first', a), ('check_first', b)):
                    self.assertEqual(messages[1]['content'], prefix + s.checks.format_instruction(form))
                self.assertEqual(a[1]['content'].split('Emit the keys in this order:')[0], b[1]['content'].split('Emit the keys in this order:')[0])
                for seed in design['seeds']:
                    node = {'seed': seed, 'max_tokens': 640, 'format': 'json', 'messages': direct}
                    historical_node = {**node, 'messages': old.messages(c, rule, 'facts')}
                    self.assertEqual(runner.render_request(design, node, {}), runner.render_request(old.make_design('confirmation'), historical_node, {}))

    def test_shuffle_is_full_predeclared_schedule(self):
        design = s.make_design('matched')
        _, slots = s.planned_nodes(design)
        expected = [r['node_id'] for r in slots]
        random.Random(20261025).shuffle(expected)
        self.assertEqual(expected, [n['id'] for n in s.planned_nodes(design)[0]])

    def test_guard_rejects_closed_and_outside(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'ROOT', Path(tmp).resolve()):
            base = Path(tmp).resolve() / 'research' / 'outputs'
            fresh = base / 'fresh'
            fresh.mkdir(parents=True)
            self.assertEqual(s.guard_output(fresh / 'new.json'), fresh / 'new.json')
            (fresh / 'CLOSED.json').write_text('{}')
            for p in (fresh / 'new.json', base / 'decision-check-20261025' / 'x.json', Path(tmp) / 'tracked.json'):
                with self.assertRaises((ValueError, runner.ExperimentError)):
                    s.guard_output(p)
            with self.assertRaises(runner.ExperimentError):
                s.guard_output(Path(tmp).parent / 'outside.json')

    def test_preview_nondispatchable_and_design_types_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'
            d = s.make_design('confirmation')
            p.write_bytes(json_bytes(d))
            preview = s.preview(p)
            self.assertEqual(len(preview['requests']), 72)
            self.assertNotIn('nodes', preview)
            for row in preview['requests']:
                self.assertEqual(row['sha256'], runner.sha(json_bytes(row['request'])))
            d['cases'][0]['x'] = float(d['cases'][0]['x'])
            p.write_bytes(json_bytes(d))
            with self.assertRaises(ValueError):
                s.read_design(p)


class ParsingAndScoringTests(unittest.TestCase):
    def test_exact_schema_rejects_bad_forms(self):
        case = s.current_case(s.make_design('matched')['cases'][0], 'changed')
        good = answer('check_first', case)
        invalid = [good + ' trailing', '```json\n' + good + '\n```',
                   good.replace('"x": 18', '"x": 18, "x": 18'),
                   good.replace('"x": 18', '"x": NaN'), good.replace('"x": 18', '"x": Infinity'),
                   good.replace('"x": 18', '"x": 1e999'),
                   answer('check_first', case, changes={'x': True}),
                   answer('check_first', case, changes={'x': 18.0}),
                   answer('check_first', case, changes={'current_threshold': '13'}),
                   answer('check_first', case, changes={'relation': 'EQ'}),
                   answer('check_first', case, account=' '),
                   answer('check_first', case, action='UNKNOWN'), '[]', '{}']
        for text in invalid:
            with self.subTest(text=text):
                parsed = s.parse_action({'status': 'complete', 'text': text}, 'check_first')
                self.assertFalse(parsed['action_valid'])
                self.assertIsNone(s.simulate(case, parsed)['utility'])

    def test_direct_order_is_inapplicable(self):
        case = s.make_design('reproduction')['cases'][0]
        parsed = s.parse_action({'status': 'complete', 'text': answer('direct', case, reverse=True)}, 'direct')
        self.assertTrue(parsed['action_valid'])
        self.assertEqual(parsed['actual_key_order'], ['account', 'action'])
        self.assertIsNone(parsed['requested_key_order'])
        self.assertIsNone(parsed['requested_order_compliant'])

    def test_bad_check_wrong_order_long_account_retain_action(self):
        case = s.current_case(s.make_design('matched')['cases'][0], 'changed')
        parsed = s.parse_action({'status': 'complete', 'text': answer('check_first', case,
                               changes={'x': 99, 'current_threshold': 50, 'relation': 'LT'},
                               reverse=True, account='word ' * 101)}, 'check_first')
        self.assertTrue(parsed['action_valid'])
        self.assertFalse(parsed['requested_order_compliant'])
        self.assertFalse(parsed['within_requested_account_length'])
        self.assertEqual(s.simulate(case, parsed)['utility'], 0)
        diagnostic = s.checks.check_diagnostics(case, parsed, 'check_first')
        self.assertFalse(diagnostic['correct_check'])
        self.assertTrue(diagnostic['incorrect_check_correct_direct'])

    def test_current_rule_projection_and_equality(self):
        design, slots, records = fixture_rows()
        report = s.score_rows(design, slots, records)
        self.assertTrue(all(r['correct_direct'] for r in report['rows']))
        self.assertTrue(all(r['correct_check'] for r in report['rows'] if r['condition'] != 'direct'))
        self.assertEqual(len(report['contrasts']), 9)
        self.assertTrue(all(c['difference'] == 0 and c['ci95'] == [0, 0] for c in report['contrasts'].values()))
        for rule in s.RULES:
            c = s.current_case(design['cases'][0], rule)
            c['x'] = c['threshold']
            parsed = s.parse_action({'status': 'complete', 'text': answer('check_first', c)}, 'check_first')
            self.assertEqual(parsed['relation'], 'GE')
            self.assertEqual(parsed['action'], 'ROUTE_HIGH')
            self.assertEqual(s.simulate(c, parsed)['cost'], 0)

    def test_malformed_and_incomplete_are_missing_not_zero(self):
        design, slots, records = fixture_rows()
        for index, slot in enumerate(slots[:3]):
            records[slot['node_id']] = {'status': 'complete' if index == 0 else 'incomplete', 'text': 'not json'}
        report = s.score_rows(design, slots, records)
        self.assertEqual(sum(r['score'] is None for r in report['rows']), 3)
        self.assertTrue(all(r['cost'] is None for r in report['rows'][:3]))

    def test_check_action_dissociations_and_measure(self):
        c = s.current_case(s.make_design('matched')['cases'][0], 'changed')
        for action, expected_cost, field in (('ROUTE_LOW', 4, 'correct_check_wrong_direct'), ('MEASURE', 1, 'correct_check_measure')):
            p = s.parse_action({'status': 'complete', 'text': answer('check_first', c, action=action)}, 'check_first')
            self.assertTrue(s.checks.check_diagnostics(c, p, 'check_first')[field])
            self.assertEqual(s.simulate(c, p)['cost'], expected_cost)

    def test_complete_pair_means_equal_world_weight(self):
        d, slots, records = fixture_rows()
        rows = s.score_rows(d, slots, records)['rows']
        # World 0 gets one observed +4 pair; world 1 two observed zero pairs.
        keep = []
        for r in rows:
            r = dict(r)
            r['valid'] = r['base_index'] in (0, 1) and r['rule'] == 'changed' and not (r['base_index'] == 0 and r['seed'] == 20260909)
            r['score'] = (4 if r['base_index'] == 0 and r['condition'] == 'check_first' else 0) if r['valid'] else None
            keep.append(r)
        result = s.contrast(keep, d, 'bundle_changed')
        self.assertEqual(result['valid_pairs'], 3)
        self.assertEqual(result['contributing_worlds'], 2)
        self.assertEqual(result['difference'], 2)
        self.assertEqual(result['partial_worlds'], [d['cases'][0]['base_id']])

    def test_interaction_uses_complete_quadruples(self):
        d, slots, records = fixture_rows()
        rows = s.score_rows(d, slots, records)['rows']
        for r in rows:
            r['score'] = (-4 if r['condition'] == 'direct' and r['rule'] == 'changed' else 0)
            if r['base_index'] == 0 and r['rule'] == 'unchanged' and r['condition'] == 'direct':
                r['valid'] = False
                r['score'] = None
        result = s.contrast(rows, d, 'bundle_interaction')
        self.assertEqual(result['valid_quadruples'], 10)
        self.assertEqual(result['contributing_worlds'], 5)
        self.assertEqual(result['difference'], 4)
        self.assertTrue(all(not r['valid'] for r in result['seed_differences'][:2]))
        with self.assertRaises(ValueError):
            s.contrast(rows + [rows[0]], d, 'bundle_changed')

    def test_no_complete_pairs_has_null_interval(self):
        d, slots, records = fixture_rows()
        rows = s.score_rows(d, slots, records)['rows']
        for r in rows:
            r['valid'], r['score'] = False, None
        result = s.contrast(rows, d, 'bundle_changed')
        self.assertIsNone(result['difference'])
        self.assertIsNone(result['ci95'])
        self.assertEqual(result['valid_pairs'], 0)

    def test_reproduction_gate_counts_wrong_direct_at_both_seeds(self):
        d, slots, records = fixture_rows('reproduction', reproduced_errors)
        report = s.score_rows(d, slots, records)
        self.assertTrue(report['reproduction_decision']['qualified'])
        self.assertEqual(report['reproduction_decision']['worlds_wrong_at_both_seeds'], 2)
        rows = deepcopy(report['rows'])
        # Unchanged wrong actions are complete valid actions and do not change gate.
        for r in rows:
            if r['rule'] == 'unchanged':
                r['wrong_route'] = True
        self.assertTrue(s.reproduction_decision(rows, d)['qualified'])
        rows[0]['valid'] = False
        self.assertFalse(s.reproduction_decision(rows, d)['qualified'])
        rows = deepcopy(report['rows'])
        for r in rows:
            if r['base_index'] == 1 and r['rule'] == 'changed' and r['seed'] == 7:
                r['wrong_route'] = False
                r['action'] = 'MEASURE'
        self.assertFalse(s.reproduction_decision(rows, d)['qualified'])

    def test_practical_gate_all_criteria_and_not_selected_secondary(self):
        def output(n, c):
            return answer(n['condition'], c, action=s.route(c['x'], 50) if n['kind'] == 'changed' and n['condition'] == 'direct' else None)
        d, slots, records = fixture_rows(callback=output)
        report = s.score_rows(d, slots, records)
        self.assertTrue(report['primary_gate']['qualified'])
        self.assertEqual(report['primary_gate']['difference'], 4)
        primary = deepcopy(report['contrasts'][s.PRIMARY])
        primary['valid_pairs'] = 11
        self.assertFalse(s.practical_gate(primary, d)['qualified'])
        primary = deepcopy(report['contrasts'][s.PRIMARY])
        for row in primary['seed_differences']:
            if row['seed'] == 7:
                row['difference'] = 0
        self.assertFalse(s.practical_gate(primary, d)['qualified'])
        primary = deepcopy(report['contrasts'][s.PRIMARY])
        primary['difference'] = .99
        self.assertFalse(s.practical_gate(primary, d)['qualified'])


class ReceiptChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def execute(self, split, *, repro=None, matched=None, callback=None, limit=None):
        design_path = self.root / (split + '-design.json')
        design_path.write_bytes(json_bytes(s.make_design(split)))
        protocol, ledger = s.build(design_path, reproduction_gate=repro, matched_gate=matched)
        protocol_path = self.root / (split + '-protocol.json')
        protocol_path.write_bytes(json_bytes(protocol))
        run = self.root / 'research' / 'outputs' / split
        runner.prepare(protocol_path, run, repository=self.root)
        output = []
        for node in protocol['nodes']:
            case = s.current_case(protocol['truth'][node['episode']], node['kind'])
            output.append(callback(node, case) if callback else answer(node['condition'], case))
        fake = Fake(output)
        runner.run_protocol(run, transport=fake, limit=limit)
        report = s.score(design_path, run)
        score_path = self.root / (split + '-score.json')
        score_path.write_bytes(json_bytes(report))
        return design_path, run, score_path, report, protocol, fake

    def gate(self, data):
        d, run, score_path, *_ = data
        out = self.root / (s.read_design(d)['split'] + '-gate.json')
        out.write_bytes(json_bytes(s.make_gate(d, run, score_path)))
        return out

    def test_full_chain_null_matched_still_permits_confirmation(self):
        reproduction = self.execute('reproduction', callback=reproduced_errors)
        repro = self.gate(reproduction)
        matched = self.execute('matched', repro=repro)
        match = self.gate(matched)
        self.assertFalse(s.read_gate(match)['decision']['qualified'])
        confirmation = self.execute('confirmation', repro=repro, matched=match)
        self.assertFalse(confirmation[3]['confirmation']['practical_replicated_improvement'])
        self.assertEqual(len(confirmation[3]['rows']), 72)
        for data in (reproduction, matched, confirmation):
            preview = s.preview(data[0])
            self.assertEqual(preview['schedule'], [n['id'] for n in data[4]['nodes']])
            self.assertEqual([r['request'] for r in preview['requests']], data[5].requests)
        out = self.root / 'research' / 'outputs' / 'readings'
        with patch.object(s, 'guard_output', side_effect=lambda p: runner.guard_output(p, self.root)):
            receipt = s.reading(confirmation[0], confirmation[1], out)
        self.assertEqual(receipt['packets'], 36)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertTrue(all(r['seed'] == 7 for r in key))
        self.assertEqual({r['condition'] for r in key}, set(s.FORMATS))
        self.assertNotIn('case_id', (out / 'reading.md').read_text())

    def test_failed_reproduction_prevents_later_build_and_reads_twelve(self):
        reproduction = self.execute('reproduction')
        gate = self.gate(reproduction)
        self.assertFalse(s.read_gate(gate)['decision']['qualified'])
        d = self.root / 'matched-design.json'
        d.write_bytes(json_bytes(s.make_design('matched')))
        with self.assertRaises(ValueError):
            s.build(d, reproduction_gate=gate)
        out = self.root / 'research' / 'outputs' / 'readings'
        with patch.object(s, 'guard_output', side_effect=lambda p: runner.guard_output(p, self.root)):
            self.assertEqual(s.reading(reproduction[0], reproduction[1], out)['packets'], 12)

    def test_pending_cannot_gate_or_read(self):
        data = self.execute('reproduction', callback=reproduced_errors, limit=1)
        with self.assertRaises(ValueError):
            self.gate(data)
        with self.assertRaises(ValueError):
            s.reading(data[0], data[1], self.root / 'unused')

    def test_tampered_gate_score_and_unexpected_gate_rejected(self):
        data = self.execute('reproduction', callback=reproduced_errors)
        gate = self.gate(data)
        v = json.loads(gate.read_text())
        v['decision']['qualified'] = False
        gate.write_bytes(json_bytes(v))
        with self.assertRaises(ValueError):
            s.read_gate(gate)
        with self.assertRaises(ValueError):
            s.build(data[0], reproduction_gate=gate)
        report = json.loads(data[2].read_text())
        report['rows'][0]['score'] = 10
        data[2].write_bytes(json_bytes(report))
        with self.assertRaises(ValueError):
            s.make_gate(data[0], data[1], data[2])

    def test_missing_required_gate_rejected(self):
        for split in ('matched', 'confirmation'):
            d = self.root / (split + '.json')
            d.write_bytes(json_bytes(s.make_design(split)))
            with self.assertRaises(ValueError):
                s.build(d)


if __name__ == '__main__':
    unittest.main()
