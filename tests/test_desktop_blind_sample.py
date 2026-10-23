"""`probes/desktop_blind_sample.py`: the sample withholds labels, spaces its picks, and skips
each session's opening entries (default 1, `--skip N`, `--include-first`)."""
import json, os, subprocess, sys, tempfile, unittest

PROBE = os.path.join(os.path.dirname(__file__), '..', 'probes', 'desktop_blind_sample.py')


def session(root, name, n):
    d = os.path.join(root, name, 'journals'); os.makedirs(d)
    for k in range(1, n + 1):
        json.dump({'pending': {'entry': {'observedStep': 30 * k, 'id': f'{name}-{k}', 'text': f'{name} entry {k}'}}},
                  open(os.path.join(d, f'journal-{30 * k:04d}.json'), 'w'))
    return os.path.join(root, name)


def run(root, *args):
    out = os.path.join(root, 'out')
    subprocess.run([sys.executable, PROBE, '--out', out, *args], check=True, capture_output=True)
    key = json.load(open(os.path.join(out, 'blind-sample-key.json')))
    md = open(os.path.join(out, 'blind-sample.md')).read()
    return key, md


class BlindSample(unittest.TestCase):
    def test_default_skips_the_first_entry_and_withholds_labels(self):
        with tempfile.TemporaryDirectory() as root:
            a, b = session(root, 'left', 10), session(root, 'right', 10)
            key, md = run(root, '--per', '2', '--seed', '1', f'left={a}', f'right={b}')
            self.assertEqual(sorted(r['step'] for r in key if r['label'] == 'left'), [60, 300])
            self.assertEqual(len(key), 4)
            self.assertNotIn('left', md.split('\n\n', 1)[0]); self.assertNotIn('right', md.split('\n\n', 1)[0])
            self.assertNotIn('left=', md); self.assertIn('## 1 · step', md)

    def test_skip_n_clears_the_shared_opening(self):
        with tempfile.TemporaryDirectory() as root:
            a = session(root, 'armA', 40)
            key, _ = run(root, '--per', '2', '--skip', '9', f'armA={a}')
            self.assertEqual(sorted(r['step'] for r in key), [300, 1200])

    def test_include_first_keeps_the_first_entry(self):
        with tempfile.TemporaryDirectory() as root:
            a = session(root, 'armA', 5)
            key, _ = run(root, '--per', '2', '--include-first', f'armA={a}')
            self.assertEqual(sorted(r['step'] for r in key), [30, 150])


if __name__ == '__main__':
    unittest.main()
