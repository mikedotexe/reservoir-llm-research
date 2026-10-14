#!/usr/bin/env python3
"""Compare the portable reviewed-case validator with unchanged native Swift source.

Offline and read-only: compiles a temporary harness, never opens historical paths.
Run on macOS after staging resources; result is an execution receipt, not a study.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
DESKTOP = ROOT / 'desktop/ReservoirScope'
SOURCE = ROOT / 'native/ReservoirScope/Sources/ReservoirScope/ResearchCase.swift'

def digest(text): return hashlib.sha256(text.encode()).hexdigest()
def fixture(content='Supplied source.\nA remembered claim remains unresolved.', quote='Supplied source.'):
    return {'format':'research-cases-v1','cases':[{'id':'case','title':'Frozen account','question':'What was supplied?', 'summary':'A bounded reading.', 'author':'Reader','sourceOwner':'Source','interval':'Frozen interval','limits':['No runtime claim'], 'materials':[{'id':'source','title':'Source','kind':'supplied text','content':content,'sha256':digest(content),'sourcePath':'Z:\\absent\\journal.txt'}], 'claims':[{'id':'definition','classification':'supported','materialID':'source','quote':quote,'evidenceIDs':['source'],'explanation':'The supplied line says this.'}], 'sequence':[{'title':'Read source','detail':'Recorded supplied page.','materialIDs':['source'],'status':'observed'},{'title':'Later outcome','detail':'Not checked.','materialIDs':[],'status':'notObserved'}]}]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    subprocess.run(['cargo','build','-p','reservoir-core','--bin','reservoir-core','--locked'],cwd=DESKTOP,check=True)
    rows=[('canonical-reviewed-cases',json.loads((DESKTOP/'src-tauri/resources/research-cases-v1.json').read_bytes()),True),('minimal-inert-path',fixture(),True)]
    for name,content,quote,expected in [
        ('canonical-duplicate','é e\u0301','é',False),('canonical-match','e\u0301','é',True),
        ('accent-not-partial','café','e',False),('nonoverlap','aaa','aa',True),
        ('ligature-not-folded','ﬃ','ffi',False),('width-not-folded','Ａ','A',False),
        ('flag-not-partial','🇦🇺','🇦',False),('emoji-zwj-not-partial','👩‍🔬','👩',False),
        ('emoji-modifier-not-partial','👍🏽','👍',False),('crlf-not-partial','\r\n','\r',False),
        ('combining-mark-not-partial','a\u0301','\u0301',False),('later-valid-match','a\u0301a','a',True),
        ('indic-cluster-not-partial','क्ष','ष',False),('ideographic-quote','記録した言葉。','言葉',True),
    ]: rows.append((name,fixture(content,quote),expected))
    for name,mutate in [
        ('changed-embedded-bytes',lambda c:c['materials'][0].update(content='changed')),
        ('missing-evidence',lambda c:c['claims'][0].update(evidenceIDs=['absent'])),
        ('missing-limits',lambda c:c.update(limits=[])),
        ('unrecognized-classification',lambda c:c['claims'][0].update(classification='improved')),
        ('observed-without-evidence',lambda c:c['sequence'][0].update(materialIDs=[])),
        ('foundation-zero-width-whitespace',lambda c:c.update(author='\u200b')),
        ('duplicate-canonical-material-id',lambda c:c['materials'].extend([dict(c['materials'][0],id='é'),dict(c['materials'][0],id='e\u0301')])),
    ]:
        v=fixture();mutate(v['cases'][0]);rows.append((name,v,False))
    canonical=fixture();canonical['cases'][0]['materials'][0]['id']='é';canonical['cases'][0]['claims'][0].update(materialID='e\u0301',evidenceIDs=['e\u0301']);canonical['cases'][0]['sequence'][0]['materialIDs']=['e\u0301'];rows.append(('canonical-reference',canonical,True))
    with tempfile.TemporaryDirectory(prefix='reservoir-case-conformance-') as td:
        work=Path(td);harness=work/'main.swift'
        harness.write_text('import Foundation\n@main struct Check { static func main() { do { _ = try ResearchCaseCatalog.decode(Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))); print("passed") } catch { print(error.localizedDescription); exit(1) } } }\n')
        subprocess.run(['swiftc','-parse-as-library',str(SOURCE),str(harness),'-o',str(work/'native-case')],check=True)
        checks=[]
        for name,value,expected in rows:
            data=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();p=work/(name+'.json');p.write_bytes(data)
            swift=subprocess.run([str(work/'native-case'),str(p)],capture_output=True,text=True)
            rust=subprocess.run([str(DESKTOP/'target/debug/reservoir-core'),'verify',str(p),'--json'],capture_output=True,text=True)
            result=json.loads(rust.stdout)
            match=(swift.returncode==0)==expected and (rust.returncode==0)==expected
            checks.append({'name':name,'inputSha256':hashlib.sha256(data).hexdigest(),'expectedPass':expected,'swiftExit':swift.returncode,'rustExit':rust.returncode,'matched':match,'rustScope':result['scope']})
        receipt={'schema':'reservoir-scope.case-conformance.v1','executedAtUtc':datetime.now(timezone.utc).isoformat(),'nativeSource':str(SOURCE.relative_to(ROOT)),'nativeSourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'swiftVersion':subprocess.check_output(['swift','--version'],text=True).strip(),'modelsContacted':False,'historicalPathsAccessed':False,'checks':checks,'passed':all(x['matched'] for x in checks),'limits':'This finite corpus is not exhaustive Unicode-version or cross-platform qualification.'}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
        print(json.dumps({'passed':receipt['passed'],'checks':len(checks),'output':str(args.output)}))
        if not receipt['passed']:raise SystemExit(1)
if __name__=='__main__':main()
