import json
import unittest
import prepare_inputs as p

class TransformTests(unittest.TestCase):
    def fixture(self, memory):
        return ('Reservoir Scope · ongoing journal · reservoir-journal-v8\nOpen invitation.\n\nSESSION CONTEXT\nFixed.'
         '\n\nOPTIONAL READOUT\nNumbers unchanged.\n\nPREVIOUS JOURNAL\nFull previous text as one JSON string: '
         +json.dumps(memory, ensure_ascii=False)+'\nEND PREVIOUS JOURNAL\n\nWRITING BOUNDARY\nFixed boundary.\n\n'
         'Write the next entry in whatever direction seems worth pursuing.')

    def test_quoted_headings_unicode_and_newlines_are_exact(self):
        memory = 'grey… 🌀\n\nOPTIONAL READOUT\n\nPREVIOUS JOURNAL\n\nWRITING BOUNDARY\nquote: "é"'
        original = self.fixture(memory)
        swapped, parts = p.split_prompt(original, memory)
        self.assertEqual(original, parts['prefix']+parts['readout']+parts['memory']+parts['suffix'])
        self.assertEqual(swapped, parts['prefix']+parts['memory']+parts['readout']+parts['suffix'])
        self.assertEqual(len(original.encode()),len(swapped.encode()))

    def test_rejects_wrong_decoded_memory(self):
        with self.assertRaises(ValueError): p.split_prompt(self.fixture('a'),'b')

    def test_rejects_ambiguous_outer_marker(self):
        with self.assertRaises(ValueError): p.split_prompt(self.fixture('a')+'\n\nOPTIONAL READOUT\n','a')

    def test_rejects_missing_marker(self):
        with self.assertRaises(ValueError): p.split_prompt(self.fixture('a').replace('\n\nOPTIONAL READOUT\n',''),'a')

    def test_rejects_changed_version(self):
        with self.assertRaises(ValueError): p.split_prompt(self.fixture('a').replace('reservoir-journal-v8','reservoir-journal-v7'),'a')

    def test_rejects_changed_invitation(self):
        with self.assertRaises(ValueError): p.split_prompt(self.fixture('a')+' Be novel.','a')

if __name__ == '__main__': unittest.main()
