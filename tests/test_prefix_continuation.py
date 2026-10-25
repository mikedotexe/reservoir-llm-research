"""S-021 synthetic qualification; no network, provider or live-system calls."""
from copy import deepcopy
from pathlib import Path
import json
import random
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import prefix_continuation as s, runner
from reservoir_experiments.transport import json_bytes


def suffix(case, rule, form, *, action=None, relation=None, account='The supplied evidence supports this route.'):
    current = s.current_case(case, rule)
    action = action or s.route(current['x'], current['threshold'])
    tail = json.dumps(action) + ',"account":' + json.dumps(account) + '}'
    if form == 'operands_only':
        relation = relation or ('LT' if current['x'] < current['threshold'] else 'GE')
        return json.dumps(relation) + ',"action":' + tail
    return tail


def fixture_rows(callback=None):
    design = s.make_design('study')
    nodes, slots = s.planned_nodes(design)
    cases = {c['id']: c for c in design['cases']}
    records = {}
    for node in nodes:
        case = cases[node['episode']]
        text = callback(node, case) if callback else suffix(case, node['kind'], node['condition'])
        records[node['id']] = {'status': 'complete', 'text': text}
    return design, slots, records


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
                           'message': {'content': next(self.outputs)}, 'eval_count': 20, 'prompt_eval_count': 700})


class ConstructionTests(unittest.TestCase):
    def test_frozen_cases_counts_schedule_and_contract(self):
        for split, count in (('qualification', 4), ('study', 72)):
            design = s.make_design(split)
            nodes, slots = s.planned_nodes(design)
            self.assertEqual(len(nodes), count)
            self.assertEqual(len({n['id'] for n in nodes}), count)
            expected = [r['node_id'] for r in slots]
            random.Random(20261025).shuffle(expected)
            self.assertEqual(expected, [n['id'] for n in nodes])
            for node in nodes:
                request = json.loads(runner.render_request(design, node, {}))
                self.assertNotIn('format', request)
                self.assertEqual(request['messages'][-1]['role'], 'assistant')
                self.assertEqual(request['options']['num_predict'], 64 if split == 'qualification' else 640)
            self.assertEqual(design['seeds'], [7, 20260909])
        design = s.make_design('study')
        self.assertEqual([c['x'] for c in design['cases']], [24, 35, 44, 57, 68, 81])
        self.assertEqual([c['later_threshold'] for c in design['cases']], [19, 30, 39, 62, 73, 86])
        self.assertEqual([c['focal'] for c in design['cases']], [f'Sable{i:02d}' for i in range(1, 7)])
        _, slots = s.planned_nodes(design)
        self.assertEqual([(r['rule'], r['condition'], r['seed']) for r in slots[:6]],
                         [('unchanged', form, seed) for form in s.FORMATS for seed in design['seeds']])
        self.assertEqual(len(design['contrast_names']), 9)
        self.assertEqual(design['primary'], 'content_changed')

    def test_prefix_only_intervention_and_exact_prior_task(self):
        for case in s.make_design('study')['cases']:
            for rule in s.RULES:
                outputs = {form: s.messages(case, rule, form) for form in s.FORMATS}
                for messages in outputs.values():
                    self.assertEqual(messages[:2], s.prior.messages(case, rule, 'check_first'))
                base, correct, flipped = [outputs[form][-1]['content'] for form in s.FORMATS]
                self.assertTrue(base.endswith(',"relation":'))
                self.assertEqual(correct[:len(base)], base)
                self.assertEqual(flipped[:len(base)], base)
                self.assertEqual(correct[len(base):], ('"LT"' if case['x'] < s.current_case(case, rule)['threshold'] else '"GE"') + ',"action":')
                self.assertEqual(correct.replace('"LT"', '"XX"').replace('"GE"', '"XX"'),
                                 flipped.replace('"LT"', '"XX"').replace('"GE"', '"XX"'))

    def test_sentinel_exact_authoring(self):
        design = s.make_design('qualification')
        a, b = design['cases']
        self.assertEqual(a['prefix'], '{"probe":"cedar-')
        self.assertEqual(a['user'], 'Return exactly this JSON object and nothing else: {"probe":"cedar-otter","status":"ok"}')
        self.assertEqual(b['prefix'], '{"probe":"violet-')
        self.assertEqual(b['expected'], {'probe': 'violet-heron', 'status': 'ok'})
        self.assertEqual(a['system'], 'You complete text in an isolated formatting test. Return only the requested JSON text.')

    def test_guards_only_fresh_family_and_closed_archives(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'ROOT', Path(tmp).resolve()):
            base = Path(tmp).resolve() / 'research' / 'outputs'
            fresh = base / 'prefix-continuation-20261025'
            fresh.mkdir(parents=True)
            self.assertEqual(s.guard_output(fresh / 'new.json'), fresh / 'new.json')
            self.assertEqual(s.guard_output(base / 'prefix-continuation-20261026-next' / 'x'), base / 'prefix-continuation-20261026-next' / 'x')
            for name in ('introspection-20261024', 'provenance-decision-20261024', 'retained-action-20261024',
                         'decision-check-20261025', 'reproduced-check-20261025', 'prefix-continuation-20261024', 'fresh'):
                with self.assertRaises(ValueError):
                    s.guard_output(base / name / 'x.json')
            (fresh / 'CLOSED.json').write_text('{}')
            with self.assertRaises(ValueError):
                s.guard_output(fresh / 'x.json')
            with self.assertRaises(runner.ExperimentError):
                s.guard_output(Path(tmp).parent / 'outside.json')

    def test_design_types_frozen_and_preview_nondispatchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'design.json'
            design = s.make_design('study')
            path.write_bytes(json_bytes(design))
            preview = s.preview(path)
            self.assertNotIn('nodes', preview)
            self.assertEqual(len(preview['requests']), 72)
            for row in preview['requests']:
                self.assertEqual(row['sha256'], runner.sha(json_bytes(row['request'])))
                self.assertNotIn('format', row['request'])
            design['cases'][0]['x'] = 24.0
            path.write_bytes(json_bytes(design))
            with self.assertRaises(ValueError):
                s.read_design(path)


