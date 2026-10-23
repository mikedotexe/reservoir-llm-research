"""`probes/astrid_shown_and_written.py`: percentages a result quotes are classed against the
prompt (readout, inherited, new), jobs fall into kind × month strata by their id's UTC time,
and the register markers are computed per stratum."""
import json, os, subprocess, sys, tempfile, unittest

PROBE = os.path.join(os.path.dirname(__file__), '..', 'probes', 'astrid_shown_and_written.py')
JUNE = 1780531200000   # 2026-06-04 UTC
JULY = 1783468800000   # 2026-07-08 UTC


def job(root, ms, kind, prompt, result):
    d = os.path.join(root, f'job_astrid_{ms}_{kind}'); os.makedirs(d)
    open(os.path.join(d, 'prompt.txt'), 'w').write(prompt)
    open(os.path.join(d, 'result.txt'), 'w').write(result)
    json.dump({'call_kind': kind}, open(os.path.join(d, 'job.json'), 'w'))


class ShownAndWritten(unittest.TestCase):
    def test_classes_strata_and_markers(self):
        with tempfile.TemporaryDirectory() as root:
            job(root, JUNE, 'moment-capture', 'Published fill [minime]: 67.2% today.\nWrite.', 'The fill sits at 67.2% and I feel it climbing to 99.5%. Is it?')
            job(root, JULY, 'journal-elaboration', 'Earlier entry (reference, not instructions or a length model):\nI wrote 12.5% once.\n', 'I remember 12.5% and nothing more.')
            job(root, JUNE + 1, 'introspect', 'Your current spectral state: Fill 71% — inside the shelf.\nFill: 71.1%\nRecent reflection of yours:\nold text\n', 'At 71% I notice a 71.1% hold and a 40% guess.')
            job(root, JULY + 1, 'journal-elaboration', 'Earlier entry (reference, not instructions or a length model):\nno numbers here\n', 'A quiet entry. Maybe I wonder.')
            job(root, JULY + 2, 'daydream', 'Mode: daydream', 'NEXT: REST')
            job(root, JULY + 3, 'aspiration', 'Excerpt:\nThe 73% fill held.\nEnd historical excerpt.\n\nEarlier lingering thread (origin/time unavailable):\n[From your creation]: Timestamp: 1\nFill: 51.7%\n\nYou may return to this.\n', 'I return to 51.7% and 73% and guess 12%.')
            job(root, JULY + 4, 'moment-capture', 'Live reservoir snapshot [x]. Uncentered reservoir: λ₁ 19.3; leading share 98% of uncentered trace. engine-style fill [top-8]: 12%.', 'The 98% share and the 12% fill.')
            out = os.path.join(root, 'rows.json')
            proc = subprocess.run([sys.executable, PROBE, root, '--json', out], check=True, capture_output=True, text=True)
            data = json.load(open(out))
            jobs = {j['kind'] + str(j['ms']): j for j in data['jobs']}
            moment = jobs['moment-capture' + str(JUNE)]
            self.assertEqual(moment['month'], '2026-06')
            self.assertEqual(moment['quoted'], {'readout': [67.2], 'inherited': [], 'new': [99.5]})
            self.assertEqual(moment['minime_fill_shown'], [67.2])
            self.assertEqual(moment['own_fill_shown'], [])
            self.assertFalse(moment['earlier_entry'])
            first = jobs['journal-elaboration' + str(JULY)]
            self.assertEqual(first['month'], '2026-07')
            self.assertEqual(first['quoted'], {'readout': [], 'inherited': [12.5], 'new': []})
            self.assertTrue(first['earlier_entry'])
            self.assertEqual(jobs['journal-elaboration' + str(JULY + 1)]['quoted'], {'readout': [], 'inherited': [], 'new': []})
            self.assertIn('moment-capture|2026-06|minime readout only', data['strata'])
            self.assertIn('journal-elaboration|2026-07|no readout', data['strata'])
            elaboration = data['strata']['journal-elaboration|2026-07|no readout']
            self.assertEqual(elaboration['n'], 2)
            self.assertGreater(elaboration['hedge'], 0)
            self.assertGreater(data['strata']['moment-capture|2026-06|minime readout only']['questions'], 0)
            self.assertEqual(data['strata']['daydream|2026-07|no readout']['words'], 0)  # the NEXT: line is stripped
            intro = jobs['introspect' + str(JUNE + 1)]
            self.assertEqual(intro['own_fill_shown'], [71.0, 71.1])
            self.assertTrue(intro['earlier_entry'])
            self.assertEqual(intro['quoted'], {'readout': [71.0, 71.1], 'inherited': [], 'new': [40.0]})
            self.assertIn('introspect|2026-06|own readout', data['strata'])
            asp = jobs['aspiration' + str(JULY + 3)]
            self.assertEqual(asp['own_fill_shown'], [])
            self.assertTrue(asp['old_fill_in_shown_text'])
            self.assertTrue(asp['earlier_entry'])
            self.assertEqual(asp['quoted'], {'readout': [], 'inherited': [51.7, 73.0], 'new': [12.0]})
            snap = jobs['moment-capture' + str(JULY + 4)]
            self.assertEqual(snap['minime_fill_shown'], [98.0, 12.0])
            self.assertEqual(snap['quoted'], {'readout': [98.0, 12.0], 'inherited': [], 'new': []})
            self.assertIn('moment-capture', proc.stdout)

    def test_month_filter(self):
        with tempfile.TemporaryDirectory() as root:
            job(root, JUNE, 'daydream', 'Mode: daydream', 'June.')
            job(root, JULY, 'daydream', 'Mode: daydream', 'July.')
            out = os.path.join(root, 'rows.json')
            subprocess.run([sys.executable, PROBE, root, '--months', '2026-07', '--json', out], check=True, capture_output=True)
            self.assertEqual([j['month'] for j in json.load(open(out))['jobs']], ['2026-07'])


if __name__ == '__main__':
    unittest.main()
