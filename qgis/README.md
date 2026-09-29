# QGIS

`qgis/table_mountain_3D.qgs` is a **build artifact**, not a hand-saved file:
`scripts/build_project.py` loads it headlessly, enforces the canonical state,
and writes plain XML; `scripts/verify_project.py` is the pre-commit gate.
Rebuilding twice from unchanged inputs produces a byte-identical file
(`sha256`), which is what makes the committed project diff reviewable.

## Build

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/build_project.py
```

`--input`/`--output` default to `qgis/table_mountain_3D.qgs`; pass
`--input qgis/table_mountain_3D.qgz` to migrate a legacy `.qgz`. The build
enforces:

- project CRS `EPSG:32734`;
- the layer tree (`Elevation` / `Paths` / `Shapes` / `Basemaps`) with
  `Hiking Trails` first under `Paths`;
- the 2D categorized trail renderer rebuilt from `styles/trail_colors.csv`
  (172 categories on `name`), also frozen into the `Standard` named style
  (QGIS serialises the current style's snapshot on save);
- the 3D categorized trail renderer from the same palette (metalrough lines,
  terrain-clamped). Headless QGIS cannot restore 3D renderers from XML, so the
  build re-creates it live every run and verification reads the serialised
  block;
- the four map themes (`3D terrain texture`, `Aerial Imagery`,
  `Trail Inspection`, `Single-part trails`);
- basemap sources: the CoCT aerial as the MapProxy WMS endpoint in
  `EPSG:32734` (layer `coct_aerial`, MapProxy cache grid `utm34s`), OSM as the
  cached MapProxy XYZ tiles;
- relative local paths (`../data/...`) throughout the XML so the project
  survives a move or clone;
- `trail_presentation_macro.py` embedded verbatim in the `Macros` section;
- the canonical 3D scene XML (terrain map-theme `3D terrain texture`,
  `texture-size="512"`, bloom, colour grading, eye-dome lighting, camera) with
  layer ids resolved by name, and a canonical atlas `LayerSet`.

## Verify

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/verify_project.py
```

Run on every commit and push as the `verify-project` pre-commit hook. Exits
non-zero with a named failure if any invariant drifted (e.g. a GUI save that
drops the 3D renderer or rewrites the 3D scene); fix with the build script.

## GUI saves and side files

Every GUI save in QGIS ≥ 3.22 writes a `<name>.qgs~` backup file and a
`<name>_attachments.zip` archive next to the project. Neither can be disabled.
Both are regenerable, so they are gitignored (`*.qgs~`, `*_attachments.zip`)
and never committed. The tracked `.qgs` is always the output of
`scripts/build_project.py`; if a GUI save drifts the tracked file, reconcile it
by rebuilding rather than by committing the GUI version:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/build_project.py
```

## Basemaps and attribution

- `OpenStreetMap` — cached XYZ tiles from the local MapProxy
  (`tiles/1.0.0/osm/webmercator`). OSM attribution is required in any
  published map, render, or export.
- `City of Cape Town Aerial Photography (2026 January)` — restricted CoCT
  imagery served locally through MapProxy WMS (`coct_aerial`, fetched in
  `EPSG:32734`). Do not publish restricted imagery until the intended
  commercial or non-commercial use is confirmed.

## Native QGIS features per layer

Each layer expresses its rendering and interaction with the native QGIS
feature that fits it; nothing is emulated by scripts or extra layers.

| Layer / group | Data source | Native feature |
|---|---|---|
| Named trails | `../data/vector/osm/tm_hiking_trails_dissolved.gpkg` | Single categorized layer; 2D **and** 3D categorized renderer (QGIS 4.2); subset-string filter macros for isolation and single-part filtering; named styles; map themes |
| Park boundary | `../data/vector/osm/tmnp_relation_338191.gpkg` | Styled vector layer; clip source for the Processing rebuild model |
| Crop extent | `../data/vector/osm/tmnp_extent_north_up.gpkg` | Styled layer; textured overlay in the 3D scene |
| Contours | `../data/vector/coct/contours_2m_within_bound.gpkg` | Styled layer included in themes |
| Terrain / DEM | `../data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif` | 3D terrain elevation source; theme-driven terrain texture (`map-theme`, `texture-size="512"`); overview sidecars |
| Basemaps | MapProxy `coct_aerial` WMS (`EPSG:32734`) + OSM XYZ | WMS / XYZ providers with a local cache |
| Inspection rasters + raw OSM layers | `../data/imagery/…`, `../data/osm/…` | `Trail Inspection` map theme |
| Per-trail output | coverage layer (`Hiking Trails`) | Print-layout Atlas with coverage-driven pages, data-defined titles, feature scaling |
| 3D scene | project | Terrain, camera pose (editable in the 4.2 camera dialog), MSAA / bloom / colour grading, categorized 3D line symbols |

## Declined features

Evaluated and deliberately not adopted (no feature used for its own sake),
each with the reason:

- `.qgz` storage — breaks reviewable diffs; plain `.qgs` XML is the artifact.
- GeoPackage-embedded styles (`gpkg_style`) — would split the palette truth
  from `styles/trail_colors.csv`.
- Virtual layers / embedded-layers list — no aggregate-query need; the data
  is on disk.
- Temporal rendering — the scene is static.
- Vector tiles — offline, version-pinned GeoPackage data is the point; XYZ
  already serves OSM context.
- PostgreSQL project storage / project versioning (QGIS 4.0) — git is the
  version system.
- Atlas "limit coverage rendering to current feature" (QGIS 4.0) — pages
  intentionally show surrounding trail context; re-evaluate only if
  per-page isolation is wanted.
- Layer notes for provenance — provenance lives in
  `trail_datasets.manifest.json` and the `data/` READMEs.
- Skybox-environment lighting (QGIS 4.2) — not Python-bound in 4.2.2; the
  current bloom / colour-grading / MSAA look suffices.
