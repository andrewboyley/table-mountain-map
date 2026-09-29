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

## Basemaps and attribution

- `OpenStreetMap` — cached XYZ tiles from the local MapProxy
  (`tiles/1.0.0/osm/webmercator`). OSM attribution is required in any
  published map, render, or export.
- `City of Cape Town Aerial Photography (2026 January)` — restricted CoCT
  imagery served locally through MapProxy WMS (`coct_aerial`, fetched in
  `EPSG:32734`). Do not publish restricted imagery until the intended
  commercial or non-commercial use is confirmed.
