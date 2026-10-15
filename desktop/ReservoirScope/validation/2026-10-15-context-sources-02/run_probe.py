#!/usr/bin/env python3
"""Frozen standalone context-sources probe. Stdlib; no app, feedback or retries.

Only the supplied owned supervisor receipts choose a literal loopback endpoint.
HTTP completion mirrors the app transport, not journal/save/quality acceptance.
The socket watchdog enforces a whole-exchange deadline even for trickled headers.
Receipt identities establish local provenance, not authentication of a live PID.
"""
from __future__ import annotations
import argparse
import datetime as dt
from decimal import Decimal
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import signal
import socket
import stat
import threading
import time

MAX_RESPONSE = 1 << 20
MAX_PROMPT = 256 << 10
RESERVE = 1 << 20
MODEL = 'gemma3:4b'
DIGEST = 'a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a'
OVERLAY_SHA = 'b055ddd7c91e67c75fae0df183b234836ef11eb3a96574b9da458b06576196fa'
SELECTION_SHA = '7de0ae35b3d231201679b2242484cb24a9122a8f9ce866b8554dfe6384a2d86a'
STAGE_SHA = '76cf4002d95bffcf6ef2665f728739e15ffb9aff1726dd8270510b50beeca3dc'
CACHE = '/Users/v/other/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.12.1-real-gemma3-4b'
EXECUTABLE = '/Applications/Ollama.app/Contents/Resources/ollama'
EXECUTABLE_SHA = '3501c7c3d9885269fb5b3d141a0a3789e868f6ad15150d4a07b195965be33a5d'
PLIST_SHA = '10d340acf299d8357c8f8c699bc1c7cb10ae0e16508f39795a31d023fe6ecbe8'
DESKTOP = Path(__file__).resolve().parents[2]
ORDER = [(step, c) for i, step in enumerate((30,60,90,120,330,360)) for c in ('AB' if i % 2 == 0 else 'BA')]
BOUNDS = dict(model=MODEL, modelManifestSha256=DIGEST, contextTokens=8192,
              outputTokens=1024, temperature=0, requestDeadlineSeconds=180,
              inventoryDeadlineSeconds=5, probeBudgetSeconds=900,
              storageBudgetBytes=64 << 20, serviceLifetimeSeconds=1200,
              minimumServiceRemainingAtStart=1140, softwareSelectionSha256=OVERLAY_SHA)


def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def encoded(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def ordinary_path(path, directory=False):
    path = Path(path)
    require(path.is_absolute(), 'Absolute path required')
    require(path == path.resolve(strict=True), 'Symlink/noncanonical path refused')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'Ordinary file/directory required')
    require(info.st_uid == os.getuid(), 'Owned path required')
    return path


def read_bound(path, limit=MAX_RESPONSE, expected=None):
    path = ordinary_path(path)
    with path.open('rb') as f: data = f.read(limit + 1)
    require(len(data) <= limit, 'Input size bound exceeded')
    if expected is not None: require(sha(data) == expected, f'Hash mismatch: {path}')
    return data


def identity(path, data): return dict(path=str(path), bytes=len(data), sha256=sha(data))


def load_inputs(path, expected):
    raw = read_bound(path, expected=expected); doc = json.loads(raw)
    require(doc['schema'] == 'reservoir-context-sources-inputs-v1', 'Input schema mismatch')
    plan_ref = doc['runPlan']; plan_raw = read_bound(plan_ref['path'], expected=plan_ref['sha256'])
    require(len(plan_raw) == plan_ref['bytes'], 'Plan size mismatch')
    plan = json.loads(plan_raw)
    require(plan['schema'] == 'reservoir-context-sources-plan-v1' and plan['episodeId'] == doc['episodeId'], 'Plan identity mismatch')
    for key, value in BOUNDS.items():
        require(type(plan[key]) is type(value) and plan[key] == value, f'Frozen bound mismatch: {key}')
    require(len(doc['slots']) == 12, 'Exactly twelve slots required')
    refs = [identity(path, raw), identity(plan_ref['path'], plan_raw)]; prompts = []
    for i, (slot, (step, condition)) in enumerate(zip(doc['slots'], ORDER), 1):
        require(slot['slot'] == i and slot['anchorStep'] == step and slot['condition'] == condition, 'Frozen slot order mismatch')
        ref = slot['prompt']; data = read_bound(ref['path'], MAX_PROMPT, ref['sha256'])
        require(len(data) == ref['bytes'], 'Prompt size mismatch')
        prompts.append(data.decode('utf-8')); refs.append(identity(ref['path'], data))
    return plan, doc, prompts, refs


