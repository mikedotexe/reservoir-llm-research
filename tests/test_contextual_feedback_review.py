import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PROBE = Path(__file__).resolve().parents[1] / 'probes/contextual_feedback_review.py'
SPEC = importlib.util.spec_from_file_location('contextual_feedback_review', PROBE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ContextualReviewTests(unittest.TestCase):
    def test_failures_missing_cells_and_teacher_text_keep_separate_denominators(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trials = [dict(id=name, kind=kind, arm='contextual', state='persisted',
                           seed=91, case='worker') for name, kind in (
                ('free-complete', 'free'), ('free-empty', 'free'),
                ('free-admission', 'free'), ('free-missing', 'free'),
                ('fixed-teacher', 'fixed'))]
            (root / 'protocol.json').write_text(json.dumps(dict(trials=trials)))
            complete = dict(text='A revision.\nNEXT: REST\n```\nNEXT: READ_MORE\n```',
                            finish='stop', completion_tokens=25, seconds=2)
            for identity, result, outcome, error in (
                ('free-complete', complete, 'stop', None),
                ('free-empty', dict(text='', finish='stop'), 'stop', None),
                ('free-admission', None, 'technical_error',
                 'RuntimeError: no idle live-service window within 120 seconds'),
                ('fixed-teacher', dict(text='Imposed text', finish='length'), 'length', None)):
                (root / (identity + '.json')).write_text(json.dumps(
                    dict(result=result, outcome=outcome, error=error)))
            result = MODULE.review(root)
            self.assertEqual(result['missing'], ['free-missing'])
            self.assertEqual(result['denominators']['free'],
                             dict(planned=4, recorded=3, generated=2, nonempty_terminal=1))
            self.assertEqual(result['cells'][0]['next_choice']['raw'], 'REST')
            self.assertEqual(result['cells'][2]['outcome_class'], 'resource_admission_failure')
            self.assertIsNone(result['cells'][-1]['next_choice'])
            self.assertFalse(result['length_is_success_criterion'])

    def test_annotation_requires_exact_response_and_verbatim_quote(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = 'free-worker-91-contextual'
            spec = dict(id=identity, kind='free', arm='contextual', state='persisted', seed=91, case='worker')
            (root / 'protocol.json').write_text(json.dumps(dict(trials=[spec])))
            response = 'The worker is reused.'
            (root / (identity + '.json')).write_text(json.dumps(dict(
                outcome='stop', result=dict(text=response, finish='stop'))))
            annotation = dict(trial_id=identity, response_sha256=hashlib.sha256(response.encode()).hexdigest(),
                              claims=[dict(quote='worker is reused', verdict='supported')])
            path = root / 'claim-annotations.json'
            path.write_text(json.dumps([annotation]))
            self.assertEqual(MODULE.review(root)['unannotated_free'], [])
            annotation['claims'][0]['quote'] = 'A fabricated quote'
            path.write_text(json.dumps([annotation]))
            with self.assertRaisesRegex(ValueError, 'quote not present'):
                MODULE.review(root)
            annotation['claims'] = []
            annotation['response_sha256'] = 'different'
            path.write_text(json.dumps([annotation]))
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                MODULE.review(root)


if __name__ == '__main__':
    unittest.main()
