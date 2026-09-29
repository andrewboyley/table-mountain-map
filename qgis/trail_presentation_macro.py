#!/usr/bin/env python3
"""Trail presentation macro for the single categorized layer.

The trail inventory is one layer ("Hiking Trails") fed by the dissolved OSM
GeoPackage, drawn with a 172-category 2D + 3D categorized renderer. This macro
drives its presentation with native QGIS features only:

  * `isolate(name)` -- filter the layer to one trail and zoom to it;
  * `show_all()` -- clear the filter so every named trail is shown;
  * `show_single_part_trails()` -- filter to the single-part ("n_parts" = 1)
    trail set;
  * `show_aerial_imagery()` -- switch the whole map to the aerial baseline;
  * preset (map theme) rebuild -- "Trail Inspection", "Single-part trails" and
    "Aerial Imagery" are re-created from explicit, deterministic states using
    hand-built MapThemeRecords.

The macro is idempotent and adds no layers: the project layer count is
unchanged after a run.

Note on QGIS 4.2.2: QgsMapThemeCollection.createThemeFromCurrentState() and
applyTheme() hard-crash this build (segfault), so presets are captured as
hand-built MapThemeRecords and applied by writing tree-node visibility directly.
Both paths are native project state: the presets save and reload with the
project. The imported `home` data is untouched.

Stored in the project's Macros section under `Macros` / `pythonCode`. Invoke it
from the Python Console in one call:

    exec(QgsProject.instance().readEntry('Macros', '/pythonCode')[0])
"""

from qgis.core import (
    QgsExpression,
    QgsMapThemeCollection,
    QgsProject,
)

TRAIL_LAYER = "Hiking Trails"
PRESET_INSPECTION = "Trail Inspection"
PRESET_AERIAL = "Aerial Imagery"
PRESET_SINGLE_PART = "Single-part trails"

# Layers that stay visible beside the trail layer in the inspection baseline
# (exact names must match the tree; a renamed layer is resolved by fragment).
CONTEXT_LAYERS = [
    "Tracks",
    "Unnamed trails",
    "Table Mountain NP boundary",
    "TMNP crop extent",
    "OpenStreetMap",
]
AERIAL_FRAGMENT = "City of Cape Town"


def _find_layer(fragment: str):
    """Resolve a layer by exact name, falling back to a substring match."""
    p = QgsProject.instance()
    found = p.mapLayersByName(fragment)
    if found:
        return found[0]
    for layer in p.mapLayers().values():
        if fragment in layer.name():
            return layer
    return None


def _trail_layer():
    p = QgsProject.instance()
    found = p.mapLayersByName(TRAIL_LAYER)
    if not found:
        raise RuntimeError(f"trail layer {TRAIL_LAYER!r} not found; nothing changed")
    return found[0]


def _checked(layer, visible: bool) -> None:
    if layer is None:
        return
    root = QgsProject.instance().layerTreeRoot()
    node = root.findLayer(layer.id())
    if node is not None:
        node.setItemVisibilityChecked(visible)


def _group_checked(name: str, visible: bool) -> None:
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(name)
    if group is not None:
        group.setItemVisibilityChecked(visible)


def _filter_expression(name: str) -> str:
    """QGIS expression selecting exactly one trail by OSM name."""
    return f'"name" = {QgsExpression.quotedValue(name)}'


def _zoom_to(layer) -> None:
    """Best-effort zoom to a layer's (filtered) extent; no-op without a canvas."""
    try:
        from qgis.utils import iface
    except Exception:
        return
    canvas = iface.mapCanvas()
    if canvas is None:
        return
    extent = layer.extent()
    if extent is not None and not extent.isEmpty():
        canvas.setExtent(extent)
        canvas.refresh()


def isolate(name: str) -> None:
    """Show exactly one named trail; every other trail is filtered out."""
    layer = _trail_layer()
    layer.setSubsetString(_filter_expression(name))
    _checked(layer, True)
    _zoom_to(layer)


def show_all() -> None:
    """Clear the trail filter so every named trail is visible again."""
    _trail_layer().setSubsetString("")


def show_single_part_trails() -> None:
    """Restrict to trails forming one unbroken line ('n_parts' = 1)."""
    layer = _trail_layer()
    layer.setSubsetString('"n_parts" = 1')
    _checked(layer, True)
    _zoom_to(layer)


def show_aerial_imagery() -> None:
    """Switch the whole map to the aerial-imagery baseline."""
    _apply_preset(PRESET_AERIAL)


# ----------------------------------------------------------------------------
# preset rebuild (manual MapThemeRecords; capture API segfaults on 4.2.2)
# ----------------------------------------------------------------------------


def _set_all(visible: bool) -> None:
    p = QgsProject.instance()
    root = p.layerTreeRoot()
    for layer in p.mapLayers().values():
        node = root.findLayer(layer.id())
        if node is not None:
            node.setItemVisibilityChecked(visible)


def _snapshot(name: str) -> None:
    p = QgsProject.instance()
    root = p.layerTreeRoot()
    mtc = p.mapThemeCollection()
    record = QgsMapThemeCollection.MapThemeRecord()
    for layer in p.mapLayers().values():
        lr = QgsMapThemeCollection.MapThemeLayerRecord(layer)
        node = root.findLayer(layer.id())
        lr.isVisible = bool(node is not None and node.isVisible())
        record.addLayerRecord(lr)
    if mtc.hasMapTheme(name):
        mtc.removeMapTheme(name)
    mtc.insert(name, record)


def _apply_preset(name: str) -> None:
    p = QgsProject.instance()
    root = p.layerTreeRoot()
    record = p.mapThemeCollection().mapThemeState(name)
    if record is None:
        raise RuntimeError(f"preset {name!r} not found")
    for lr in record.layerRecords():
        layer = lr.layer()
        if layer is None:
            continue
        node = root.findLayer(layer.id())
        if node is not None:
            node.setItemVisibilityChecked(bool(lr.isVisible))


def _rebuild_presets() -> None:
    """Recreate the three presentation presets from explicit states."""
    p = QgsProject.instance()

    # group headers: keep the inspection groups on, Elevation off
    for group_name in ("Paths", "Shapes", "Basemaps"):
        _group_checked(group_name, True)
    _group_checked("Elevation", False)

    # inspection baseline: trail layer + context over OSM, nothing else
    _set_all(False)
    for fragment in [TRAIL_LAYER, *CONTEXT_LAYERS]:
        _checked(_find_layer(fragment), True)
    _snapshot(PRESET_INSPECTION)

    # single-part view shares the baseline; the trail filter does the work
    _snapshot(PRESET_SINGLE_PART)

    # aerial view: only the city aerial
    _set_all(False)
    _checked(_find_layer(AERIAL_FRAGMENT), True)
    _snapshot(PRESET_AERIAL)

    # restore the inspection baseline as the saved state
    _set_all(False)
    for fragment in [TRAIL_LAYER, *CONTEXT_LAYERS]:
        _checked(_find_layer(fragment), True)


def _run() -> None:
    # sanity: the single trail layer must exist before anything else runs
    _trail_layer()
    _rebuild_presets()
    print(
        "trail presentation applied: presets="
        f"{QgsProject.instance().mapThemeCollection().mapThemes()}"
    )


_run()
