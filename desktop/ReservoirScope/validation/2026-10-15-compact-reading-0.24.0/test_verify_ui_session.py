"""File-only controls for the owner-lock/session enumeration repair."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verify_ui_session', Path(__file__).with_name('verify_ui_session.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SessionDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name)
        (self.store / 'owner').write_bytes(b'owned synthetic lock\n')
        self.session = self.store / 'sustained-123-1'
        self.session.mkdir()

    def test_regular_owner_and_one_session_are_bound_separately(self):
        session, owner, names = helper.discover_session(self.store)
        self.assertEqual(session, self.session)
        self.assertEqual(owner, helper.identity(self.store / 'owner'))
        self.assertEqual(names, ['owner', 'sustained-123-1'])

    def test_multiple_sessions_are_rejected(self):
        (self.store / 'sustained-124-2').mkdir()
        with self.assertRaisesRegex(ValueError, 'exactly one session'):
            helper.discover_session(self.store)

    def test_unexpected_file_is_rejected(self):
        (self.store / 'unexpected').write_bytes(b'not a session')
        with self.assertRaisesRegex(ValueError, 'Unexpected entry'):
            helper.discover_session(self.store)

    def test_session_named_regular_file_is_rejected(self):
        (self.store / 'sustained-124-2').write_bytes(b'not a directory')
        with self.assertRaisesRegex(ValueError, 'ordinary directory'):
            helper.discover_session(self.store)

    def test_session_symlink_is_rejected(self):
        (self.store / 'sustained-124-2').symlink_to(self.session, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'ordinary directory'):
            helper.discover_session(self.store)

    def test_owner_symlink_is_rejected(self):
        owner = self.store / 'owner'
        owner.unlink()
        owner.symlink_to(self.session, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'ordinary file'):
            helper.discover_session(self.store)


if __name__ == '__main__':
    unittest.main()
