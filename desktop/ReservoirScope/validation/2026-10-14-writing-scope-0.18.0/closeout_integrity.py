"""Bind closeout documentation to the already built/tested runtime and retained evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, subprocess, sys
DESKTOP=Path(__file__).resolve().parents[2]
ROOT=DESKTOP.parents[1]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(DESKTOP/'scripts'))
from qualification_receipt import source_inventory, package_inventory
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((OUT/'source-before-build-01.json').read_text())['sourceBefore']
old={e['path']:e for e in base}; new={e['path']:e for e in source_inventory()}
changed=[{'path':p,'before':old.get(p),'after':new.get(p)} for p in sorted(old.keys()|new.keys()) if old.get(p)!=new.get(p)]
assert [e['path'] for e in changed]==['shared/reservoir-scope/PARITY.md'],changed
pkg=json.loads((OUT/'archive-check-01.json').read_text())
assert package_inventory(Path(pkg['app']))==pkg['package']
assert sha(Path(pkg['archive']))==pkg['archiveSha256']
assert sha(Path(pkg['pinnedExecutable']))==pkg['executableSha256']
for e in json.loads((OUT/'prior-package-preserved-01.json').read_text())['files']:
    assert sha(Path(e['path']))==e['sha256']
freeze=json.loads((OUT/'prospective-freeze-01.json').read_text())
for e in freeze['files']: assert sha(OUT/e['path'])==e['sha256'],e['path']
source='desktop/ReservoirScope/crates/reservoir-core/src/sustained.rs'
previous=subprocess.check_output(['git','show','HEAD:'+source],cwd=ROOT).decode()
current=(ROOT/source).read_text()
prompts=[]
for i in range(1,6):
    pattern=rf'^fn prompt_v{i}\b.*?^}}'
    a=re.search(pattern,previous,re.M|re.S).group(); b=re.search(pattern,current,re.M|re.S).group()
    assert a==b
    prompts.append({'version':f'v{i}','unchanged':True,'sha256':hashlib.sha256(b.encode()).hexdigest()})
fixtures=[]
for f in subprocess.check_output(['git','ls-files','desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts'],cwd=ROOT).decode().splitlines():
    oldbytes=subprocess.check_output(['git','show','HEAD:'+f],cwd=ROOT)
    assert (ROOT/f).read_bytes()==oldbytes
    fixtures.append({'path':f,'sha256':sha(ROOT/f)})
checks=['rust-checks-01.json','rust-checks-02.json','frontend-checks-01.json','frontend-comment-addendum-01.json','synthetic-harness-tests-01.json','package-build-01.json','archive-check-01.json','historical-replay-01.json','original-export-evidence-01.json','recovered-export-evidence-01.json','recovery-comparison-01.json','fixture-retention-01.json']
receipt={'schema':'reservoir-v6-closeout-integrity-v1','capturedAtUtc':datetime.now(timezone.utc).isoformat(),'status':'passed','sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'qualificationUsesWorkingSource':True,'sourceInventoryDocumentationChanges':changed,'runtimeAndTestInputsUnchangedSinceBuild':True,'packageInventoryUnchanged':True,'archiveAndPinnedExecutableUnchanged':True,'prior017ArchiveAndExecutablePreserved':True,'frozenProspectiveFilesUnchanged':True,'historicalPromptBodies':prompts,'historicalPromptFixtures':fixtures,'evidence':[{'path':n,'sha256':sha(OUT/n)} for n in checks],'roadmapSha256':sha(ROOT/'TAURI-ROADMAP.md'),'limits':'No commit, push, real-model episode, remote CI, Windows/Linux package, GPU/energy or additional duration qualification is performed by this check.'}
with (OUT/'closeout-integrity-01.json').open('x') as out: json.dump(receipt,out,indent=2);out.write('\n')
print(json.dumps({'status':receipt['status'],'sourceChanges':[x['path'] for x in changed],'historicalPromptVersions':len(prompts),'historicalFixtureFiles':len(fixtures),'packageFiles':len(pkg['package']['files'])}))
