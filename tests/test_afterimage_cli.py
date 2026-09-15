"""The file-based trace command works without an index and refuses wrong IDs."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from reservoir_research.cli import main
from tests.test_afterimages import AFTERIMAGE, capture, exposure, source


class AfterimageCliTests(unittest.TestCase):
    def test_account_without_cache_and_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            bundle, out, db = root / 'capture.json', root / 'report', root / 'no-index.sqlite3'
            bundle.write_text(json.dumps(capture(source('exposure', exposure(included=False)))), encoding='utf-8')
            arguments = ['--db', str(db), 'afterimage-trace', AFTERIMAGE, '--capture', str(bundle), '--out', str(out)]
            with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(main(arguments), 0, stderr.getvalue())
            result = json.loads(stdout.getvalue())
            self.assertEqual(result['summary']['included_false'], 1)
            self.assertFalse(db.exists())
            before = (out / 'account.md').read_bytes()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertNotEqual(main(arguments), 0)
            self.assertEqual((out / 'account.md').read_bytes(), before)

    def test_requested_identity_must_match_before_output_creation(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            bundle, out = root / 'capture.json', root / 'report'
            bundle.write_text(json.dumps(capture()), encoding='utf-8')
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = main(['afterimage-trace', AFTERIMAGE + '_wrong', '--capture', str(bundle), '--out', str(out)])
            self.assertNotEqual(result, 0)
            self.assertFalse(out.exists())
