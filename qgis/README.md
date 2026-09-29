# QGIS

`qgis/table_mountain_3D.qgs` is a build artifact, not a hand-saved file. `scripts/build_project.py` loads it headlessly, applies the canonical state, and writes plain XML. `scripts/verify_project.py` is the pre-commit gate for the artifact. Rebuilding twice from unchanged inputs produces a byte-identical file (same `sha256`). That property keeps the committed project diff reviewable.

## Build the project

```bash
just build
```

The underlying script accepts `--input` and `--output`, defaulting to `qgis/table_mountain_3D.qgs`. Pass `--input qgis/table_mountain_3D.qgz` to migrate a legacy `.qgz`. The build enforces:

- project CRS `EPSG:32734`.
- the layer tree (`Elevation` / `Paths` / `Shapes` / `Basemaps`) with `Hiking Trails` first under `Paths`.
- the 2D categorized trail renderer rebuilt from `styles/trail_colors.csv` (172 categories on `name`), also frozen into the `Standard` named style (QGIS serialises the current style's snapshot on save).
- the 3D categorized trail renderer from the same palette (metalrough lines, terrain-clamped). Headless QGIS cannot restore 3D renderers from XML, so the build re-creates it live every run and verification reads the serialised block.
- the four map themes (`3D terrain texture`, `Aerial Imagery`, `Trail Inspection`, `Single-part trails`).
- basemap sources: the CoCT aerial as the MapProxy WMS endpoint in `EPSG:32734` (layer `coct_aerial`, MapProxy cache grid `utm34s`), OSM as the cached MapProxy XYZ tiles.
- relative local paths (`../data/...`) throughout the XML so the project survives a move or clone.
- `trail_presentation_macro.py` embedded verbatim in the `Macros` section.
- the canonical 3D scene XML (terrain map-theme `3D terrain texture`, `texture-size="512"`, bloom, colour grading, eye-dome lighting, camera) with layer ids resolved by name, and a canonical atlas `LayerSet`.

## Run the project gate

```bash
just verify-project
```

This runs at commit and push time as the `verify-project` pre-commit hook. It exits non-zero with a named failure when an invariant drifts. A GUI save can drop the 3D renderer or rewrite the 3D scene. Fix the drift by rebuilding with `just build`.

## GUI saves and side files

Every GUI save in QGIS 3.22 or later writes a `<name>.qgs~` backup file and a `<name>_attachments.zip` archive next to the project. You cannot disable either one. Both are regenerable, so they are gitignored (`*.qgs~`, `*_attachments.zip`) and never committed.

The tracked `.qgs` is always the output of `scripts/build_project.py`. If a GUI save drifts the tracked file, rebuild it. Do not commit the GUI version.

```bash
just build
```

## Basemaps and attribution

- `OpenStreetMap`: cached XYZ tiles from the local MapProxy (`tiles/1.0.0/osm/webmercator`). OSM attribution is required in any published map, render, or export.
- `City of Cape Town Aerial Photography (2026 January)`: restricted CoCT imagery served locally through MapProxy WMS (`coct_aerial`, fetched in `EPSG:32734`). Do not publish restricted imagery until the intended commercial or non-commercial use is confirmed.

## Native QGIS features per layer

Each layer expresses its rendering and interaction with the native QGIS feature that fits it. Nothing is emulated by scripts or extra layers.

| Layer / group | Data source | Native feature |
|---|---|---|
| Named trails | `../data/vector/osm/tm_hiking_trails_dissolved.gpkg` | Single categorized layer. 2D and 3D categorized renderer (QGIS 4.2). Subset-string filter macros for isolation and single-part filtering. Named styles. Map themes |
| Park boundary | `../data/vector/osm/tmnp_relation_338191.gpkg` | Styled vector layer. Clip source for the Processing rebuild model |
| Crop extent | `../data/vector/osm/tmnp_extent_north_up.gpkg` | Styled layer. Textured overlay in the 3D scene |
| Contours | `../data/vector/coct/contours_2m_within_bound.gpkg` | Styled layer included in themes |
| Terrain / DEM | `../data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif` | 3D terrain elevation source. Theme-driven terrain texture (`map-theme`, `texture-size="512"`). Overview sidecars |
| Basemaps | MapProxy `coct_aerial` WMS (`EPSG:32734`) + OSM XYZ | WMS / XYZ providers with a local cache |
| Inspection rasters + raw OSM layers | `../data/imagery/…`, `../data/osm/…` | `Trail Inspection` map theme |
| Per-trail output | coverage layer (`Hiking Trails`) | Print-layout Atlas with coverage-driven pages, data-defined titles, feature scaling |
| 3D scene | project | Terrain, camera pose (editable in the 4.2 camera dialog), MSAA / bloom / colour grading, categorized 3D line symbols |

## Declined features

Features evaluated and deliberately not adopted, each with the reason. No feature is used for its own sake.

- `.qgz` storage: breaks reviewable diffs. Plain `.qgs` XML is the artifact.
- GeoPackage-embedded styles (`gpkg_style`): splits the palette truth away from `styles/trail_colors.csv`.
- Virtual layers / embedded-layers list: no aggregate-query need. The data is on disk.
- Temporal rendering: the scene is static.
- Vector tiles: offline, version-pinned GeoPackage data is the point. XYZ already serves OSM context.
- PostgreSQL project storage / project versioning (QGIS 4.0): git is the version system.
- Atlas "limit coverage rendering to current feature" (QGIS 4.0): pages intentionally show surrounding trail context. Re-evaluate only if per-page isolation is wanted.
- Layer notes for provenance: provenance lives in `trail_datasets.manifest.json` and the `data/` READMEs.
- Skybox-environment lighting (QGIS 4.2): not Python-bound in 4.2.2. The current bloom / colour-grading / MSAA look suffices.
