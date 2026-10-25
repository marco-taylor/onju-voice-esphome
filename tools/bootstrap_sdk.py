#!/usr/bin/env python3
"""Reconstruct the exact production SDK from pinned archives and source overlays.

No firmware is built or installed. The generated SDK and download cache are ignored.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "onju-voice-assets/tetele-production"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/sdk")
    args = parser.parse_args()
    spec = json.loads((ASSETS / "sdk-manifest.json").read_text())
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    archives = {}
    try:
        for archive in spec["archives"]:
            cached = args.cache_dir / (archive["id"] + ".tar.gz")
            if not cached.exists():
                with urllib.request.urlopen(archive["url"], timeout=120) as response:
                    data = response.read()
                if digest(data) != archive["sha256"]:
                    raise RuntimeError("Download checksum mismatch: " + archive["id"])
                cached.write_bytes(data)
            if digest(cached.read_bytes()) != archive["sha256"]:
                raise RuntimeError("Cache checksum mismatch: " + archive["id"])
            archives[archive["id"]] = tarfile.open(cached, "r:gz")
        target = ASSETS / "sdk/esp-adf"
        for relative, entry in spec["files"].items():
            # Never extract arbitrary archive paths or symlinks.
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError("Invalid manifest path")
            if "overlay" in entry:
                data = (ASSETS / "sdk-overlay" / relative).read_bytes()
            else:
                archive = archives[entry["archive"]]
                member = archive.getmember(entry["member"])
                if not member.isfile():
                    raise RuntimeError("Expected archive file: " + relative)
                data = archive.extractfile(member).read()
            if len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
                raise RuntimeError("SDK file checksum mismatch: " + relative)
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            if not output.exists() or output.read_bytes() != data:
                output.write_bytes(data)
        actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
        if actual != set(spec["files"]):
            raise RuntimeError("Unexpected SDK files present; use a fresh checkout")
        print(f"SDK verified: {len(actual)} files, exact production content")
    finally:
        for archive in archives.values():
            archive.close()


if __name__ == "__main__":
    main()
