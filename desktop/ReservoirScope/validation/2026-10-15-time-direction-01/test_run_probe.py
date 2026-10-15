"""Owned fake-loopback and temp-file qualification; no installed model/service access."""
import contextlib
import http.server
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('probe',Path(__file__).with_name('run_probe.py'))
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def response(**extra):
    d={'model':p.MODEL,'done':True,'message':{'role':'assistant','content':'A full synthetic reply.'},'done_reason':'stop','eval_count':12}
    d.update(extra); return p.encoded(d)


def plan(root):
    return dict(p.BOUNDS,schema='reservoir-time-direction-plan-v1',episodeId='fake-test',ownedServiceDirectory=str(root/'service'),softwareSelectionPath=str(root/'overlay.json'))


def slots(): return [dict(slot=i,anchorStep=s,condition=c,status='unstarted') for i,(s,c) in enumerate(p.ORDER,1)]


@contextlib.contextmanager
def server(action):
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def do_GET(self): self.act()
        def do_POST(self): self.act()
        def act(self):
            data=self.rfile.read(int(self.headers.get('Content-Length','0')))
            calls.append((self.command,self.path,data))
            try: action(self,len(calls))
            except (BrokenPipeError,ConnectionResetError,OSError): pass
    service=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    service.daemon_threads=True
    thread=threading.Thread(target=service.serve_forever,kwargs={'poll_interval':.01},daemon=True);thread.start()
    try: yield service.server_port,calls
    finally: service.shutdown();service.server_close();thread.join(1)


def send(handler,data,status=200):
    handler.send_response(status);handler.send_header('Content-Length',str(len(data)));handler.end_headers();handler.wfile.write(data)


class HttpTests(unittest.TestCase):
    def test_exact_body_and_no_proxy(self):
        prompt='Quoted "text" and \u2028 line.'; body=p.request_body(prompt,plan(Path('/tmp')))
        self.assertEqual(body,p.encoded({'messages':[{'content':prompt,'role':'user'}],'model':p.MODEL,'options':{'num_ctx':8192,'num_predict':1024,'temperature':0},'stream':False}))
        with server(lambda h,n:send(h,response())) as (port,calls),patch.dict(os.environ,{'HTTP_PROXY':'http://127.0.0.1:1','ALL_PROXY':'http://127.0.0.1:1'}):
            result,raw=p.exchange(port,'POST','/api/chat',body,1,threading.Event())
        self.assertIsNone(result['error']);self.assertEqual(len(calls),1);self.assertEqual(calls[0][2],body)
    def test_redirect_never_followed(self):
        def action(h,n):
            h.send_response(302);h.send_header('Location','http://127.0.0.1:1/foreign');h.send_header('Content-Length','0');h.end_headers()
        with server(action) as (port,calls): result,_=p.exchange(port,'GET','/api/tags',None,1,threading.Event())
        self.assertEqual(result['status'],302);self.assertIsNotNone(result['error']);self.assertEqual(len(calls),1)
    def test_503_never_retried(self):
        with server(lambda h,n:send(h,b'failure',503)) as (port,calls): result,raw=p.exchange(port,'POST','/api/chat',b'{}',1,threading.Event())
        self.assertEqual(raw,b'failure');self.assertEqual(len(calls),1);self.assertIsNotNone(result['error'])
    def test_oversize_prefix_retained(self):
        with server(lambda h,n:send(h,b'x'*(p.MAX_RESPONSE+1))) as (port,calls): result,raw=p.exchange(port,'POST','/api/chat',b'{}',2,threading.Event())
        self.assertEqual(len(raw),p.MAX_RESPONSE);self.assertTrue(result['responseTruncated']);self.assertIsNotNone(result['error'])
    def test_total_deadline_trickled_body_preserves_partial(self):
        def action(h,n):
            h.send_response(200);h.send_header('Content-Length','100');h.end_headers()
            for _ in range(100): h.wfile.write(b'x');h.wfile.flush();time.sleep(.025)
        with server(action) as (port,calls): result,raw=p.exchange(port,'POST','/api/chat',b'{}',.13,threading.Event())
        self.assertTrue(result['error'].startswith('deadline'));self.assertGreater(len(raw),0);self.assertLess(result['elapsedSeconds'],.6);self.assertEqual(len(calls),1)
    def test_total_deadline_trickled_headers(self):
        def action(h,n):
            for byte in b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}':
                h.connection.sendall(bytes([byte]));time.sleep(.025)
        with server(action) as (port,calls): result,_=p.exchange(port,'GET','/api/tags',None,.13,threading.Event())
        self.assertTrue(result['error'].startswith('deadline'));self.assertLess(result['elapsedSeconds'],.6)
    def test_cancel_interrupts_owned_socket_only(self):
        cancel=threading.Event()
        def action(h,n):
            h.send_response(200);h.send_header('Content-Length','100');h.end_headers();h.wfile.write(b'x');h.wfile.flush();cancel.set();time.sleep(.2)
        with server(action) as (port,calls): result,raw=p.exchange(port,'POST','/api/chat',b'{}',2,cancel)
        self.assertTrue(result['error'].startswith('interrupted'));self.assertLess(result['elapsedSeconds'],.6)
    def test_premature_eof_is_failure_even_parseable_prefix(self):
        def action(h,n):
            h.send_response(200);h.send_header('Content-Length','200');h.end_headers();h.wfile.write(b'{}');h.close_connection=True
        with server(action) as (port,calls): result,raw=p.exchange(port,'GET','/api/tags',None,1,threading.Event())
        self.assertEqual(raw,b'{}');self.assertIsNotNone(result['error'])


