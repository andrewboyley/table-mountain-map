#!/usr/bin/env python3
"""Enforce the canonical state of the QGIS project and write the plain-XML .qgs.

Usage::

    python3 scripts/build_project.py [--input FILE] [--output FILE]

The project file is a *build artifact*: QGIS runs headless (offscreen) and
applies every machine-checkable invariant, so the committed
``qgis/table_mountain_3D.qgs`` is reproducible and its diffs are reviewable.

What the build enforces (all idempotent):

* project CRS ``EPSG:32734``;
* the structured layer tree (Elevation / Paths / Shapes / Basemaps), with the
  ``Hiking Trails`` layer first under Paths;
* the 2D categorized trail renderer rebuilt from ``qgis/styles/trail_colors.csv``
  (172 categories on ``name``), also frozen into the ``Standard`` named style
  (QGIS serialises the current style's snapshot, not the live renderer);
* the 3D categorized trail renderer rebuilt from the same palette (metalrough
  lines, width 3.6, offset 20, terrain-clamped).  Headless QGIS cannot restore
  3D renderers from XML, so the build re-creates it live on every run and the
  verification gate reads the serialised block;
* the four map themes (``3D terrain texture``, ``Aerial Imagery``,
  ``Trail Inspection``, ``Single-part trails``), saved baseline = Inspection;
* relative local data sources (``../data/...``);
* basemap sources: CoCT aerial as the MapProxy WMS endpoint in ``EPSG:32734``
  (layer ``coct_aerial``), OSM as cached MapProxy XYZ tiles;
* ``qgis/trail_presentation_macro.py`` re-embedded into the ``Macros`` section;
* the canonical 3D scene XML stamped afterwards with layer ids resolved by name
  (terrain map-theme / ``texture-size="512"`` / bloom / colour grading /
  camera -- settings QGIS rewrites on a normal save), and a canonical layout
  LayerSet.

Running the build twice against unchanged inputs yields a byte-identical file
(sha256), which is checked by the verification gate in ``verify_project.py``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PyQt6.QtGui import QColor
from qgis._3d import (
    Qgs3DRendererCategory,
    Qgs3DTypes,
    QgsCategorized3DRenderer,
    QgsLine3DSymbol,
    QgsMetalRoughMaterialSettings,
)
from qgis.core import (
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsLineSymbol,
    QgsMapLayerStyle,
    QgsMapThemeCollection,
    QgsProject,
    QgsRendererCategory,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT = ROOT / "qgis" / "table_mountain_3D.qgs"
CSV_PATH = ROOT / "qgis" / "styles" / "trail_colors.csv"
MACRO_PATH = ROOT / "qgis" / "trail_presentation_macro.py"

PROJECT_CRS = "EPSG:32734"

TRAIL_LAYER_NAME = "Hiking Trails"
AERIAL_LAYER_NAME = "City of Cape Town Aerial Photography (2026 January)"
OSM_LAYER_NAME = "OpenStreetMap"
# The DEM feeds the 3D terrain. Site names below are matched as substrings so
# the whole-name layer ids do not have to be hard-coded in this script.
DEM_PART = "table_mountain_contours_2m_interpolated"
CONTOURS_PART = "contours_2m_within_bound"
TRAIL_SRC = "../data/vector/osm/tm_hiking_trails_dissolved.gpkg|layername=hiking_trails"
CONTOURS_SRC = "../data/vector/coct/contours_2m_within_bound.gpkg|layername=contours_2m_within_bound"

# Canonical basemap layer sources (QGIS wms-provider datasource strings).
# Aerial: MapProxy WMS in the project CRS; the cache grid is utm34s so
# MapProxy fetches the upstream CoCT service in its native EPSG:32734.
# OSM: MapProxy cached XYZ tiles, north-west origin (OSM tile scheme).
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

# 3D scene layers in render order. "Annotations" was a stale scene entry (no
# such layer exists in the project) and is intentionally not part of the
# canonical stamp; ids are resolved by layer name at stamp time, and names
# that cannot be resolved are dropped rather than stamped with dead ids.
SCENE_LAYER_PARTS = (
    "Tracks",
    "Unnamed trails",
    TRAIL_LAYER_NAME,
    "Table Mountain NP boundary",
    "TMNP crop extent",
    OSM_LAYER_NAME,
)

GROUP_ORDER = ("Elevation", "Paths", "Shapes", "Basemaps")

# Canonical 3D scene XML, captured from the project and parameterised only by
# the DEM layer id (terrain source) and the in-scene layer ids. Everything
# else -- origin, camera, colour, lights, shading, bloom, colour grading,
# eye-dome lighting, navigation sync -- is fixed by this template, because
# QGIS rewrites the terrain map-theme / texture-size and drops the scene layer
# list on a plain save.
QGS3D_STAMP = """<qgis3d>
        <origin x="260616" y="6.24445e+06" z="3508.74"/>
        <extent showIn2dView="0" xMax="269887.76541704527" xMin="251408.3582293698" yMax="6244589.4887585994" yMin="6195216.9347602576"/>
        <camera camera-movement-speed="0.050000000000000003" camera-navigation-mode="terrain-based-navigation" field-of-view="65" projection-type="1"/>
        <color background="255,255,255,255,rgb:1,1,1,1" selection="255,255,0,255,rgb:1,1,0,1"/>
        <crs>
          <spatialrefsys nativeFormat="Wkt">
            <wkt>PROJCRS["WGS 84 / UTM zone 34S",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],MEMBER["World Geodetic System 1984 (G2296)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["UTM zone 34S",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",21,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",10000000,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Navigation and medium accuracy spatial referencing."],AREA["Between 18°E and 24°E, southern hemisphere between 80°S and equator, onshore and offshore. Angola. Botswana. Democratic Republic of the Congo (Zaire). Namibia. South Africa. Zambia."],BBOX[-80,18,0,24]],ID["EPSG",32734]]</wkt>
            <proj4>+proj=utm +zone=34 +south +datum=WGS84 +units=m +no_defs</proj4>
            <srsid>3184</srsid>
            <srid>32734</srid>
            <authid>EPSG:32734</authid>
            <description>WGS 84 / UTM zone 34S</description>
            <projectionacronym>utm</projectionacronym>
            <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <lights>
          <sun-light atmospheric-pressure="1013.25" color="255,255,255,255,rgb:1,1,1,1" id="1ee21be8-80f7-40ca-8f80-7f163ca82746" intensity="1.3999999999999999" reference-elevation="0" sun-time="2025-09-28T16:30:00Z" temperature="22"/>
        </lights>
        <terrain elevation-offset="0" exaggeration="1" layer="{dem_layer_id}" map-theme="3D terrain texture" max-ground-error="5" max-terrain-error="3" resolution="100" shading-enabled="1" show-labels="0" skirt-height="0" terrain-rendering-enabled="1" texture-size="512">
          <shading-material ambient="26,26,26,255,rgb:0.1000076,0.1000076,0.1000076,1" diffuse="196,168,124,255,rgb:0.7686275,0.6588235,0.4862745,1" ka="1" kd="1" ks="1" opacity="1" shininess="0" specular="255,255,255,255,rgb:1,1,1,1" type="phong">
            <data-defined-properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data-defined-properties>
          </shading-material>
          <layers>
{scene_layer_ids}          </layers>
          <generator type="dem"/>
        </terrain>
        <shadow-rendering light-source="1ee21be8-80f7-40ca-8f80-7f163ca82746" max-shadow-rendering-distance="1500" shadow-bias="9.9999997473787516e-06" shadow-rendering-enabled="1"/>
        <screen-space-ambient-occlusion enabled="1" intensity="0.5" radius="25" threshold="0.5"/>
        <bloom enabled="1" intensity="0.050000000000000003" radius="0.0050000000000000001"/>
        <color-grading exposure="0.14999999999999999" tone-mapping="Clamp"/>
        <debug flags="0" stop-updates="0"/>
        <eye-dome-lighting enabled="1" eye-dome-lighting-distance="1" eye-dome-lighting-strength="1000"/>
        <navigation-sync view-frustum-visualization-enabled="1" view-sync-mode="0"/>
        <debug-settings depthmap-corner="2" depthmap-enabled="0" depthmap-size="0.20000000000000001"/>
        <axis3d defaultViewportSize="40" horizontal="End" maxViewportRatio="0.5" minViewportRatio="0.06" mode="Crs" vertical="Top"/>
        <map-overlay enabled="1"/>
      </qgis3d>"""


def read_palette() -> list[tuple[str, str, float]]:
    rows: list[tuple[str, str, float]] = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for record in csv.DictReader(f):
            rows.append((record["name"], record["color"], float(record["width_mm"])))
    if len(rows) != 172:
        sys.exit(f"trail palette must have 172 rows, found {len(rows)}")
    return rows


def _pin_symbol_ids(symbol, key: str) -> None:
    """Give every symbol layer a deterministic id so builds are byte-identical."""
    for i in range(symbol.symbolLayerCount()):
        symbol.symbolLayer(i).setId(
            "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"{key}|layer{i}")) + "}"
        )


def make_2d(
    rows: list[tuple[str, str, float]],
    color_override: str | None = None,
    width_override: str | None = None,
) -> QgsCategorizedSymbolRenderer:
    """2D categorized renderer on ``name`` from the CSV palette."""
    cats = []
    for name, color, width in rows:
        sym = QgsLineSymbol.createSimple(
            {
                "color": color_override or color,
                "width": width_override or f"{width}",
                "capstyle": "round",
                "joinstyle": "round",
            }
        )
        _pin_symbol_ids(sym, f"tmnp-2d:{name}")
        cats.append(QgsRendererCategory(name, sym, name))
    r = QgsCategorizedSymbolRenderer("name", cats)
    src = QgsLineSymbol.createSimple({"color": "#999999", "width": "0.26"})
    _pin_symbol_ids(src, "tmnp-2d:__source__")
    r.setSourceSymbol(src)
    return r


def make_3d(rows: list[tuple[str, str, float]]) -> QgsCategorized3DRenderer:
    """3D categorized renderer: one metalrough line per trail, terrain-clamped."""

    def line3d(color: str) -> QgsLine3DSymbol:
        s = QgsLine3DSymbol()
        s.setWidth(3.6)
        s.setOffset(20)
        s.setAltitudeClamping(Qgs3DTypes.AltClampTerrain)
        s.setAltitudeBinding(Qgs3DTypes.AltBindVertex)
        m = QgsMetalRoughMaterialSettings()
        m.setBaseColor(QColor(color))
        m.setMetalness(0.05)
        m.setRoughness(0.55)
        s.setMaterialSettings(m)
        return s

    r = QgsCategorized3DRenderer()
    r.setClassAttribute("name")
    for name, color, _width in rows:
        r.addCategory(Qgs3DRendererCategory(name, line3d(color)))
    r.setSourceSymbol(line3d("#888888"))
    return r


def find_layer(p: QgsProject, part: str):
    """First layer whose name contains ``part``; None when absent."""
    for ly in p.mapLayers().values():
        if part in ly.name():
            return ly
    return None


def canonical_group(layer_name: str) -> str | None:
    if layer_name == TRAIL_LAYER_NAME or layer_name in ("Tracks", "Unnamed trails"):
        return "Paths"
    if DEM_PART in layer_name or CONTOURS_PART in layer_name:
        return "Elevation"
    if layer_name in (OSM_LAYER_NAME, AERIAL_LAYER_NAME):
        return "Basemaps"
    if (
        "Table Mountain NP boundary" in layer_name
        or "TMNP crop extent" in layer_name
        or layer_name in ("tiles_grid", "land_coast_only")
    ):
        return "Shapes"
    return None


def enforce_tree(p: QgsProject) -> None:
    """Ensure the canonical groups exist and every layer sits under its group."""
    root = p.layerTreeRoot()
    for gname in GROUP_ORDER:
        if root.findGroup(gname) is None:
            root.addGroup(gname)
    for ly in p.mapLayers().values():
        group_name = canonical_group(ly.name())
        if group_name is None:
            continue
        group = root.findGroup(group_name)
        node = root.findLayer(ly.id())
        if node is None or node.parent() is not group:
            if node is not None:
                node.parent().removeChildNode(node)
            group.addLayer(ly)
    trail_node = root.findLayer(find_layer(p, TRAIL_LAYER_NAME).id())
    paths = root.findGroup("Paths")
    if (
        trail_node is not None
        and paths is not None
        and paths.children().index(trail_node) != 0
    ):
        paths.removeChildNode(trail_node)
        paths.insertLayer(0, find_layer(p, TRAIL_LAYER_NAME))


def enforce_theme_records(p: QgsProject) -> None:
    """Rebuild the four map themes deterministically; saved baseline = Inspection."""
    root = p.layerTreeRoot()
    mtc = p.mapThemeCollection()

    for gname in ("Paths", "Shapes", "Basemaps"):
        g = root.findGroup(gname)
        if g is not None:
            g.setItemVisibilityChecked(True)
    el = root.findGroup("Elevation")
    if el is not None:
        el.setItemVisibilityChecked(False)

    def set_vis(part: str, visible: bool) -> None:
        ly = find_layer(p, part)
        if ly is None:
            return
        node = root.findLayer(ly.id())
        if node is not None:
            node.setItemVisibilityChecked(visible)

    def set_all(visible: bool) -> None:
        for ly in p.mapLayers().values():
            node = root.findLayer(ly.id())
            if node is not None:
                node.setItemVisibilityChecked(visible)

    def snapshot(name: str) -> None:
        rec = QgsMapThemeCollection.MapThemeRecord()
        for ly in p.mapLayers().values():
            lr = QgsMapThemeCollection.MapThemeLayerRecord(ly)
            node = root.findLayer(ly.id())
            lr.isVisible = bool(node is not None and node.isVisible())
            rec.addLayerRecord(lr)
        if mtc.hasMapTheme(name):
            mtc.removeMapTheme(name)
        mtc.insert(name, rec)

    def apply_preset(name: str) -> None:
        rec = mtc.mapThemeState(name)
        if rec is None:
            return
        for lr in rec.layerRecords():
            ly = lr.layer()
            if ly is None:
                continue
            node = root.findLayer(ly.id())
            if node is not None:
                node.setItemVisibilityChecked(bool(lr.isVisible))

    # Inspection baseline (mirrors the pre-collapse inspection state; the
    # Elevation group stays hidden, so contours/DEM record as off).
    set_all(False)
    for part in (
        TRAIL_LAYER_NAME,
        "Tracks",
        "Unnamed trails",
        CONTOURS_PART,
        "Table Mountain NP boundary",
        "TMNP crop extent",
        OSM_LAYER_NAME,
        DEM_PART,
    ):
        set_vis(part, True)
    snapshot("Trail Inspection")
    snapshot("Single-part trails")  # single-layer model is filter-driven

    # Aerial view: only the CoCT aerial.
    set_all(False)
    set_vis("City of Cape Town", True)
    snapshot("Aerial Imagery")

    # Terrain theme: nothing visible, all records off.
    set_all(False)
    snapshot("3D terrain texture")

    # Saved baseline = inspection.
    apply_preset("Trail Inspection")


def enforce_basemaps(p: QgsProject) -> None:
    aerial = find_layer(p, "City of Cape Town")
    osm = find_layer(p, OSM_LAYER_NAME)
    if aerial is None or osm is None:
        sys.exit("project is missing the aerial or OSM basemap layer")
    if aerial.source() != AERIAL_WMS_SOURCE:
        aerial.setDataSource(AERIAL_WMS_SOURCE, aerial.name(), "wms")
    if osm.source() != OSM_XYZ_SOURCE:
        osm.setDataSource(OSM_XYZ_SOURCE, osm.name(), "wms")


def relativize_paths(xml_text: str) -> str:
    """Rewrite local source paths to be project-relative.

    Done as a post-write text patch on purpose: calling ``setDataSource()``
    on the trail layer during the build silently drops the serialised 3D
    renderer (verified), so local paths are relativised in the XML instead of
    through the layer API. The project directory is ``qgis/``, so a source
    under the repo root becomes ``../data/...``. This covers the maplayer
    ``<datasource>`` elements, the ``<layer-tree-layer source=...>`` nodes and
    the atlas map's ``coverageLayerSource`` -- every place QGIS writes the
    resolved absolute path.
    """
    return xml_text.replace(str(ROOT) + "/", "../")


def canonicalize_category_uuids(xml_text: str) -> str:
    """Replace renderer-v2 category ``uuid`` attributes with deterministic ones.

    QGIS assigns a fresh random UUID every time a categorized renderer is
    constructed, so two builds would otherwise differ only in these
    attributes. A deterministic uuid5 over (value, symbol index) makes the
    artifact byte-reproducible. The 3D renderer categories have no uuid, and
    other renderers (Tracks, boundary, ...) keep canonical uuids too since
    they are derived from the same stable input.
    """

    def sub(match: re.Match) -> str:
        tag = match.group(0)
        value = re.search(r'\bvalue="([^"]*)"', tag)
        symbol = re.search(r'\bsymbol="([^"]*)"', tag)
        key = "{}|{}".format(
            value.group(1) if value else "",
            symbol.group(1) if symbol else "",
        )
        new_uuid = "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, "tmnp-trail:" + key)) + "}"
        return re.sub(r'\buuid="[^"]*"', 'uuid="' + new_uuid + '"', tag, count=1)

    return re.sub(r"<category\b[^>]*\buuid=\"[^\"]*\"[^>]*/>", sub, xml_text)


def stamp_qgis3d(xml_text: str, id_by_part: dict[str, str]) -> str:
    scene = "".join(
        f'            <layer id="{id_by_part[part]}"/>\n'
        for part in SCENE_LAYER_PARTS
        if part in id_by_part
    )
    stamp = QGS3D_STAMP.replace("{dem_layer_id}", id_by_part[DEM_PART]).replace(
        "{scene_layer_ids}", scene
    )
    m = re.search(r"<qgis3d>.*?</qgis3d>", xml_text, re.DOTALL)
    if not m:
        sys.exit("no <qgis3d> block found in the written project")
    return xml_text[: m.start()] + stamp + xml_text[m.end() :]


def patch_layerset(xml_text: str, trail_id: str, contours_id: str) -> str:
    """Force the atlas map's LayerSet to coverage + contours (relative)."""
    ls = re.search(r"<LayerSet>.*?</LayerSet>", xml_text, re.DOTALL)
    if ls is None:
        return xml_text
    new_ls = (
        "<LayerSet>\n"
        f'          <Layer name="{TRAIL_LAYER_NAME}" provider="ogr" source="{TRAIL_SRC}">{trail_id}</Layer>\n'
        f'          <Layer name="contours_2m_within_bound" provider="ogr" source="{CONTOURS_SRC}">{contours_id}</Layer>\n'
        "        </LayerSet>"
    )
    return xml_text[: ls.start()] + new_ls + xml_text[ls.end() :]


