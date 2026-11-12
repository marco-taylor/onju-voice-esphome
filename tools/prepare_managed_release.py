#!/usr/bin/env python3
"""Package one ESPHome build into a GitHub-latest manifest and immutable artifacts.

No upload, flash, tag or release API. Factory and OTA are never built separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

REPOSITORY = "marco-taylor/onju-voice-esphome"
PROJECT = "tetele.onju_voice_satellite"  # Preserve the established project identity.
HARDWARE = "onju-voice-esp32s3-16mb-8mb-psram"
MANIFEST_NAME = "onju-voice.manifest.json"
OTA_NAME = "onju-voice.ota.bin"
FACTORY_NAME = "onju-voice.factory.bin"
SEMVER = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"


def digest(data, algorithm="sha256"):
    return hashlib.new(algorithm, data).hexdigest()


def validate_manifest(manifest, expected_version=None):
    assert manifest["project"] == PROJECT, "Wrong project"
    assert manifest["hardware"] == HARDWARE, "Wrong board"
    assert re.fullmatch(SEMVER, manifest["version"]), "Not a release SemVer"
    if expected_version is not None:
        assert manifest["version"] == expected_version
    assert len(manifest["builds"]) == 1
    build = manifest["builds"][0]
    assert build["chipFamily"] == "ESP32-S3", "Wrong chip family"
    ota = build["ota"]
    assert re.fullmatch(r"[0-9a-f]{32}", ota["md5"]), "Invalid MD5"
    assert re.fullmatch(r"[0-9a-f]{64}", ota["sha256"]), "Invalid SHA256"
    prefix = f"https://github.com/{REPOSITORY}/releases/download/v{manifest['version']}/"
    assert ota["path"] == prefix + OTA_NAME, "OTA URL must be pinned to this release"
    assert ota["release_url"] == f"https://github.com/{REPOSITORY}/releases/tag/v{manifest['version']}"
    assert ota["size"] > 256
    return manifest


def create_manifest(version, ota_bytes, include_factory=False):
    prefix = f"https://github.com/{REPOSITORY}/releases/download/v{version}/"
    build = {"chipFamily": "ESP32-S3", "ota": {
        "path": prefix + OTA_NAME,
        "md5": digest(ota_bytes, "md5"),  # Official on-device ESPHome integrity field.
        "sha256": digest(ota_bytes),     # Release verification; not consumed by HTTP OTA.
        "size": len(ota_bytes),
        "summary": "Onju Voice firmware. Install only a hardware-approved release.",
        "release_url": f"https://github.com/{REPOSITORY}/releases/tag/v{version}",
    }}
    if include_factory:
        build["parts"] = [{"path": prefix + FACTORY_NAME, "offset": 0}]
    return validate_manifest({"name": "Onju Voice ESPHome", "version": version,
                              "project": PROJECT, "hardware": HARDWARE, "builds": [build]}, version)


def package(build, output, source_revision, require_factory=False):
    build = Path(build).resolve()
    main = (build / "src/main.cpp").read_text()
    defines = (build / "src/esphome/core/defines.h").read_text()
    version = re.search(r'#define ESPHOME_PROJECT_VERSION "([^"\n]+)"', defines)[1]
    project = re.search(r'#define ESPHOME_PROJECT_NAME "([^"\n]+)"', defines)[1]
    assert project == PROJECT
    assert re.fullmatch(SEMVER, version)
    assert 'USE_ONJU_IDENTITY' in defines and 'onju_identity::pre_setup(' in main and ', nullptr);' in main, "Only the generic profile-aware distribution build is allowed"
    assert 'onju_identity_seed' not in main, "Never publish a private bootstrap image"
    assert 'static_ip:' not in main and '!secret' not in main, "Distribution build must use provisioned Wi-Fi"
    info = json.loads((build / "build_info.json").read_text())
    assert info["esphome_version"] == "2026.10.2"
    ota = (build / "build/firmware.ota.bin").read_bytes()
    assert ota[0] == 0xE9 and int.from_bytes(ota[12:14], "little") == 9, "Not an ESP32-S3 application"
    assert (build / "build/onju-voice.bin").read_bytes() == ota, "OTA file differs from the actual linked app image"
    assert len(ota) < 0x7C0000, "App exceeds current OTA partition"
    assert ota[32:36] == bytes.fromhex("3254cdab"), "App descriptor missing: do not package a factory image as OTA"
    assert all(s in defines for s in ['USE_IMPROV_SERIAL', 'USE_UPDATE', 'USE_OTA'])
    assert all(s in main for s in ["http_request::HttpRequestUpdate", "http_request::OtaHttpRequestComponent", "ESPHomeOTAComponent"])
    factory_path = build / "build/firmware.factory.bin"
    factory = factory_path.read_bytes() if factory_path.exists() else None
    if require_factory:
        assert factory is not None, "A release needs the factory from this same build"
        assert re.fullmatch(r"[0-9a-f]{40}", source_revision), "Release requires an exact committed source revision"
    if factory is not None:
        # ESPHome's ESP32-S3 custom 16 MB layout: read, do not infer, app0 offset.
        import struct
        entries = []
        table = (build / "build/partition_table/partition-table.bin").read_bytes()
        for pos in range(0,len(table),32):
            entry = table[pos:pos+32]
            if entry[:2] != b"\xaa\x50": break
            magic,kind,subtype,address,size,label,flags = struct.unpack("<HBBII16sI",entry)
            entries.append((kind,subtype,address,size,label.rstrip(b"\0").decode()))
        apps = [e for e in entries if e[0] == 0 and e[1] in (16,17)]
        assert len(apps)==2, "Expected native two-slot OTA layout"
        offset = next(e[2] for e in apps if e[1]==16)
        ota_offset = next(e[2] for e in entries if e[0]==1 and e[1]==0)
        assert factory[offset:offset+len(ota)] == ota, "Factory application differs from validated OTA application"
        assert factory[0] == 0xE9 and factory[0x8000:0x8002] == b"\xaa\x50", "Incomplete USB image"
        assert len(factory) >= offset + len(ota)
        flash_files = json.loads((build / "build/flasher_args.json").read_text())["flash_files"]
        offsets = set()
        for address, filename in flash_files.items():
            address = int(address, 0)
            offsets.add(address)
            segment = (build / "build" / filename).read_bytes()
            assert factory[address:address+len(segment)] == segment, "Factory segment differs: " + filename
        assert {0, 0x8000, ota_offset, offset}.issubset(offsets), "Missing bootloader/partition/OTA-data/app segment"
    output = Path(output)
    assert not output.exists(), "Never overwrite a prepared artifact directory"
    output.mkdir(parents=True)
    (output / OTA_NAME).write_bytes(ota)
    if factory is not None:
        (output / FACTORY_NAME).write_bytes(factory)
    manifest = create_manifest(version, ota, factory is not None)
    (output / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    source_root = Path(__file__).resolve().parents[1]
    source_files = [source_root / "onju-voice.yaml", source_root / "onju-voice-assets/tetele-production/sdk-manifest.json"]
    source_files += [p for p in (source_root / "onju-voice-assets/tetele-production/components").rglob("*") if p.is_file() and p.suffix in (".py", ".h", ".cpp") and "__pycache__" not in p.parts]
    source_hashes = {str(p.relative_to(source_root)): digest(p.read_bytes()) for p in source_files}
    provenance = {"source_hashes": source_hashes, "project": project, "version": version, "source_revision": source_revision,
                  "esphome": info, "factory_app_equals_ota": factory is not None,
                  "local_preview_only": not require_factory,
                  "ota_sha256": digest(ota), "ota_md5": digest(ota, "md5")}
    (output / "build-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    assets = sorted(p for p in output.iterdir() if p.is_file())
    (output / "SHA256SUMS").write_text("".join(f"{digest(p.read_bytes())}  {p.name}\n" for p in assets))
    # Read back all packaged artifacts, independently of the above creation loop.
    for line in (output / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((output/name).read_bytes()).hexdigest() == expected
    assert (output/OTA_NAME).read_bytes() == ota
    return provenance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--commit", default="LOCAL-UNCOMMITTED")
    p.add_argument("--require-factory", action="store_true")
    a = p.parse_args()
    print(json.dumps(package(a.build, a.out, a.commit, a.require_factory), indent=2))


if __name__ == "__main__":
    main()
