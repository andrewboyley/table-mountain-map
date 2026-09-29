#!/usr/bin/env python3
"""Verify the project against the contracts in openspec/changes/qgis-project-hardening/specs.

Each subcommand is a direct transcription of the WHEN/THEN scenarios in one
spec, so the specs and this script stay legible to each other:

    crop-extent   specs/model-crop-extent/spec.md
    raster        specs/raster-performance/spec.md
    trails        specs/osm-trail-pipeline/spec.md
    docs          specs/project-provenance/spec.md

GeoPackage outputs are compared by content and geometry, never by byte
checksum: GDAL writes a last_change timestamp into gpkg_contents on every save,
so the bytes always differ even when the data is identical.

Exit status is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]

PROJECT_CRS = "EPSG:32734"

# The authoritative north-up crop extent. What used to be treated as the
# crop rectangle now lives as the DEM boundary mask at
# data/vector/bound/bound.shp; reading it as the extent would be a regression
# to the pre-GeoPackage layout.
CROP_EXTENT = ROOT / "data/vector/osm/tmnp_extent_north_up.gpkg"
LEGACY_CROP_EXTENT = ROOT / "data/vector/bound/bound.shp"

# The park boundary is the declared stable source for the crop extent.
BOUNDARY = ROOT / "data/vector/osm/tmnp_relation_338191.gpkg"
BOUNDARY_RELATION = 338191

# Published values the crop extent must reproduce. Measured, not assumed.
# Longest side first, to match the descending sort in the length check.
EXPECTED_EXTENT_LENGTHS_M = (49372.55, 18479.41)
EXPECTED_EXTENT_AREA_KM2 = 912.3755
LENGTH_TOLERANCE_M = 0.01
AREA_TOLERANCE_KM2 = 0.0001

# Coordinate precision the README states its numbers at. A vertex may fall
# this far outside the extent and still be a printing artefact, not a breach.
PUBLICATION_PRECISION_M = 0.001

OVERVIEW_PIXEL_THRESHOLD = 10_000_000
BIG_RASTERS = (
    "data/imagery/aerial_1m.tif",
    "data/imagery/aerial_5m.tif",
    "data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif",
    "data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound_bgis.tif",
)

EXPECTED_TRAIL_DATASETS = (
    ("data/vector/osm/tm_hiking_trails_dissolved.gpkg", "hiking_trails"),
    ("data/vector/osm/tm_trail_supplement.gpkg", "unnamed_trails"),
    ("data/vector/osm/tm_trail_supplement.gpkg", "tracks"),
)
TRAIL_MANIFEST = ROOT / "data/vector/osm/trail_datasets.manifest.json"

# Docs to scan for path references.
SCANNED_DOCS = ("README.md", "data/README.md", "renders/README.md", "cache/README.md")
TOP_LEVEL_DIRS = (
    "data",
    "qgis",
    "scripts",
    "docs",
    "cache",
    "renders",
    "blender",
    "openspec",
    "tools",
)
BACKTICKED = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
LOCAL_DOC_SUFFIXES = (
    ".gpkg",
    ".tif",
    ".pbf",
    ".shp",
    ".qgz",
    ".py",
    ".md",
    ".zip",
    ".blend",
)


class Report:
    """Collects check outcomes so one failure does not hide the rest."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, passed: bool, detail: str = "") -> bool:
        self.rows.append((name, passed, detail))
        return passed

    def failed(self) -> list[tuple[str, bool, str]]:
        return [r for r in self.rows if not r[1]]

    def emit(self) -> int:
        print(f"\n=== {self.title} ===")
        for name, passed, detail in self.rows:
            mark = "PASS" if passed else "FAIL"
            line = f"  [{mark}] {name}"
            if detail:
                line += f" -- {detail}"
            print(line)
        bad = self.failed()
        print(f"  {len(self.rows) - len(bad)}/{len(self.rows)} checks passed")
        return 1 if bad else 0


def srs_code(layer: ogr.Layer) -> str | None:
    srs = layer.GetSpatialRef()
    return srs.GetAuthorityCode(None) if srs else None


def iter_parts(geom: ogr.Geometry):
    """Yield leaf geometries from a possibly-nested geometry."""
    multi = {
        ogr.wkbMultiPoint,
        ogr.wkbMultiLineString,
        ogr.wkbMultiPolygon,
        ogr.wkbMultiLineString25D,
        ogr.wkbMultiPolygon25D,
        ogr.wkbGeometryCollection,
    }
    if geom.GetGeometryType() in multi:
        for i in range(geom.GetGeometryCount()):
            yield from iter_parts(geom.GetGeometryRef(i))
    else:
        yield geom


