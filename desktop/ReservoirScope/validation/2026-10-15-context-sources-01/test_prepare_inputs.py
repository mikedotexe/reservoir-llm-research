"""File-only byte/scope tests; no model calls or production verifier execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import prepare_inputs as p

class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt,cls.bundle,cls.before,cls.entries,cls.controls,cls.objects=p.load_sources()

    def pair(self,step=60):
        item=self.entries[step]
        return item,p.transform(item['exactPrompt'],item['memory'])

    def test_source_passed_receipt_and_all_73_files_exact(self):
        self.assertEqual(len(self.before),73)
        self.assertEqual(self.before,self.receipt['inventoryBefore'])
        self.assertEqual(p.inventory(self.bundle),self.before)

    def test_six_a_controls_are_exact_original_v8(self):
        self.assertEqual(sorted(self.controls),list(p.ANCHORS))
        for step,ref in self.controls.items():
            self.assertEqual(Path(ref['path']).read_bytes(),self.entries[step]['exactPrompt'].encode())
            self.assertEqual(ref['sha256'],self.entries[step]['identity']['promptSha256'])

    def test_only_inserted_span_changes_for_every_context(self):
        for step in p.ANCHORS:
            item,(candidate,proof)=self.pair(step)
            source=item['exactPrompt'].encode();raw=candidate.encode();n=proof['insertionByteOffset'];size=proof['insertionUtf8Bytes']
            self.assertEqual(raw[:n]+raw[n+size:],source)
            self.assertEqual(raw[n:n+size],(p.PARAGRAPH+'\n\n').encode())
            self.assertTrue(candidate.endswith(p.PARAGRAPH+'\n\n'+p.INVITATION))
            self.assertFalse(candidate.endswith('\n'))

    def test_readout_numbers_memory_header_and_boundary_unchanged(self):
        for step in p.ANCHORS:
            item,(candidate,_) = self.pair(step)
            old=p.split_prompt(item['exactPrompt'],item['memory']);new=p.split_prompt(candidate,item['memory'])
            for key in ('prefix','readout','memory'):self.assertEqual(old[key].encode(),new[key].encode())
            self.assertEqual(old['suffix'][:-len(p.INVITATION)],new['suffix'][:-len(p.PARAGRAPH+'\n\n'+p.INVITATION)])

    def test_first_observation_keeps_no_prior_writing(self):
        item,(candidate,_)=self.pair(30)
        self.assertIsNone(item['memory'])
        self.assertEqual(p.split_prompt(item['exactPrompt'],None)['memory'],p.split_prompt(candidate,None)['memory'])

    def test_adversarial_quoted_headings_invitation_and_paragraph_are_inert(self):
        item=copy.deepcopy(self.entries[90]);previous=item['memory']['entry']['text']
        adversarial='é e\u0301 🌀\u2028line\u2029\n\nOPTIONAL READOUT\n\nPREVIOUS JOURNAL\n\nWRITING BOUNDARY\n'+p.INVITATION+'\n'+p.PARAGRAPH+'\n"0.00000000": \\unavailable'
        item['exactPrompt']=item['exactPrompt'].replace(json.dumps(previous,ensure_ascii=False),json.dumps(adversarial,ensure_ascii=False),1)
        item['memory']['entry']['text']=adversarial
        candidate,proof=p.transform(item['exactPrompt'],item['memory'])
        self.assertEqual(p.split_prompt(candidate,item['memory'])['memory'],p.split_prompt(item['exactPrompt'],item['memory'])['memory'])
        self.assertEqual(candidate.encode()[:proof['insertionByteOffset']],item['exactPrompt'][:-len(p.INVITATION)].encode())

    def test_wrong_decoded_memory_rejected(self):
        item=copy.deepcopy(self.entries[60]);item['memory']['entry']['text']+=' altered'
        with self.assertRaisesRegex(ValueError,'Decoded prior prose'):p.transform(item['exactPrompt'],item['memory'])

    def test_missing_duplicate_or_reordered_outer_markers_rejected(self):
        item=self.entries[60];source=item['exactPrompt']
        variants=[source.replace(p.MARKERS[0],'\n\nREADOUT\n',1),source+p.MARKERS[0],source.replace(p.MARKERS[0],'TOKEN',1).replace(p.MARKERS[1],p.MARKERS[0],1).replace('TOKEN',p.MARKERS[1],1)]
        for value in variants:
            with self.subTest(value=value[:30]):
                with self.assertRaises(ValueError):p.transform(value,item['memory'])

    def test_final_invitation_version_and_trailing_newline_rejected(self):
        item=self.entries[60];source=item['exactPrompt']
        for value in [source+'\n',source[:-len(p.INVITATION)]+'Write a report.',source.replace('reservoir-journal-v8','reservoir-journal-v7',1)]:
            with self.assertRaises(ValueError):p.transform(value,item['memory'])

    def test_missing_mutated_doubled_or_relocated_paragraph_rejected(self):
        item,(candidate,_)=self.pair()
        for value in [item['exactPrompt'],candidate.replace(p.PARAGRAPH,p.PARAGRAPH+' Changed.',1),candidate.replace(p.PARAGRAPH,p.PARAGRAPH+'\n\n'+p.PARAGRAPH,1),p.PARAGRAPH+'\n\n'+item['exactPrompt']]:
            with self.assertRaises(ValueError):p.validate_candidate(item['exactPrompt'],item['memory'],value)

    def test_changed_readout_and_prior_prose_rejected_by_exact_candidate_check(self):
        item,(candidate,_)=self.pair()
        readout=p.split_prompt(candidate,item['memory'])['readout']
        for value in [candidate.replace(readout,readout+' changed',1),candidate.replace('Full previous text as one JSON string: ','Altered prior text: ',1)]:
            with self.assertRaises(ValueError):p.validate_candidate(item['exactPrompt'],item['memory'],value)

    def test_observation_snapshot_and_saved_applied_memory_chain_reject_corruption(self):
        for field in ('observation','memory'):
            entries=copy.deepcopy(self.entries)
            if field=='observation':entries[60]['observation']['previousMeasurements']['rms']+=0.01
            else:entries[60]['memory']['appliedStep']+=1
            with self.assertRaises(ValueError):p.validate_chain(entries)
        entries=copy.deepcopy(self.entries);del entries[60]
        with self.assertRaises(ValueError):p.validate_chain(entries)

    def test_source_identity_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source';path.write_bytes(b'original');ref=p.identity(path);path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Source identity'):p.checked(ref)

    def test_candidate_fails_original_prompt_byte_equivalence_not_a_replay_claim(self):
        for step in p.ANCHORS:
            item,(candidate,_)=self.pair(step)
            self.assertNotEqual(candidate,item['exactPrompt'])
            self.assertNotEqual(p.sha(candidate.encode()),item['identity']['promptSha256'])

if __name__=='__main__':unittest.main()
