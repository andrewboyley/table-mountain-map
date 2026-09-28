# Table Mountain 3D

This project prepares City of Cape Town elevation data, OpenStreetMap context, and a Blender scene for a metrically scaled Table Mountain model.

## Project layout

```text
qgis/                 QGIS project files
data/
  osm/                OSM PBF files and extracts
  terrain/            DEM, DTM, contour, and height-map data
  vector/             COCT and OSM vector context
  imagery/            permitted imagery and textures
docs/                 research findings and attribution notes
scripts/
  duckdb/             DuckDB and OSM extraction scripts
  blender/            Blender build and render scripts
cache/                temporary processing files
renders/              final images and animation output
```

`opencode.json` stays in the project root so OpenCode can discover it. The Python environment is kept in the root `.venv` directory.

## Rebuilding from a fresh clone

A clone is about 1.3 MB. The large source and derived binaries are excluded by `.gitignore` and are rebuilt by a bootstrap script:

```bash
git clone <repo> table-mountain-pov
cd table-mountain-pov
scripts/bootstrap.sh
```

The script is idempotent, so re-running it only does missing work. Steps:

| Step | What it does | Network |
|---|---|---|
| `tools` | creates `.venv` from `scripts/duckdb/requirements.txt` | yes (PyPI) |
| `osmium` | fetches the Geofabrik South Africa PBF, then clips it to the park extent | yes (~420 MB) |
| `gpkg` | `ogr2ogr` builds the five-layer `EPSG:32734` GeoPackage | no |
| `contours` | extracts the COCT 2 m contour archive | **manual, see below** |
| `park` | exports TMNP boundary (OSM relation 338191) from the GeoPackage | no |
| `bbox` | builds the minimum bounding rectangle around that boundary | no |
| `official` | prints how to fetch the DEFF/SAPAD reference boundary | no |

Run a single step with `--step NAME`, or check integrity without fetching anything with `--verify`.

### System requirements

GDAL and osmium are not installed by the venv:

```bash
# Debian/Ubuntu
sudo apt install gdal-bin osmium-tool
# conda
conda install -c conda-forge gdal osmium
```

### The one manual step

The COCT 2 m contour archive is 753 MB and is not in git. Obtain it from the
[City of Cape Town Open Data Portal](https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::city-of-cape-town-ground-level-map-2m-contours-cct-glm-2019)
and save it as `data/vector/coct/GLM_2m_-1536768105596229130.zip`, then verify it:

```bash
echo adf09db8b963e6814eae2aec63240bf870d31bfcaade46d8db96f50f65c3f880 \
  data/vector/coct/GLM_2m_-1536768105596229130.zip | sha256sum -c -
```

If the portal is unreachable, request the dataset from `city.maps@capetown.gov.za`.

### Verifying a build

```bash
python3 scripts/verify_data.py
```

Checks SHA-256 of the pinned raw downloads, feature counts and CRS of every derived layer, the TMNP boundary area in square metres, and that the QGIS project uses `EPSG:32734` with only relative paths so it survives a move or clone.

The clip PBF rebuilds **byte-identically**. The GeoPackage does not, and cannot: GDAL writes a `last_change` timestamp into `gpkg_contents` on every save, so the bytes always differ even when the data is identical. That is why the GeoPackage is checked by content and geometry rather than by checksum.

## Current data

- `data/osm/south-africa-latest.osm.pbf` — Geofabrik South Africa extract, timestamped 2026-09-24, with OSM attribution required.
- `data/osm/table-mountain-national-park.osm.pbf` — rectangular Table Mountain National Park extent clip.
- `data/vector/table-mountain-national-park.gpkg` — GDAL/ogr2ogr OSM layers from the clipped PBF, in `EPSG:32734`.
- `data/vector/osm/tmnp_relation_338191.gpkg` — Table Mountain National Park boundary, OSM relation 338191, 249.91 km², `EPSG:32734`.
- `data/vector/osm/tmnp_minimum_bounding_rectangle.gpkg` — smallest (minimum-area) rotated rectangle enclosing that boundary, 766.26 km², `EPSG:32734`.
- `data/vector/coct/protected_areas/` — DEFF/SAPAD official park boundary, for comparison only.
- `qgis/table_mountain_3D.qgz` — QGIS project.
- `docs/terrain_data_findings.md` — elevation-source research and access limits.
- `docs/osm_pbf_inspection.md` — DuckDB inspection results and Table Mountain feature IDs.

## Model crop rectangle

`TMNP minimum bounding rectangle` is the QGIS layer to crop raster and vector
data against. It is the minimum-area rotated rectangle that contains the whole
park boundary, computed by `native:orientedminimumboundingbox`.

| Property | Value |
|---|---|
| Sides | 15,350.59 m × 49,917.29 m |
| Area | 766.2598 km² |
| Long axis | 5.0454° off grid north (N 5.05° W) |
| CRS | `EPSG:32734` |
| Corner v0 | E 265504.213, N 6245080.005 |
| Corner v1 | E 250213.104, N 6243729.986 |
| Corner v2 | E 254603.118, N 6194006.112 |
| Corner v3 | E 269894.227, N 6195356.131 |

The rotated rectangle is 16.01% smaller in area than the north-up bounding box
(18,479.41 m × 49,372.55 m = 912.3755 km²). It is tight: no part of the
boundary lies outside it, and the extreme park points sit on its edges.

## DuckDB inspection

The project-local `.venv` contains DuckDB 1.5.5 and the Python timezone support needed by the community `osmium` extension. Install or refresh the environment with:

```bash
uv pip install --python .venv/bin/python -r scripts/duckdb/requirements.txt
```

Inspect the PBF with:

```bash
.venv/bin/python scripts/duckdb/inspect_pbf.py --name-like "Table Mountain"
```

The script uses `osmium_read()` explicitly so it receives reconstructed OSM geometries rather than the native node/way/relation reader.

## Working rules

- Use `EPSG:32734` for final geometry and physical scale.
- Treat rendered WMS images as visual references, not measured elevation rasters.
- Do not use restricted City imagery until the intended commercial or non-commercial use is confirmed.
- Keep OSM attribution with any published map, render, or export.
