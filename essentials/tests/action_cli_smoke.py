#!/usr/bin/env python3
"""Run actual action CLI pairs and attack exported records. Synthetic fixtures only.
No model/service is discovered or contacted. Existing source/example files are read only.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, pathlib, subprocess, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

def require(value, message):
    if not value:
        raise AssertionError(message)

def execute(cli, *args):
    return subprocess.run([str(cli), *map(str,args)], capture_output=True, text=True, timeout=90)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli',type=pathlib.Path,required=True)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    args=parser.parse_args()
    pairs=[]; corruption=[]
    with tempfile.TemporaryDirectory(prefix='essentials-action-cli-') as folder:
        temp=pathlib.Path(folder); records={}
        for recipe in sorted((ROOT/'actions/recipes').glob('*.json')):
            if recipe.stem.endswith('independent'): continue
            spec=json.loads(recipe.read_text()); spec['steps']=91
            config=temp/(recipe.stem+'-spec.json'); output=temp/(recipe.stem+'.json')
            config.write_text(json.dumps(spec))
            run=execute(args.cli,'actions','--config',config,'--output',output)
            require(run.returncode==0,f'{recipe.stem}: run failed: {run.stderr[-2000:]}')
            record=json.loads(output.read_text()); records[spec['stage']]=record
            check=execute(args.cli,'verify',output)
            require(check.returncode==0,f'{recipe.stem}: verify failed: {check.stderr[-2000:]}')
            right=record['right']; left=record.get('left')
            require(len(right['frames'])==91 and record['status']=='completed',f'{recipe.stem}: incomplete run')
            require(all(len(f['state'])==32 and len(f['input'])==66 for f in right['frames']), 'Wrong dimensions')
            for arm in [left,right]:
                if not arm: continue
                for entry in arm['journals']:
                    require(hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'],'Journal content hash')
                    require(any(p.is_file() and json.loads(p.read_text()).get('text') == entry['text'] for p in output.with_suffix('.journals').rglob('*.json')),
                            'No saved journal file contains the exported text')
            differences=[]
            if left:
                require(len(left['frames'])==91,'Pair frame count differs')
                require(all(a['externalInput']==b['externalInput'] for a,b in zip(left['frames'],right['frames'])),'External forcing differs')
                differences=[max(abs(x-y) for x,y in zip(a['state'],b['state'])) for a,b in zip(left['frames'],right['frames'])]
            if spec['stage'] in [3,4,6]: require(all(x==0 for x in differences),'Observation/output/fixed-memory changed reservoir')
            if spec['stage']==5:
                require(all(x==0 for x in differences[:30]) and differences[30]>0,'Feedback did not first diverge at step31')
                require(left['journals'] and [x['text'] for x in left['journals']]==[x['text'] for x in right['journals']], 'Fixed reply texts differ')
                require(all(f['semanticInput']==[0.0]*48 for f in left['frames']),'Output-only arm got semantic feedback')
                require(right['actions'][0]['applicationStep']==31,'Missing exact next-step receipt')
            if spec['stage']==8:
                require(all(a['input']==b['input'] for a,b in zip(left['frames'],right['frames'])),'Controller pair full inputs differ')
                require(any(a['retentionUsed']!=b['retentionUsed'] for a,b in zip(left['frames'],right['frames'])),'Controller did not actuate')
            pairs.append({'recipe':recipe.name,'stage':spec['stage'],'steps_per_arm':91,'journal_count_selected':len(right['journals']),
                          'first_differing_state_step':next((i+1 for i,v in enumerate(differences) if v>0),None),
                          'maximum_coordinate_difference':max(differences,default=0),'verify':check.stdout.strip()})
        def reject(name,stage,mutate):
            broken=copy.deepcopy(records[stage]); mutate(broken)
            path=temp/(name+'.json'); path.write_text(json.dumps(broken))
            result=execute(args.cli,'verify',path)
            require(result.returncode!=0,f'Accepted corrupted record: {name}')
            corruption.append({'case':name,'rejected':True,'reason':result.stderr.strip()[-1000:]})
        reject('changed-state',5,lambda r:r['right']['frames'][30]['state'].__setitem__(0,.999))
        reject('wrong-dimension',5,lambda r:r['right']['frames'][30]['state'].pop())
        reject('changed-journal-text',5,lambda r:r['right']['journals'][0].__setitem__('text','fabricated replacement'))
        reject('changed-journal-hash',5,lambda r:r['right']['journals'][0].__setitem__('sha256','0'*64))
        reject('premature-feedback-receipt',5,lambda r:r['right']['actions'][0].__setitem__('applicationStep',30))
        reject('changed-prompt',5,lambda r:r['right']['actions'][0].__setitem__('prompt','fabricated prompt'))
        reject('changed-tape-vector',5,lambda r:r['tape']['packets'][0]['semanticVector'].__setitem__(0,.9))
        reject('changed-reference-spectrum',5,lambda r:r['tape']['packets'][0]['referenceEigenvalues'].__setitem__(0,99))
        reject('changed-memory-exposure',6,lambda r:r['right']['actions'][1].__setitem__('memoryText','fabricated memory'))
        reject('mismatched-selected-stage',5,lambda r:r['right'].__setitem__('stage',4))
        reject('mismatched-left-weights',5,lambda r:r['left']['model']['recurrentWeights'].__setitem__(0,.12345))
        reject('invented-format',5,lambda r:r.__setitem__('format','unknown-format'))
    receipt={'schema':'essentials.action_cli_qualification.v1','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'cli_sha256':hashlib.sha256(args.cli.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
             'pairs':pairs,'corruption':corruption,'status':'passed','scope':'Eight synthetic fixed-reply recipes and malformed export rejection through the real CLI; no model or live system contacted.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'passed','pairs':len(pairs),'malformed_exports_rejected':len(corruption),'output':str(args.output)},indent=2))

if __name__=='__main__': main()
