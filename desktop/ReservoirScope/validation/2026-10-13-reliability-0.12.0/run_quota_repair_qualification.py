from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime
root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent
label="quota-repair-final-01"
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def identity(path):
 b=path.read_bytes();return {"path":str(path.relative_to(root)),"sizeBytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
paths=[root/p for p in ["src-tauri/src/sustained.rs","src-tauri/src/sustained_store.rs","src-tauri/src/sustained_tests.rs","src-tauri/src/sustained_quota_tests.rs","crates/reservoir-core/src/sustained.rs"]]
binary=root/"target/release/bundle/macos/Reservoir Scope Tauri Preview.app/Contents/MacOS/reservoir-scope-desktop"
if not binary.exists():
 matches=list((root/"target/release/bundle/macos").glob("*.app/Contents/MacOS/reservoir-scope-desktop"));assert len(matches)==1;binary=matches[0]
env=dict(os.environ,DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer",SDKROOT="/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk")
evidence=root/"target/qa/0.12-natural-quota-repaired-01";evidence.mkdir()
env["RESERVOIR_QUOTA_EVIDENCE"]=str(evidence)
receipt={"startedAtUtc":now(),"scope":"Source-only isolated tests; no app/provider actions or package rebuild. Concurrent frozen-binary soak cannot be used as idle-energy comparison during this interval.","sourcesBefore":[identity(p) for p in paths],"frozenPackageBefore":identity(binary),"commands":[]}
with (out/(label+"-started.json")).open("x") as f:json.dump(receipt,f,indent=2)
commands=[("natural",["cargo","test","--locked","-p","reservoir-scope-desktop","natural_quota_repaired_","--","--ignored","--nocapture","--test-threads=1"]),("desktop-tests",["cargo","test","--locked","-p","reservoir-scope-desktop","--all-targets"]),("clippy",["cargo","clippy","--locked","--workspace","--all-targets","--","-D","warnings"])]
for name,args in commands:
 entry={"name":name,"command":args,"startedAtUtc":now()}
 with (out/(label+"-"+name+".log")).open("x") as log:
  process=subprocess.run(args,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 entry.update(endedAtUtc=now(),exitCode=process.returncode)
 receipt["commands"].append(entry)
 print(json.dumps(entry),flush=True)
 if process.returncode:break
receipt.update(endedAtUtc=now(),sourcesAfter=[identity(p) for p in paths],frozenPackageAfter=identity(binary))
receipt["sourceUnchanged"]=receipt["sourcesBefore"]==receipt["sourcesAfter"]
receipt["frozenPackageUnchanged"]=receipt["frozenPackageBefore"]==receipt["frozenPackageAfter"]
with (out/(label+"-qualification.json")).open("x") as f:json.dump(receipt,f,indent=2)
assert receipt["sourceUnchanged"] and receipt["frozenPackageUnchanged"]
sys.exit(max(c["exitCode"] for c in receipt["commands"]))