def verify_refs(refs):
    for ref in refs:
        data = read_bound(ref['path'], expected=ref['sha256'])
        require(len(data) == ref['bytes'], 'Retained input size changed')


def check_owned(plan, now=None):
    """Read only exact named supervisor metadata; never enumerate/contact processes."""
    directory = ordinary_path(plan['ownedServiceDirectory'], True)
    require(directory.parent == (DESKTOP/'target/qa').resolve(), 'Service directory must be in this desktop QA root')
    require(directory.name == '0.20-context-sources-gemma3-4b-run02', 'Unexpected owned service identity')
    for terminal in ('stop-request', 'supervision-result.json'):
        require(not (directory/terminal).exists(), 'Owned service already stopping/finished')
    refs = []; docs = {}
    for name in ('launch-intent.json', 'owned-process.json', 'endpoint.json'):
        raw = read_bound(directory/name); refs.append(identity(directory/name, raw)); docs[name] = json.loads(raw)
    launch, proc, endpoint = [docs[n] for n in ('launch-intent.json','owned-process.json','endpoint.json')]
    raw = read_bound(plan['softwareSelectionPath'], expected=plan['softwareSelectionSha256'])
    refs.append(identity(plan['softwareSelectionPath'], raw)); overlay = json.loads(raw)
    require(overlay['modelSelectionSha256'] == SELECTION_SHA and overlay['stageReceiptSha256'] == STAGE_SHA, 'Software/model selection mismatch')
    require(overlay['stageReceiptPath'] == CACHE+'/stage-receipt.json', 'Stage path mismatch')
    staged = read_bound(overlay['stageReceiptPath'], expected=STAGE_SHA); refs.append(identity(overlay['stageReceiptPath'], staged))
    require(launch['argv'] == [EXECUTABLE, 'serve'] and launch['workingDirectory'] == str(directory), 'Owned argv/path mismatch')
    require(launch['cacheDirectory'] == CACHE and launch['homePreserved'] is True, 'Cache/HOME mismatch')
    require(launch['maximumLifetimeSeconds'] == plan['serviceLifetimeSeconds'], 'Service lifetime mismatch')
    require(launch['selectionSha256'] == SELECTION_SHA and launch['stageReceiptSha256'] == STAGE_SHA, 'Launch selection mismatch')
    expected_env = {'OLLAMA_HOST':'127.0.0.1:0', 'OLLAMA_MODELS':CACHE+'/models', 'OLLAMA_NO_CLOUD':'1', 'OLLAMA_NOPRUNE':'1', 'OLLAMA_NUM_PARALLEL':'1', 'OLLAMA_MAX_LOADED_MODELS':'1', 'OLLAMA_MAX_QUEUE':'1', 'OLLAMA_CONTEXT_LENGTH':'4096', 'OLLAMA_KEEP_ALIVE':'2m', 'OLLAMA_LOAD_TIMEOUT':'60s', 'OLLAMA_DEBUG':'0', 'OLLAMA_DEBUG_LOG_REQUESTS':'false', 'OLLAMA_NOHISTORY':'1'}
    require(launch['childOverrides'] == expected_env, 'Child isolation flags mismatch')
    require(proc['software'] == launch['software'] and proc['softwareSelection'] == launch['softwareSelection'], 'Launch/process software mismatch')
    software = launch['software']; swsel = launch['softwareSelection']; selected = overlay['installedSoftware']
    require(software['versionFromPlist'] == selected['CFBundleShortVersionString'] == selected['CFBundleVersion'] == '0.40.5', 'Version mismatch')
    for kind, want_path, want_sha, want_size, path_key, hash_key, size_key in (
        ('executable',EXECUTABLE,EXECUTABLE_SHA,52290224,'resolvedExecutablePath','executableSha256','executableSizeBytes'),
        ('plist','/Applications/Ollama.app/Contents/Info.plist',PLIST_SHA,1377,'plistPath','plistSha256','plistSizeBytes')):
        info = software[kind]
        require(info['path'] == selected[path_key] == want_path and info['sha256'] == selected[hash_key] == want_sha and info['sizeBytes'] == selected[size_key] == want_size, 'Software identity mismatch')
    require(swsel['receipt']['path'] == plan['softwareSelectionPath'] and swsel['receipt']['sha256'] == OVERLAY_SHA and swsel['stageReceipt']['sha256'] == STAGE_SHA and swsel['modelSelectionSha256'] == SELECTION_SHA, 'Overlay receipt mismatch')
    root_info = launch['supervisionRootIdentity']; actual = directory.stat()
    require(str(actual.st_dev) == root_info['device'] and str(actual.st_ino) == root_info['inode'], 'Supervision directory identity mismatch')
    pid = proc['pid']; port = endpoint['port']
    require(type(pid) is int and pid > 1 and proc['pgid'] == proc['sid'] == endpoint['pid'] == pid and type(proc['directChildOfSupervisorPid']) is int and proc['directChildOfSupervisorPid'] > 1, 'Owned process identity mismatch')
    require(type(port) is int and 1 <= port <= 65535 and endpoint['endpoint'] == f'http://127.0.0.1:{port}', 'Literal endpoint mismatch')
    require(endpoint['selectionSha256'] == SELECTION_SHA, 'Endpoint model selection mismatch')
    spawned = proc['spawnedAtMonotonicSeconds']; now = time.monotonic() if now is None else now
    require(type(spawned) in (float,int) and math.isfinite(spawned) and 0 <= now-spawned <= 1200, 'Invalid/stale monotonic service clock')
    remaining = 1200-(now-spawned)
    require(remaining >= plan['minimumServiceRemainingAtStart'], 'Insufficient owned service lifetime at probe start')
    return port, refs, dict(pid=pid, spawnedAtMonotonicSeconds=spawned, serviceRemainingAtStartSeconds=remaining, spawnedAtUtc=proc['spawnedAtUtc'], receiptAtUtc=utc(), scope='Owned supervisor receipts; no independent process inspection/authentication.')


