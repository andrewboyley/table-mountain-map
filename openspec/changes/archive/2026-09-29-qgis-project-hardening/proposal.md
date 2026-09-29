## Why

The QGIS project renders a 3.8 GB stripped TIFF with no overviews, carries 172
ad-hoc trail layers with no reproducible build, and documents a crop rectangle
that exists nowhere on disk. Each of these was measured, not guessed, and each
has a QGIS-native fix that the project is currently not using.

The project already does several things right — relative paths, spatial
indexes, a projected CRS in metres — so this change is about the specific
gaps that were verified, not a general rewrite.

## What Changes

### Model crop extent becomes north-up and singular

The README documents a minimum-area **rotated** rectangle (15,350.59 ×
49,917.29 m, 766.2598 km², long axis 5.0454° off grid north). That file does
not exist. What exists is `qgis/bound.shp` — a **north-up** 20,203.79 ×
52,136.38 m (1053.3526 km²) rectangle named `bound (model extent)`, sitting in
the QGIS directory rather than the data directory.

The north-up rectangle is the one we want, so the rotated rectangle is dropped
and the north-up one is promoted to a real, versioned, correctly-named layer.

**BREAKING**: the published crop-extent values change. Every published
dimension, area and corner coordinate in `README.md` describes the rotated
rectangle and becomes wrong. Consumers reading those numbers get a rectangle
37.5% larger in area.

The rectangle is also **stale**. It was built at 14:56 on 2026-09-25; the OSM
extract it came from was re-clipped at 15:00 the same day and now reaches
**508.5 m further north**. Impact today is nil — every vertex of all 2,162
trail features and the park boundary was tested against the rectangle and
**zero** fall outside — but the rectangle must be regenerated so it describes
the current extract rather than a superseded one.

### Rasters get overviews and internal tiling

All three large rasters are stripped TIFFs with no `.ovr` sidecar, so GDAL
reads enormous swathes of a 4 GB file to draw any given view.

| Raster | Dimensions | Size | Overviews |
|---|---|---|---|
| `aerial_1m.tif` | 19,305 × 51,585 (~996 Mpx) | 3.8 GB | none |
| `aerial_5m.tif` | 4,041 × 10,427 (42 Mpx) | 160 MB | none |
| `…_within_bound.tif` | 4,042 × 10,428 (42 Mpx) | — | none |

Overviews are written as sidecars, so the originals are not rewritten and the
change is reversible by deleting the `.ovr`.

### Trail presentation uses native QGIS features

172 layers exist in a `Hiking Trails` group. The goal — isolate one trail
without touching 171 other checkboxes — is what QGIS's **mutually exclusive
group** does natively, in one click, on the group that already exists.

Also in scope: **multiple styles per layer**, so different looks no longer
require duplicating a layer; **visibility presets**, so whole map
configurations switch with one click; and a **categorized renderer on `name`**,
so the legend itself becomes the trail picker.

A full collapse from 172 layers to 1 is offered as a **BREAKING** option and is
not assumed — see the open question in the design.

### 3D scene uses the 4.2 feature set

The project is named `table_mountain_3D` and runs QGIS 4.2, which shipped a
large 3D feature set this project does not use: terrain settings, the camera
controls dialog for placing the camera in map coordinates, physically based
materials, skybox environmental lighting, colour grading, bloom and MSAA.

