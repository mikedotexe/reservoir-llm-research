#!/usr/bin/env python3
"""Independently check the retained S-006 deployment/outcome account offline.

Recomputes file identities, clocks, response hashes and source/activation links.
Runs the exact compiled new scanner over every retained response and journal,
including texts excluded by the preliminary marker screen. No live access.
"""
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from flywheel_natural_capture import ROOT, BOUNDS, era, sha


def main():
    root=ROOT/'research/outputs/2026-09-07-flywheel-natural';c=root/'capture';r=root/'final-report'
    manifest=json.loads((c/'manifest.json').read_text())
    for x in manifest:
        b=(c/x['capture']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256'],x['capture']
    coverage=json.loads((r/'coverage.json').read_text());replay=json.loads((r/'replay.json').read_text());inputs=json.loads((r/'inputs.json').read_text())
    audit=json.loads((c/'deployment/audit.json').read_text());activation=json.loads((c/'deployment/activation-projected.json').read_text());selection=json.loads((c/'deployment/active-selection.json').read_text())
    assert activation['status']=='activated_verified' and activation['activation_performed']
    assert selection['manifest_sha256']==activation['manifest_sha256'] and selection['stage']==activation['stage']
    stack=json.loads((c/'deployment/environment-selected.json').read_text())
    expected={'before':activation['old_pid'],'after':activation['new_process']['pid']}
    for i,label in enumerate(['before','after']):
        inv=json.loads((c/f'deployment/{label}-inputs.json').read_text());man=json.loads((c/f'deployment/{label}-manifest.json').read_text())
        assert sha((c/f'deployment/{label}-inputs.json').read_bytes())==man['source_inputs']['sha256']
        assert len(inv['files'])==audit[label]['source_count'] and all(x['matches'] for x in audit[label]['source_checks'])
        declared_manifest=activation['old_identity']['manifest_sha256'] if label=='before' else activation['manifest_sha256']
        assert sha((c/f'deployment/{label}-manifest.json').read_bytes())==declared_manifest
        assert stack[i]['record']['processes']['stack']['bridge']['pid']==expected[label]
        assert stack[i]['record']['artifacts']['binaries']['spectral-bridge']['sha256']==audit[label]['binary_sha256']
        source=(c/f'source/{label}-dialogue_runtime.rs').read_text();identity=replay['source_identities'][label]
        assert sha(source.encode())==identity['source_sha256']
        matching=[x for x in inv['files'] if x['path'].endswith('/astrid/capsules/spectral-bridge/src/llm/provider/dialogue_runtime.rs')]
        assert len(matching)==1 and matching[0]['sha256']==identity['source_sha256']
        start=source.index('#[derive(Debug, Clone, Copy)]\nstruct KnownModelControlMarkerMatch');end=source.index('fn control_marker_placement_counts(',start);span=source[start:end]
        harness=(r/f'{label}-harness.rs').read_text();assert span in harness and sha(span.encode())==identity['scanner_span_sha256']
        assert sha(harness.encode())==identity['harness_sha256'];assert sha((r/f'{label}-scanner').read_bytes())==identity['binary_sha256']
        lines=(r/f'{label}-output.tsv').read_text().splitlines();assert len(lines)==len(inputs)
        for n,line in enumerate(lines):
            i,hextext,detail=line.split('\t');assert int(i)==n
            assert bytes.fromhex(hextext).decode()==replay['outputs'][label][n]['output']
    assert len(audit['diff']['changed'])==2 and len(audit['diff']['added'])==1 and not audit['diff']['removed']
    evidence=[];counts=Counter();pids=Counter();seen=set()
    for x in manifest:
        f=x['capture'];p=c/f
        if f.startswith('generations/'):
            j=json.loads(p.read_text());period=era(j['created_at_unix_ms']/1000);assert period==x['era'];assert j['pid']==expected[period]
            key=(j['generation_id'],j['attempt_index']);assert key not in seen;seen.add(key)
            counts[period]+=1;pids[(period,j['pid'])]+=1
            response=j.get('response_text')
            if response is not None:
                assert sha(response.encode())==j['response_sha256'];evidence.append((f,'normalized_response',response))
        elif f.startswith('journals/'):
            t=int(re.search(r'_(\d{10})\.txt$',f).group(1));assert era(t)==x['era'];evidence.append((f,'journal',p.read_text()))
        elif f.startswith('accepted/'):
            raw=p.read_bytes();assert sha(raw)==p.stem;j=json.loads(raw);res=json.loads(j['attempt']['response_json']);text=res['choices'][0]['message']['content'];evidence.append((f,'accepted_provider_response',text))
            assert len([q for q in coverage['attempts'] if q['response_sha256']==sha(j['accepted_completion'].encode())])==1
    assert dict(counts)=={k:v['attempts'] for k,v in coverage['summary'].items()}
    # An exact-scanner pass over ALL retained text independently checks the
    # preliminary regex/literal screen's zero, including escaped marker forms.
    wire=('\n'.join(text.encode().hex() for _,_,text in evidence)+'\n').encode()
    with tempfile.TemporaryDirectory(prefix='flywheel-screen-verify-') as tmp:
        binary=Path(tmp)/'scanner';binary.write_bytes((r/'after-scanner').read_bytes());binary.chmod(0o700)
        assert sha(binary.read_bytes())==replay['source_identities']['after']['binary_sha256']
        run=subprocess.run([str(binary)],input=wire,capture_output=True,timeout=180,cwd=tmp);run.check_returncode()
    lines=run.stdout.decode().splitlines();assert len(lines)==len(evidence)
    for n,line in enumerate(lines):
        i,hextext,detail=line.split('\t');assert int(i)==n and detail==''
        assert bytes.fromhex(hextext).decode()==evidence[n][2]
    # Explicit expected bytes for the four known defects and six controls.
    assert len(inputs)==10 and all(x['kind']=='synthetic_control' for x in inputs)
    for n,x in enumerate(inputs):
        before=replay['outputs']['before'][n]['output'];after=replay['outputs']['after'][n]['output']
        if n<4:assert before==x['text'].replace('<end_of_turn>','') and after==x['text']
        else:assert before==after
    assert replay['natural_focal_occurrences']==0
    result={'status':'passed','capture_files_verified':len(manifest),'release_source_inputs_verified_at_capture':{k:audit[k]['source_count'] for k in ['before','after']},'activation_manifest_source_binary_links':'matched','historical_stack_receipt_and_generation_pids':'matched','exact_scanner_screen':{'texts':len(evidence),'kinds':dict(Counter(k for _,k,_ in evidence)),'marker_occurrences':0,'input_stream_sha256':sha(wire),'scanner_output_sha256':sha(run.stdout)},'synthetic_defects_fixed':4,'controls_unchanged':6,'generation_counts':dict(counts),'limits':'Historical runtime records plus current retained bytes; no fresh process probe. No raw-provider census or operational-benefit estimate. Source inventory full bytes were read during capture; this verifier checks retained receipts and exact relevant source.'}
    (root/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
