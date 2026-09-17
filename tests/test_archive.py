import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from reservoir_research import archive

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.source = self.root / 'source'; self.source.mkdir()
        (self.source / '.git').mkdir(); (self.source / '.git' / 'HEAD').write_text('history')
        (self.source / 'private').mkdir(); (self.source / 'private' / 'evidence').write_text('retained')
        (self.source / '.build').mkdir(); (self.source / '.build' / 'cache').write_text('omit')
        self.dest = self.root / 'snapshot'
    def snapshot(self): return archive.snapshot(self.source, self.dest)
    def alter(self, fn):
        p = self.dest / 'manifest.json'; d = json.loads(p.read_text()); fn(d)
        p.write_text(json.dumps(d))
    def test_restore_without_source_preserves_history_evidence_and_modes(self):
        (self.source / 'link').symlink_to('private/evidence')
        receipt = self.snapshot(); self.assertEqual(receipt['files'], 2)
        self.source.rename(self.root / 'unavailable')
        restored = self.root / 'restored'; archive.restore(self.dest, restored)
        self.assertEqual((restored / 'link').read_text(), 'retained')
        self.assertEqual((restored / '.git' / 'HEAD').read_text(), 'history')
        self.assertFalse((restored / '.build').exists())
        self.assertFalse((restored / 'private' / 'evidence').stat().st_mode & 0o077)
    def test_modified_file_and_unlisted_file_rejected(self):
        self.snapshot(); p = self.dest / 'tree/private/evidence'; p.write_text('changed!')
        with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
        p.write_text('retained'); (self.dest / 'tree/extra').write_text('extra')
        with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
    def test_missing_file_rejected(self):
        self.snapshot(); (self.dest / 'tree/private/evidence').unlink()
        with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
    def test_nonprivate_permissions_rejected(self):
        self.snapshot(); (self.dest / 'tree/private/evidence').chmod(0o644)
        with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
    def test_traversal_duplicate_and_invalid_mode_rejected(self):
        self.snapshot(); original = (self.dest / 'manifest.json').read_bytes()
        for mutate in [lambda d:d['entries'].append(dict(d['entries'][0])),
                       lambda d:d['entries'][0].update(path='../escape'),
                       lambda d:d['entries'][0].update(mode=0o777),
                       lambda d:d.update(status='incomplete')]:
            with self.subTest(mutate=mutate):
                (self.dest / 'manifest.json').write_bytes(original); self.alter(mutate)
                with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
    def test_external_link_and_special_file_rejected(self):
        link=self.source/'link'; link.symlink_to('../outside')
        with self.assertRaises(archive.ArchiveError): self.snapshot()
        link.unlink(); os.mkfifo(self.source/'pipe')
        with self.assertRaises(archive.ArchiveError): self.snapshot()
    def test_existing_destination_and_nested_destination_rejected(self):
        self.snapshot()
        with self.assertRaises(archive.ArchiveError): self.snapshot()
        with self.assertRaises(archive.ArchiveError): archive.restore(self.dest, self.source)
        with self.assertRaises(archive.ArchiveError): archive.snapshot(self.source, self.source/'nested')
        alias=self.root/'alias';alias.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(archive.ArchiveError): archive.snapshot(self.source,alias/'nested')
    def test_copy_failure_preserves_incomplete_snapshot(self):
        with patch.object(archive, '_copy', side_effect=OSError('disk full')):
            with self.assertRaises(archive.ArchiveError): self.snapshot()
        self.assertTrue((self.dest/'started.json').exists())
        self.assertFalse((self.dest/'manifest.json').exists())
        with self.assertRaises(archive.ArchiveError): archive.verify(self.dest)
    def test_provenance_is_never_opened(self):
        self.snapshot(); self.alter(lambda d:d.update(source_provenance='/not/available/ever'))
        archive.verify(self.dest); archive.restore(self.dest,self.root/'copy')

if __name__ == '__main__': unittest.main()