def request_body(prompt, plan):
    return encoded({'model':plan['model'], 'stream':False, 'messages':[{'role':'user','content':prompt}], 'options':{'num_ctx':plan['contextTokens'],'num_predict':plan['outputTokens'],'temperature':plan['temperature']}})


def exchange(port, method, path, body, seconds, cancel, cap=MAX_RESPONSE):
    """One connection/one attempt, no proxy, redirect or retry. Own socket only."""
    start = time.monotonic(); deadline = start+seconds; done = threading.Event(); expired = threading.Event()
    lock = threading.Lock(); held = [None]; raw = bytearray()
    result = dict(method=method, path=path, atUtc=utc(), startedMonotonicSeconds=start, status=None, headers=[], responseTruncated=False, error=None)
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=seconds)
    def watchdog():
        while not done.is_set():
            left = deadline-time.monotonic()
            if cancel.is_set() or left <= 0:
                if left <= 0: expired.set()
                with lock:
                    if held[0] is not None:
                        try: held[0].shutdown(socket.SHUT_RDWR)
                        except OSError: pass
                return
            done.wait(min(.02,left))
    watch = threading.Thread(target=watchdog, daemon=True); watch.start()
    try:
        if cancel.is_set(): raise InterruptedError('Cancelled before connection')
        conn.connect()
        with lock: held[0] = conn.sock
        if cancel.is_set() or expired.is_set() or time.monotonic() >= deadline: raise TimeoutError('Deadline/cancellation before request')
        conn.auto_open = 0
        conn.request(method, path, body=body, headers={'Content-Type':'application/json','Accept':'application/json','Accept-Encoding':'identity','Connection':'close'})
        response = conn.getresponse(); result['status'] = response.status
        headers = response.getheaders(); require(len(encoded(headers)) <= 16384, 'Response headers metadata bound exceeded')
        result['headers'] = headers
        while True:
            chunk = response.read1(min(16384, cap+1-len(raw)))
            if not chunk: break
            raw.extend(chunk)
            if len(raw) > cap:
                result['responseTruncated'] = True; del raw[cap:]; raise ValueError('Response exceeds 1 MiB bound')
            if time.monotonic() >= deadline: raise TimeoutError('Total response deadline')
        require(response.length in (None,0), 'Premature EOF before declared response length')
        if cancel.is_set(): raise InterruptedError('Cancelled during exchange')
        if expired.is_set() or time.monotonic() >= deadline: raise TimeoutError('Total response deadline')
        require(200 <= response.status < 300, f'HTTP status {response.status}; no redirect/retry')
    except (Exception, KeyboardInterrupt) as error:
        result['error'] = ('interrupted' if cancel.is_set() or isinstance(error,(InterruptedError,KeyboardInterrupt)) else 'deadline' if expired.is_set() or time.monotonic() >= deadline else type(error).__name__)+': '+str(error)[:2048]
    finally:
        done.set(); watch.join(timeout=.2); conn.close()
    result.update(elapsedSeconds=time.monotonic()-start, endedAtUtc=utc(), rawBytes=len(raw), rawSha256=sha(raw), deadlineSeconds=seconds)
    return result, bytes(raw)


