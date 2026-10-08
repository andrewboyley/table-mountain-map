#!/usr/bin/env python3
"""Download the two source files that data/ starts from.

data/ is empty in git, so a fresh clone begins with `just fetch-sources`:

  1. Geofabrik South Africa extract -> data/osm/south-africa-latest.osm.pbf
     Verified against Geofabrik's published .md5 sidecar. `-latest` rolls
     forward about weekly, so the hash is not pinned here.

  2. City of Cape Town 2 m contours -> data/vector/coct/<portal name>.zip
     Asked for from the COCT ArcGIS Hub site, which answers with a resultUrl
     for its cached export. The SHA-256 of the archive this project was built
     from is printed for comparison; a mismatch just means the portal
     regenerated the export.

Standard library only: no GDAL, no QGIS.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
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
# SHA-256 of the export the contours in this repo were derived from.
COCT_SHA256 = "adf09db8b963e6814eae2aec63240bf870d31bfcaade46d8db96f50f65c3f880"

UA = {"User-Agent": "table-mountain-pov fetch-sources"}


def download(url: str, dest: Path) -> tuple[str, str]:
    """Stream url into dest (via a .part file). Return (md5, sha256)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    md5, sha = hashlib.md5(), hashlib.sha256()
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=120) as response:
        total = int(response.headers.get("Content-Length") or 0)
        with part.open("wb") as out:
            done = 0
            while chunk := response.read(1 << 20):
                out.write(chunk)
                md5.update(chunk)
                sha.update(chunk)
                done += len(chunk)
                if total and done % (100 << 20) == 0:
                    print(f"    {done >> 20} / {total >> 20} MiB", flush=True)
    part.replace(dest)
    return md5.hexdigest(), sha.hexdigest()


def fetch_pbf() -> None:
    if PBF_PATH.exists():
        print(f"pbf: already present, {PBF_PATH.relative_to(ROOT)}")
        return
    print("pbf: downloading south-africa-latest.osm.pbf")
    md5, _ = download(PBF_URL, PBF_PATH)
    with urllib.request.urlopen(PBF_URL + ".md5", timeout=60) as response:
        expected = response.read().decode().split()[0]
    if md5 != expected:
        sys.exit(f"pbf: md5 {md5} does not match Geofabrik sidecar {expected}")
    print(f"pbf: md5 {md5} matches the Geofabrik sidecar")


def fetch_coct() -> None:
    existing = sorted(COCT_DIR.glob("GLM_2m_*.zip"))
    if existing:
        print(f"coct: already present, {existing[0].relative_to(ROOT)}")
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

    dest = COCT_DIR / result_url.rsplit("/", 1)[-1]
    print(f"coct: downloading {dest.name}")
    _, sha = download(result_url, dest)
    if sha == COCT_SHA256:
        print(f"coct: sha256 {sha} matches the recorded archive")
    else:
        print(f"coct: sha256 {sha} (recorded archive: {COCT_SHA256})")
        print(
            "coct: differs from the recorded archive; the portal may have regenerated it"
        )


def main() -> None:
    fetch_pbf()
    fetch_coct()


if __name__ == "__main__":
    main()
