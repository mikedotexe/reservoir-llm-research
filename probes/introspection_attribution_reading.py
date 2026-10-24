#!/usr/bin/env python3
"""Compare the two saved S-013 reader annotations without overwriting judgments."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_experiments import runner

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reading',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    folder=args.reading
    receipt=runner.read_json(folder/'receipt.json')
    if receipt['study']!='S-013': raise ValueError('Only S-013 annotations supported')
    for name,digest in receipt['files'].items():
        if runner.sha((folder/name).read_bytes())!=digest: raise ValueError('Reading export changed')
    readers={name:runner.read_json(folder/f'reader-{name}-pass2.json') for name in ('a','b')}
    keys=runner.read_json(folder/'allocation-key.json')
    ids={f"{k['packet_number']:03d}" for k in keys}
    for name,r in readers.items():
        if set(r['packets'])!=ids or not (folder/f'reader-{name}-pass1.json').exists():
            raise ValueError('Missing first-pass record or incomplete annotation coverage')
    rows=[]
    for key in keys:
        number=f"{key['packet_number']:03d}"
        labels={name:r['packets'][number]['current_value_claim'] for name,r in readers.items()}
        rows.append({'packet':number,'node_id':key['node_id'],'episode':key['episode'],
                     'condition':key['condition'],'status':key['status'],'labels':labels,
                     'exact_agreement':labels['a']==labels['b'],
                     'unsupported_marker_agreement':(labels['a']=='explicit_unsupported_current')==(labels['b']=='explicit_unsupported_current'),
                     'joint_explicit_unsupported':all(v=='explicit_unsupported_current' for v in labels.values())})
    grouped=defaultdict(list)
    for row in rows: grouped[row['condition']].append(row)
    result={'study':'S-013','selected':len(rows),'rows':rows,
            'reader_counts':{name:dict(Counter(row['labels'][name] for row in rows)) for name in readers},
            'exact_category_agreement':sum(row['exact_agreement'] for row in rows),
            'unsupported_marker_agreement':sum(row['unsupported_marker_agreement'] for row in rows),
            'joint_explicit_unsupported':sum(row['joint_explicit_unsupported'] for row in rows),
            'conditions':{condition:{'selected':len(group),'joint_explicit_unsupported':sum(r['joint_explicit_unsupported'] for r in group)} for condition,group in sorted(grouped.items())},
            'boundary':'Agreement across separate same-model contexts, not independent human validation. Original category definitions differ; no relabeling or merged supported-current count.',
            'input_hashes':{name:runner.sha((folder/name).read_bytes()) for name in ('receipt.json','allocation-key.json','reader-a-pass1.json','reader-b-pass1.json','reader-a-pass2.json','reader-b-pass2.json')},
            'code_sha256':runner.sha(Path(__file__).read_bytes())}
    runner.write_json(runner.guard_output(args.out,ROOT),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','input_hashes')},indent=2))
if __name__=='__main__':main()
