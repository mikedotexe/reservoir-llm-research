#!/usr/bin/env bash
# Production staging against temporary repository fixtures only; no install.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
python3 - "$task_native_dir" <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
native=Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="reservoir-source-staging-") as folder:
    root=Path(folder); source=root/"repo"; staged=root/"staged"
    n=source/"native/ReservoirScope"; e=source/"essentials"
    (n/"Sources/ReservoirScope").mkdir(parents=True)
    (n/"Tests").mkdir()
    geometry=n/"Tests/Fixtures/geometry-bookmarks"
    geometry.mkdir(parents=True)
    for name, content in (("sample.json", "{}\n"), ("generate.py", "# fixture generator\n"), ("README.md", "Fixture description\n")):
        (geometry/name).write_text(content)
    (e/"reservoir").mkdir(parents=True)
    (source/"fixtures").mkdir()
    (n/"Package.swift").write_text("// native package fixture\n")
    (e/"Package.swift").write_text("// core package fixture\n")
    (e/"build.sh").write_text("# core build fixture\n")
    (e/"reservoir/Current.swift").write_text("// current core\n")
    (n/"Sources/ReservoirScope/Current.swift").write_text("// current native\n")
    shutil.copy2(native/"stage-package.py",n/"stage-package.py")
    resource=source/"fixtures/example.json";resource.write_text('{"fixture":1}\n')
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    def manifest():
        (n/"resource-manifest.json").write_text(json.dumps({"schema":"reservoir-scope.resources.v1",
            "release":{"version":"test","build":1},"resources":[
                {"name":"example.json","source":"fixtures/example.json","sha256":sha(resource)}]}))
    manifest()
    subprocess.run(["git","init","-q",str(source)],check=True)
    subprocess.run(["git","-C",str(source),"add","."],check=True)
    subprocess.run(["git","-C",str(source),"-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","-qm","Frozen fixture"],check=True)
    staged.mkdir(); (staged/"unrelated-output").write_text("preserve\n")
    def run(operation,ok=True):
        command=["python3",str(native/"stage-package.py"),operation,"--destination",str(staged)]
        if operation=="stage":command+=["--repo",str(source)]
        result=subprocess.run(command,capture_output=True,text=True)
        assert (result.returncode==0)==ok,result.stdout+result.stderr
    run("stage")
    target=staged/"native/ReservoirScope"
    assert (target/"Package.swift").read_bytes()==(n/"Package.swift").read_bytes()
    assert (staged/"essentials/Package.swift").exists()
    assert (target/"../../essentials/Package.swift").resolve()==(staged/"essentials/Package.swift").resolve()
    assert (target/"Sources/ReservoirScope/Resources/example.json").read_bytes()==resource.read_bytes()
    assert (staged/"unrelated-output").read_text()=="preserve\n"
    run("verify-stage")
    for path in geometry.iterdir():
        assert (target/"Tests/Fixtures/geometry-bookmarks"/path.name).read_bytes()==path.read_bytes()
    (target/"Tests/Fixtures/geometry-bookmarks/sample.json").write_text('{"changed":true}\n')
    run("verify-stage",False)
    run("stage")
    (target/"Sources/ReservoirScope/Current.swift").write_text("// changed\n")
    run("verify-stage",False)
    run("stage")
    (target/"Sources/ReservoirScope/Extra.swift").write_text("// undeclared\n")
    run("verify-stage",False)
    run("stage")
    (target/"Sources/ReservoirScope/Resources/example.json").unlink()
    run("verify-stage",False)
    run("stage")
    (target/"Sources/ReservoirScope/Resources/extra.json").write_text("{}")
    run("verify-stage",False)
    run("stage")
    resource.write_text('{"fixture":2}\n')
    run("stage",False)
    manifest();run("stage")
    (n/"Sources/ReservoirScope/Current.swift").unlink()
    (n/"Sources/ReservoirScope/Replacement.swift").write_text("// replacement\n")
    run("stage")
    assert not (target/"Sources/ReservoirScope/Current.swift").exists()
    assert not (target/"Sources/ReservoirScope/Extra.swift").exists()
    before=(staged/"staged-inputs.json").read_bytes()
    run("stage")
    assert before==(staged/"staged-inputs.json").read_bytes()
    print("16 source-staging checks passed: coherent dependency paths, resource identity, drift rejection, pruning, repeatability and retained geometry fixture identity.")
PY