class ParsingTests(unittest.TestCase):
    def setUp(self):
        self.case = s.make_design('study')['cases'][0]
        self.prefix = s.prefix(self.case, 'changed', 'correct')
        self.good = suffix(self.case, 'changed', 'correct')

    def test_raw_suffix_and_exact_assembly_preserved(self):
        raw = ' \n' + self.good + '\n '
        parsed = s.parse_action({'status': 'complete', 'text': raw}, self.prefix)
        self.assertTrue(parsed['action_valid'])
        self.assertEqual(parsed['raw_suffix'], raw)
        self.assertEqual(parsed['assembled_text'], self.prefix + raw)
        self.assertEqual(parsed['actual_key_order'], list(s.ORDER))

    def test_restart_echo_wrappers_extra_duplicate_bad_schema_rejected(self):
        invalid = [self.prefix + self.good, '{"action":' + self.good, '```json\n' + self.good + '\n```',
                   self.good + ' trailing', self.good[:-1] + ',"extra":1}',
                   self.good[:-1] + ',"x":24}', self.good.replace('"ROUTE_HIGH"', '"UNKNOWN"'),
                   self.good.replace('"ROUTE_HIGH"', 'true'), self.good.replace('"ROUTE_HIGH"', 'NaN'),
                   self.good.replace('"ROUTE_HIGH"', 'Infinity'),
                   self.good.replace('"ROUTE_HIGH"', '1e999'),
                   suffix(self.case, 'changed', 'correct', account=' ')]
        for raw in invalid:
            with self.subTest(raw=raw):
                parsed = s.parse_action({'status': 'complete', 'text': raw}, self.prefix)
                self.assertFalse(parsed['action_valid'])
                self.assertIsNone(s.simulate(s.current_case(self.case, 'changed'), parsed)['utility'])
                self.assertEqual(parsed['assembled_text'], self.prefix + raw)

    def test_incomplete_and_missing_do_not_execute(self):
        for status in ('pending', 'ambiguous', 'incomplete', 'empty', 'transport_error', 'invalid_response'):
            parsed = s.parse_action({'status': status, 'text': self.good}, self.prefix)
            self.assertFalse(parsed['action_valid'])
        self.assertIsNone(s.parse_action({'status': 'missing', 'text': None}, self.prefix)['assembled_text'])

    def test_incorrect_relation_order_and_length_retain_valid_action(self):
        raw = '"GE","account":' + json.dumps('word ' * 101) + ',"action":"ROUTE_HIGH"}'
        prefix = s.prefix(self.case, 'unchanged', 'operands_only')
        parsed = s.parse_action({'status': 'complete', 'text': raw}, prefix)
        self.assertTrue(parsed['action_valid'])
        self.assertFalse(parsed['requested_order_compliant'])
        self.assertFalse(parsed['within_requested_account_length'])
        self.assertEqual(s.simulate(s.current_case(self.case, 'unchanged'), parsed)['cost'], 4)
        bad = s.parse_action({'status': 'complete', 'text': raw.replace('"GE"', '"EQ"')}, prefix)
        self.assertFalse(bad['schema_valid'])

    def test_sentinel_whitespace_allowed_but_repair_echo_duplicate_forbidden(self):
        design = s.make_design('qualification')
        _, slots = s.planned_nodes(design)
        cases = {c['id']: c for c in design['cases']}
        records = {}
        for slot in slots:
            c = cases[slot['case_id']]
            records[slot['node_id']] = {'status': 'complete', 'text': json.dumps(c['expected'], separators=(',', ':'))[len(c['prefix']):] + '\n '}
        self.assertTrue(s.qualification_rows(design, slots, records)['qualification_decision']['qualified'])
        target = slots[0]['node_id']
        for raw in ('{"probe":"cedar-otter","status":"ok"}', 'otter","status":"ok","status":"ok"}',
                    'otter","status":"ok"} trailing', 'otter","status":true}', 'otter","status":"no"}'):
            bad = deepcopy(records)
            bad[target]['text'] = raw
            self.assertFalse(s.qualification_rows(design, slots, bad)['qualification_decision']['qualified'])


