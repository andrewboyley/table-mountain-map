#!/usr/bin/env python3
"""Trail presentation configuration macro.

Applies the whole trail-group presentation in one invocation, using native
QGIS features only (design.md decision 6):

  * the "Hiking Trails" group becomes a mutually exclusive group, so checking
    one trail clears the other 171 in a single action;
  * every trail layer carries two NAMED styles ("Standard" and "Emphasis")
    served by the same data source, so switching looks never duplicates layers;
  * every trail legend entry is labelled with the trail's OSM name (parsed
    from its subset filter), not a layer identity;
  * duplicate display labels are surfaced, never silently merged;
  * each trail node records its part count as the tree-node custom property
    `trail/part_count`;
  * three visibility presets are (re)created from explicit, deterministic
    states: "Trail Inspection", "Aerial Imagery" and "Single-part trails"
    (the last shows exactly the 144 single-part trails, while multi-part
    trails stay reachable through the mutually exclusive group).

The macro is idempotent and adds no layers: the project layer count is
unchanged after a run.

Note on QGIS 4.2.2: QgsMapThemeCollection.createThemeFromCurrentState() and
applyTheme() hard-crash this build (segfault, reproduced with three clean
vector layers), so presets are captured as hand-built MapThemeRecords and
applied by writing tree node visibility directly. Both paths are native
project state: the presets save and reload with the project.

Stored in the project's Macros section under `Macros` / `pythonCode`. Invoke it
from the Python Console in one call:

    exec(QgsProject.instance().readEntry('Macros', '/pythonCode')[0])
"""

from qgis.core import (
    QgsProject,
    QgsMapLayerStyle,
    QgsMapThemeCollection,
)
from PyQt6.QtGui import QColor

TRAIL_GROUP = "Hiking Trails"
PRESET_INSPECTION = "Trail Inspection"
PRESET_AERIAL = "Aerial Imagery"
PRESET_SINGLE_PART = "Single-part trails"
INSPECTED_TRAIL = "Kasteelspoort Path"


def _parse_subset_name(subset: str) -> str | None:
    """Extract the OSM name from a QGIS-generated `name = 'X'` subset.

    QGIS escapes apostrophes by doubling them, so `'Smuts'' Track'` means the
    name `Smuts' Track`.
    """
    body = subset.strip()
    if not (body.startswith("name = '") and body.endswith("'")):
        return None
    inner = body[len("name = '") : -1]
    return inner.replace("''", "'")


