"""CLI adapters for offline daily evidence; no database or source discovery."""
import json
from pathlib import Path
from . import load_packet, make_manifest, build_report, verify_report
from .inputs import DailyError, require, write_new_json
from reservoir_research.study_capture import encoded, sha

def configure(subparsers):
    study = subparsers.add_parser("study", help="Offline studies from retained research evidence")
    study_sub = study.add_subparsers(dest="study_command", required=True)
    daily = study_sub.add_parser("daily", help="Build or verify a manifest-bound S-007 daily packet")
    daily_sub = daily.add_subparsers(dest="daily_command", required=True)
    manifest = daily_sub.add_parser("manifest", help="Declare retained inputs and their current hashes")
    manifest.add_argument("packet", type=Path)
    manifest.add_argument("--data-root", type=Path, required=True)
    manifest.add_argument("--history", type=Path, action="append", required=True)
    manifest.add_argument("--eras", type=Path, default=Path(__file__).with_name("era-definitions-v1.json"))
    manifest.add_argument("--out", type=Path, required=True, help="New manifest file; never overwritten")
    for name in ("build", "verify"):
        command = daily_sub.add_parser(name)
        command.add_argument("manifest", type=Path)
        command.add_argument("--data-root", type=Path, help="Root containing the declared relative paths")
        command.add_argument("--out", type=Path, required=name == "build", help="New output directory; never overwritten")
        if name == "verify":
            command.add_argument("--report", type=Path, required=True)
            command.add_argument("--annotations", type=Path, help="Must equal the manifest-declared annotations")

def run(args):
    if args.daily_command == "manifest":
        value = make_manifest(args.packet, args.data_root, args.history, json.loads(args.eras.read_bytes()))
        # Validate before writing; the data root is explicit, never a captured source path.
        require(not args.out.exists(), "Manifest output already exists")
        write_new_json(args.out, value)
        return {"status": "declared", "manifest": str(args.out), "sha256": sha(args.out.read_bytes()),
                "note": "Input declaration is not evidence verification."}
    packet = load_packet(args.manifest, args.data_root)
    if args.daily_command == "build":
        report = build_report(packet)
        files = {"report.json": encoded(report)}
        for row in report["studies"]:
            if row["id"] in report["close_reading_ids"]:
                require(Path(row["id"]).name == row["id"] and row["id"] not in (".", ".."),
                        "Unsafe generation identity")
                files[row["id"] + ".md"] = ("# " + row["id"] + "\n\n" + row["completed"]
                    + "\n\n## Supplied user input\n\n" + row["user_text"]
                    + "\n\n## Authored response\n\n" + row["text"] + "\n").encode()
        args.out.mkdir(mode=0o700)
        for name, raw in files.items():
            with (args.out / name).open("xb") as stream:
                stream.write(raw)
            (args.out / name).chmod(0o600)
        return {"status": "built", "report": str(args.out / "report.json"),
                "report_sha256": sha(files["report.json"]), "generation_count": report["generation_count"],
                "close_reading_ids": report["close_reading_ids"], "manifest_sha256": packet.manifest_sha256}
    result = verify_report(packet, args.report, args.annotations)
    if args.out:
        args.out.mkdir(mode=0o700)
        for name, value in (("verification.json", result["verification"]),
                            ("verified-claim-checks.json", result["verified_claims"]),
                            ("pipeline-verification.json", result["pipeline"])):
            write_new_json(args.out / name, value)
    return {"status": "verified", **result}