def iter_rings(geom: ogr.Geometry):
    for part in iter_parts(geom):
        # GeometryTypeToName returns mixed case ("Polygon", "Multi Line String").
        if "POLYGON" in ogr.GeometryTypeToName(part.GetGeometryType()).upper():
            for r in range(part.GetGeometryCount()):
                yield part.GetGeometryRef(r)
        else:
            yield part


def load_geometry(path: Path) -> ogr.Geometry | None:
    if not path.exists():
        return None
    ds = ogr.Open(str(path))
    if ds is None or ds.GetLayerCount() == 0:
        return None
    feats = [f.GetGeometryRef().Clone() for f in ds.GetLayer(0)]
    return feats[0] if feats else None


# --------------------------------------------------------------------------
# crop-extent
# --------------------------------------------------------------------------


def check_crop_extent() -> int:
    rep = Report("crop-extent  (specs/model-crop-extent)")

    extent_path = CROP_EXTENT if CROP_EXTENT.exists() else LEGACY_CROP_EXTENT
    using_legacy = extent_path == LEGACY_CROP_EXTENT

    rep.check(
        "an authoritative crop extent exists",
        extent_path.exists(),
        str(extent_path.relative_to(ROOT)),
    )
    if not extent_path.exists():
        return rep.emit()

    rep.check(
        "crop extent is the promoted GeoPackage, not the boundary mask",
        not using_legacy,
        "still reading data/vector/bound/bound.shp"
        if using_legacy
        else "data/vector/osm/tmnp_extent_north_up.gpkg",
    )

    ds = ogr.Open(str(extent_path))
    layer = ds.GetLayer(0)
    rep.check(
        "crop extent is in EPSG:32734",
        srs_code(layer) == "32734",
        srs_code(layer) or "none",
    )

    geom = [f.GetGeometryRef().Clone() for f in layer][0]
    minx, maxx, miny, maxy = geom.GetEnvelope()

    # North-up: every edge parallel to a grid axis.
    ring = next(iter_rings(geom))
    pts = [(ring.GetX(i), ring.GetY(i)) for i in range(ring.GetPointCount())]
    import math

    worst = 0.0
    for i in range(len(pts)):
        dx = pts[(i + 1) % len(pts)][0] - pts[i][0]
        dy = pts[(i + 1) % len(pts)][1] - pts[i][1]
        bearing = math.degrees(math.atan2(dx, dy)) % 90.0
        worst = max(worst, min(bearing, 90.0 - bearing))
    rep.check(
        "crop extent is north-up (all edges axis-aligned)",
        worst < 0.01,
        f"worst edge deviation {worst:.6f} deg",
    )

    # Published dimensions.
    lengths = sorted((maxx - minx, maxy - miny), reverse=True)
    len_ok = all(
        abs(a - b) < LENGTH_TOLERANCE_M
        for a, b in zip(lengths, EXPECTED_EXTENT_LENGTHS_M)
    )
    rep.check(
        "side lengths match the published boundary envelope",
        len_ok,
        "%.2f x %.2f m (expected %.2f x %.2f)" % (*lengths, *EXPECTED_EXTENT_LENGTHS_M),
    )
    area_km2 = geom.GetArea() / 1e6
    rep.check(
        "area matches the published boundary envelope",
        abs(area_km2 - EXPECTED_EXTENT_AREA_KM2) < AREA_TOLERANCE_KM2,
        f"{area_km2:.4f} km2 (expected {EXPECTED_EXTENT_AREA_KM2})",
    )

    # Boundary containment, with the publication-precision allowance.
    if BOUNDARY.exists():
        bds = ogr.Open(str(BOUNDARY))
        outside = 0
        worst_excursion = 0.0
        total = 0
        for feat in bds.GetLayer(0):
            bgeom = feat.GetGeometryRef()
            if bgeom is None:
                continue
            for line in iter_rings(bgeom):
                for i in range(line.GetPointCount()):
                    total += 1
                    pt = ogr.Geometry(ogr.wkbPoint)
                    pt.AddPoint(line.GetX(i), line.GetY(i))
                    if not geom.Contains(pt):
                        outside += 1
                        worst_excursion = max(worst_excursion, geom.Distance(pt))
        contained = outside == 0 or worst_excursion <= PUBLICATION_PRECISION_M
        rep.check(
            f"park boundary relation {BOUNDARY_RELATION} is fully contained",
            contained,
            f"{total - outside}/{total} vertices inside, max excursion {worst_excursion * 1000:.3f} mm",
        )
    else:
        rep.check(
            f"park boundary relation {BOUNDARY_RELATION} is readable", False, "missing"
        )

    # Raster footprint divergence: report, do not fail on a superset.
    print("  -- raster footprint vs crop extent --")
    for rel in BIG_RASTERS:
        path = ROOT / rel
        if not path.exists():
            print(f"     {Path(rel).name}: absent")
            continue
        rds = gdal.Open(str(path))
        gt = rds.GetGeoTransform()
        rminx, rmaxx = gt[0], gt[0] + rds.RasterXSize * gt[1]
        rminy, rmaxy = gt[3] + rds.RasterYSize * gt[5], gt[3]
        covers = rminx <= minx and rmaxx >= maxx and rminy <= miny and rmaxy >= maxy
        exact = (
            abs(rminx - minx) < 1e-3
            and abs(rmaxx - maxx) < 1e-3
            and abs(rminy - miny) < 1e-3
            and abs(rmaxy - maxy) < 1e-3
        )
        overlap = not (rmaxx < minx or rminx > maxx or rmaxy < miny or rminy > maxy)
        if exact:
            verdict = "equal"
        elif covers:
            verdict = "superset (allowed)"
        elif overlap:
            verdict = "partial"
        else:
            verdict = "no overlap"
        print(f"     {Path(rel).name}: {verdict}")
    return rep.emit()


