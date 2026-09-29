#!/usr/bin/env python3
"""Offscreen verification gate for ``qgis/table_mountain_3D.qgs``.

Usage::

    python3 scripts/verify_project.py [--project qgis/table_mountain_3D.qgs]

Loads the saved project headlessly and asserts the machine-checkable
invariants that ``scripts/build_project.py`` enforces, so a hand-edited or
GUI-resaved project that breaks the contract fails with a named check.  The
checks are a direct transcription of the WHEN/THEN scenarios in
``openspec/changes/managed-project-build-and-verify/specs/``:

    project-build        specs/project-build/spec.md
    basemap-services     specs/basemap-services/spec.md

Because headless QGIS has no 3D engine it cannot restore 3D renderers from
XML (``renderer3D()`` is always ``None`` on reload), so the 3D contract --
the categorized trail renderer, the terrain map-theme / ``texture-size`` and
the bloom / colour-grading / camera settings -- is verified against the
serialised XML of the project file itself.

Exit status is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.core import (
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsProject,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT = ROOT / "qgis" / "table_mountain_3D.qgs"
CSV_PATH = ROOT / "qgis" / "styles" / "trail_colors.csv"
MACRO_PATH = ROOT / "qgis" / "trail_presentation_macro.py"

PROJECT_CRS = "EPSG:32734"
TRAIL_LAYER_NAME = "Hiking Trails"
AERIAL_LAYER_NAME = "City of Cape Town Aerial Photography (2026 January)"
OSM_LAYER_NAME = "OpenStreetMap"

REQUIRED_THEMES = (
    "3D terrain texture",
    "Aerial Imagery",
    "Trail Inspection",
    "Single-part trails",
)
ATLAS_LAYOUT = "Named Trail Atlas"

AERIAL_WMS_SOURCE = (
    "crs=EPSG%3A32734&dpiMode=7&featureCount=10&format=image%2Fpng"
    "&layers=coct_aerial&styles&tilePixelRatio=0"
    "&url=http%3A%2F%2Flocalhost%2Fmapproxy%2Fmapproxy%2Fservice"
)
OSM_XYZ_SOURCE = (
    "crs=EPSG%3A3857&format&type=xyz"
    "&url=http%3A%2F%2Flocalhost%2Fmapproxy%2Fmapproxy%2Ftiles%2F1.0.0"
    "%2Fosm%2Fwebmercator%2F%7Bz%7D%2F%7Bx%7D%2F%7By%7D.png&zmax=19&zmin=0"
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


def load_palette() -> list[tuple[str, str, float]]:
    rows: list[tuple[str, str, float]] = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for record in csv.DictReader(f):
            rows.append((record["name"], record["color"], float(record["width_mm"])))
    return rows


def maplayer_blocks(xml_text: str) -> list[str]:
    return re.findall(r"<maplayer\b[^>]*>.*?</maplayer>", xml_text, re.DOTALL)


def block_for_layer(xml_text: str, layer_name: str) -> str | None:
    for block in maplayer_blocks(xml_text):
        m = re.search(r"<layername>([^<]+)</layername>", block)
        if m and m.group(1) == layer_name:
            return block
    return None


def qgis3d_block(xml_text: str) -> str | None:
    m = re.search(r"<qgis3d>.*?</qgis3d>", xml_text, re.DOTALL)
    return m.group(0) if m else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify the QGIS project file")
    ap.add_argument(
        "--project", default=str(DEFAULT_PROJECT), help="project (.qgs) to verify"
    )
    args = ap.parse_args(argv)

    project = Path(args.project)
    if not project.exists():
        print(f"project file missing: {project}")
        return 1

    rep = Report("project  (specs/project-build, basemap-services)")
    xml_text = project.read_text(encoding="utf-8", errors="replace")
    palette = load_palette()

    app = QgsApplication([], False)
    app.initQgis()
    try:
        p = QgsProject()
        if not p.read(str(project)):
            return rep.check("project loads", False, str(project)) or rep.emit()
        rep.check("project loads", True, project.name)

        # --- project identity -------------------------------------------------
        rep.check(
            "project CRS is EPSG:32734",
            p.crs().authid() == PROJECT_CRS,
            str(p.crs().authid()),
        )

        trails = p.mapLayersByName(TRAIL_LAYER_NAME)
        rep.check(
            "exactly one Hiking Trails layer",
            len(trails) == 1,
            f"{len(trails)} found",
        )
        if not trails:
            return rep.emit()
        trail = trails[0]
        rep.check(
            "Hiking Trails is a vector layer",
            trail.isValid() and trail.providerType() == "ogr",
        )
        rep.check(
            "trail layer has no subset filter",
            trail.subsetString() == "",
            repr(trail.subsetString()),
        )

        # --- 2D categorized renderer, palette-complete ------------------------
        r2 = trail.renderer()
        rep.check(
            "2D renderer is categorized on name",
            isinstance(r2, QgsCategorizedSymbolRenderer)
            and r2.classAttribute() == "name",
        )
        if isinstance(r2, QgsCategorizedSymbolRenderer):
            cats = Counter(
                (
                    c.value(),
                    c.symbol().color().name().lower(),
                    round(float(c.symbol().width()), 6),
                )
                for c in r2.categories()
            )
            want = Counter(
                (name, color.lower(), round(width, 6)) for name, color, width in palette
            )
            missing = sorted((want - cats).elements())
            extra = sorted((cats - want).elements())
            rep.check(
                "2D categories cover the palette exactly",
                not missing and not extra,
                f"{len(cats)} categories, {len(want)} palette rows; "
                + (f"missing {missing[:3]}…" if missing else "")
                + (f"extra {extra[:3]}…" if extra else ""),
            )

        # --- 3D categorized renderer (serialised XML: headless has no 3D) -----
        tblock = block_for_layer(xml_text, TRAIL_LAYER_NAME) or ""
        m3 = re.search(r"<renderer-3d\b[^>]*>", tblock)
        r3_ok = (
            m3 is not None
            and re.search(r'attribute="name"', m3.group(0)) is not None
            and 'type="categorized"' in m3.group(0)
        )
        if m3 is not None:
            j3 = tblock.find("</renderer-3d>", m3.end())
            r3_seg = tblock[m3.end() : j3] if j3 >= 0 else tblock[m3.end() :]
            r3_cats = len(re.findall(r"<category\b", r3_seg))
        else:
            r3_cats = 0
        rep.check(
            "3D renderer is categorized on name",
            r3_ok,
            m3.group(0)[:120] if m3 else "no <renderer-3d> block",
        )
        rep.check(
            "3D renderer has the full palette (172 categories)",
            r3_cats == len(palette),
            f"{r3_cats} categories",
        )

        # --- themes ------------------------------------------------------------
        themes = set(p.mapThemeCollection().mapThemes())
        missing_themes = [t for t in REQUIRED_THEMES if t not in themes]
        rep.check(
            "all four map themes exist",
            not missing_themes,
            f"missing {missing_themes}"
            if missing_themes
            else ", ".join(sorted(themes)),
        )

        # --- 3D scene stamp (XML) ----------------------------------------------
        q3 = qgis3d_block(xml_text) or ""
        terrain = re.search(r"<terrain\b[^>]*>", q3)
        terrain_attrs = terrain.group(0) if terrain else ""
        layer_ids = {ly.id() for ly in p.mapLayers().values()}
        rep.check(
            "terrain map-theme is '3D terrain texture'",
            'map-theme="3D terrain texture"' in terrain_attrs,
        )
        rep.check(
            "terrain texture-size is 512",
            'texture-size="512"' in terrain_attrs,
        )
        rep.check(
            "terrain source layer resolves to a project layer",
            bool(terrain)
            and re.search(r'layer="([^"]+)"', terrain_attrs).group(1) in layer_ids,
        )
        for needle, label in (
            ('<bloom enabled="1"', "bloom enabled"),
            ("<color-grading ", "colour grading"),
            ('<eye-dome-lighting enabled="1"', "eye-dome lighting"),
            ('shadow-rendering-enabled="1"', "shadow rendering"),
            ('field-of-view="65"', "camera FOV 65"),
        ):
            rep.check(f"3D stamp: {label}", needle in q3)
        scene_ids = re.findall(r"<layers>\s*(.*?)\s*</layers>", q3, re.DOTALL)
        scene_lid = (
            re.findall(r'<layer id="([^"]+)"', scene_ids[0]) if scene_ids else []
        )
        dangling = [lid for lid in scene_lid if lid not in layer_ids]
        rep.check(
            "every 3D scene layer id resolves to a project layer",
            not dangling,
            f"dangling {dangling}" if dangling else f"{len(scene_lid)} scene layers",
        )

        # --- atlas --------------------------------------------------------------
        layout = p.layoutManager().layoutByName(ATLAS_LAYOUT)
        atlas_ok = layout is not None
        rep.check("Named Trail Atlas layout exists", atlas_ok)
        pages = -1
        if atlas_ok:
            atlas = layout.atlas()
            cov = atlas.coverageLayer()
            rep.check(
                "atlas coverage is Hiking Trails",
                cov is not None and cov.name() == TRAIL_LAYER_NAME,
                cov.name() if cov else "no coverage layer",
            )
            try:
                atlas.beginRender()
                pages = atlas.count()
                atlas.endRender()
            # QGIS/Qt raise heterogeneous exception types offscreen; degrade to
            # an unavailable page count instead of failing the gate.
            except Exception as exc:  # pragma: no cover - defensive  # noqa: BLE001
                pages = -1
                print(f"  note: atlas page count unavailable ({exc})")
            rep.check(
                "atlas produces 172 pages",
                pages == len(palette),
                f"{pages} pages",
            )

        # --- layout LayerSet (XML) ----------------------------------------------
        ls = re.search(r"<LayerSet>.*?</LayerSet>", xml_text, re.DOTALL)
        ls_entries = (
            dict(re.findall(r'<Layer name="([^"]+)"[^>]*>([^<]+)</Layer>', ls.group(0)))
            if ls
            else {}
        )
        want_ls = {TRAIL_LAYER_NAME, "contours_2m_within_bound"}
        rep.check(
            "atlas map LayerSet is coverage + contours",
            set(ls_entries) == want_ls,
            ", ".join(sorted(ls_entries)) if ls_entries else "no LayerSet",
        )
        if ls_entries and set(ls_entries) == want_ls:
            bad_src = [
                name
                for name, src_raw in re.findall(
                    r'<Layer name="([^"]+)"[^>]* source="([^"]*)"', ls.group(0)
                )
                if not src_raw.startswith("../data/")
            ]
            rep.check(
                "LayerSet sources are project-relative", not bad_src, str(bad_src)
            )

        # --- basemap sources -----------------------------------------------------
        aerial = p.mapLayersByName(AERIAL_LAYER_NAME)
        osm = p.mapLayersByName(OSM_LAYER_NAME)
        rep.check("aerial layer exists", len(aerial) == 1)
        rep.check("OSM layer exists", len(osm) == 1)
        if aerial and osm:
            aerial_src = html.unescape(aerial[0].source())
            osm_src = html.unescape(osm[0].source())
            rep.check(
                "aerial is the MapProxy WMS endpoint in EPSG:32734",
                aerial_src == AERIAL_WMS_SOURCE and "type=xyz" not in aerial_src,
                aerial_src[:90],
            )
            rep.check(
                "OSM stays on cached XYZ tiles",
                osm_src == OSM_XYZ_SOURCE,
                osm_src[:90],
            )

        # --- relative paths & resolvable sources (XML) ---------------------------
        bad_abs: list[str] = []
        bad_missing: list[str] = []
        for block in maplayer_blocks(xml_text):
            provider = re.search(r"<provider>([^<]+)</provider>", block)
            if not provider or provider.group(1) not in ("ogr", "gdal"):
                continue
            ds = re.search(r"<datasource>(.*?)</datasource>", block, re.DOTALL)
            if not ds:
                continue
            src = html.unescape(ds.group(1))
            path_part = src.split("|", 1)[0]
            if not path_part.startswith("../"):
                bad_abs.append(src[:80])
                continue
            resolved = (project.resolve().parent / path_part).resolve()
            if not resolved.exists():
                bad_missing.append(str(resolved))
        rep.check(
            "local layer sources are project-relative",
            not bad_abs,
            f"{len(bad_abs)} absolute: {bad_abs[:2]}…",
        )
        rep.check(
            "every local source file exists",
            not bad_missing,
            f"missing {bad_missing[:2]}…",
        )

        # --- embedded macro ------------------------------------------------------
        stored, ok = p.readEntry("Macros", "/pythonCode")
        macro_src = MACRO_PATH.read_text(encoding="utf-8")
        rep.check(
            "presentation macro is embedded verbatim",
            ok and stored == macro_src,
            f"{len(stored)} vs {len(macro_src)} chars",
        )

        return rep.emit()
    finally:
        app.exitQgis()


if __name__ == "__main__":
    sys.exit(main())
