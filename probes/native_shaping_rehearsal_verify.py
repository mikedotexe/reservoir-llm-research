#!/usr/bin/env python3
"""Audit retained native rehearsal arithmetic and byte provenance; no sibling read."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import tomllib


def normdiff(a, b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def verify(root: Path):
    p=json.loads((root/'protocol.json').read_text())
    r=json.loads((root/'results.json').read_text())
    execution=json.loads((root/'execution-receipt.json').read_text())
    manifest=json.loads((root/'source-manifest.json').read_text())
    hashes=[hashlib.sha256((root/v['retained']).read_bytes()).hexdigest()==v['sha256'] for v in manifest['files']]
    output_hashes=[hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in execution['outputs'].items()]
    parity=[]
    for row in r['parity']:
        tag=f"{row['mode']}-{row['start_boundary']}"
        paths=json.loads((root/f'parity-paths-{tag}.json').read_text())
        blobs=[struct.pack('<'+str(sum(map(len,arr)))+'f',*[x for state in arr for x in state]) for arr in paths['paths']]
        finals=json.loads((root/f'final-checkpoints-{tag}.json').read_text())
        for state in finals.values():
            state['spectral'].pop('last_profile')
        bit_equal=all(v==blobs[0] for v in blobs)
        exact_snapshot=finals['ordinary']==finals['restored']
        parity.append({'case':tag,'f32_state_paths_bit_identical':bit_equal,
            'bit_report_matches':bit_equal==row['all_state_paths_bit_identical'],
            'ordinary_restored_final_snapshot_exact_values':exact_snapshot,
            'ordinary_restored_rng_exact':finals['ordinary']['rng_state']==finals['restored']['rng_state']})
    error=0.
    counts={'one_shot':0,'sequence':0,'returned':0,'saturated_runs':0,'edit_receipts':0}
    arithmetic_pass=True
    for row in r['responses']:
        response=json.loads((root/f"response-{row['id']}.json").read_text())
        base=json.loads((root/f"parity-paths-synchronous_profile-{row['start_boundary']}.json").read_text())['paths'][0]
        actual=[normdiff(a,b) for a,b in zip(response['states'],base)]
        max_error=max(abs(a-b) for a,b in zip(actual,row['separation_l2']))
        error=max(error,max_error)
        threshold=actual[row['reference_boundary']]*p['return_threshold_fraction']
        dwell=p['return_dwell_boundaries']
        returned=next((i for i in range(row['reference_boundary']+1,len(actual)-dwell+1) if all(x<=threshold for x in actual[i:i+dwell])),None)
        arithmetic_pass &= max_error<=1e-12 and returned==row['return_boundary']
        for edit in response['edits']:
            arithmetic_pass &= abs(normdiff(edit['before'],edit['after'])-edit['actual_l2'])<1e-12
            # Recorded immediate deltas use native f32 subtraction, with rounding.
            expected=[struct.unpack('<f',struct.pack('<f',a-b))[0] for a,b in zip(edit['after'],edit['before'])]
            arithmetic_pass &= expected==edit['actual_delta']
            counts['edit_receipts']+=1
        counts['sequence' if row['sequence'] else 'one_shot']+=1
        counts['returned']+=returned is not None
        counts['saturated_runs']+=row['any_observed_saturation']
    old=tomllib.loads((root/'source/Cargo.lock').read_text())
    new=tomllib.loads((root/'resolved-Cargo.lock').read_text())
    old_packages={(a['name'],a['version']):a for a in old['package']}
    dependencies=[{'name':a['name'],'version':a['version'],
        'same_source_lock_checksum':old_packages.get((a['name'],a['version']),{}).get('checksum')==a.get('checksum')}
        for a in new['package'] if a['name']!='native-shaping-rehearsal']
    once=[v for v in r['responses'] if not v['sequence']]
    sequence=[v for v in r['responses'] if v['sequence']]
    result={'source_hashes_pass':all(hashes),'execution_output_hashes_pass':all(output_hashes),
        'dependencies':dependencies,'dependencies_match_source_lock':all(v['same_source_lock_checksum'] for v in dependencies),
        'parity':parity,'response_arithmetic_pass':arithmetic_pass,'max_l2_recomputation_error':error,'counts':counts,
        'one_shot_return_range':[min(v['return_boundary'] for v in once),max(v['return_boundary'] for v in once)],
        'sequence_return_range':[min(v['return_boundary'] for v in sequence),max(v['return_boundary'] for v in sequence)],
        'one_shot_peak_gain_range':[min(v['peak_gain_over_reference'] for v in once),max(v['peak_gain_over_reference'] for v in once)],
        'sequence_peak_gain_over_post_final_edit_reference_range':[min(v['peak_gain_over_reference'] for v in sequence),max(v['peak_gain_over_reference'] for v in sequence)],
        'gate':all(hashes) and all(output_hashes) and arithmetic_pass and all(v['bit_report_matches'] for v in parity)}
    (root/'verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['dependencies','parity']},indent=2))
    if not result['gate']:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'research/outputs/2026-09-07-native-shaping-rehearsal')
    verify(parser.parse_args().output)
