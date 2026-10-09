#!/usr/bin/env python3
"""Download the two source files that data/ starts from.

data/ is empty in git, so a fresh clone begins with `just fetch-sources`:

  1. Geofabrik South Africa extract -> data/osm/south-africa-latest.osm.pbf
     Verified against Geofabrik's published .md5 sidecar. `-latest` rolls
     forward about weekly, so the hash is not pinned here.

  2. City of Cape Town 2 m contours -> data/vector/coct/GLM_2m_contours.zip
     Asked for from the COCT ArcGIS Hub site, which answers with a resultUrl
     for its cached export. The portal does not publish a checksum. This script
     verifies the downloaded ZIP structure and reports its SHA-256.

Standard library only: no GDAL, no QGIS.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBF_URL = "https://download.geofabrik.de/africa/south-africa-latest.osm.pbf"
PBF_PATH = ROOT / "data/osm/south-africa-latest.osm.pbf"

COCT_ITEM = "bbd5614ce9154e649265dae5e9d26018"
COCT_API = (
    "https://odp-cctegis.opendata.arcgis.com/api/download/v1/items/"
    f"{COCT_ITEM}/shapefile?redirect=false&layers=1"
)
COCT_DIR = ROOT / "data/vector/coct"
COCT_PATH = COCT_DIR / "GLM_2m_contours.zip"

UA = {"User-Agent": "table-mountain-pov fetch-sources"}


def digest(path: Path) -> tuple[str, str]:
    """Return MD5 and SHA-256 for path."""
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def download(url: str, dest: Path) -> tuple[str, str]:
    """Stream url into a temporary file. Return its MD5 and SHA-256."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    part.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            total = int(response.headers.get("Content-Length") or 0)
            with part.open("wb") as out:
                done = 0
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    done += len(chunk)
                    if total and done % (100 << 20) == 0:
                        print(f"    {done >> 20} / {total >> 20} MiB", flush=True)
        return digest(part)
    except BaseException:
        part.unlink(missing_ok=True)
        raise


def accept_download(part: Path, dest: Path) -> None:
    """Atomically replace dest with validated part."""
    part.replace(dest)


def geofabrik_md5() -> str:
    """Return the current Geofabrik MD5 sidecar value."""
    with urllib.request.urlopen(PBF_URL + ".md5", timeout=60) as response:
        return response.read().decode().split()[0]


def fetch_pbf() -> None:
    expected = geofabrik_md5()
    if PBF_PATH.exists():
        md5, _ = digest(PBF_PATH)
        if md5 == expected:
            print(f"pbf: verified existing {PBF_PATH.relative_to(ROOT)}")
            return
        PBF_PATH.unlink()
        print("pbf: discarded file with stale or invalid checksum")

    print("pbf: downloading south-africa-latest.osm.pbf")
    md5, _ = download(PBF_URL, PBF_PATH)
    part = PBF_PATH.with_name(PBF_PATH.name + ".part")
    if md5 != expected:
        part.unlink(missing_ok=True)
        sys.exit(f"pbf: md5 {md5} does not match Geofabrik sidecar {expected}")
    accept_download(part, PBF_PATH)
    print(f"pbf: md5 {md5} matches the Geofabrik sidecar")


def validate_coct_archive(path: Path) -> None:
    """Fail when path is not a readable ZIP archive."""
    if not zipfile.is_zipfile(path):
        sys.exit(f"coct: {path.name} is not a ZIP archive")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            sys.exit(f"coct: {path.name} has a corrupt member")


def fetch_coct() -> None:
    if COCT_PATH.exists():
        validate_coct_archive(COCT_PATH)
        _, sha = digest(COCT_PATH)
        print(f"coct: verified existing {COCT_PATH.relative_to(ROOT)} (sha256 {sha})")
        return

    request = urllib.request.Request(COCT_API, headers=UA)
    result_url = None
    for _ in range(60):
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
        if payload.get("status") == "Completed":
            result_url = payload["resultUrl"]
            break
        if payload.get("status") in {"Failed", "Error"}:
            sys.exit(f"coct: export failed: {payload.get('message')}")
        print(f"coct: {payload.get('status')}, waiting...", flush=True)
        time.sleep(10)
    if not result_url:
        sys.exit("coct: export still not ready after 10 minutes")

    print(f"coct: downloading {COCT_PATH.name}")
    _, sha = download(result_url, COCT_PATH)
    part = COCT_PATH.with_name(COCT_PATH.name + ".part")
    validate_coct_archive(part)
    accept_download(part, COCT_PATH)
    print(f"coct: sha256 {sha}")


def main() -> None:
    fetch_pbf()
    fetch_coct()


if __name__ == "__main__":
    main()