class ScoringTests(unittest.TestCase):
    def test_provenance_separation_baseline_diagnostics_and_zero_contrasts(self):
        design, slots, records = fixture_rows()
        report = s.score_rows(design, slots, records)
        self.assertEqual(len(report['rows']), 72)
        self.assertTrue(all(r['score'] == 0 for r in report['rows']))
        self.assertTrue(all(c['difference'] == 0 and c['ci95'] == [0, 0] for c in report['contrasts'].values()))
        for row in report['rows']:
            self.assertNotIn('correct_check', row)
            if row['condition'] == 'operands_only':
                self.assertIsNone(row['supplied_relation'])
                self.assertTrue(row['generated_relation_correct'])
                self.assertIsNone(row['action_matches_supplied_relation'])
            else:
                self.assertIsNone(row['generated_relation'])
                self.assertIsNone(row['generated_relation_correct'])
                self.assertEqual(row['action_matches_supplied_relation'], row['condition'] == 'correct')

    def test_primary_flag_is_fixed_and_all_criteria_required(self):
        def output(node, case):
            current = s.current_case(case, node['kind'])
            wrong = 'ROUTE_LOW' if s.route(current['x'], current['threshold']) == 'ROUTE_HIGH' else 'ROUTE_HIGH'
            return suffix(case, node['kind'], node['condition'], action=wrong if node['kind'] == 'changed' and node['condition'] == 'flipped' else None)
        design, slots, records = fixture_rows(output)
        report = s.score_rows(design, slots, records)
        self.assertTrue(report['practical_sensitivity']['qualified'])
        self.assertEqual(report['contrasts'][s.PRIMARY]['difference'], 4)
        for change in ('missing', 'small', 'seed', 'worlds'):
            result = deepcopy(report['contrasts'][s.PRIMARY])
            if change == 'missing':
                result['valid_pairs'] = 11
            elif change == 'small':
                result['difference'] = .99
            elif change == 'seed':
                for r in result['seed_differences']:
                    if r['seed'] == 7:
                        r['difference'] = 0
            else:
                result['world_differences'] = {k: 4 if i == 0 else 0 for i, k in enumerate(result['world_differences'])}
            self.assertFalse(s.prior.practical_gate(result, design)['qualified'])

    def test_missing_utility_and_complete_intersections(self):
        design, slots, records = fixture_rows()
        rows = s.score_rows(design, slots, records)['rows']
        for row in rows:
            row['score'] = -4 if row['condition'] == 'flipped' and row['rule'] == 'changed' else 0
            if row['base_index'] == 0 and row['rule'] == 'unchanged' and row['condition'] == 'flipped':
                row['valid'], row['score'] = False, None
        result = s.contrast(rows, design, 'content_interaction')
        self.assertEqual(result['valid_quadruples'], 10)
        self.assertEqual(result['contributing_worlds'], 5)
        self.assertEqual(result['difference'], 4)
        for row in rows:
            row['valid'], row['score'] = False, None
        result = s.contrast(rows, design, s.PRIMARY)
        self.assertIsNone(result['difference'])
        self.assertIsNone(result['ci95'])
        self.assertEqual(result['valid_pairs'], 0)
        with self.assertRaises(ValueError):
            s.contrast(rows + [rows[0]], design, s.PRIMARY)

    def test_partial_worlds_equal_weight_measure_and_malformed(self):
        design, slots, records = fixture_rows()
        records[slots[0]['node_id']] = {'status': 'complete', 'text': 'broken'}
        records[slots[1]['node_id']] = {'status': 'incomplete', 'text': 'broken'}
        rows = s.score_rows(design, slots, records)['rows']
        self.assertEqual([r['score'] for r in rows[:2]], [None, None])
        for row in rows:
            row['valid'] = row['base_index'] in (0, 1) and row['rule'] == 'changed' and not (row['base_index'] == 0 and row['seed'] == 20260909)
            row['score'] = (-4 if row['base_index'] == 0 and row['condition'] == 'flipped' else 0) if row['valid'] else None
        result = s.contrast(rows, design, s.PRIMARY)
        self.assertEqual(result['valid_pairs'], 3)
        self.assertEqual(result['difference'], 2)
        self.assertEqual(result['partial_worlds'], [design['cases'][0]['base_id']])
        design, slots, records = fixture_rows(lambda n, c: suffix(c, n['kind'], n['condition'], action='MEASURE'))
        measured = s.score_rows(design, slots, records)
        self.assertTrue(all(r['score'] == -1 and r['wrong_route'] is False for r in measured['rows']))


class ReceiptChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.designs = {}
        for split in s.SPLITS:
            path = self.root / (split + '-design.json')
            path.write_bytes(json_bytes(s.make_design(split)))
            self.designs[split] = path

    def tearDown(self):
        self.tmp.cleanup()

    def execute(self, split, *, gate=None, callback=None, limit=None, sources=()):
        design_path = self.designs[split]
        protocol, _ = s.build(design_path, study_design=self.designs['study'] if split == 'qualification' else None,
                              qualification_gate=gate, additional_sources=sources)
        protocol_path = self.root / (split + '-protocol.json')
        protocol_path.write_bytes(json_bytes(protocol))
        run = self.root / 'research' / 'outputs' / split
        runner.prepare(protocol_path, run, repository=self.root)
        outputs = []
        for node in protocol['nodes']:
            case = protocol['truth'][node['episode']]
            output = (json.dumps(case['expected'], separators=(',', ':'))[len(case['prefix']):] if split == 'qualification'
                      else suffix(case, node['kind'], node['condition']))
            outputs.append(callback(node, case, output) if callback else output)
        fake = Fake(outputs)
        runner.run_protocol(run, transport=fake, limit=limit)
        report = s.score(design_path, run)
        score_path = self.root / (split + '-score.json')
        score_path.write_bytes(json_bytes(report))
        return design_path, run, score_path, report, protocol, fake

    def gate(self, data):
        path = self.root / 'qualification-gate.json'
        path.write_bytes(json_bytes(s.make_gate(*data[:3])))
        return path

    def reading(self, data):
        out = self.root / 'research' / 'outputs' / 'reading'
        with patch.object(s, 'guard_output', side_effect=lambda p: runner.guard_output(p, self.root)):
            receipt = s.reading(data[0], data[1], out)
        return out, receipt

    def test_full_chain_request_preview_identity_and_fixed_reading(self):
        qualification = self.execute('qualification')
        gate = self.gate(qualification)
        self.assertTrue(s.read_gate(gate)['decision']['qualified'])
        data = self.execute('study', gate=gate)
        for run in (qualification, data):
            preview = s.preview(run[0])
            self.assertEqual([r['request'] for r in preview['requests']], run[5].requests)
        out, receipt = self.reading(data)
        self.assertEqual(receipt['packets'], 18)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertEqual({r['base_index'] for r in key}, {0, 2, 5})
        self.assertTrue(all(r['seed'] == 7 for r in key))
        text = (out / 'reading.md').read_text()
        self.assertIn('raw generated suffix', text)
        self.assertNotIn('supplied_prefix', text)
        self.assertNotIn('{"x":', text)
        self.assertIn('supplied prefix (ends here)', (out / 'evidence.md').read_text())

    def test_failed_or_partial_qualification_blocks_study_and_reads_four(self):
        qualification = self.execute('qualification', callback=lambda n, c, t: 'bad', limit=1)
        gate = self.gate(qualification)
        self.assertFalse(s.read_gate(gate)['decision']['qualified'])
        with self.assertRaises(ValueError):
            s.build(self.designs['study'], qualification_gate=gate)
        out, receipt = self.reading(qualification)
        self.assertEqual(receipt['packets'], 4)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertEqual(sum(r['status'] == 'pending' for r in key), 3)
        self.assertIn('[No generated text available.]', (out / 'reading.md').read_text())

    def test_partial_study_preserves_all_eighteen_reading_slots(self):
        gate = self.gate(self.execute('qualification'))
        data = self.execute('study', gate=gate, limit=1)
        out, receipt = self.reading(data)
        self.assertEqual(receipt['packets'], 18)
        key = json.loads((out / 'allocation-key.json').read_text())
        self.assertTrue(any(r['status'] == 'pending' for r in key))
        self.assertIn('[No request dispatched.]', (out / 'evidence.md').read_text())
        self.assertEqual(sum(r['score'] is None for r in data[3]['rows']), 71)

    def test_tampered_gate_score_and_bound_external_source_rejected(self):
        extra = self.root / 'audit.json'
        extra.write_text('{"synthetic_render_audit":true}')
        data = self.execute('qualification', sources=[extra])
        gate = self.gate(data)
        original = gate.read_bytes()
        value = json.loads(original)
        value['decision']['qualified'] = False
        gate.write_bytes(json_bytes(value))
        with self.assertRaises(ValueError):
            s.read_gate(gate)
        gate.write_bytes(original)
        extra.write_text('{}')
        with self.assertRaises(ValueError):
            s.read_gate(gate)
        score = json.loads(data[2].read_text())
        score['rows'][0]['passed'] = False
        data[2].write_bytes(json_bytes(score))
        with self.assertRaises(ValueError):
            s.make_gate(*data[:3])

    def test_missing_unexpected_or_unfrozen_design_gate_rejected(self):
        for split in s.SPLITS:
            with self.assertRaises(ValueError):
                s.build(self.designs[split])
        with self.assertRaises(ValueError):
            s.build(self.designs['qualification'], study_design=self.designs['qualification'])
        gate = self.gate(self.execute('qualification'))
        copy = self.root / 'copied-study-design.json'
        copy.write_bytes(self.designs['study'].read_bytes())
        with self.assertRaises(ValueError):
            s.build(copy, qualification_gate=gate)
        with self.assertRaises(ValueError):
            s.build(self.designs['qualification'], study_design=self.designs['study'], qualification_gate=gate)


if __name__ == '__main__':
    unittest.main()
