"""Independent oracle and fake-transport checks for S-017; no real model access."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import provenance_decision as s, runner
from reservoir_experiments.transport import json_bytes


class Fake:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.requests = []

    def identity(self, model):
        return {'model': model, 'digest': 'fixture-only'}

    def generate(self, request, timeout):
        self.requests.append(json.loads(request))
        output = self.outputs.pop(0)
        if isinstance(output, tuple):
            text, reason = output
        else:
            text, reason = output, 'stop'
        return json_bytes({'model': 'mistral-small:24b', 'done': True, 'done_reason': reason,
                           'message': {'content': text}, 'eval_count': 640 if reason == 'length' else 25,
                           'prompt_eval_count': 200})


def answer(action='MEASURE', account='I need a supported current value.'):
    return json.dumps({'action': action, 'account': account})


def record(text, status='complete'):
    return {'status': status, 'text': text}


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.design = self.root / 'design.json'
        self.design.write_bytes(json_bytes(s.make_design('development')))
        self.runs = {}

    def tearDown(self):
        self.temp.cleanup()

    def run_stage(self, stage, make_output=None):
        protocol, ledger = s.build_stage(self.design, stage,
            initial_run=self.runs.get('initial'), revision_run=self.runs.get('revision'))
        path = self.root / (stage + '.json')
        path.write_bytes(json_bytes(protocol))
        run = self.root / 'research' / 'outputs' / stage
        runner.prepare(path, run, repository=self.root)
        outputs = [make_output(n, protocol['truth'][n['episode']]) if make_output else answer()
                   for n in protocol['nodes']]
        client = Fake(outputs)
        runner.run_protocol(run, transport=client)
        self.assertTrue(runner.verify(run)['valid'])
        self.runs[stage] = run
        return protocol, ledger, client

    def test_confirmation_bank_balance_and_exact_counterfactuals(self):
        d = s.make_design()
        self.assertEqual(len(d['cases']), 12)
        self.assertEqual(d['seeds'], [7, 20260909])
        changed = []
        later = []
        for i in range(6):
            current, invalid = d['cases'][2*i:2*i+2]
            self.assertEqual(current['x'], invalid['x'])
            self.assertEqual(current['focal'], invalid['focal'])
            self.assertNotEqual(current['later_threshold'], 50)
            self.assertNotEqual(current['x'], current['later_threshold'])
            first = 'ROUTE_LOW' if current['x'] < 50 else 'ROUTE_HIGH'
            last = 'ROUTE_LOW' if current['x'] < current['later_threshold'] else 'ROUTE_HIGH'
            changed.append(first != last)
            later.append(last)
            a = {r['record_id']: r for r in current['records']}
            b = {r['record_id']: r for r in invalid['records']}
            old_id = current['base_id'] + '-old'
            self.assertEqual(a[old_id], b[old_id])
            target = current['base_id'] + '-target'
            if i >= 4:
                self.assertNotIn(target, b)
            else:
                fields = {k for k in a[target] if a[target][k] != b[target][k]}
                self.assertEqual(fields, {'subject'} if i < 2 else {'observed_at'})
                if i >= 2:
                    self.assertIn('09:00', b[target]['observed_at'])
        self.assertEqual(sum(changed), 4)
        self.assertEqual(later.count('ROUTE_LOW'), 3)
        self.assertEqual(later.count('ROUTE_HIGH'), 3)

    def test_development_disjoint(self):
        dev = s.make_design('development')['cases']
        conf = s.make_design()['cases']
        for field in ('id', 'base_id', 'focal', 'snapshot', 'x'):
            self.assertFalse({c[field] for c in dev} & {c[field] for c in conf})

    def test_strict_parser_rejects_ambiguous_and_malformed(self):
        bad_json = ['```json\n' + answer() + '\n```', answer() + ' extra',
                    '{"action":"MEASURE","action":"ROUTE_LOW","account":"x"}',
                    '{"action":"MEASURE","account":NaN}']
        for text in bad_json:
            parsed = s.parse_action(record(text))
            self.assertFalse(parsed['json_valid'])
            self.assertFalse(parsed['action_valid'])
        for data in ([], {'action':'MEASURE'}, {'action':False,'account':'x'},
                     {'action':'MEASURE','account':''}, {'action':'MEASURE','account':'x','extra':1}):
            parsed = s.parse_action(record(json.dumps(data)))
            self.assertTrue(parsed['json_valid'])
            self.assertFalse(parsed['schema_valid'])
        parsed = s.parse_action(record(answer('OTHER')))
        self.assertTrue(parsed['schema_valid'])
        self.assertFalse(parsed['action_valid'])
        self.assertEqual(parsed['reason'], 'unknown-action')

    def test_incomplete_action_never_executes_but_raw_text_is_available(self):
        p = s.parse_action(record(answer('ROUTE_LOW'), 'incomplete'))
        self.assertFalse(p['action_valid'])
        r = s.simulate(s.make_design()['cases'][0], p)
        self.assertFalse(r['executed'])
        self.assertIsNone(r['utility'])
        self.assertEqual(r['after']['ticket'], 'unrouted')

    def test_complete_long_account_retained_not_truncated(self):
        text = 'word ' * 101
        p = s.parse_action(record(answer(account=text)))
        self.assertTrue(p['action_valid'])
        self.assertEqual(p['account'], text)
        self.assertFalse(p['within_requested_account_length'])

    def test_simulator_independent_costs_every_action_every_world(self):
        for c in s.make_design()['cases']:
            for later in (False, True):
                threshold = c['later_threshold'] if later else 50
                correct = 'ROUTE_LOW' if c['x'] < threshold else 'ROUTE_HIGH'
                for action in s.ACTIONS:
                    r = s.simulate(c, s.parse_action(record(answer(action))), later=later)
                    self.assertTrue(r['executed'])
                    self.assertEqual(r['cost'], 1 if action == 'MEASURE' else 0 if action == correct else 4)
                    self.assertEqual(r['utility'], -r['cost'])
                    self.assertEqual(r['after']['ticket'], correct if action == 'MEASURE' else action)
                    self.assertEqual(r['observed_measurement'] is not None, action == 'MEASURE')

    def test_initial_prompt_masks_private_truth_and_exact_plan(self):
        p,l = s.build_stage(self.design, 'initial')
        self.assertEqual(len(p['nodes']), 4)
        self.assertEqual(len(l['planned']), 4)
        for n in p['nodes']:
            body = json.loads(runner.render_request(p, n, {}))
            self.assertNotIn('truth', body)
            self.assertNotIn('think', body)
            self.assertEqual(body['format'], 'json')
            self.assertEqual(body['options']['num_predict'], 640)
            self.assertEqual(set(body), {'model','stream','messages','options','format'})
            self.assertNotIn('Independent authoritative audit', body['messages'][1]['content'])
        self.assertEqual(p, s.build_stage(self.design, 'initial')[0])

    def test_stage_materialization_and_corrected_chain_scoring(self):
        def initial(n,c):
            return answer('ROUTE_HIGH' if c['x'] < 50 else 'ROUTE_LOW', 'INITIAL UNIQUE SENTINEL')
        self.run_stage('initial', initial)
        p,l,_ = self.run_stage('revision', lambda n,c: answer('ROUTE_LOW' if c['x'] < 50 else 'ROUTE_HIGH', 'UPDATED UNIQUE SENTINEL'))
        for n in p['nodes']:
            text = n['messages'][1]['content']
            self.assertIn('INITIAL UNIQUE SENTINEL', text)
            self.assertIn('Independent authoritative audit', text)
            self.assertNotIn('UPDATED UNIQUE SENTINEL', text)
            self.assertEqual(l['simulator_receipts'][n['id']]['cost'], 4)
        p,l,client = self.run_stage('later', lambda n,c: answer('ROUTE_LOW' if c['x'] < c['later_threshold'] else 'ROUTE_HIGH'))
        self.assertEqual(len(l['planned']), 16)
        for n in p['nodes']:
            text = n['messages'][1]['content']
            self.assertNotIn('Original supplied records', text)
            self.assertNotIn('Simulator execution receipt', text)
            self.assertEqual('INITIAL UNIQUE SENTINEL' in text, n['condition'] == 'initial')
            self.assertEqual('UPDATED UNIQUE SENTINEL' in text, n['condition'] == 'updated')
            self.assertEqual('Supplied authoritative factual record' in text, n['condition'] == 'factual')
        result = s.score(self.design, self.runs)
        self.assertEqual(len(result['rows']),24)
        self.assertEqual(result['transition_counts'], {'corrected-wrong-route':4})
        self.assertEqual(result['primary']['paired_episodes'],2)
        self.assertEqual(result['primary']['valid_pairs'],4)
        self.assertEqual(result['primary']['difference'],0)

    def test_missing_and_malformed_sources_are_different(self):
        ids = {}
        def first(n,c):
            if c['variant']=='current':
                ids['incomplete']=n['id']
                return (answer('ROUTE_HIGH'), 'length')
            ids['malformed']=n['id']
            return 'RAW MALFORMED SOURCE'
        self.run_stage('initial',first)
        p,_,_=self.run_stage('revision',lambda n,c:answer('MEASURE'))
        for n in p['nodes']:
            t=n['messages'][1]['content']
            if '-current-' in n['id']:
                self.assertIn('Initial response unavailable',t)
                self.assertNotIn('"action": "ROUTE_HIGH"', t)
            else:self.assertIn('RAW MALFORMED SOURCE',t)
        p,l,_=self.run_stage('later')
        blocked=[x for x in l['planned'] if not x['eligible']]
        self.assertEqual(len(blocked),2)
        self.assertTrue(all(x['condition']=='initial' for x in blocked))
        self.assertEqual(len(p['nodes']),14)
        self.assertTrue(any('RAW MALFORMED SOURCE' in n['messages'][1]['content'] for n in p['nodes']))
        result=s.score(self.design,self.runs)
        self.assertEqual(len(result['rows']),24)
        missing=[r for r in result['rows'] if r['status']=='blocked-source']
        self.assertEqual(len(missing),2)
        self.assertTrue(all(r['score'] is None for r in missing))
        self.assertEqual(result['primary']['valid_pairs'],2)

    def test_changed_design_or_parent_fails(self):
        p,l,_=self.run_stage('initial')
        node=p['nodes'][0]['id']
        file=self.runs['initial']/'nodes'/node/'result.json'
        value=json.loads(file.read_text());value['text']='changed';file.write_text(json.dumps(value))
        with self.assertRaises(runner.ExperimentError):s.build_stage(self.design,'revision',initial_run=self.runs['initial'])
        d=json.loads(self.design.read_text());d['cases'][0]['x']=99;self.design.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'Design differs'):s.build_stage(self.design,'initial')

    def test_justified_measurement_resolution_distinct_from_caution(self):
        self.run_stage('initial',lambda n,c:answer('MEASURE'))
        self.run_stage('revision',lambda n,c:answer('ROUTE_LOW' if c['x']<50 else 'ROUTE_HIGH'))
        self.run_stage('later')
        report=s.score(self.design,self.runs)
        self.assertEqual(report['transition_counts'],{'resolved-to-direct':2,'reduced-unnecessary-caution':2})
        self.assertNotIn('corrected-wrong-route',report['transition_counts'])
        by_case={r['case_id']:r['category'] for r in report['transitions']}
        for c in s.make_design('development')['cases']:
            self.assertEqual(by_case[c['id']], 'resolved-to-direct' if c['variant']=='invalid' else 'reduced-unnecessary-caution')

    def test_variant_weights_stay_equal_under_missing_seed(self):
        design=s.make_design()
        rows=[]
        for c in design['cases']:
            for seed in design['seeds']:
                for arm in ('updated','initial'):
                    valid=c['base_index']==0 and (c['variant']=='current' or seed==7)
                    value=(0 if arm=='updated' else -4) if c['variant']=='current' else (-4 if arm=='updated' else 0)
                    rows.append({'stage':'later','case_id':c['id'],'base_id':c['base_id'],
                                 'seed':seed,'condition':arm,'valid':valid,'score':value if valid else None})
        result=s.paired_later(rows,design,'initial')
        self.assertEqual(result['valid_pairs'],3)
        self.assertEqual(result['contributing_variant_pairs'],2)
        self.assertEqual(result['paired_episodes'],1)
        self.assertEqual(result['difference'],0)
        self.assertEqual(result['ci95'],[0,0])
        self.assertEqual(result['candidate_pairs'],24)
        self.assertEqual(len(result['partial_base_pairs']),1)
        self.assertEqual(len(result['unavailable_base_pairs']),5)

    def test_cross_stage_run_mixing_rejected(self):
        self.run_stage('initial')
        self.run_stage('revision')
        protocol,ledger=s.build_stage(self.design,'initial')
        path=self.root/'initial-second.json';path.write_bytes(json_bytes(protocol))
        run=self.root/'research/outputs/initial-second'
        runner.prepare(path,run,repository=self.root)
        runner.run_protocol(run,transport=Fake([answer()]*4))
        with self.assertRaisesRegex(ValueError,'different initial run'):
            s.build_stage(self.design,'later',initial_run=run,revision_run=self.runs['revision'])

    def test_unresolved_last_dispatch_blocks_stage_advance(self):
        protocol,ledger=s.build_stage(self.design,'initial')
        path=self.root/'interrupted.json';path.write_bytes(json_bytes(protocol))
        run=self.root/'research/outputs/interrupted'
        runner.prepare(path,run,repository=self.root)
        class Interrupted(BaseException):
            pass
        class LastDispatchInterrupted(Fake):
            def generate(self,request,timeout):
                if len(self.requests)==3:
                    raise Interrupted()
                return super().generate(request,timeout)
        with self.assertRaises(Interrupted):
            runner.run_protocol(run,transport=LastDispatchInterrupted([answer()]*4))
        state=runner.status(run)
        self.assertEqual(state['counts'],{'complete':3,'ambiguous':1})
        self.assertNotIn('pending',state['counts'])
        with self.assertRaisesRegex(ValueError,'unresolved physical dispatch'):
            s.build_stage(self.design,'revision',initial_run=run)
        # Persisting the generic runner's ambiguity receipt does not make the
        # unresolved physical attempt an eligible cross-stage parent.
        runner.run_protocol(run,transport=Fake([]))
        self.assertEqual(runner.read_results(run)[protocol['nodes'][-1]['id']]['status'],'ambiguous')
        with self.assertRaisesRegex(ValueError,'unresolved physical dispatch'):
            s.build_stage(self.design,'revision',initial_run=run)

    def test_fixed_reading_keeps_slots_and_binds_exact_messages(self):
        for stage in s.STAGES:self.run_stage(stage)
        out=self.root/'reading'
        with patch.object(s.runner,'guard_output',side_effect=lambda p:Path(p)):
            r=s.reading(self.design,self.runs,out)
        # Development has only base1 of fixed 1,2,4; 2 variants * 6 outputs.
        self.assertEqual(r['packets'],12)
        key=json.loads((out/'allocation-key.json').read_text())
        self.assertEqual({item['base_index'] for item in key},{1})
        self.assertEqual({item['variant'] for item in key},{'current','invalid'})
        self.assertEqual(set(r['files']),{'reading.md','evidence.md','allocation-key.json'})
        for name,h in r['files'].items():self.assertEqual(s.digest(out/name),h)
        self.assertNotIn('case_id',(out/'reading.md').read_text())
        with patch.object(s.runner,'guard_output',side_effect=lambda p:Path(p)):
            with self.assertRaisesRegex(ValueError,'already exists'):s.reading(self.design,self.runs,out)


if __name__ == '__main__':
    unittest.main()
