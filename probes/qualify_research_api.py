#!/usr/bin/env python3
"""Isolated black-box qualification. Starts only the supplied binary and a fake Ollama.

Run from the repository root with Python 3.14. Every run lives in a new temporary
root. No existing app, model service, or research store is discovered or contacted.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_control.cli import Client, read_descriptor


def until(check, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = check()
        if value: return value
        time.sleep(.05)
    raise AssertionError('Timed out waiting for isolated qualification state')


def main():
    p = argparse.ArgumentParser(); p.add_argument('binary', type=Path); p.add_argument('--report', type=Path)
    args = p.parse_args(); binary = args.binary.resolve()
    calls = []; lock = threading.Lock(); active = 0; maximum = 0
    slow_entered=threading.Event(); release_slow=threading.Event()
    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, value):
            data = json.dumps(value).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            assert self.path == '/api/tags'; self.send({'models':[{'name':name, 'digest':'a'*64} for name in ['arm-a','arm-b','arm-c','embed-test','slow-test']]})
        def do_POST(self):
            nonlocal active, maximum
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with lock: active += 1; maximum = max(maximum, active); calls.append({'path':self.path, 'body':body})
            try:
                if body.get("model")=="slow-test": slow_entered.set(); release_slow.wait(15)
                time.sleep(.15)
                if self.path == '/api/chat': self.send({'model':body['model'], 'done':True, 'done_reason':'stop', 'message':{'role':'assistant','content':'A deterministic local test observation.'}, 'eval_count':9})
                elif self.path == '/api/embed': self.send({'model':'embed-test','embeddings':[[.1]*64]})
                else: raise AssertionError(self.path)
            finally:
                with lock: active -= 1
    provider = ThreadingHTTPServer(('127.0.0.1',0),Provider)
    threading.Thread(target=provider.serve_forever,daemon=True).start()
    proc = None
    with tempfile.TemporaryDirectory(prefix='reservoir-api-qualification-') as temp:
        root=Path(temp); data=root/'data'; descriptor=data/'automation-v1/endpoint.json'; log=(root/'app.log').open('w')
        def start():
            process=subprocess.Popen([str(binary),'--research-api','--data-root',str(data)],stdout=log,stderr=log)
            until(lambda: descriptor.exists() or process.poll() is not None)
            assert process.poll() is None, (root/'app.log').read_text()
            return process, Client(read_descriptor(descriptor))
        def operation(method,path,body=None,key=None):
            op=client.request(method,path,body,key); result=client.wait(op['id'],90)
            assert result['status']=='completed',result
            return result['result']
        try:
            proc,client=start()
            endpoint=f'http://127.0.0.1:{provider.server_port}'
            recipe={'version':1,'maxConcurrentRequests':1,'baseConfig':{'turnEvery':3,'paceMs':100,'maximumSteps':150,'maximumTurns':60,'language':{'backend':'ollama','endpoint':endpoint,'contextTokens':8192}},'arms':[{'name':name,'overrides':{'language':{'model':name}}} for name in ['arm-a','arm-b','arm-c']]}
            recipe['arms'][0]['interventions']=[{'kind':'configuration','at':{'step':7},'patch':{'reservoirNodes':48}}, {'kind':'prompt','at':{'step':12},'prompt':'Qualification question after growth.','includeTelemetry':False}]
            experiment=operation('POST','/v1/experiments',recipe,'prepare-once'); runs=experiment['runIds']
            assert len(runs)==3 and not calls
            repeat=operation('POST','/v1/experiments',recipe,'prepare-once'); assert repeat['id']==experiment['id']
            operation('POST',f"/v1/experiments/{experiment['id']}/actions/start",{})
            until(lambda: all(client.request('GET',f'/v1/runs/{r}')['journalCount']>=3 for r in runs))
            page=client.request('GET',f'/v1/runs/{runs[0]}/entries?limit=1')
            until(lambda: client.request('GET',f'/v1/runs/{runs[0]}')['journalCount']>=6)
            next_page=client.request('GET',f"/v1/runs/{runs[0]}/entries?limit=1&cursor={page['nextCursor']}")
            assert page['snapshot']==next_page['snapshot'] and page['entries'][0]['entryId']!=next_page['entries'][0]['entryId']
            interventions=client.request('GET',f'/v1/runs/{runs[0]}/interventions')['operations']
            for intervention in interventions: assert client.wait(intervention['id'],30)['status']=='completed'
            settings=client.request('GET',f'/v1/runs/{runs[1]}/settings')
            operation('PATCH',f'/v1/runs/{runs[1]}/settings',{'expectedConfigurationRevision':settings['configurationRevision'],'patch':{'embeddingModel':'embed-test','textAdmission':'utf8-v1'}})
            until(lambda: any(c['path']=='/api/embed' for c in calls))
            operation('POST',f"/v1/experiments/{experiment['id']}/actions/pause",{})
            assert maximum==1, maximum
            assert any(c['path']=='/api/chat' and any(m.get('content')=='Qualification question after growth.' for m in c['body']['messages']) for c in calls)
            exports=[]
            for i,run in enumerate(runs):
                exported=client.export(run,root/f'export-{i}',f'export-{i}')
                assert exported['status']=='completed',exported
                exports.append(exported['report'])
            assert client.request('GET',f'/v1/runs/{runs[0]}/settings')['configured']['reservoirNodes']==48
            # CLI is exercised through its real command entry point, not only the client class.
            cli=subprocess.run([sys.executable,'-m','reservoir_control','--endpoint-file',str(descriptor),'entries','list',runs[0],'--all'],text=True,capture_output=True,check=True)
            all_entries=json.loads(cli.stdout); assert all_entries['total']>=6
            slow=operation('POST','/v1/runs',{'config':{'turnEvery':3,'paceMs':100,'language':{'backend':'ollama','endpoint':endpoint,'model':'slow-test','contextTokens':8192}}})['runId']
            operation('POST',f'/v1/runs/{slow}/actions/start',{})
            assert slow_entered.wait(15)
            pending=client.request('PATCH',f'/v1/runs/{slow}/settings',{'expectedConfigurationRevision':0,'patch':{'leak':.2}})
            until(lambda:client.request('GET',f"/v1/operations/{pending['id']}")['status']=='running')
            time.sleep(.1)
            operation('POST',f'/v1/runs/{slow}/actions/stop',{})
            release_slow.set();outcome=client.wait(pending['id'],30)
            assert outcome['status'] in ('cancelled','needsAttention','failed'),outcome
            assert client.request('GET',f'/v1/runs/{slow}')['phase']=='stopped'
            assert client.request('GET',f'/v1/runs/{slow}/settings')['configurationRevision']==0
            count=len(calls); proc.send_signal(signal.SIGTERM); assert proc.wait(20)==0
            until(lambda:not descriptor.exists()); proc,client=start(); time.sleep(.4)
            assert len(calls)==count
            retained=client.request('GET','/v1/runs')['runs'];assert all(r['phase']=='retained' for r in retained)
            # Recovered journals and scans remain readable without loading or starting a run.
            client.request('GET',f'/v1/runs/{runs[0]}/sonar')
            client.request('GET',f"/v1/runs/{runs[0]}/entries/{all_entries['entries'][0]['entryId']}")
            operation('POST',f'/v1/runs/{runs[0]}/actions/resume',{})
            until(lambda:len(calls)>count)
            operation('POST',f'/v1/runs/{runs[0]}/actions/pause',{})
            report={'status':'passed','runs':3,'maximumConcurrentProviderCalls':maximum,'providerCalls':len(calls),'stablePagination':True,'scheduledGrowth':{'from':32,'to':48,'boundaryStep':7},'scheduledCustomPrompt':True,'codecTransition':True,'restartDispatches':0,'stopSupersedesPendingChange':True,'cliEntries':all_entries['total'],'verifiedExports':exports}
            if args.report: args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report,indent=2))
        except Exception:
            print((root/'app.log').read_text(),file=sys.stderr);raise
        finally:
            if proc and proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try: proc.wait(20)
                except subprocess.TimeoutExpired: proc.kill();proc.wait()
            release_slow.set();provider.shutdown();log.close()

if __name__=='__main__':main()
