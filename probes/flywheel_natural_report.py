#!/usr/bin/env python3
"""Offline coverage and exact-source scanner replay of captured S-006 outputs.

Reads only a research capture. Retains all attempt statuses; no model inference,
network, live imports or source mutation. Rust harness executes locally from a
temporary directory. Its scanner span and marker constant are verbatim source.
"""
import argparse
from collections import Counter,defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from flywheel_natural_capture import ROOT, BOUNDS, era, sha


def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def timestamp(j):
    v=j.get('timestamp_unix_s',j.get('timestamp'))
    if v is None:return None
    try:return float(v)
    except ValueError:return datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    c=a.capture.resolve();out=a.out.resolve()
    if not c.is_relative_to(ROOT/'research/outputs') or out.exists() or not out.is_relative_to(ROOT/'research/outputs'):ap.error('Use research capture and new research output')
    items=json.loads((c/'manifest.json').read_text())
    for x in items:
        b=(c/x['capture']).read_bytes();assert sha(b)==x['sha256'] and len(b)==x['bytes'],x['capture']
    out.mkdir(parents=True,mode=0o700)
    constants=(c/'source/after-fallback_contracts.rs').read_text();s=constants.index('const KNOWN_MODEL_CONTROL_MARKERS:');e=constants.index('];',s)+2;constant=constants[s:e]
    # These Rust literals use JSON-compatible string escapes (including newline).
    tokens=[json.loads('"'+value+'"') for value in re.findall(r'"([^"\n]+)"',constant)]
    def markers(text):return any(token in text for token in tokens)
    inputs=[];attempts=[];journals=[];accepted=[];diagnostics={};by_response=defaultdict(list)
    for item in items:
        f=item['capture'];p=c/f
        if f.startswith('generations/'):
            j=json.loads(p.read_text());response=j.get('response_text');valid=response is None or sha(response.encode())==j.get('response_sha256')
            assert valid,f
            row={k:j.get(k) for k in ['generation_id','attempt_index','pid','status','backend','model','contract_version','created_at_unix_ms','response_sha256','elapsed_s']}
            row.update(capture=f,era=item['era'],response_available=response is not None,marker_bearing=markers(response or ''))
            attempts.append(row)
            if response is not None:by_response[sha(response.encode())].append(row)
            if row['marker_bearing']:inputs.append({'kind':'generation_normalized_response','capture':f,'era':item['era'],'text':response})
        elif f.startswith('journals/'):
            text=p.read_text();row={'capture':f,'era':item['era'],'filename_unix':item['filename_unix'],'marker_bearing':markers(text)};journals.append(row)
            if row['marker_bearing']:inputs.append({'kind':'journal_full_text','capture':f,'era':item['era'],'text':text})
    for item in items:
        f=item['capture']
        if not f.startswith('accepted/'):continue
        j=json.loads((c/f).read_text());assert sha((c/f).read_bytes())==Path(f).stem
        response=json.loads(j['attempt']['response_json']);raw=response.get('choices',[{}])[0].get('message',{}).get('content') if response.get('choices') else response.get('message',{}).get('content')
        completion=j['accepted_completion'];links=by_response.get(sha(completion.encode()),[])
        row={'capture':f,'schema':j.get('schema'),'raw_response_available':isinstance(raw,str),'raw_marker_bearing':markers(raw or ''),'completion_sha256':sha(completion.encode()),'generation_candidates':[x['capture'] for x in links],'candidate_eras':sorted({x['era'] for x in links}),'provider_route':j['attempt'].get('provider_route'),'provider_model':j['attempt'].get('provider_model')}
        accepted.append(row)
        if raw is not None and markers(raw) and links:
            inputs.append({'kind':'accepted_provider_raw_response','capture':f,'era':row['candidate_eras'][0] if len(row['candidate_eras'])==1 else 'ambiguous','text':raw,'generation_candidates':row['generation_candidates']})
    for item in items:
        f=item['capture']
        if not f.startswith('diagnostics/'):continue
        rows=[];unknown=[]
        for i,line in enumerate((c/f).read_text().splitlines()):
            try:j=json.loads(line);t=timestamp(j)
            except Exception as ex:unknown.append({'line':i+1,'error':str(ex)});continue
            rows.append({'line':i+1,'time':t,'era':era(t) if t is not None else None,'record':j})
        selected=[x for x in rows if x['era']]
        diagnostics[Path(f).name]={'total_lines':len(rows),'parse_errors':unknown,'first_time':min((x['time'] for x in rows if x['time'] is not None),default=None),'last_time':max((x['time'] for x in rows if x['time'] is not None),default=None),'selected':selected}
    summary={}
    for period in BOUNDS:
        g=[x for x in attempts if x['era']==period];j=[x for x in journals if x['era']==period]
        summary[period]={'attempts':len(g),'unique_generations':len({x['generation_id'] for x in g}),'statuses':dict(Counter(x['status'] for x in g)),'responses_available':sum(x['response_available'] for x in g),'marker_bearing_responses':sum(x['marker_bearing'] for x in g),'pids':dict(Counter(x['pid'] for x in g)),'backend_model_contract':dict(Counter('|'.join([x['backend'],x['model'],x['contract_version']]) for x in g)),'journals':len(j),'marker_bearing_journals':sum(x['marker_bearing'] for x in j),'accepted_artifacts_with_unique_completion_match':sum(len(x['generation_candidates'])==1 and x['candidate_eras']==[period] for x in accepted),'cleanup_receipts':sum(x['era']==period for x in diagnostics['control_marker_cleanup.jsonl']['selected'])}
    write(out/'coverage.json',{'summary':summary,'attempts':attempts,'journals':journals,'accepted_artifacts':accepted,'diagnostics':diagnostics,'marker_vocabulary':tokens,'capture_files_verified':len(items)})
    controls=[('bracket_relation','<end_of_turn> [sic] (appears) at the boundary',True),('annotation_en','<end_of_turn> [sic]– appears at the boundary',True),('annotation_em','<end_of_turn> [sic]— appears at the boundary',True),('annotation_ellipsis','<end_of_turn> [sic]… appears at the boundary',True),('ordinary_quote','"<end_of_turn>"',False),('plain_relation','<end_of_turn> appears',False),('existing_annotation','<end_of_turn> [sic] appears',False),('bare_marker','<end_of_turn>',False),('not_marker','ordinary text',False),('unlisted_relation','<end_of_turn> [sic] creates',False)]
    inputs.extend({'kind':'synthetic_control','capture':name,'era':None,'text':text,'expected_changed':changed} for name,text,changed in controls)
    write(out/'inputs.json',inputs)
    outputs={};identities={};rustc=shutil.which('rustc');assert rustc
    for period in ['before','after']:
        source=(c/f'source/{period}-dialogue_runtime.rs').read_text();start=source.index('#[derive(Debug, Clone, Copy)]\nstruct KnownModelControlMarkerMatch');end=source.index('fn control_marker_placement_counts(',start);span=source[start:end]
        oldconstants=(c/f'source/{period}-fallback_contracts.rs').read_text();cs=oldconstants.index('const KNOWN_MODEL_CONTROL_MARKERS:');ce=oldconstants.index('];',cs)+2;assert oldconstants[cs:ce]==constant
        harness='#![allow(dead_code)]\nuse std::io::{self, BufRead};\n'+constant+'\n'+span+'''
fn main() {
 for (i,line) in io::stdin().lock().lines().enumerate() {
  let line=line.unwrap();
  let b: Vec<u8>=(0..line.len()).step_by(2).map(|n|u8::from_str_radix(&line[n..n+2],16).unwrap()).collect();
  let text=String::from_utf8(b).unwrap();
  let (out,matches)=scan_known_model_control_markers(&text);
  let hex:String=out.as_bytes().iter().map(|b|format!("{:02x}",b)).collect();
  let detail=matches.iter().map(|m|format!("{}:{}:{}",m.occurrence.start,m.occurrence.end,m.reference_syntax.is_some() as u8)).collect::<Vec<_>>().join(",");
  println!("{}\\t{}\\t{}",i,hex,detail);
 }
}
'''
        (out/f'{period}-harness.rs').write_text(harness)
        with tempfile.TemporaryDirectory(prefix='flywheel-natural-') as tmp:
            tmp=Path(tmp);src=tmp/'scanner.rs';binary=tmp/'scanner';src.write_text(harness)
            build=subprocess.run([rustc,'--edition=2021',str(src),'-o',str(binary)],capture_output=True,timeout=60);(out/f'{period}-build.txt').write_bytes(build.stdout+build.stderr);build.check_returncode()
            b=binary.read_bytes();(out/f'{period}-scanner').write_bytes(b)
            run=subprocess.run([str(binary)],input=('\n'.join(x['text'].encode().hex() for x in inputs)+'\n').encode(),capture_output=True,timeout=180,cwd=tmp);run.check_returncode();assert sha(binary.read_bytes())==sha(b)
        (out/f'{period}-output.tsv').write_bytes(run.stdout)
        results=[]
        for line in run.stdout.decode().splitlines():
            i,output,detail=line.split('\t');assert int(i)==len(results)
            matches=[]
            for term in detail.split(','):
                if term:
                    l,r,kept=map(int,term.split(':'));matches.append({'start_byte':l,'end_byte':r,'preserved':bool(kept)})
            results.append({'output':bytes.fromhex(output).decode(),'matches':matches})
        assert len(results)==len(inputs)
        outputs[period]=results;identities[period]={'source_sha256':sha(source.encode()),'scanner_span_sha256':sha(span.encode()),'scanner_start_line':source[:start].count('\n')+1,'scanner_end_line':source[:end].count('\n'),'harness_sha256':sha(harness.encode()),'binary_sha256':sha(b),'constant_sha256':sha(constant.encode())}
    changed=[];natural_occurrences=[]
    for i,x in enumerate(inputs):
        before=outputs['before'][i];after=outputs['after'][i]
        assert [(m['start_byte'],m['end_byte']) for m in before['matches']]==[(m['start_byte'],m['end_byte']) for m in after['matches']]
        differences=[{'start_byte':old['start_byte'],'end_byte':old['end_byte'],'preserved_before':old['preserved'],'preserved_after':new['preserved']} for old,new in zip(before['matches'],after['matches']) if old!=new]
        if differences:changed.append({'input_index':i,'kind':x['kind'],'capture':x['capture'],'era':x['era'],'differences':differences})
        if x['kind']=='synthetic_control':assert bool(differences)==x['expected_changed'],x['capture']
        else:natural_occurrences.append({'input_index':i,'capture':x['capture'],'kind':x['kind'],'era':x['era'],'marker_occurrences':len(after['matches']),'focal_opportunities':len(differences),'preserved_before':sum(m['preserved'] for m in before['matches']),'preserved_after':sum(m['preserved'] for m in after['matches'])})
    result={'scope':'Exact scanner on retained texts. Generation responses are after normalization; journals may include wrappers and code examples. Accepted artifact linkage is exact-completion candidate association, not a guaranteed attempt ID. Synthetic controls are separate.','source_identities':identities,'rustc':subprocess.check_output([rustc,'--version']).decode().strip(),'natural_occurrences':natural_occurrences,'changed':changed,'outputs':outputs,'natural_focal_occurrences':sum(x['focal_opportunities'] for x in natural_occurrences),'synthetic_cases':len(controls)}
    write(out/'replay.json',result)
    print(json.dumps({'coverage':summary,'natural_marker_bearing_texts':len(natural_occurrences),'natural_focal_occurrences':result['natural_focal_occurrences'],'synthetic_cases':len(controls),'changed':changed},indent=2))

if __name__=='__main__':main()
