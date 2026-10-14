#!/usr/bin/env python3
"""An isolated ephemeral fake provider for the packaged UI receipt; never a model."""
import http.server, json, time, threading
from pathlib import Path
root=Path('target/qa/0.11-ui').resolve()
lock=threading.Lock()
model='reservoir-fixture:0.11'
def event(data):
    with lock, (root/'requests.jsonl').open('a') as f:
        f.write(json.dumps({'timeNs':str(time.time_ns()),**data},ensure_ascii=False)+'\n')
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self): self.handle_request(None)
    def do_POST(self):
        count=int(self.headers.get('Content-Length','0'))
        if count>1048576: self.send_error(413);return
        self.handle_request(json.loads(self.rfile.read(count)))
    def handle_request(self,body):
        config=json.loads((root/'control.json').read_text())
        event({'event':'received','method':self.command,'path':self.path,'body':body,'mode':config})
        if config.get('hold'):
            deadline=time.monotonic()+60
            while not (root/'release').exists() and time.monotonic()<deadline: time.sleep(.05)
        if self.path=='/api/tags' and self.command=='GET':
            response={'models':[{'name':model,'model':model,'digest':'owned-fixture-no-model-weights'}]}
        elif self.path=='/api/chat' and self.command=='POST':
            text=config.get('text','The retained field changes after saved words return as bounded input.')
            reply=json.dumps({'action':'WRITE_JOURNAL','text':text}) if body.get('format')=='json' else text
            response={'model':model,'done':not config.get('incomplete',False),'message':{'content':reply},'done_reason':'stop','eval_count':24}
        else: self.send_error(404);return
        data=json.dumps(response).encode()
        try:
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            event({'event':'sent','path':self.path,'response':response})
        except (BrokenPipeError,ConnectionResetError): event({'event':'client-closed','path':self.path})
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
info={'endpoint':f'http://127.0.0.1:{server.server_port}','model':model,'kind':'owned synthetic provider, no model service'}
with (root/'endpoint.json').open('x') as f:json.dump(info,f,indent=2)
print(json.dumps(info),flush=True)
try: server.serve_forever()
except KeyboardInterrupt: server.server_close()
