# Table Mountain 3D

This project prepares City of Cape Town elevation data, OpenStreetMap context, and a Blender scene for a metrically scaled Table Mountain model.

## Project layout

```text
qgis/                 QGIS project, styles, macro, model, and docs
data/
  osm/                OSM PBF files and extracts
  elevation/          DEM, DTM, contour, and height-map data
  vector/             COCT and OSM vector context
  imagery/            permitted imagery and textures
docs/                 research findings and attribution notes
scripts/              verification and terrain-processing scripts
cache/                temporary processing files
renders/              final images and animation output
blender/              Blender scenes
docker-mapproxy/      local MapProxy service for the basemaps
```

`opencode.json` stays in the project root so OpenCode can find it. `.mcp.json` stays next to it. The two files serve different tool ecosystems. VS Code, Cline, and other MCP clients read `.mcp.json`. OpenCode reads `opencode.json`, which also defines the project slash commands `/verify`, `/check`, `/gates`, and `/commit` plus the shell permission rules. Both stay tracked. The Python environment lives in the root `.venv` directory.

## Restoring local data after a fresh clone

The repository excludes large source and derived binaries on purpose. Restore them from the sources recorded in the `data/` READMEs, then make sure the restored state is correct. Run this from the repository root:

```bash
python3 scripts/verify_data.py
```

The verified trail outputs can be rebuilt with the single QGIS Processing-model command in `data/README.md`. Terrain-source research and access limits are in `docs/terrain_data_findings.md`.

### System requirements

GDAL and osmium are not installed by the venv:

```bash
# Debian/Ubuntu
sudo apt install gdal-bin osmium-tool
# conda
conda install -c conda-forge gdal osmium
```

### The one manual data source

The COCT 2 m contour archive is 753 MB and is not in git. Get it from the [City of Cape Town Open Data Portal](https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::city-of-cape-town-ground-level-map-2m-contours-cct-glm-2019) and save it as `data/vector/coct/GLM_2m_-1536768105596229130.zip`. Then run the checksum command:

```bash
echo adf09db8b963e6814eae2aec63240bf870d31bfcaade46d8db96f50f65c3f880 \
  data/vector/coct/GLM_2m_-1536768105596229130.zip | sha256sum -c -
```

If the portal is unreachable, request the dataset from `city.maps@capetown.gov.za`.

### Make sure a build is correct

```bash
python3 scripts/verify_data.py
```

This makes sure that the SHA-256 of the pinned raw downloads is correct. It makes sure that the feature counts and CRS of every derived layer are correct. It makes sure that the TMNP boundary area matches the recorded value. It makes sure that the QGIS project uses `EPSG:32734` with only relative paths. The relative paths let the project survive a move or clone.

The QGIS project lives at `qgis/table_mountain_3D.qgs` as plain XML. It is a build artifact, not a hand-saved file. `python3 scripts/build_project.py` loads it headlessly, applies the canonical state, and writes plain XML. `python3 scripts/verify_project.py` is the gate that runs at commit time. It loads the `.qgs` headlessly and exits non-zero when any invariant is wrong. Running `build_project.py` twice on unchanged inputs writes byte-identical files, so the project diff stays reviewable.

The clip PBF rebuilds byte-identically. The GeoPackage cannot, because GDAL writes a `last_change` timestamp into `gpkg_contents` on every save. The bytes always differ when the data is identical. That is why the GeoPackage is compared by content and geometry, not by checksum.

You can run the same gates with `just`. `just` rebuilds the project and runs the verification gates. `just check` runs every pre-commit hook on all files. `just verify` builds the contour-DEM intermediates first, then runs the three verification scripts. The `justfile` lists every recipe.

## Scripts

Every tracked script is load-bearing. Each one either backs a pre-commit or push gate, or is a documented data-pipeline step.

| Script | Purpose |
|---|---|
| `scripts/build_project.py` | Rebuild `qgis/table_mountain_3D.qgs` headlessly. Byte-identical for unchanged inputs |
| `scripts/verify_project.py` | Pre-commit gate: loads the `.qgs` offscreen and asserts the project invariants |
| `scripts/verify_data.py` | Pre-push gate and manual `all` sweep: data inventory, documented paths, raster performance, trail outputs |
| `scripts/build_contour_dem.py` | Build the 5 m contour-derived DEM from the COCT 2 m contours |
| `scripts/verify_contour_dem.py` | Validate the contour-derived DEM against the source contours and the boundary |

The former texture-pipeline scripts (`build_texture_rasters.py`, `apply_terrain_texture.py`) were removed. Their input file (formerly `aerial.tif`, renamed `aerial_1m.tif`) was superseded months ago and nothing referenced their outputs. The provenance is recorded in `data/imagery/README.md`.

## Current data

- `data/osm/south-africa-latest.osm.pbf`: Geofabrik South Africa extract, timestamped 2026-09-24, with OSM attribution required.
- `data/osm/table-mountain-bound-extent.osm.pbf`: rectangular Table Mountain National Park extent clip used by the trail model.
- `data/vector/osm/tmnp_relation_338191.gpkg`: Table Mountain National Park boundary, OSM relation 338191, 249.91 km², `EPSG:32734`.
- `data/vector/osm/tmnp_extent_north_up.gpkg`: authoritative north-up model crop envelope derived from relation 338191, `EPSG:32734`.
- `data/vector/osm/tm_hiking_trails_dissolved.gpkg`, `data/vector/osm/tm_hiking_trails_named.gpkg`, and `data/vector/osm/tm_trail_supplement.gpkg`: reproducible named-trail and bulk trail outputs. Provenance is in `data/vector/osm/trail_datasets.manifest.json`.
- `qgis/table_mountain_3D.qgs`: QGIS project (plain XML, reproducible build artifact, see "Make sure a build is correct").
- `docs/terrain_data_findings.md`: elevation-source research and access limits.
- `docs/osm_pbf_inspection.md`: DuckDB inspection results and Table Mountain feature IDs.

## Model crop extent

`TMNP crop extent (north-up)` is the authoritative model crop layer. It is the axis-aligned envelope of the whole park boundary in `EPSG:32734`, derived from OSM relation 338191 and stored in `data/vector/osm/tmnp_extent_north_up.gpkg`.

| Property | Value |
|---|---|
| East–west × north–south | 18,479.41 m × 49,372.55 m |
| Area | 912.3755 km² |
| CRS | `EPSG:32734` |

The envelope is north-up and contains every boundary vertex. Existing imagery and elevation rasters are retained as supersets. They are not re-cropped.

## Working rules

- Use `EPSG:32734` for final geometry and physical scale.
- Keep OSM attribution with any published map, render, or export.
- Treat rendered WMS images as visual references, not measured elevation rasters.
- Do not use restricted City imagery until the intended commercial or non-commercial use is confirmed.