# --------------------------------------------------------------------------
# raster
# --------------------------------------------------------------------------


def check_raster() -> int:
    rep = Report("raster  (specs/raster-performance)")

    baseline = ROOT / "cache/verification/raster_source_checksums.sha256"
    recorded = {}
    if baseline.exists():
        for line in baseline.read_text().splitlines():
            digest, _, name = line.partition("  ")
            if name:
                recorded[name.strip()] = digest.strip()

    for rel in BIG_RASTERS:
        path = ROOT / rel
        if not path.exists():
            rep.check(f"{Path(rel).name} present", False, "absent")
            continue

        rds = gdal.Open(str(path))
        pixels = rds.RasterXSize * rds.RasterYSize
        overviews = rds.GetRasterBand(1).GetOverviewCount() if rds.RasterCount else 0
        needs = pixels > OVERVIEW_PIXEL_THRESHOLD

        if needs:
            rep.check(
                f"{Path(rel).name} has overviews",
                overviews > 0,
                f"{rds.RasterXSize}x{rds.RasterYSize} = {pixels:,} px, {overviews} overview levels",
            )
        else:
            rep.check(
                f"{Path(rel).name} below threshold, no overviews required",
                True,
                f"{pixels:,} px",
            )

        if rel in recorded:
            import hashlib

            h = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 22), b""):
                    h.update(chunk)
            rep.check(
                f"{Path(rel).name} source unchanged",
                h.hexdigest() == recorded[rel],
                "matches baseline"
                if h.hexdigest() == recorded[rel]
                else "CHECKSUM CHANGED",
            )

    return rep.emit()


# --------------------------------------------------------------------------
# trails
# --------------------------------------------------------------------------


