"""Standard-library client; no model calls, proxy use, or direct run-store writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ClientError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError("The local API attempted a redirect")


def read_descriptor(path: Path) -> dict:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ClientError("Discovery file must be an ordinary file")
    if os.name == "posix" and (info.st_uid != os.getuid() or info.st_mode & 0o077):
        raise ClientError("Discovery credentials must be readable only by their owner")
    if info.st_size > 16384:
        raise ClientError("Discovery file is too large")
    data = json.loads(path.read_text())
    url = urllib.parse.urlsplit(data.get("url", ""))
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port
            or url.username or url.password or url.query or url.fragment or url.path):
        raise ClientError("Discovery must identify a literal loopback HTTP endpoint")
    if data.get("version") != 1 or not isinstance(data.get("token"), str) or len(data["token"]) != 64:
        raise ClientError("Invalid discovery contract")
    data["discoveryFile"] = str(path)
    return data


def discover(explicit: str | None = None) -> list[dict]:
    explicit = explicit or os.environ.get("RESERVOIR_SCOPE_ENDPOINT_FILE")
    if explicit:
        return [read_descriptor(Path(explicit))]
    if sys.platform == "darwin":
        parent = Path.home() / "Library/Application Support"
    elif os.name == "nt":
        parent = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        parent = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    found = []
    if parent.exists():
        for app in parent.iterdir():
            if not (app.name == "research.reservoir.scope" or app.name.startswith("research.reservoir.scope.")):
                continue
            path = app / "automation-v1/endpoint.json"
            try:
                descriptor = read_descriptor(path)
                os.kill(int(descriptor["pid"]), 0)
                found.append(descriptor)
            except (OSError, ValueError, KeyError, ClientError):
                continue
    return found


class Client:
    def __init__(self, descriptor: dict):
        self.descriptor = descriptor
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method: str, path: str, body=None, key=None, raw=False):
        if not path.startswith("/v1/") or path.startswith("//"):
            raise ClientError("API paths must start with /v1/")
        headers = {"Authorization": "Bearer " + self.descriptor["token"], "Accept": "application/json"}
        data = None
        if method != "GET":
            headers["Idempotency-Key"] = key or str(uuid.uuid4())
            headers["Content-Type"] = "application/json"
            data = json.dumps(body if body is not None else {}, allow_nan=False).encode()
        req = urllib.request.Request(self.descriptor["url"] + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=60) as response:
                payload = response.read(64 * 1024 * 1024 + 1)
                if len(payload) > 64 * 1024 * 1024:
                    raise ClientError("API response exceeded the client bound")
                return payload if raw else json.loads(payload)
        except urllib.error.HTTPError as e:
            try:
                error = json.loads(e.read(16384))["error"]
                raise ClientError(f"{error['code']}: {error['message']}") from None
            except (ValueError, KeyError):
                raise ClientError(f"Local API returned HTTP {e.code}") from None
        except urllib.error.URLError as e:
            raise ClientError(f"Local API unavailable: {e.reason}") from None

    def wait(self, operation: str, timeout: float = 660):
        deadline = time.monotonic() + timeout
        while True:
            result = self.request("GET", "/v1/operations/" + quote(operation))
            if result["status"] not in ("queued", "running", "scheduled"):
                return result
            if time.monotonic() >= deadline:
                raise ClientError(f"Still pending: {operation}. Continue with reservoirctl wait {operation}.")
            time.sleep(0.2)

    def export(self, run: str, output: Path, key: str | None):
        if output.exists():
            raise ClientError("Export destination must be a new directory")
        op = self.request("POST", f"/v1/runs/{quote(run)}/exports", key=key)
        op = self.wait(op["id"])
        if op["status"] != "completed":
            return op
        export_id = op["result"]["exportId"]
        base = f"/v1/exports/{quote(export_id)}"
        index = self.request("GET", base + "/files")
        output.mkdir(parents=True, exist_ok=False)
        try:
            for item in index["files"]:
                relative = PurePosixPath(item["path"])
                if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
                    raise ClientError("Export contains an unsafe relative path")
                data = self.request("GET", base + "/content?" + urllib.parse.urlencode({"path": str(relative)}), raw=True)
                if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ClientError("Export bytes differ from the verified snapshot")
                target = output.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(data)
        except Exception:
            # Keep incomplete evidence, clearly marked, instead of claiming success.
            (output / "INCOMPLETE.txt").write_text("Download failed; this directory is not a complete verified export.\n")
            raise
        return {"status": "completed", "directory": str(output.resolve()), "report": op["result"]["report"]}


def quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def load_json(path: str):
    return json.load(sys.stdin) if path == "-" else json.loads(Path(path).read_text())


def parser():
    p = argparse.ArgumentParser(prog="reservoirctl", description=__doc__)
    p.add_argument("--endpoint-file")
    p.add_argument("--instance", help="Explicit instance ID or application ID")
    p.add_argument("--key", help="Reusable idempotency key for a mutation")
    p.add_argument("--wait", action="store_true", help="Wait for a mutation's durable result")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    sub.add_parser("capabilities")
    sub.add_parser("schema")
    sub.add_parser("openapi")
    validate = sub.add_parser("validate", help="Check a config, recipe, or action text without execution")
    validate.add_argument("kind", choices=["configuration", "recipe", "action"]); validate.add_argument("file"); validate.add_argument("--run")
    interventions = sub.add_parser("interventions").add_subparsers(dest="action", required=True)
    listing = interventions.add_parser("list"); listing.add_argument("run")
    schedule = interventions.add_parser("schedule"); schedule.add_argument("run"); schedule.add_argument("file")
    cancel = interventions.add_parser("cancel"); cancel.add_argument("operation")
    req = sub.add_parser("request"); req.add_argument("method", choices=["GET", "POST", "PATCH"]); req.add_argument("path"); req.add_argument("--json")
    wait = sub.add_parser("wait"); wait.add_argument("operation"); wait.add_argument("--timeout", type=float, default=660)
    watch = sub.add_parser("watch"); watch.add_argument("--interval", type=float, default=2); watch.add_argument("--count", type=int, default=0)
    runs = sub.add_parser("runs").add_subparsers(dest="action", required=True)
    runs.add_parser("list")
    get = runs.add_parser("get"); get.add_argument("run")
    create = runs.add_parser("create"); create.add_argument("file")
    clone = runs.add_parser("clone"); clone.add_argument("run"); clone.add_argument("--overrides")
    for action in ["start", "pause", "resume", "stop", "retry-save", "retry-writing", "retry-encoding", "skip-feedback", "extend-limits"]:
        command = runs.add_parser(action); command.add_argument("run"); command.add_argument("--json")
    entries = sub.add_parser("entries").add_subparsers(dest="action", required=True)
    page = entries.add_parser("list"); page.add_argument("run"); page.add_argument("--limit", type=int, default=25); page.add_argument("--cursor"); page.add_argument("--all", action="store_true")
    entry = entries.add_parser("get"); entry.add_argument("run"); entry.add_argument("entry")
    settings = sub.add_parser("settings").add_subparsers(dest="action", required=True)
    get = settings.add_parser("get"); get.add_argument("run", nargs="?")
    edit = settings.add_parser("set"); edit.add_argument("run"); edit.add_argument("file"); edit.add_argument("--expected-revision", type=int)
    concurrency = settings.add_parser("concurrency"); concurrency.add_argument("maximum", type=int)
    for noun in ["recipes", "experiments"]:
        commands = sub.add_parser(noun).add_subparsers(dest="action", required=True)
        commands.add_parser("list")
        get = commands.add_parser("get"); get.add_argument("id")
        create = commands.add_parser("save" if noun == "recipes" else "prepare"); create.add_argument("file")
        if noun == "experiments":
            for action in ["start", "pause", "resume", "stop"]:
                c = commands.add_parser(action); c.add_argument("id")
    export = sub.add_parser("export"); export.add_argument("run"); export.add_argument("--output", required=True)
    return p


def execute(client: Client, a):
    command = a.command
    get = lambda path: client.request("GET", path)
    mutate = lambda method, path, body=None: client.request(method, path, body, a.key)
    if command == "validate":
        body = {"kind": a.kind}
        if a.run: body["runId"] = a.run
        body[{"configuration": "config", "recipe": "recipe", "action": "text"}[a.kind]] = (sys.stdin.read() if a.file == "-" else Path(a.file).read_text()) if a.kind == "action" else load_json(a.file)
        return client.request("POST", "/v1/validate", body)
    if command == "openapi": return get("/v1/openapi.json")
    if command == "interventions":
        if a.action == "cancel": return mutate("POST", f"/v1/operations/{quote(a.operation)}/cancel", {})
        path = f"/v1/runs/{quote(a.run)}/interventions"
        if a.action == "list": return get(path)
        return mutate("POST", path, load_json(a.file))
    if command in ("capabilities", "schema"):
        return get("/v1/" + command)
    if command == "request":
        return client.request(a.method, a.path, load_json(a.json) if a.json else None, a.key)
    if command == "wait":
        return client.wait(a.operation, a.timeout)
    if command == "export":
        return client.export(a.run, Path(a.output), a.key)
    if command == "runs":
        if a.action == "list": return get("/v1/runs")
        if a.action == "create": return mutate("POST", "/v1/runs", {"config": load_json(a.file)})
        path = "/v1/runs/" + quote(a.run)
        if a.action == "get": return get(path)
        if a.action == "clone": return mutate("POST", path + "/clone", {"overrides": load_json(a.overrides) if a.overrides else {}})
        return mutate("POST", path + "/actions/" + a.action, load_json(a.json) if a.json else {})
    if command == "entries":
        path = f"/v1/runs/{quote(a.run)}/entries"
        if a.action == "get": return get(path + "/" + quote(a.entry))
        query = {"limit": a.limit}
        if a.cursor: query["cursor"] = a.cursor
        page = get(path + "?" + urllib.parse.urlencode(query))
        if not a.all: return page
        entries = list(page["entries"])
        while page["nextCursor"]:
            query["cursor"] = page["nextCursor"]
            page = get(path + "?" + urllib.parse.urlencode(query)); entries.extend(page["entries"])
        return {"snapshot": page["snapshot"], "entries": entries, "total": len(entries)}
    if command == "settings":
        if a.action == "concurrency": return mutate("PATCH", "/v1/settings", {"maxConcurrentRequests": a.maximum})
        path = f"/v1/runs/{quote(a.run)}/settings" if a.run else "/v1/settings"
        if a.action == "get": return get(path)
        revision = a.expected_revision if a.expected_revision is not None else get(path)["configurationRevision"]
        return mutate("PATCH", path, {"expectedConfigurationRevision": revision, "patch": load_json(a.file)})
    if command in ("recipes", "experiments"):
        path = "/v1/" + command
        if a.action == "list": return get(path)
        if a.action in ("save", "prepare"): return mutate("POST", path, load_json(a.file))
        path += "/" + quote(a.id)
        if a.action == "get": return get(path)
        return mutate("POST", path + "/actions/" + a.action)
    raise ClientError("Unsupported command")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        candidates = discover(args.endpoint_file)
        if args.command == "discover":
            print(json.dumps([{k: v for k, v in c.items() if k != "token"} for c in candidates], indent=2)); return 0
        if args.instance:
            candidates = [c for c in candidates if args.instance in (c["instanceId"], c["applicationId"])]
        if len(candidates) != 1:
            raise ClientError("Select one running app with --instance or --endpoint-file; use reservoirctl discover to list them")
        client = Client(candidates[0])
        if args.command == "watch":
            if args.interval < 0.1: raise ClientError("Watch interval must be at least 0.1 seconds")
            count = 0
            while not args.count or count < args.count:
                print(json.dumps(client.request("GET", "/v1/runs")), flush=True); count += 1; time.sleep(args.interval)
            return 0
        result = execute(client, args)
        if args.wait and isinstance(result, dict) and result.get("status") in ("queued", "running", "scheduled"):
            result = client.wait(result["id"])
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 1 if isinstance(result, dict) and (result.get("status") in ("failed", "needsAttention", "cancelled") or result.get("valid") is False) else 0
    except KeyboardInterrupt:
        return 130
    except (ClientError, OSError, ValueError, KeyError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr); return 1
