#!/usr/bin/env python3
"""Synthetic signed bundle qualification of v2 package identity; no app launch."""
from pathlib import Path
import hashlib, json, os, plistlib, shutil, subprocess, sys, tempfile
native=Path(__file__).resolve().parents[1]
repo=native.parents[1]
cache=Path(os.environ.get("RESERVOIR_SCOPE_IDENTITY_TEST_CORE",str(Path.home()/".cache/reservoir-research/ReservoirScope-build/essentials")))
if not (cache/"lib/libEssentialsCore.a").exists():
    raise SystemExit("Pass a qualified core cache with RESERVOIR_SCOPE_IDENTITY_TEST_CORE.")
with tempfile.TemporaryDirectory(prefix="reservoir-package-identity-") as folder:
    root=Path(folder);stage=root/"staged-repo"
    def command(args,success=True):
        result=subprocess.run(list(map(str,args)),capture_output=True,text=True)
        if (result.returncode==0)!=success:raise AssertionError(result.stdout+result.stderr)
        return result
    command(["python3",native/"stage-package.py","stage","--repo",repo,"--destination",stage])
    app=root/"Synthetic identity fixture.app"
    (app/"Contents/MacOS").mkdir(parents=True)
    shutil.copytree(stage/"native/ReservoirScope/Sources/ReservoirScope/Resources",app/"Contents/Resources")
    # These never execute. Their signatures exercise packaging, not application behavior.
    shutil.copyfile("/usr/bin/true",app/"Contents/MacOS/ReservoirScope")
    (app/"Contents/MacOS/ReservoirScope").chmod(0o755)
    shutil.copyfile("/usr/bin/true",app/"Contents/MacOS/essentials-run")
    (app/"Contents/MacOS/essentials-run").chmod(0o755)
    (app/"Contents/Info.plist").write_bytes(plistlib.dumps({
        "CFBundleName":"Synthetic identity fixture","CFBundleIdentifier":"research.reservoir.identity.fixture",
        "CFBundleExecutable":"ReservoirScope","CFBundlePackageType":"APPL",
        "CFBundleShortVersionString":"0.14.0","CFBundleVersion":"19"}))
    command(["codesign","--force","--sign","-",app/"Contents/MacOS/essentials-run"])
    create=["python3",native/"package-identity.py","create","--app",app,"--repo",repo,"--stage",stage,"--core-cache",cache]
    create += ["--expected-staged-sha256", hashlib.sha256((stage/"staged-inputs.json").read_bytes()).hexdigest(),
               "--expected-core-sha256", hashlib.sha256((cache/"lib/libEssentialsCore.a").read_bytes()).hexdigest()]
    command(create)
    altered = create.copy(); altered[-1] = "0" * 64; command(altered,False)
    altered = create.copy(); altered[-3] = "0" * 64; command(altered,False)
    command(["codesign","--force","--sign","-",app])
    verify=["python3",native/"package-identity.py","verify","--app",app]
    command(verify)
    command(verify+["--stage",stage])
    resource=app/"Contents/Resources/research-cases-v1.json"
    original=resource.read_bytes()
    resource.write_bytes(original+b" ")
    command(verify,False)
    resource.write_bytes(original)
    held=root/"held-resource";resource.rename(held)
    command(verify,False)
    held.rename(resource)
    extra=app/"Contents/Resources/unlisted.json";extra.write_text("{}")
    command(verify,False);extra.unlink()
    runner=app/"Contents/MacOS/essentials-run";original_runner=runner.read_bytes()
    runner.write_bytes(original_runner+b"changed")
    command(verify,False);runner.write_bytes(original_runner)
    staged_source=stage/"native/ReservoirScope/Sources/ReservoirScope/ResearchCase.swift"
    original_source=staged_source.read_bytes()
    staged_source.write_bytes(original_source+b"\n// drift")
    command(verify+["--stage",stage],False);command(create,False)
    staged_source.write_bytes(original_source)
    extra_source=stage/"native/ReservoirScope/Sources/ReservoirScope/Unexpected.swift"
    extra_source.write_text("// drift\n")
    command(verify+["--stage",stage],False);extra_source.unlink()
    command(verify+["--stage",stage])
    canonical=root/"canonical"
    for relative in json.loads((stage/"staged-inputs.json").read_text())["files"]:
        target=canonical/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(stage/relative,target)
    (canonical/"native/ReservoirScope/Sources/ReservoirScope/Unexpected.swift").write_text("// new source after staging\n")
    canonical_create=create.copy();canonical_create[canonical_create.index("--repo")+1]=canonical
    command(canonical_create,False)
    print("13 package-identity checks passed: copied verification, selected-stage verification, resource omission/addition/content, runner and staged-input drift. Synthetic signed fixture; no application or model launched.")