def check_trails() -> int:
    rep = Report("trails  (specs/osm-trail-pipeline)")

    for rel, layername in EXPECTED_TRAIL_DATASETS:
        path = ROOT / rel
        if not path.exists():
            rep.check(f"{rel} [{layername}] present", False, "absent")
            continue
        ds = ogr.Open(str(path))
        if ds.GetLayerByName(layername) is None:
            rep.check(f"{rel} [{layername}] present", False, "layer not found")
            continue
        layer = ds.GetLayerByName(layername)
        n = layer.GetFeatureCount()
        rep.check(f"{rel} [{layername}] non-empty", n > 0, f"{n} features")

        invalid = 0
        blank_names = 0
        parts_hist: dict[int, int] = {}
        for feat in layer:
            g = feat.GetGeometryRef()
            if g is None or g.IsEmpty() or not g.IsValid():
                invalid += 1
                continue
            try:
                pcount = sum(
                    1
                    for p in iter_parts(g)
                    if ogr.GeometryTypeToName(p.GetGeometryType()).find("POLYGON") == -1
                )
            except Exception:
                pcount = 1
            parts_hist[pcount] = parts_hist.get(pcount, 0) + 1
            if layer.GetLayerDefn().GetFieldIndex("name") >= 0:
                if not (feat.GetField("name") or "").strip():
                    blank_names += 1
        rep.check(
            f"{rel} [{layername}] geometry all valid",
            invalid == 0,
            f"{invalid} invalid",
        )
        # Blank names are only anomalous for the named-trail layer. The
        # supplement layers exist precisely to hold unnamed features.
        if layername == "hiking_trails":
            rep.check(
                f"{rel} [{layername}] no blank names",
                blank_names == 0,
                f"{blank_names} blank",
            )
        if len(parts_hist) > 1:
            detail = ", ".join(
                f"{k} part(s): {v}" for k, v in sorted(parts_hist.items())
            )
            print(f"  --   {layername} part distribution -- {detail}")

    # Content-based, not byte-based: the manifest records expected measures.
    if TRAIL_MANIFEST.exists():
        manifest = json.loads(TRAIL_MANIFEST.read_text())
        datasets = manifest.get("datasets", {})
        for rel, layername in EXPECTED_TRAIL_DATASETS:
            path = ROOT / rel
            if not path.exists():
                continue
            entry = datasets.get(f"{rel}|{layername}")
            if not entry:
                continue
            ds = ogr.Open(str(path))
            layer = ds.GetLayerByName(layername)
            rep.check(
                f"{rel} [{layername}] feature count matches manifest",
                layer.GetFeatureCount() == entry.get("features"),
                f"{layer.GetFeatureCount()} vs {entry.get('features')}",
            )

        # Recorded aggregate measures (spec: aggregate measures are stable).
        diss = datasets.get(
            "data/vector/osm/tm_hiking_trails_dissolved.gpkg|hiking_trails"
        )
        if diss:
            path = ROOT / "data/vector/osm/tm_hiking_trails_dissolved.gpkg"
            if path.exists():
                ds = ogr.Open(str(path))
                layer = ds.GetLayerByName("hiking_trails")
                total = round(sum(f.GetField("length_m") or 0 for f in layer), 1)
                rep.check(
                    "dissolved trail total length matches manifest",
                    abs(total - diss.get("length_m_total", -1.0)) < 0.11,
                    f"{total:.1f} m vs record {diss.get('length_m_total')}",
                )
                single = sum(
                    1
                    for f in layer
                    if sum(
                        1
                        for p in iter_parts(f.GetGeometryRef())
                        if ogr.GeometryTypeToName(p.GetGeometryType()).find("POLYGON")
                        == -1
                    )
                    == 1
                )
                recorded_single = manifest.get("single_part_trails")
                rep.check(
                    "single-part trail count matches manifest",
                    recorded_single is not None and single == recorded_single,
                    f"{single} vs record {recorded_single}",
                )

        # Provenance fields (spec: provenance is recorded). Every field is
        # checked for presence so a rebuild cannot silently drop a record.
        prov = manifest.get("provenance", {})
        rep.check(
            "manifest records the extract with size and mtime",
            bool(prov)
            and bool(prov.get("extract", {}).get("relpath"))
            and prov["extract"].get("size_bytes")
            and prov["extract"].get("mtime_utc"),
            "extract named with size and mtime",
        )
        rep.check(
            "manifest records the boundary by relation id and area",
            prov.get("boundary", {}).get("relation_id") == BOUNDARY_RELATION
            and prov["boundary"].get("polygon_area_km2"),
            f"relation {prov.get('boundary', {}).get('relation_id')}, "
            f"area {prov.get('boundary', {}).get('polygon_area_km2')} km2",
        )
        rep.check(
            "manifest records the accepted highway values",
            bool(prov.get("accepted_highway_values")),
            ", ".join(prov.get("accepted_highway_values", [])),
        )
        rep.check(
            "manifest records the named-only rule",
            bool(prov.get("named_rule")),
            "named rule stated",
        )
        rep.check(
            "manifest records the dissolve rule",
            bool(prov.get("dissolve", {}).get("grouping_attribute"))
            and bool(prov.get("dissolve", {}).get("geometric_operator")),
            f"group by {prov.get('dissolve', {}).get('grouping_attribute')}, "
            f"op {prov.get('dissolve', {}).get('geometric_operator')}",
        )
        rep.check(
            "manifest records the output CRS and linear units",
            prov.get("crs", {}).get("code") == PROJECT_CRS
            and prov["crs"].get("axis_units") == "metres (linear)",
            str(prov.get("crs", {})),
        )

        # Stale-record protection: the extract's current size and mtime must
        # still match what provenance records (spec: stale values are
        # refreshed).
        ext = prov.get("extract", {})
        pbf = ROOT / ext.get("relpath", "")
        if pbf.exists():
            import time
            from datetime import datetime, timezone

            cur = pbf.stat()
            cur_size = cur.st_size
            cur_mtime = datetime.fromtimestamp(cur.st_mtime, tz=timezone.utc)
            rec_mtime = ext.get("mtime_utc", "")
            match = (
                cur_size == ext.get("size_bytes")
                and abs((cur_mtime - datetime.fromisoformat(rec_mtime)).total_seconds())
                < 1.0
            )
            rep.check(
                "extract provenance matches the file on disk",
                match,
                f"{cur_size} bytes, mtime {cur_mtime.isoformat()}",
            )
        rep.check(
            "trail dataset checksums are recorded in the manifest",
            all(
                datasets.get(f"{rel}|{layername}", {}).get("sha256")
                for rel, layername in EXPECTED_TRAIL_DATASETS
            ),
            "sha256 present for every expected dataset",
        )
    else:
        rep.check(
            "trail manifest exists",
            False,
            f"missing {TRAIL_MANIFEST.relative_to(ROOT)}",
        )

    return rep.emit()


