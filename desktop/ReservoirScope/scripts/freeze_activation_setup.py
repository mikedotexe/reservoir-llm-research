"""Freeze and stage the preview's exact bootstrap, wheels and local model hashes.

Development/release tool only; never called by the app. Requires packaging, already
present in the qualified activation environment. Downloads bootstrap assets only,
never imports MLX or performs inference. Existing output files must match exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

from packaging.tags import compatible_tags, cpython_tags, mac_platforms
from packaging.utils import parse_wheel_filename

APP = Path(__file__).resolve().parents[1]
PYTHON_TAG = "20260510"
PYTHON_VERSION = "3.12.13"
UV_VERSION = "0.10.8"
PYTHON_NAME = f"cpython-{PYTHON_VERSION}+{PYTHON_TAG}-aarch64-apple-darwin-install_only.tar.gz"
PYTHON_SHA = "5a30271f8d345a5b02b0c9e4e31e0f1e1455a8e4a04fba95cd9762472abc3b17"
UV_NAME = "uv-aarch64-apple-darwin.tar.gz"
UV_SHA = "c3a6fff5b6b4abddff863117878194e35dbc6b0267d61ad259ab9896f9b8dcbb"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        "User-Agent": "ReservoirScope-activation-setup-freeze/1"}), timeout=60)


def write_exact(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Refusing to replace different frozen bytes: {path}")
    if not path.exists():
        path.write_bytes(data)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def download(url, path, expected):
    if not path.exists():
        with request(url) as response:
            data = response.read()
        if sha(data) != expected:
            raise ValueError(f"Bootstrap digest mismatch: {path.name}")
        write_exact(path, data)
    if sha(path.read_bytes()) != expected:
        raise ValueError(f"Existing bootstrap digest mismatch: {path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=APP / "activation_setup_bundle")
    parser.add_argument("--model", type=Path, default=APP / ".activation-models/qwen3-4b")
    args = parser.parse_args()
    root = args.output.resolve()
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    python_url = f"https://github.com/astral-sh/python-build-standalone/releases/download/{PYTHON_TAG}/{PYTHON_NAME.replace('+', '%2B')}"
    uv_url = f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/{UV_NAME}"
    download(python_url, assets / PYTHON_NAME, PYTHON_SHA)
    download(uv_url, assets / UV_NAME, UV_SHA)
    with tarfile.open(assets / UV_NAME) as archive:
        member = archive.getmember("uv-aarch64-apple-darwin/uv")
        uv = archive.extractfile(member).read()
        write_exact(assets / "uv", uv)
        (assets / "uv").chmod(0o755)
        for member in archive.getmembers():
            if member.isfile() and Path(member.name).name.startswith(("LICENSE", "COPYRIGHT")):
                write_exact(root / "licenses" / ("uv-" + Path(member.name).name), archive.extractfile(member).read())
    with tarfile.open(assets / PYTHON_NAME) as archive:
        license_count = 0
        for member in archive.getmembers():
            relative = Path(member.name)
            if member.isfile() and relative.suffix != ".py" and ("licenses" in relative.parts or relative.name.startswith(("LICENSE", "COPYING"))):
                write_exact(root / "licenses" / "python" / relative, archive.extractfile(member).read())
                license_count += 1
        if not license_count:
            raise ValueError("Python archive has no redistributable license material")
    notices = []
    for filename in ("LICENSE-MIT", "LICENSE-APACHE"):
        url = f"https://raw.githubusercontent.com/astral-sh/uv/{UV_VERSION}/{filename}"
        with request(url) as response:
            data = response.read()
        relative = "licenses/uv/" + filename
        write_exact(root / relative, data)
        notices.append({"path": relative, "url": url, "sha256": sha(data)})
    # The installation-only archive omits several linked-library notices from the
    # full distribution. Preserve the release-tagged upstream collection too.
    with request(f"https://api.github.com/repos/astral-sh/python-build-standalone/git/trees/{PYTHON_TAG}?recursive=1") as response:
        tree = json.load(response)["tree"]
    for item in tree:
        if item["type"] == "blob" and item["path"].startswith("LICENSE") and "/" not in item["path"]:
            url = f"https://raw.githubusercontent.com/astral-sh/python-build-standalone/{PYTHON_TAG}/{item['path']}"
            with request(url) as response:
                data = response.read()
            relative = "licenses/python-build-standalone/" + item["path"]
            write_exact(root / relative, data)
            notices.append({"path": relative, "url": url, "sha256": sha(data)})
    write_exact(root / "licenses/SOURCES.json", json_bytes(notices))
    platforms = list(mac_platforms((26, 0), "arm64"))
    tags = list(cpython_tags((3, 12), platforms=platforms)) + list(compatible_tags((3, 12), interpreter="cp312", platforms=platforms))
    rank = {tag: i for i, tag in reversed(list(enumerate(tags)))}
    wheels = []
    for line in (APP / "activation-requirements.lock").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==")
        with request(f"https://pypi.org/pypi/{name}/{version}/json") as response:
            metadata = json.load(response)
        candidates = []
        for item in metadata["urls"]:
            if item["packagetype"] != "bdist_wheel" or item.get("yanked"):
                continue
            _, _, _, wheel_tags = parse_wheel_filename(item["filename"])
            compatible = [rank[tag] for tag in wheel_tags if tag in rank]
            if compatible:
                candidates.append((min(compatible), item["filename"], item))
        if not candidates:
            raise ValueError(f"No compatible wheel for {name}=={version}")
        item = sorted(candidates)[0][2]
        wheels.append({"name": name, "version": version, "filename": item["filename"],
                       "sha256": item["digests"]["sha256"], "bytes": item["size"], "url": item["url"]})
    lock = "# Frozen CPython 3.12 / macOS 26 arm64 wheels; no dependency resolution.\n"
    lock += "".join(f"{w['name']}=={w['version']} --hash=sha256:{w['sha256']}\n" for w in wheels)
    write_exact(root / "activation-wheels.lock", lock.encode())
    write_exact(root / "wheels.json", json_bytes({"schema": "activation-setup-wheels-v1", "wheels": wheels}))
    provenance = json.loads((args.model / "model-provenance.json").read_text())
    files = []
    for item in provenance["files"]:
        path = args.model / item["path"]
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"Existing model differs: {path}")
        files.append({**item, "bytes": path.stat().st_size,
                      "url": f"https://huggingface.co/{provenance['modelId']}/resolve/{provenance['revision']}/{item['path']}"})
    model = {"schema": "activation-setup-model-v1", "modelId": provenance["modelId"],
             "revision": provenance["revision"], "files": files, "provenance": provenance}
    write_exact(root / "model-files.json", json_bytes(model))
    manifest = {"schema": "activation-setup-manifest-v1", "runtimeId": "cpython-3.12.13-20260510-mlx0.32.4-v1",
                "platform": {"system": "Darwin", "architecture": "arm64", "minimumMacOSMajor": 26},
                "python": {"version": PYTHON_VERSION, "archivePath": "assets/" + PYTHON_NAME,
                           "archiveSha256": PYTHON_SHA, "archiveBytes": (assets / PYTHON_NAME).stat().st_size,
                           "executableRelativePath": "python/bin/python3.12", "url": python_url},
                "uv": {"version": UV_VERSION, "path": "assets/uv", "sha256": sha(uv), "bytes": len(uv),
                       "archiveSha256": UV_SHA, "url": uv_url},
                "locks": {key: {"path": filename, "sha256": sha((root / filename).read_bytes())}
                          for key, filename in [("wheels", "activation-wheels.lock"), ("wheelInventory", "wheels.json"), ("model", "model-files.json")]},
                "minimumFreeBytes": 8 * 1024**3}
    write_exact(root / "setup-manifest.json", json_bytes(manifest))
    print(json.dumps({"status": "frozen", "output": str(root), "wheels": len(wheels), "modelFiles": len(files),
                      "manifestSha256": sha(json_bytes(manifest)), "modelBytes": sum(f['bytes'] for f in files)}))


if __name__ == "__main__":
    main()
