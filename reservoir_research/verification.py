"""One offline verification entry point. No models, network requests or live readers.

Executed and explicitly inherited coverage are distinct. Missing platform tools,
inputs, or human acceptance never become a passing automated check.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

GROUPS = ("python", "numerics", "native-model", "native-presentation", "research-replay", "package")
MODEL_SCRIPTS = ("check-actions-ui.sh", "check-essentials-ui.sh", "check-exploration-ui.sh",
                 "check-guided-lessons.sh", "check-evidence.sh", "check-native-action-response.sh",
                 "check-state-response.sh", "check-state-surface-data.sh", "check-source-staging.sh",
                 "check-readiness-and-cases.sh", "check-package-identity.sh", "check-geometry-bookmarks.sh",
                 "check-research-cases-workspace.sh")
CORE_LAYOUTS = ("check-action-comparison-layout.sh", "check-action-inspector-layout.sh",
                "check-essentials-layout.sh", "check-essentials-run-layout.sh", "check-exploration-layout.sh",
                "check-research-case-layout.sh", "check-guided-playback-presentation.sh")
OUT_SCRIPTS = ("check-dynamic-state-surface.sh", "check-shared-state-camera.sh",
               "check-topographic-renderer.sh", "check-watermark-view.sh",
               "check-geometry-bookmarks.sh", "check-geometry-bookmark-presentation.sh",
               "check-research-cases-workspace.sh")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def configure(subparsers):
    parser = subparsers.add_parser("verify", help="Run grouped offline verification; never invokes a model")
    parser.add_argument("--group", choices=GROUPS + ("all-offline",), action="append", default=[])
    parser.add_argument("--out", type=Path, help="New directory for logs and machine-readable receipt")
    parser.add_argument("--app", type=Path, help="Explicit packaged app to verify")
    parser.add_argument("--daily-manifest", type=Path)
    parser.add_argument("--daily-report", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--inherit", type=Path, action="append", default=[],
                        help="Explicit prior verification receipt; only identical input/source coverage may inherit")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds per check (default: 1800)")

def source_identity(root, group, args):
    paths = set()
    if group in ("python", "research-replay"):
        for base in ("reservoir_research", "tests", "probes"):
            paths.update(p for p in (root / base).rglob("*") if p.is_file() and p.suffix in (".py", ".json"))
        paths.add(root / "pyproject.toml")
    elif group in ("numerics", "native-model", "native-presentation"):
        for base in ("essentials", "native/ReservoirScope"):
            paths.update(p for p in (root / base).rglob("*")
                         if p.is_file() and p.suffix in (".swift", ".sh", ".py", ".json")
                         and not any(x in p.parts for x in (".build", "validation", "__pycache__")))
    else:
        paths.add(root / "native/ReservoirScope/package-identity.py")
    if group in ("native-model", "native-presentation"):
        paths.update((root / "research/examples").glob("*.json"))
        manifest_path = root / "native/ReservoirScope/resource-manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_bytes())
            for item in manifest["resources"]:
                relative = Path(item["source"])
                target = (root / relative).resolve()
                if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(root):
                    raise ValueError("Resource identity path escapes the repository")
                if not target.is_file():
                    raise ValueError("Canonical verification resource is missing: " + str(relative))
                paths.add(target)
    value = {str(p.relative_to(root)): digest(p) for p in sorted(paths) if p.exists()}
    value["environment:platform"] = platform.platform()
    value["environment:architecture"] = platform.machine()
    value["environment:python"] = sys.version
    if group in ("numerics", "native-model", "native-presentation", "package") and shutil.which("xcrun"):
        for name, command in (("swift", ["xcrun", "swiftc", "--version"]),
                              ("sdk", ["xcrun", "--show-sdk-version"])):
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
                value["environment:" + name] = result.stdout.strip() if result.returncode == 0 else "unavailable"
            except (OSError, subprocess.TimeoutExpired):
                value["environment:" + name] = "unavailable"
    if group == "research-replay":
        for key, path in (("daily-manifest", args.daily_manifest), ("daily-report", args.daily_report)):
            value["input:" + key] = digest(path) if path and path.is_file() else None
        # Daily load/verify independently hashes every retained input and full lineage.
    if group == "package" and args.app:
        app = args.app.resolve()
        value.update({"app:" + str(p.relative_to(app)): digest(p)
                      for p in sorted(app.rglob("*")) if p.is_file()})
    return value

def inherited_group(group, identity, receipts):
    for path in receipts:
        receipt = json.loads(path.read_bytes())
        if receipt.get("schema") != "reservoir-research-verification-v1":
            continue
        for old in receipt.get("groups", []):
            if old.get("group") == group and old.get("outcome") == "passed" and old.get("source_identity") == identity:
                # Runtime package/research inputs must be checked afresh, including symlinks.
                if group in ("package", "research-replay"):
                    continue
                return dict(group=group, status="inherited", outcome="passed",
                            source_identity=identity, inherited_from_sha256=digest(path),
                            inherited_from=str(path), commands=[])
    return None

def _execute(command, root, env, log, timeout):
    try:
        with log.open("w") as stream:
            completed = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                       timeout=timeout, check=False)
        return dict(command=command, exit_code=completed.returncode, log=log.name,
                    log_sha256=digest(log), outcome="passed" if completed.returncode == 0 else "failed")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(command=command, outcome="incomplete", error=str(exc),
                    log=log.name, log_sha256=digest(log) if log.exists() else None)

def run(args, root=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    for name in ("app", "daily_manifest", "daily_report", "data_root"):
        path = getattr(args, name)
        if path is not None:
            setattr(args, name, path.expanduser().resolve())
    args.inherit = [p.expanduser().resolve() for p in args.inherit]
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")
    groups = list(dict.fromkeys(args.group or ["python"]))
    if "all-offline" in groups:
        groups = list(GROUPS)
    if args.out:
        args.out.mkdir(mode=0o700)
        out = args.out.resolve()
    else:
        out = Path(tempfile.mkdtemp(prefix="reservoir-verification-"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    cache = out / "cache"; cache.mkdir()
    env["XDG_CACHE_HOME"] = str(cache)
    core = out / "core"
    env["ESSENTIALS_BUILD_DIR"] = str(core)
    env["RESERVOIR_SCOPE_IDENTITY_TEST_CORE"] = str(core)
    receipt = dict(schema="reservoir-research-verification-v1",
                   created_at_utc=datetime.now(timezone.utc).isoformat(),
                   platform=platform.platform(), architecture=platform.machine(),
                   python=sys.version, models_contacted=False, live_sources_read=False,
                   groups=[], human_newcomer_acceptance="not_run")
    built_core = False
    for group in groups:
        identity = source_identity(root, group, args)
        result = inherited_group(group, identity, args.inherit)
        if result:
            receipt["groups"].append(result)
            continue
        result = dict(group=group, status="executed", outcome="passed", source_identity=identity, commands=[])
        receipt["groups"].append(result)
        native = root / "native/ReservoirScope"
        commands = []
        if group == "python":
            commands = [[sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]]
        elif group in ("numerics", "native-model", "native-presentation"):
            if platform.system() != "Darwin" or not shutil.which("xcrun") or not shutil.which("swift"):
                result.update(status="incomplete", outcome="incomplete", reason="Requires the macOS Swift toolchain")
                continue
            if group == "numerics":
                commands = [["zsh", str(root / "essentials/check.sh")]]
            else:
                if not built_core:
                    command = ["zsh", str(root / "essentials/build.sh")]
                    item = _execute(command, root, env, out / (group + "-core-build.log"), args.timeout)
                    result["commands"].append(item)
                    if item["outcome"] != "passed":
                        result.update(outcome=item["outcome"], status="incomplete" if item["outcome"] == "incomplete" else "executed")
                        continue
                    built_core = True
                scripts = MODEL_SCRIPTS if group == "native-model" else tuple(
                    p.name for p in sorted(native.glob("check-*.sh")) if p.name not in MODEL_SCRIPTS)
                for script in scripts:
                    command = ["bash", str(native / script)]
                    dest = out / script.removesuffix(".sh")
                    if script == "check-readiness-and-cases.sh":
                        command += [str(core / "lib"), str(dest), str(root / "research/examples/research-cases-v1.json")]
                    elif script == "check-guided-lessons.sh":
                        command += [str(core / "lib"), str(root / "essentials/examples/portable"), str(dest)]
                    elif script in ("check-actions-ui.sh", "check-essentials-ui.sh", "check-exploration-ui.sh"):
                        command += [str(core / "lib")]
                    elif script in CORE_LAYOUTS:
                        command += [str(core / "lib"), str(dest)]
                    elif script in OUT_SCRIPTS:
                        command += [str(dest)]
                    commands.append(command)
        elif group == "research-replay":
            if not args.daily_manifest or not args.daily_report:
                result.update(status="incomplete", outcome="incomplete",
                              reason="Requires --daily-manifest and --daily-report; no live capture is inferred")
                continue
            command = [sys.executable, "-B", "-m", "reservoir_research", "study", "daily", "verify",
                       str(args.daily_manifest), "--report", str(args.daily_report)]
            if args.data_root:
                command += ["--data-root", str(args.data_root)]
            commands = [command]
        elif group == "package":
            if not args.app:
                result.update(status="incomplete", outcome="incomplete", reason="Requires --app")
                continue
            if platform.system() != "Darwin" or not shutil.which("codesign"):
                result.update(status="incomplete", outcome="incomplete", reason="Requires macOS signing tools")
                continue
            commands = [[sys.executable, "-B", str(native / "package-identity.py"), "verify", "--app", str(args.app)]]
        for index, command in enumerate(commands):
            item = _execute(command, root, env, out / f"{group}-{index + 1}.log", args.timeout)
            result["commands"].append(item)
            if item["outcome"] != "passed":
                result["outcome"] = item["outcome"]
                if item["outcome"] == "incomplete":
                    result["status"] = "incomplete"
        if source_identity(root, group, args) != identity:
            result.update(outcome="incomplete", status="incomplete", reason="Inputs changed while checks were running")
    receipt["outcome"] = ("failed" if any(g["outcome"] == "failed" for g in receipt["groups"])
                          else "incomplete" if any(g["outcome"] == "incomplete" for g in receipt["groups"]) else "passed")
    path = out / "verification.json"
    with path.open("x") as stream:
        json.dump(receipt, stream, indent=2); stream.write("\n")
    return dict(receipt, receipt_path=str(path)), (0 if receipt["outcome"] == "passed" else 2)