The CRS choice already pays off here. Terrain `Max ground error` is
interpreted in map units, and in a lat/lon project the minimum allowed value
(0.1) is enormous in degrees, pinning terrain to coarse tiles
([QGIS#61384](https://github.com/qgis/QGIS/issues/61384)). At `EPSG:32734`
the values are already in metres and the problem cannot occur.

### Per-trail map pages via Atlas

Each of the 172 trails has a bounding box, so Atlas can drive one layout page
per trail from a coverage layer instead of 172 hand-built maps.

### The trail pipeline becomes reproducible

The trail work that produced `tm_hiking_trails_dissolved.gpkg` and
`tm_trail_supplement.gpkg` is documented nowhere — no build script, no
checksum, no README line. It is the most fragile artefact in the repository by
the project's own stated standard, which `.gitignore` states as *"tracked is
the reproducible definition of the project"*.

Notably, the crop rectangle that *was* lost was recoverable, because four
decimal places of its dimensions survive in the README. The trail data is
present on disk and **unrecoverable**, because nothing records how it was
made. That asymmetry is the argument for this part of the change.

The original pipeline lived in QGIS Processing — the lost MBR was computed by
`native:orientedminimumboundingbox`. The trail pipeline drifted to shell
`ogr2ogr` plus 172 individual API calls. A Processing model restores both
runnability from the GUI and reproducibility as a side effect.

### Documentation stops describing files that do not exist

`data/README.md` names `terrain/` (the directory is `elevation/`), a
`vector/coct/README.md` that is absent, an 8,100,239-byte PBF (the real file is
9,390,457 bytes under a different name), and a five-layer GeoPackage of
154,377 features that does not exist. Four references to absent files, zero
references to files that are present.

Note the docs are **stale, not fabricated** — every geographic claim in
`README.md` was tested and holds to four decimal places, and the 2 m contour
clip really does describe the data. The knowledge is sound; the inventory is
wrong.

## Capabilities

### New Capabilities

- `model-crop-extent`: the single north-up rectangle that all raster and
  vector derivatives are cropped to, its derivation from the OSM extract, and
  its published dimensions.
- `raster-performance`: overview and tiling requirements that keep large
  rasters interactive at every zoom level.
- `trail-layer-presentation`: isolating, styling and switching individual
  trails in the layer tree using native QGIS features rather than layer
  proliferation.
- `terrain-3d-scene`: the 3D map view configuration for the POV render —
  terrain, camera placement, materials, lighting and post-processing.
- `trail-atlas-outputs`: generating per-trail map pages from the trail extents.
- `osm-trail-pipeline`: rebuilding the trail datasets from the OSM extract
  deterministically and verifying them by checksum.
- `project-provenance`: documentation that names only files which exist, and
  derived data that is traceable to the command that produced it.

### Modified Capabilities

None — `openspec/specs/` is empty, so there is no existing behaviour to amend.

## Impact

**Files added**

- A north-up crop-extent GeoPackage under `data/vector/`, replacing
  `qgis/bound.shp` as the authoritative rectangle.
- `.ovr` sidecars for the three large rasters.
- A Processing model and/or build script for the trail pipeline.
- Checksums for the trail datasets.
- An Atlas layout and a coverage layer.
- Saved QGIS visibility presets, layer styles and a project macro.

**Files modified**

- `qgis/table_mountain_3D.qgz` — layer tree, group settings, styles,
  presets, 3D view config, Atlas.
- `README.md` — the crop-rectangle table becomes north-up; the four missing
  file references are corrected.
- `data/README.md` — `terrain/` → `elevation/`, PBF identity, GeoPackage
  inventory.

**Explicitly out of scope**

- Replacing the PBF → `ogr2ogr` → GeoPackage workflow with vector tiles or
  QuickOSM. Those suit basemap-style rendering and live targeted queries; this
  project needs offline, version-pinned, reproducible vector data. The existing
  approach is correct and stays.
- Initialising a git repository. It is the missing half of the
  `.gitignore` philosophy and worth doing, but it is a repo-level decision
  unrelated to QGIS configuration, so it is flagged rather than folded in.
- The 508.5 m of OSM extract north of the current rectangle. It lies outside
  the park and is already excluded by the park clip; it is regenerated with the
  rectangle, not separately investigated.

**Risks**

- Adding overviews to a 3.8 GB raster is long-running and disk-intensive.
  Sidecars are removable, so it is reversible.
- Toggling 172 layers has crashed the QGIS instance once already, during
  remove/re-add churn. Layer-tree surgery should be done by a saved macro
  rather than incremental API calls, both for crash-safety and speed.
- `aerial_5m.tif` currently matches `bound.shp` to +0.00 m. Changing the
  rectangle's source risks altering the alignment of already-built rasters;
  the regenerated rectangle must be compared against the raster geotransforms
  before anything downstream is rebuilt.