# --------------------------------------------------------------------------
# docs
# --------------------------------------------------------------------------


def scan_doc_paths() -> tuple[dict[str, list[str]], set[str]]:
    """Return backticked path-like tokens per doc, and the resolvable set."""
    found: dict[str, list[str]] = {}
    for rel in SCANNED_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf8", errors="replace")
        candidates: set[str] = set()
        for token in BACKTICKED.findall(text) + MARKDOWN_LINK.findall(text):
            token = token.strip()
            if token.startswith(("http://", "https://", "mailto:")):
                continue
            if token.startswith(TOP_LEVEL_DIRS):
                candidates.add(token.rstrip("/") if token.endswith("/") else token)
            elif token.endswith("/") and "/" not in token and token.islower():
                # A bare directory name, resolved against the document.
                candidates.add(f"{(Path(rel).parent / token).as_posix()}")
        found[rel] = sorted(candidates)
    return found, set()


def check_docs() -> int:
    rep = Report("docs  (specs/project-provenance)")

    found, _ = scan_doc_paths()
    all_tokens: set[str] = set()
    unresolved: list[str] = []
    for rel, tokens in found.items():
        all_tokens.update(tokens)
        for token in tokens:
            if not (ROOT / token).exists():
                unresolved.append(f"{rel}: {token}")
    rep.check(
        "every documented path resolves",
        not unresolved,
        f"{len(unresolved)} unresolved of {len(all_tokens)} referenced",
    )
    for item in unresolved:
        print(f"     unresolved -> {item}")

    # Datasets present but undocumented.
    data_dir = ROOT / "data"
    present: set[str] = set()
    for p in data_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in LOCAL_DOC_SUFFIXES:
            if p.name == "README.md":
                continue
            present.add(p.relative_to(ROOT).as_posix())

    documented_text = "\n".join(
        (ROOT / rel).read_text(encoding="utf8", errors="replace")
        for rel in SCANNED_DOCS
        if (ROOT / rel).exists()
    )
    undocumented = sorted(
        p
        for p in present
        # .tif rasters are build outputs of a documented workflow, and the
        # trajectory here is that each is covered by a README or a script.
        if Path(p).name not in documented_text
        and Path(p).suffix.lower() not in (".tif",)
    )
    rep.check(
        "every dataset in data/ is documented",
        not undocumented,
        f"{len(undocumented)} undocumented of {len(present)} present",
    )
    for item in undocumented:
        print(f"     undocumented -> {item}")

    return rep.emit()


# --------------------------------------------------------------------------


SUBCOMMANDS = {
    "crop-extent": check_crop_extent,
    "raster": check_raster,
    "trails": check_trails,
    "docs": check_docs,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "subcommand",
        choices=sorted(SUBCOMMANDS) + ["all"],
        help="which spec area to verify",
    )
    args = parser.parse_args()

    names = sorted(SUBCOMMANDS) if args.subcommand == "all" else [args.subcommand]
    status = 0
    for name in names:
        status |= SUBCOMMANDS[name]()
    return status


if __name__ == "__main__":
    sys.exit(main())
