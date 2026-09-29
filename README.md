# Table Mountain 3D

This project prepares City of Cape Town elevation data, OpenStreetMap context, and a Blender scene for a metrically scaled Table Mountain model.

## Project layout

```text
qgis/                 QGIS project files
data/
  osm/                OSM PBF files and extracts
  elevation/          DEM, DTM, contour, and height-map data
  vector/             COCT and OSM vector context
  imagery/            permitted imagery and textures
docs/                 research findings and attribution notes
scripts/
                    data-verification and terrain-processing scripts
cache/                temporary processing files
renders/              final images and animation output
```

`opencode.json` stays in the project root so OpenCode can discover it. The Python environment is kept in the root `.venv` directory.

## Restoring local data after a fresh clone

The repository intentionally excludes large source and derived binaries. Restore
them from the sources recorded in the `data/` READMEs, then verify the restored
state from the repository root:

```bash
python3 scripts/verify_data.py
```

The verified trail outputs can be rebuilt with the single QGIS Processing-model
command in `data/README.md`; terrain-source research and access limits are in
`docs/terrain_data_findings.md`.

### System requirements

GDAL and osmium are not installed by the venv:

```bash
# Debian/Ubuntu
sudo apt install gdal-bin osmium-tool
# conda
conda install -c conda-forge gdal osmium
```

### The one manual data source

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

The QGIS project is stored as plain XML at `qgis/table_mountain_3D.qgs` and is a reproducible build artifact rather than a hand-saved file. `python3 scripts/build_project.py` re-enforces the canonical state — project CRS, the single 172-trail categorized layer (2D and 3D), the map themes, the 3D scene XML, the basemap sources (CoCT aerial as MapProxy WMS in `EPSG:32734`, OSM on cached XYZ), relative paths, and the embedded presentation macro — and writes a byte-identical file across runs. `python3 scripts/verify_project.py` is the pre-commit gate that loads the `.qgs` headlessly and asserts every one of those invariants.

The clip PBF rebuilds **byte-identically**. The GeoPackage does not, and cannot: GDAL writes a `last_change` timestamp into `gpkg_contents` on every save, so the bytes always differ even when the data is identical. That is why the GeoPackage is checked by content and geometry rather than by checksum.

## Current data

- `data/osm/south-africa-latest.osm.pbf` — Geofabrik South Africa extract, timestamped 2026-09-24, with OSM attribution required.
- `data/osm/table-mountain-bound-extent.osm.pbf` — rectangular Table Mountain National Park extent clip used by the trail model.
- `data/vector/osm/tmnp_relation_338191.gpkg` — Table Mountain National Park boundary, OSM relation 338191, 249.91 km², `EPSG:32734`.
- `data/vector/osm/tmnp_extent_north_up.gpkg` — authoritative north-up model crop envelope derived from relation 338191, `EPSG:32734`.
- `data/vector/osm/tm_hiking_trails_dissolved.gpkg`, `data/vector/osm/tm_hiking_trails_named.gpkg` and `data/vector/osm/tm_trail_supplement.gpkg` — reproducible named-trail and bulk trail outputs; provenance is in `data/vector/osm/trail_datasets.manifest.json`.
- `qgis/table_mountain_3D.qgs` — QGIS project (plain XML, reproducible build artifact — see "Verifying a build").
- `docs/terrain_data_findings.md` — elevation-source research and access limits.
- `docs/osm_pbf_inspection.md` — DuckDB inspection results and Table Mountain feature IDs.

## Model crop extent

`TMNP crop extent (north-up)` is the authoritative model crop layer. It is the
axis-aligned envelope of the whole park boundary in `EPSG:32734`, derived from
OSM relation 338191 and stored in `data/vector/osm/tmnp_extent_north_up.gpkg`.

| Property | Value |
|---|---|
| East–west × north–south | 18,479.41 m × 49,372.55 m |
| Area | 912.3755 km² |
| CRS | `EPSG:32734` |

The envelope is north-up and contains every boundary vertex. Existing imagery
and elevation rasters are retained as supersets; they are not re-cropped.

## Working rules

- Use `EPSG:32734` for final geometry and physical scale.
- Treat rendered WMS images as visual references, not measured elevation rasters.
- Do not use restricted City imagery until the intended commercial or non-commercial use is confirmed.
- Keep OSM attribution with any published map, render, or export.