def scrub_save_attrs(xml_text: str) -> str:
    """Drop the save-stamp attributes so two builds are byte-identical."""
    return re.sub(r'\s+save(?:DateTime|User|UserFull)="[^"]*"', "", xml_text, count=3)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Enforce and write the QGIS project")
    ap.add_argument(
        "--input", default=str(DEFAULT_PROJECT), help="project to load (qgz or qgs)"
    )
    ap.add_argument("--output", default=str(DEFAULT_PROJECT), help=".qgs file to write")
    args = ap.parse_args(argv)

    rows = read_palette()

    app = QgsApplication([], False)
    app.initQgis()
    try:
        p = QgsProject()
        if not p.read(args.input):
            sys.exit(f"failed to read project {args.input}")
        out = Path(args.output)

        if p.crs().authid() != PROJECT_CRS:
            p.setCrs(QgsCoordinateReferenceSystem(PROJECT_CRS))

        trails = p.mapLayersByName(TRAIL_LAYER_NAME)
        if len(trails) != 1:
            sys.exit(
                f"expected exactly one '{TRAIL_LAYER_NAME}' layer, found {len(trails)}"
            )
        trail = trails[0]
        if not trail.isValid():
            sys.exit("Hiking Trails layer is not valid")
        if trail.subsetString():
            trail.setSubsetString("")

        # 2D: set the live renderer AND freeze it into the Standard style
        # snapshot (QGIS serialises the current style's snapshot on save).
        trail.setRenderer(make_2d(rows))
        std = QgsMapLayerStyle()
        std.readFromLayer(trail)
        trail.styleManager().addStyle("Standard", std)
        trail.styleManager().setCurrentStyle("Standard")

        enforce_tree(p)
        enforce_theme_records(p)
        enforce_basemaps(p)

        # 3D: headless QGIS cannot restore 3D renderers from XML, so rebuild
        # it live on every run. It must be the last change to the trail layer
        # -- setDataSource() on it silently drops the 3D renderer from the
        # serialised output -- so local paths are relativised as a post-write
        # XML patch instead (relativize_datasources below).
        r3d = make_3d(rows)
        r3d.setLayer(trail)
        trail.setRenderer3D(r3d)
        if trail.renderer3D() is None:
            sys.exit("3D renderer failed to attach to the trail layer")

        macro_src = MACRO_PATH.read_text(encoding="utf-8")
        p.writeEntry("Macros", "/pythonCode", macro_src)

        if not p.write(str(out)):
            sys.exit("project write failed")

        xml_text = out.read_text(encoding="utf-8", errors="replace")

        id_by_part = {part: find_layer(p, part).id() for part in SCENE_LAYER_PARTS}
        dem_layer = find_layer(p, DEM_PART)
        contours_layer = find_layer(p, CONTOURS_PART) or find_layer(p, "contours_2m")
        if dem_layer is None:
            sys.exit("3D terrain DEM layer not found")
        id_by_part[DEM_PART] = dem_layer.id()
        if contours_layer is None:
            sys.exit("contours layer not found for the atlas LayerSet")
        contours_id = contours_layer.id()

        xml_text = scrub_save_attrs(xml_text)
        xml_text = stamp_qgis3d(xml_text, id_by_part)
        xml_text = patch_layerset(xml_text, trail.id(), contours_id)
        xml_text = relativize_paths(xml_text)
        xml_text = canonicalize_category_uuids(xml_text)
        out.write_text(xml_text, encoding="utf-8")

        print(f"wrote {out} ({out.stat().st_size} bytes, sha256 {sha256(out)[:16]}…)")
        return 0
    finally:
        app.exitQgis()


if __name__ == "__main__":
    sys.exit(main())