class Obj(dict):
    def __init__(self, pairs):
        super().__init__(); self.duplicates = set()
        for key,value in pairs:
            if key in self: self.duplicates.add(key)
            self[key] = value


def parse_json(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=Obj, parse_float=Decimal, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON constant')))


def prompt_evidence(doc):
    if 'prompt_eval_count' in doc.duplicates: return dict(status='unusable', reason='duplicateField')
    value = doc.get('prompt_eval_count')
    if value is None: return None
    if type(value) is int:
        if value < 0: reason = 'negative'
        elif value > (1<<64)-1: reason = 'outOfRange'
        else: return dict(status='reported', count=str(value))
    elif isinstance(value,Decimal): reason = 'nonInteger'
    else: reason = 'wrongType'
    return dict(status='unusable', reason=reason)


def decode_response(raw, plan):
    doc = parse_json(raw); require(isinstance(doc,Obj), 'Response object required')
    require(not (doc.duplicates & {'done','message','model','done_reason','eval_count'}), 'Duplicate required/known response field')
    require(type(doc.get('done')) is bool and isinstance(doc.get('message'),Obj), 'done/message envelope invalid')
    msg = doc['message']; require('content' not in msg.duplicates and type(msg.get('content')) is str, 'message.content invalid')
    model, reason, count = doc.get('model'), doc.get('done_reason'), doc.get('eval_count')
    require(model is None or type(model) is str, 'Returned model type invalid')
    require(model is None or model == plan['model'], 'Returned model mismatch')
    require(reason is None or type(reason) is str, 'Stop reason type invalid')
    require(count is None or type(count) is int and -(1<<63) <= count < (1<<63), 'eval_count type/range invalid')
    text = msg['content']; text.encode('utf-8')  # reject lone surrogates
    complete = doc['done'] and reason != 'length' and (count is None or 0 <= count <= plan['outputTokens'])
    return text, dict(done=doc['done'], providerModel=model, stopReason=reason[:1024] if reason is not None else None, stopReasonTruncated=reason is not None and len(reason)>1024, tokenCount=str(count) if count is not None else None, providerPromptEvaluation=prompt_evidence(doc), transportComplete=complete, scope='Transport predicate only; no journal eligibility, save, application or quality claim.')


def decode_inventory(raw, plan):
    doc = parse_json(raw); require(isinstance(doc,Obj) and 'models' not in doc.duplicates and isinstance(doc.get('models'),list), 'Inventory envelope invalid')
    require(len(doc['models']) <= 10000, 'Inventory row limit')
    found = []
    for row in doc['models']:
        require(isinstance(row,Obj) and type(row.get('name')) is str and not(row.duplicates & {'name','model','digest'}), 'Inventory row invalid')
        if row['name'] == plan['model']: found.append(row)
    require(len(found) == 1, 'Exact inventory model missing/ambiguous')
    row = found[0]
    require(row.get('model') in (None,plan['model']) and row.get('digest') == plan['modelManifestSha256'], 'Exact inventory model/digest mismatch')
    return dict(model=row['name'], digest=row['digest'], inventoryOnly=True)


class Store:
    def __init__(self, directory, budget):
        self.path = Path(directory); self.path.mkdir(mode=0o700, parents=False, exist_ok=False); self.budget = budget
    def used(self):
        total = 0
        for path in self.path.iterdir():
            require(path.is_file() and not path.is_symlink(), 'Unexpected output object')
            total += path.stat().st_size
        return total
    def reserve(self, amount): require(self.used()+amount+RESERVE <= self.budget, 'Persisted storage budget insufficient before dispatch')
    def write(self, name, data):
        require('/' not in name and len(data)+self.used()+RESERVE//2 <= self.budget, 'Output storage bound')
        with (self.path/name).open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        return identity(self.path/name,data)
    def ledger(self, doc):
        data = encoded(doc)+b'\n'; require(len(data) <= RESERVE//4 and self.used()+len(data) <= self.budget, 'Ledger storage bound')
        temporary = self.path/'ledger.next'
        with temporary.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temporary,self.path/'ledger.json')


def perform(plan, prompts, slots, store, cancel, port, refs, clock=time.monotonic, http=exchange, ownership=None):
    start = clock(); result = dict(schema='reservoir-context-sources-run-v1', episodeId=plan['episodeId'], atUtc=utc(), startMonotonicSeconds=start, status='running', stopReason=None, inventory=None, slots=slots, boundaries={'noApplicationSession':True,'noFeedback':True,'noRetries':True,'completionIsTransportOnly':True})
    store.ledger(result)
    def check():
        require(not cancel.is_set(), 'Interrupted before dispatch')
        verify_refs(refs)
        for name in ('stop-request','supervision-result.json'):
            require(not (Path(plan['ownedServiceDirectory'])/name).exists(), 'Owned service terminal marker present')
    try:
        if ownership is not None:
            remaining = 1200-(start-ownership['spawnedAtMonotonicSeconds'])
            result['serviceRemainingAtProbeStartSeconds'] = remaining
            require(remaining >= plan['minimumServiceRemainingAtStart'], 'Insufficient service lifetime at actual probe start')
        check(); store.reserve(2*MAX_RESPONSE)
        meta, raw = http(port,'GET','/api/tags',None,plan['inventoryDeadlineSeconds'],cancel)
        meta['raw'] = store.write('inventory-response.bin',raw); result['inventory'] = meta
        require(meta['error'] is None, 'Readiness failed: '+str(meta['error']))
        decode_start = time.monotonic()
        meta['selected'] = decode_inventory(raw,plan)
        require(meta.get('elapsedSeconds',0)+(time.monotonic()-decode_start) < plan['inventoryDeadlineSeconds'], 'Inventory deadline exceeded after decode')
        require(clock()-start < plan['probeBudgetSeconds'], 'Probe budget exhausted during inventory')
        store.ledger(result)
        for slot,prompt in zip(slots,prompts):
            check()
            if plan['probeBudgetSeconds']-(clock()-start) < plan['requestDeadlineSeconds']:
                result['stopReason'] = 'insufficient_full_request_budget'; break
            body = request_body(prompt,plan); store.reserve(len(body)+2*MAX_RESPONSE+65536)
            prefix = f"slot-{slot['slot']:02}"
            slot['request'] = store.write(prefix+'-request.json',body)
            slot.update(status='dispatching', dispatchIntentAtUtc=utc(), dispatchIntentMonotonicSeconds=clock())
            store.ledger(result)  # intent persisted before one HTTP attempt; crash is not permission to resend
            check()
            if plan['probeBudgetSeconds']-(clock()-start) < plan['requestDeadlineSeconds']:
                slot['status'] = 'unstarted'; slot['notDispatchedReason'] = 'Budget expired during durable preparation'
                result['stopReason'] = 'insufficient_full_request_budget'; break
            meta, raw = http(port,'POST','/api/chat',body,plan['requestDeadlineSeconds'],cancel)
            slot['exchange'] = meta; slot['response'] = store.write(prefix+'-response.bin',raw)
            if meta['error'] is not None:
                slot['status'] = 'interrupted' if meta['error'].startswith('interrupted') else 'failed'; result['stopReason'] = meta['error']; break
            try:
                text, parsed = decode_response(raw,plan)
                require(clock()-slot['dispatchIntentMonotonicSeconds'] < plan['requestDeadlineSeconds'], 'Total deadline exceeded after decode')
                slot['text'] = store.write(prefix+'-text.txt',text.encode('utf-8')); slot['parsed'] = parsed
                slot['status'] = 'complete' if parsed['transportComplete'] else 'incomplete'
            except Exception as error:
                slot['status'] = 'failed'; slot['parseError'] = str(error)[:2048]
            store.ledger(result)
            if slot['status'] != 'complete': result['stopReason'] = slot.get('parseError','first_incomplete_response'); break
        else: result['stopReason'] = 'all_twelve_completed'
        result['status'] = 'completed' if result['stopReason'] == 'all_twelve_completed' else 'stopped'
    except (Exception,KeyboardInterrupt) as error:
        result['status'] = 'interrupted' if cancel.is_set() or isinstance(error,KeyboardInterrupt) else 'refused_or_failed'
        result['stopReason'] = str(error)[:2048]
        for slot in slots:
            if slot['status'] == 'dispatching': slot['status'] = 'interrupted_or_unresolved'; slot['outcomeUnknown'] = True
    finally:
        result['endedAtUtc'] = utc(); result['elapsedSeconds'] = clock()-start
        result['completedCount'] = sum(s['status']=='complete' for s in slots)
        result['unstartedCount'] = sum(s['status']=='unstarted' for s in slots)
        try: verify_refs(refs); result['inputIdentitiesUnchanged'] = True
        except Exception as error: result['inputIdentitiesUnchanged'] = False; result['identityError'] = str(error)[:2048]; result['status'] = 'failed_identity'
        store.ledger(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True); parser.add_argument('--expected-inputs-sha256',required=True); parser.add_argument('--output-directory',type=Path,required=True)
    args = parser.parse_args(); out = args.output_directory
    require(out.is_absolute() and out.parent == ordinary_path(DESKTOP/'target/qa',True), 'Fresh output must be directly under this desktop target/qa')
    require(out.name.startswith('0.20-context-sources-') and out.name != '0.20-context-sources-gemma3-4b-run02', 'Unexpected output directory name')
    store = Store(out,64<<20)
    slots = [dict(slot=i,anchorStep=step,condition=c,status='unstarted') for i,(step,c) in enumerate(ORDER,1)]
    refused = dict(schema='reservoir-context-sources-run-v1',status='preflight',atUtc=utc(),slots=slots,inputsPath=str(args.inputs),expectedInputsSha256=args.expected_inputs_sha256)
    store.ledger(refused); cancel = threading.Event(); previous = {}
    for sig in (signal.SIGINT,signal.SIGTERM): previous[sig] = signal.signal(sig, lambda *_: cancel.set())
    try:
        plan, doc, prompts, refs = load_inputs(args.inputs,args.expected_inputs_sha256)
        port, owner_refs, ownership = check_owned(plan); refs += owner_refs
        # Snapshot only named public/owned metadata and frozen prompts; no private keys or blobs.
        store.write('input-identities.json',encoded(refs)); store.write('ownership.json',encoded(ownership))
    except (Exception,KeyboardInterrupt) as error:
        refused.update(status='refused_before_network',reason=str(error)[:2048],endedAtUtc=utc(),networkRequests=0)
        store.ledger(refused); return 2
    finally:
        for sig, handler in previous.items(): signal.signal(sig,handler)
    # Preflight is over. Never rewrite a post-dispatch I/O failure as zero requests.
    for sig in previous: signal.signal(sig, lambda *_: cancel.set())
    try:
        result = perform(plan,prompts,slots,store,cancel,port,refs,ownership=ownership)
        return 0 if result['status']=='completed' else 2
    finally:
        for sig, handler in previous.items(): signal.signal(sig,handler)


if __name__ == '__main__': raise SystemExit(main())
