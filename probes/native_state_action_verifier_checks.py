#!/usr/bin/env python3
"""Challenge native receipt auditing with corrupted copies of retained evidence."""
import argparse, copy, hashlib, json
from pathlib import Path
from unittest.mock import patch
import native_state_action_verify as verifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    real_read = verifier.read
    mutations = {
        'ordinary_state_bit_change': ('ordinary-results.json', lambda x: x[0]['path'][1].__setitem__(0, x[0]['path'][1][0]+0.001)),
        'false_applied_step': ('native-96-finite.json', lambda x: x['receipts'][1].__setitem__('successful_step_id', 99)),
        'incorrect_delta': ('native-96-finite.json', lambda x: x['receipts'][1]['delta'].__setitem__(0, 0.5)),
        'invented_noise': ('native-96-finite.json', lambda x: x['receipts'][1]['realized_noise'].__setitem__(0, 0.5)),
        'coordinate_identity_swap': ('native-96-finite.json', lambda x: x['identity'].__setitem__('node_layout_id', '0'*64)),
        'unproven_fill': ('native-action-response.json', lambda x: x.__setitem__('fill', 0.65)),
        'measured_clock_claim': ('native-action-response.json', lambda x: x.__setitem__('clock', 'measured wall time')),
        'wrong_execution_protocol': ('execution.json', lambda x: x.__setitem__('protocol_sha256', '0'*64)),
    }
    result=[]
    for name, (filename, mutate) in mutations.items():
        def corrupted(path):
            value=real_read(path)
            if Path(path) == args.run / filename:
                value=copy.deepcopy(value); mutate(value)
            return value
        try:
            with patch.object(verifier, 'read', corrupted):
                verifier.audit(args.root,args.run)
        except (AssertionError, ValueError, IndexError, KeyError) as error:
            result.append({'case':name,'rejected':True,'reason':str(error)})
        else:
            raise AssertionError('corrupted evidence was accepted: '+name)
    output={'schema':'research.native_state_actions.verifier_checks.v1','checks':result,
        'count':len(result),'all_rejected':True,'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Mutated decoded evidence in memory; retained originals and application source remain unchanged.'}
    (args.root/'verifier-checks.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
