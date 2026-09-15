#!/usr/bin/env python3
"""Exercise action journals/memory through actual CLI HTTP on newly owned ports.
Uses the bounded fixture server from http_smoke.py. Never contacts an existing model.
"""
import argparse, datetime, hashlib, json, pathlib, subprocess, tempfile
import http_smoke as transport

JOURNAL = 'I notice the broad field and wonder which pattern will persist.'
transport.TEXT = json.dumps({'action':'WRITE_JOURNAL','text':JOURNAL})

def require(condition, message):
    if not condition: raise AssertionError(message)

def run(cli,*args):
    return subprocess.run([str(cli),*map(str,args)],capture_output=True,text=True,timeout=30)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli',type=pathlib.Path,required=True); parser.add_argument('--output',type=pathlib.Path,required=True)
    args=parser.parse_args(); cases=[]
    with tempfile.TemporaryDirectory(prefix='essentials-action-http-') as folder:
        root=pathlib.Path(folder)
        for scenario in ['success','partial','length','http_error','redirect']:
            with transport.fixture(scenario) as server:
                config=root/(scenario+'-spec.json'); output=root/(scenario+'.json')
                spec={'stage':6,'mode':'independentGeneration','comparePrevious':False,'steps':61 if scenario=='success' else 31,
                      'language':{'backend':'ollama','endpoint':f'http://127.0.0.1:{server.server_port}','model':transport.MODEL}}
                config.write_text(json.dumps(spec)); result=run(args.cli,'actions','--config',config,'--output',output)
                require(output.is_file(),f'{scenario}: no retained record: {result.stderr[-1500:]}')
                record=json.loads(output.read_text()); arm=record['right']; actions=arm['actions']
                captures=list(server.captures)
                require(len(captures)==(2 if scenario=='success' else 1),f'{scenario}: unexpected HTTP request count')
                require(len(actions)==len(captures),f'{scenario}: request/receipt count differs')
                for request,action in zip(captures,actions):
                    body=request['body']
                    require(request['method']=='POST' and request['path']=='/api/chat',f'{scenario}: wrong transport')
                    require(body['model']==transport.MODEL and body['stream'] is False,'Provider settings changed')
                    require(body['options']['num_predict']==256 and body['options']['temperature']==0,'Request limits changed')
                    require(body['messages']==[{'role':'user','content':action['prompt']}],'Recorded prompt differs from HTTP request')
                if scenario=='success':
                    require(result.returncode==0 and record['status']=='completed','Successful action run did not complete')
                    require([a['applicationStep'] for a in actions]==[31,61],'Wrong actual feedback boundaries')
                    require(len(arm['journals'])==2 and all(j['text']==JOURNAL for j in arm['journals']),'Journal text missing')
                    require(actions[1]['memoryText']==JOURNAL and JOURNAL in actions[1]['prompt'],'Saved memory not supplied in next HTTP request')
                    require(actions[1]['memoryEntryID']==arm['journals'][0]['id'],'Memory linked to wrong journal')
                    require(all(arm['frames'][a['applicationStep']-1]['semanticInput']==a['semanticVector'] for a in actions),'Applied input differs from action receipt')
                else:
                    require(result.returncode==1 and record['status']=='failed',f'{scenario}: failure not retained')
                    require(not arm['journals'] and len(arm['frames'])==30,'Failure saved a journal or advanced simulated time')
                    require(actions[0].get('applicationStep') is None and all(not any(f['semanticInput']) for f in arm['frames']),'Incomplete feedback applied')
                    if scenario in ['partial','length']:
                        require(actions[0]['rawReply']==transport.TEXT,'Incomplete raw output not retained')
                verified=run(args.cli,'verify',output)
                require(verified.returncode==0,f'{scenario}: retained outcome fails verification: {verified.stderr[-2000:]}')
                cases.append({'scenario':scenario,'requests':len(captures),'status':record['status'],'steps':len(arm['frames']),
                              'journals':len(arm['journals']),'verified':True,'requests_sha256':[x['body_sha256'] for x in captures]})
    receipt={'schema':'essentials.action_http_qualification.v1','status':'passed','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'cli_sha256':hashlib.sha256(args.cli.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
             'transport_fixture_sha256':hashlib.sha256(pathlib.Path(transport.__file__).read_bytes()).hexdigest(),'cases':cases,
             'scope':'Actual bounded chat transport and action/memory/application receipts against owned ephemeral loopback fixtures; no model inference.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'passed','cases':len(cases),'output':str(args.output)},indent=2))

if __name__=='__main__': main()
