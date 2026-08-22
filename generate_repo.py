#!/usr/bin/env python3
"""Build APT metadata for every Debian package in ./debs."""

from __future__ import annotations

import email.parser
import gzip
import hashlib
import io
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEBS = ROOT / "debs"


def ar_members(data: bytes):
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("Not a Debian/ar archive")
    offset = 8
    while offset < len(data):
        header = data[offset : offset + 60]
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58])
        body = data[offset + 60 : offset + 60 + size]
        yield name, body
        offset += 60 + size + (size % 2)


def control_fields(deb: Path):
    control_archive = next(
        body for name, body in ar_members(deb.read_bytes()) if name.startswith("control.tar")
    )
    with tarfile.open(fileobj=io.BytesIO(control_archive), mode="r:*") as archive:
        member = next(item for item in archive if item.name.lstrip("./") == "control")
        raw = archive.extractfile(member).read().decode("utf-8")
    return email.parser.Parser().parsestr(raw)


def digest(data: bytes, algorithm: str) -> str:
    return hashlib.new(algorithm, data).hexdigest()


def package_stanza(deb: Path) -> str:
    fields = control_fields(deb)
    data = deb.read_bytes()
    lines = [f"{key}: {value}" for key, value in fields.items()]
    lines.extend(
        [
            f"Filename: {deb.relative_to(ROOT).as_posix()}",
            f"Size: {len(data)}",
            f"MD5sum: {digest(data, 'md5')}",
            f"SHA1: {digest(data, 'sha1')}",
            f"SHA256: {digest(data, 'sha256')}",
        ]
    )
    return "\n".join(lines)


def build() -> None:
    debs = sorted(DEBS.glob("*.deb"))
    if not debs:
        raise SystemExit("No .deb files found in ./debs")

    packages = ("\n\n".join(package_stanza(deb) for deb in debs) + "\n").encode()
    (ROOT / "Packages").write_bytes(packages)
    packages_gz = gzip.compress(packages, compresslevel=9, mtime=0)
    (ROOT / "Packages.gz").write_bytes(packages_gz)

    entries = [("Packages", packages), ("Packages.gz", packages_gz)]
    release = [
        "Origin: sup3rvic0",
        "Label: sup3rvic0",
        "Suite: stable",
        "Version: 1.0",
        "Codename: ios",
        "Architectures: iphoneos-arm64",
        "Components: main",
        "Description: EvoCam repository by sup3rvic0",
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')}",
    ]
    for title, algorithm in (("MD5Sum", "md5"), ("SHA1", "sha1"), ("SHA256", "sha256")):
        release.append(f"{title}:")
        release.extend(
            f" {digest(data, algorithm)} {len(data):16d} {name}" for name, data in entries
        )
    (ROOT / "Release").write_text("\n".join(release) + "\n", encoding="utf-8", newline="\n")
    print(f"Indexed {len(debs)} package(s)")


if __name__ == "__main__":
    build()
