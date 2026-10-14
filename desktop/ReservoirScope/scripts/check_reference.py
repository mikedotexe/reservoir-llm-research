#!/usr/bin/env python3
"""Check native source/resource and derived fixture hashes without regenerating them."""
import argparse
import json
from pathlib import Path
from reference_support import ROOT, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        manifest = verify(args.repo)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Reference check failed: {error}\n")
    print(json.dumps({"status": "verified", "baselineCommit": manifest["baseline"]["commit"],
                      "sources": len(manifest["sources"]), "resources": len(manifest["resources"]),
                      "fixtures": len(manifest["fixtures"])}, sort_keys=True))


if __name__ == "__main__":
    main()