def _run() -> None:
    p = QgsProject.instance()
    root = p.layerTreeRoot()

    group = root.findGroup(TRAIL_GROUP)
    if group is None:
        raise RuntimeError(
            f"trail group {TRAIL_GROUP!r} not found; nothing was changed"
        )
    trail_nodes = [c for c in group.children() if c.nodeType() == 1]
    if len(trail_nodes) != 172:
        raise RuntimeError(
            f"expected 172 trail layers in {TRAIL_GROUP!r}, found {len(trail_nodes)}"
        )

    # --- part counts keyed by OSM name, from the dissolved dataset ----------
    # (path derived from the project's own trail layers, not hard-coded)
    from osgeo import ogr

    probe_source = trail_nodes[0].layer().source().split("|", 1)[0]
    ds = ogr.Open(probe_source)
    layer = ds.GetLayerByName("hiking_trails")
    part_counts: dict[str, int] = {}
    for f in layer:
        part_counts[f.GetField("name")] = int(f.GetField("n_parts") or 1)
    ds = None

    # --- mutually exclusive group -------------------------------------------
    group.setIsMutuallyExclusive(True)

    # --- per-trail named styles, labels and part-count properties -------------
    labels: list[str] = []
    for node in trail_nodes:
        lyr = node.layer()
        subset = lyr.subsetString()
        osm_name = _parse_subset_name(subset)
        if osm_name is None:
            print(f"WARN: {node.name()}: subset not parsed: {subset!r}")
            osm_name = node.name()
        labels.append(osm_name)

        # Legend label = OSM name (layer identity never shows alone).
        node.setName(osm_name)
        if lyr.name() != osm_name:
            lyr.setName(osm_name)

        # Part count as machine-checkable tree metadata.
        n_parts = part_counts.get(osm_name, 1)
        node.setCustomProperty("trail/part_count", n_parts)

        # Named styles: keep the original as "Standard", add "Emphasis".
        sm = lyr.styleManager()
        if "Emphasis" not in sm.styles():
            orig_rend = lyr.renderer().clone()
            symb = lyr.renderer().symbol()
            if symb is not None:
                symb.setColor(QColor(203, 24, 24))
                symb.setWidth(1.8)
            emph = QgsMapLayerStyle()
            emph.readFromLayer(lyr)
            lyr.setRenderer(orig_rend)
            if "Standard" not in sm.styles():
                std = QgsMapLayerStyle()
                std.readFromLayer(lyr)
                sm.addStyle("Standard", std)
            sm.addStyle("Emphasis", emph)
            sm.setCurrentStyle("Standard")

    # --- duplicate label surface ----------------------------------------------
    seen: dict[str, int] = {}
    dupes = []
    for label in labels:
        seen[label] = seen.get(label, 0) + 1
        if seen[label] == 2:
            dupes.append(label)
    if dupes:
        print(f"WARN: duplicate trail labels: {dupes}")

    # --- visibility presets (manual records; capture API segfaults here) ------
    mtc = p.mapThemeCollection()

    def set_layer_visible(name: str, visible: bool) -> None:
        found = p.mapLayersByName(name)
        if not found:
            print(f"WARN: layer not found: {name!r}")
            return
        node = root.findLayer(found[0].id())
        if node is not None:
            node.setItemVisibilityChecked(visible)

    def snapshot_preset(name: str, exclusive: bool = True) -> None:
        """Record every project layer's current tree visibility.

        `exclusive` is the trail-group exclusivity to apply afterwards: the
        single-part preset is captured with exclusivity OFF so the whole
        single-part set can be checked at once.
        """
        group.setIsMutuallyExclusive(exclusive)
        rec = QgsMapThemeCollection.MapThemeRecord()
        for lyr in p.mapLayers().values():
            lr = QgsMapThemeCollection.MapThemeLayerRecord(lyr)
            n = root.findLayer(lyr.id())
            lr.isVisible = bool(n is not None and n.isVisible())
            rec.addLayerRecord(lr)
        if mtc.hasMapTheme(name):
            mtc.removeMapTheme(name)
        mtc.insert(name, rec)

    def apply_preset(name: str) -> None:
        """Apply a recorded preset by writing tree visibility directly.

        The single-part preset disables exclusivity while it is shown (it is
        a filtered list, not an isolation view); every other preset restores
        exclusivity so isolation works in one click.
        """
        if name == PRESET_SINGLE_PART:
            group.setIsMutuallyExclusive(False)
        else:
            group.setIsMutuallyExclusive(True)
        rec = mtc.mapThemeState(name)
        for lr in rec.layerRecords():
            lyr = lr.layer()
            if lyr is None:
                continue
            node = root.findLayer(lyr.id())
            if node is not None:
                node.setItemVisibilityChecked(bool(lr.isVisible))
        group.setItemVisibilityChecked(True)
        aerial_group = root.findGroup("aerial")
        if aerial_group is not None:
            aerial_group.setItemVisibilityChecked(True)

    # --- explicit state A: Trail Inspection -------------------------------------
    # Exactly Kasteelspoort Path checked in the trail group; bulk trail layers
    # and reference layers visible; imagery and basemap hidden.
    for node in trail_nodes:
        node.setItemVisibilityChecked(node.name() == INSPECTED_TRAIL)
    set_layer_visible("Tracks", True)
    set_layer_visible("Unnamed trails", True)
    set_layer_visible("contours_2m_within_bound", True)
    set_layer_visible("Table Mountain NP boundary", True)
    set_layer_visible("TMNP crop extent (north-up)", True)
    set_layer_visible("land_coast_only", False)
    set_layer_visible("tiles_grid", False)
    set_layer_visible("OpenStreetMap (XYZ)", False)
    set_layer_visible("Aerial Imagery 2025Jan", False)
    set_layer_visible("aerial_1m", False)
    set_layer_visible("aerial_5m", False)
    set_layer_visible("table_mountain_contours_2m_interpolated_5m_within_bound", True)

    # Single-part trails: same baseline, only the 144 single-part trails checked.
    # Exclusivity is suspended while this filtered view is captured (and while
    # it is later applied), because a mutually exclusive group allows only one
    # checked child at a time.
    group.setIsMutuallyExclusive(False)
    for node in trail_nodes:
        node.setItemVisibilityChecked(node.customProperty("trail/part_count") == 1)
    group.setItemVisibilityChecked(True)
    snapshot_preset(PRESET_SINGLE_PART, exclusive=False)

    # Back to inspection state, then record it.
    for node in trail_nodes:
        node.setItemVisibilityChecked(node.name() == INSPECTED_TRAIL)
    group.setItemVisibilityChecked(True)
    snapshot_preset(PRESET_INSPECTION)

    # --- explicit state B: Aerial Imagery -----------------------------------------
    for node in trail_nodes:
        node.setItemVisibilityChecked(False)
    set_layer_visible("Tracks", False)
    set_layer_visible("Unnamed trails", False)
    set_layer_visible("contours_2m_within_bound", False)
    set_layer_visible("Table Mountain NP boundary", False)
    set_layer_visible("TMNP crop extent (north-up)", False)
    set_layer_visible("land_coast_only", False)
    set_layer_visible("tiles_grid", False)
    set_layer_visible("OpenStreetMap (XYZ)", False)
    set_layer_visible("Aerial Imagery 2025Jan", False)
    set_layer_visible("table_mountain_contours_2m_interpolated_5m_within_bound", False)
    set_layer_visible("aerial_1m", True)
    set_layer_visible("aerial_5m", False)
    aerial_group = root.findGroup("aerial")
    if aerial_group is not None:
        aerial_group.setItemVisibilityChecked(True)
    snapshot_preset(PRESET_AERIAL)

    # --- restore the inspection state as the saved baseline ----------------------
    apply_preset(PRESET_INSPECTION)

    print(
        f"trail presentation applied: {len(trail_nodes)} layers, "
        f"mutex={group.isMutuallyExclusive()}, "
        f"presets={mtc.mapThemes()}"
    )


_run()
