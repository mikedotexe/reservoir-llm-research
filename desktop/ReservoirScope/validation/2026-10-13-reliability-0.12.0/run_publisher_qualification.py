#!/usr/bin/env python3
"""Source-only desktop qualification; never invokes a release/package build."""
import datetime, hashlib, json, os, pathlib, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
LABEL = sys.argv[1]
ENV = {
    "DEVELOPER_DIR": "/Applications/Xcode.app/Contents/Developer",
    "SDKROOT": "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk",
}
SOURCES = ["src-tauri/src/sustained.rs", "src-tauri/src/sustained_tests.rs", "src-tauri/Cargo.toml", "Cargo.toml", "Cargo.lock"]
def identity(p):
    b=p.read_bytes()
    return {"path":str(p),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def snapshot():return [identity(ROOT/p) for p in SOURCES]
package=ROOT/"target/release/bundle/macos/ReservoirScope Tauri Preview.app/Contents/MacOS/reservoir-scope-desktop"
if not package.exists():
    candidates=list((ROOT/"target/release/bundle/macos").glob("*.app/Contents/MacOS/reservoir-scope-desktop"))
    assert len(candidates)==1,candidates
    package=candidates[0]
receipt={"scope":"Source-only pending publisher repair; historical packaged 0.12 app is not rebuilt or qualified by these tests.","startedAtUtc":stamp(),"environment":ENV,"cwd":str(ROOT),"sourcesBefore":snapshot(),"packageBefore":identity(package),"commands":[]}
receipt_path=OUT/(LABEL+"-qualification.json")
assert not receipt_path.exists()
try:
    for suffix,cmd in [("desktop-tests",["cargo","test","--locked","-p","reservoir-scope-desktop"]),("desktop-clippy",["cargo","clippy","--locked","-p","reservoir-scope-desktop","--all-targets","--","-D","warnings"])]:
        path=OUT/(LABEL+"-"+suffix+".log")
        start=stamp();t=time.monotonic()
        with path.open("x") as log:
            log.write(json.dumps({"startedAtUtc":start,"command":cmd,"environment":ENV,"cwd":str(ROOT)})+"\n");log.flush()
            result=subprocess.run(cmd,cwd=ROOT,env=os.environ|ENV,stdout=log,stderr=subprocess.STDOUT)
        receipt["commands"].append({"command":cmd,"startedAtUtc":start,"finishedAtUtc":stamp(),"elapsedSeconds":time.monotonic()-t,"exitCode":result.returncode,"log":identity(path)})
        print(suffix,result.returncode,flush=True)
        if result.returncode: break
finally:
    receipt["sourcesAfter"]=snapshot();receipt["packageAfter"]=identity(package)
    receipt["sourceUnchangedDuringChecks"]=receipt["sourcesBefore"]==receipt["sourcesAfter"]
    receipt["packageUnchangedDuringChecks"]=receipt["packageBefore"]==receipt["packageAfter"]
    receipt["finishedAtUtc"]=stamp()
    receipt["passed"]=len(receipt["commands"])==2 and all(c["exitCode"]==0 for c in receipt["commands"]) and receipt["sourceUnchangedDuringChecks"] and receipt["packageUnchangedDuringChecks"]
    with receipt_path.open("x") as f:json.dump(receipt,f,indent=2);f.write("\n")
sys.exit(0 if receipt["passed"] else 1)
