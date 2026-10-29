#!/usr/bin/env python3
"""Export a PNG/JPEG only after its declared observed geometry passes verification.

This is an explicit pipeline gate, not a global Codex hook or an OCR engine.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from verify_layout import load_json, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--measurements", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    destination = Path(args.out)
    inputs = {Path(p).resolve() for p in (args.spec, args.measurements, args.image)}
    if destination.resolve() in inputs or destination.exists():
        parser.error("Export must use a new path and must not replace an input")
    try:
        report = verify(load_json(args.spec), load_json(args.measurements), args.image)
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        print(json.dumps({"status": "UNVERIFIED", "input_error": str(error)}))
        return 2
    if report["status"] != "PASS":
        print(json.dumps(report, indent=2))
        return {"FAIL": 1, "UNVERIFIED": 2}[report["status"]]
    data = Path(args.image).read_bytes()
    if hashlib.sha256(data).hexdigest() != report["image_sha256"]:
        print(json.dumps({"status": "UNVERIFIED", "input_error": "Image changed during verification"}))
        return 2
    # Exclusive creation prevents accidental replacement of any existing output.
    with destination.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"status": "PASS", "output": str(destination), "image_sha256": report["image_sha256"],
                      "scope": report["scope"], "validation_profile": report["validation_profile"],
                      "global_composition_conformity": "NOT_ESTABLISHED"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