class DecodeTests(unittest.TestCase):
    def test_app_completeness_not_quality_gate(self):
        cfg=plan(Path('/tmp'))
        text,parsed=p.decode_response(b'{"done":true,"message":{"content":""}}',cfg)
        self.assertEqual(text,'');self.assertTrue(parsed['transportComplete'])
        for change in ({'done':False},{'done_reason':'length'},{'eval_count':1025},{'eval_count':-1}):
            with self.subTest(change=change):self.assertFalse(p.decode_response(response(**change),cfg)[1]['transportComplete'])
    def test_wrong_model_and_invalid_envelope_rejected(self):
        for raw in (response(model='other'),response(done='true'),response(eval_count=True),b'{"done":true,"done":false,"message":{"content":"x"}}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):p.decode_response(raw,plan(Path('/tmp')))
    def test_optional_prompt_evidence_never_gates(self):
        for token,expected in [('18446744073709551615',{'status':'reported','count':'18446744073709551615'}),('1e999',{'status':'unusable','reason':'nonInteger'}),('"bad"',{'status':'unusable','reason':'wrongType'}),('-1',{'status':'unusable','reason':'negative'}),('18446744073709551616',{'status':'unusable','reason':'outOfRange'}),('null',None)]:
            raw=b'{"done":true,"message":{"content":"x"},"prompt_eval_count":'+token.encode()+b'}'
            _,parsed=p.decode_response(raw,plan(Path('/tmp')));self.assertTrue(parsed['transportComplete']);self.assertEqual(parsed['providerPromptEvaluation'],expected)
        _,parsed=p.decode_response(b'{"done":true,"message":{"content":"x"},"prompt_eval_count":1,"prompt_eval_count":2}',plan(Path('/tmp')))
        self.assertEqual(parsed['providerPromptEvaluation']['reason'],'duplicateField')
    def test_duplicate_detection_linear_many_keys(self):
        raw=p.encoded({str(i):i for i in range(10000)})
        self.assertEqual(len(p.parse_json(raw)),10000)
    def test_inventory_exact_digest_and_ambiguity(self):
        row={'name':p.MODEL,'model':p.MODEL,'digest':p.DIGEST};cfg=plan(Path('/tmp'))
        self.assertEqual(p.decode_inventory(p.encoded({'models':[row]}),cfg)['digest'],p.DIGEST)
        for rows in ([],[row,row],[dict(row,digest='bad')],[dict(row,model='other')]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):p.decode_inventory(p.encoded({'models':rows}),cfg)


class RunTests(unittest.TestCase):
    def run_fake(self,root,mode='complete',budget=None,cancel=None,refs=None):
        cfg=plan(root); (root/'service').mkdir(exist_ok=True)
        if budget is not None:cfg['probeBudgetSeconds']=budget
        clock=[0.];calls=[]
        def http(port,method,path,body,seconds,event):
            calls.append(method); clock[0]+=.01
            if method=='GET':raw=p.encoded({'models':[{'name':p.MODEL,'digest':p.DIGEST}]})
            elif mode=='incomplete':raw=response(done_reason='length')
            else:raw=response()
            meta={'error':None,'status':200,'responseTruncated':False}
            if method=='POST' and mode=='failed':meta['error']='ConnectionResetError: synthetic'
            if method=='POST' and mode=='interrupt':event.set();meta['error']='interrupted: synthetic'
            if method=='POST' and mode=='changed':Path(refs[0]['path']).write_text('changed')
            return meta,raw
        store=p.Store(root/'out',64<<20)
        result=p.perform(cfg,['prompt']*12,slots(),store,cancel or threading.Event(),12345,refs or [],clock=lambda:clock[0],http=http)
        return result,calls,store
    def test_twelve_complete_order_and_ledgers(self):
        with tempfile.TemporaryDirectory() as d:
            result,calls,store=self.run_fake(Path(d))
            self.assertEqual(calls,['GET']+['POST']*12);self.assertEqual(result['completedCount'],12);self.assertEqual(result['status'],'completed')
            self.assertEqual([(s['anchorStep'],s['condition']) for s in result['slots']],p.ORDER)
            self.assertEqual(json.loads((store.path/'ledger.json').read_text()),result)
    def test_first_incomplete_retains_text_and_all_unstarted(self):
        with tempfile.TemporaryDirectory() as d:
            result,calls,store=self.run_fake(Path(d),'incomplete')
            self.assertEqual(calls,['GET','POST']);self.assertEqual(result['slots'][0]['status'],'incomplete');self.assertEqual(result['unstartedCount'],11)
            self.assertEqual(Path(result['slots'][0]['text']['path']).read_text(),'A full synthetic reply.')
    def test_failure_and_interruption_stop_without_retry(self):
        for mode in ('failed','interrupt'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                result,calls,_=self.run_fake(Path(d),mode)
                self.assertEqual(calls,['GET','POST']);self.assertEqual(result['unstartedCount'],11);self.assertIn(result['slots'][0]['status'],('failed','interrupted'))
    def test_less_than_full_deadline_leaves_all_unstarted(self):
        with tempfile.TemporaryDirectory() as d:
            result,calls,_=self.run_fake(Path(d),budget=180)
            self.assertEqual(calls,['GET']);self.assertEqual(result['unstartedCount'],12);self.assertEqual(result['stopReason'],'insufficient_full_request_budget')
    def test_cancel_before_dispatch_no_requests(self):
        with tempfile.TemporaryDirectory() as d:
            event=threading.Event();event.set();result,calls,_=self.run_fake(Path(d),cancel=event)
            self.assertEqual(calls,[]);self.assertEqual(result['unstartedCount'],12)
    def test_changed_input_stops_followup_and_marks_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();path=root/'frozen';path.write_text('old');ref=p.identity(path,b'old')
            result,calls,_=self.run_fake(root,'changed',refs=[ref])
            self.assertEqual(calls,['GET','POST']);self.assertEqual(result['status'],'failed_identity');self.assertEqual(result['unstartedCount'],11)
    def test_storage_admission_precedes_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=plan(root);store=p.Store(root/'out',p.RESERVE+1024);calls=[]
            result=p.perform(cfg,['x']*12,slots(),store,threading.Event(),1,[],http=lambda *a:calls.append(a))
            self.assertEqual(calls,[]);self.assertEqual(result['unstartedCount'],12)
    def test_probe_start_margin_rechecked_before_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=plan(root);store=p.Store(root/'out',64<<20);calls=[]
            result=p.perform(cfg,['x']*12,slots(),store,threading.Event(),1,[],clock=lambda:100.,http=lambda *a:calls.append(a),ownership={'spawnedAtMonotonicSeconds':39.})
            self.assertEqual(calls,[]);self.assertIn('actual probe start',result['stopReason'])
    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'out';p.Store(path,64<<20)
            with self.assertRaises(FileExistsError):p.Store(path,64<<20)


class IdentityTests(unittest.TestCase):
    def fixture(self,root):
        cfg=plan(root);service=root/'target/qa/0.20-time-direction-gemma3-4b-run01';service.mkdir(parents=True);cfg['ownedServiceDirectory']=str(service)
        stage=root/'stage.json';stage.write_bytes(b'{}');stage_sha=p.sha(b'{}')
        software={'versionFromPlist':'0.40.4','executable':{'path':p.EXECUTABLE,'sha256':p.EXECUTABLE_SHA,'sizeBytes':52241008},'plist':{'path':'/Applications/Ollama.app/Contents/Info.plist','sha256':p.PLIST_SHA,'sizeBytes':1377}}
        overlay={'modelSelectionSha256':p.SELECTION_SHA,'stageReceiptSha256':stage_sha,'stageReceiptPath':str(stage),'installedSoftware':{'CFBundleShortVersionString':'0.40.4','CFBundleVersion':'0.40.4','resolvedExecutablePath':p.EXECUTABLE,'executableSha256':p.EXECUTABLE_SHA,'executableSizeBytes':52241008,'plistPath':'/Applications/Ollama.app/Contents/Info.plist','plistSha256':p.PLIST_SHA,'plistSizeBytes':1377}}
        cfg['softwareSelectionPath']=str(root/'overlay.json');raw=p.encoded(overlay);Path(cfg['softwareSelectionPath']).write_bytes(raw);cfg['softwareSelectionSha256']=p.sha(raw)
        swsel={'receipt':{'path':cfg['softwareSelectionPath'],'sha256':p.sha(raw)},'stageReceipt':{'sha256':stage_sha},'modelSelectionSha256':p.SELECTION_SHA}
        env={'OLLAMA_HOST':'127.0.0.1:0','OLLAMA_MODELS':str(root)+'/models','OLLAMA_NO_CLOUD':'1','OLLAMA_NOPRUNE':'1','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_MAX_QUEUE':'1','OLLAMA_CONTEXT_LENGTH':'4096','OLLAMA_KEEP_ALIVE':'2m','OLLAMA_LOAD_TIMEOUT':'60s','OLLAMA_DEBUG':'0','OLLAMA_DEBUG_LOG_REQUESTS':'false','OLLAMA_NOHISTORY':'1'}
        stage.rename(root/'stage-receipt.json');overlay['stageReceiptPath']=str(root/'stage-receipt.json');raw=p.encoded(overlay);Path(cfg['softwareSelectionPath']).write_bytes(raw);cfg['softwareSelectionSha256']=p.sha(raw);swsel['receipt']['sha256']=p.sha(raw)
        info=service.stat();launch={'argv':[p.EXECUTABLE,'serve'],'workingDirectory':str(service),'cacheDirectory':str(root),'homePreserved':True,'maximumLifetimeSeconds':1200,'selectionSha256':p.SELECTION_SHA,'stageReceiptSha256':stage_sha,'childOverrides':env,'software':software,'softwareSelection':swsel,'supervisionRootIdentity':{'device':str(info.st_dev),'inode':str(info.st_ino)}}
        proc={'pid':12345,'pgid':12345,'sid':12345,'directChildOfSupervisorPid':12344,'spawnedAtMonotonicSeconds':100.,'spawnedAtUtc':'synthetic','software':software,'softwareSelection':swsel}
        endpoint={'pid':12345,'port':54321,'endpoint':'http://127.0.0.1:54321','selectionSha256':p.SELECTION_SHA}
        for name,doc in [('launch-intent.json',launch),('owned-process.json',proc),('endpoint.json',endpoint)]: (service/name).write_bytes(p.encoded(doc))
        return cfg,service,stage_sha
    def scoped(self,root,cfg,stage_sha):
        return patch.multiple(p,DESKTOP=root,CACHE=str(root),STAGE_SHA=stage_sha,OVERLAY_SHA=cfg['softwareSelectionSha256'])
    def test_exact_owned_receipt_chain_and_margin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();cfg,service,stage_sha=self.fixture(root)
            with self.scoped(root,cfg,stage_sha):
                port,refs,proof=p.check_owned(cfg,now=110.);self.assertEqual(port,54321);self.assertEqual(proof['serviceRemainingAtStartSeconds'],1190.)
                with self.assertRaises(ValueError):p.check_owned(cfg,now=161.)
    def test_missing_mismatched_endpoint_software_or_terminal_refused(self):
        for mutation in ('missing','pid','endpoint','software','stop'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();cfg,service,stage_sha=self.fixture(root)
                if mutation=='missing':(service/'owned-process.json').unlink()
                elif mutation=='stop':(service/'stop-request').write_text('stop')
                elif mutation=='software':
                    path=service/'launch-intent.json';doc=json.loads(path.read_text());doc['software']['versionFromPlist']='other';path.write_bytes(p.encoded(doc))
                else:
                    path=service/'endpoint.json';doc=json.loads(path.read_text());doc['pid' if mutation=='pid' else 'endpoint']=7 if mutation=='pid' else 'http://localhost:54321';path.write_bytes(p.encoded(doc))
                with self.scoped(root,cfg,stage_sha),self.assertRaises((ValueError,FileNotFoundError)):p.check_owned(cfg,now=110.)
    def test_frozen_input_hash_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'inputs.json';path.write_text('{}')
            with self.assertRaises(ValueError):p.load_inputs(path,'0'*64)
    def test_symlink_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();(root/'real').write_text('{}');(root/'link').symlink_to(root/'real')
            with self.assertRaises(ValueError):p.read_bound(root/'link')

class MainFailureTests(unittest.TestCase):
    def setup_main(self,root):
        (root/'target/qa').mkdir(parents=True)
        cfg=plan(root);ref=root/'input';ref.write_text('{}')
        argv=['run_probe.py','--inputs',str(ref),'--expected-inputs-sha256',p.sha(b'{}'),'--output-directory',str(root/'target/qa/0.20-time-direction-test')]
        return cfg,argv,root/'target/qa/0.20-time-direction-test'
    def test_missing_owner_receipt_refuses_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();cfg,argv,out=self.setup_main(root)
            with patch.object(p,'DESKTOP',root),patch('sys.argv',argv),patch.object(p,'load_inputs',return_value=(cfg,{},['x']*12,[])),patch.object(p,'check_owned',side_effect=FileNotFoundError('owned-process.json missing')),patch.object(p,'perform') as dispatch:
                self.assertEqual(p.main(),2);dispatch.assert_not_called()
            result=json.loads((out/'ledger.json').read_text());self.assertEqual(result['networkRequests'],0);self.assertEqual(len(result['slots']),12)
    def test_post_preflight_failure_never_rewritten_as_zero_requests(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();cfg,argv,out=self.setup_main(root)
            def failed(plan,prompts,slots,store,*args,**kwargs):
                store.ledger({'status':'dispatching','networkRequests':1,'slots':slots})
                raise OSError('final ledger disk failure after HTTP')
            with patch.object(p,'DESKTOP',root),patch('sys.argv',argv),patch.object(p,'load_inputs',return_value=(cfg,{},['x']*12,[])),patch.object(p,'check_owned',return_value=(1,[],{})),patch.object(p,'perform',side_effect=failed),self.assertRaises(OSError):p.main()
            result=json.loads((out/'ledger.json').read_text());self.assertEqual(result['networkRequests'],1);self.assertEqual(result['status'],'dispatching')

if __name__=='__main__':unittest.main()
