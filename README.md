# Table Mountain 3D

This project prepares City of Cape Town elevation data, OpenStreetMap context, and a Blender scene for a metrically scaled Table Mountain model.


### System requirements

GDAL and osmium are not installed by the venv:

```bash
# Debian/Ubuntu
sudo apt install gdal-bin osmium-tool
# conda
conda install -c conda-forge gdal osmium
```

## Source data and rebuild

`data/` is never tracked. Its only upstream inputs are fetched by:

```bash
just fetch-sources
```

- Geofabrik's rolling South Africa OSM PBF: `data/osm/south-africa-latest.osm.pbf` (verified against Geofabrik's MD5 sidecar).
- City of Cape Town's 2 m contour archive: `data/vector/coct/GLM_2m_*.zip`. The archive is a source file, not a build product. Unzip it into `data/vector/coct/ground_level_map_2m_contours/` before rebuilding; `Ground_Level_Map_2m_Contours.shp` and its `.dbf`, `.shx`, `.prj`, and `.cpg` sidecars are required.

The OSM file intentionally changes with Geofabrik's `-latest` release. Rebuild provenance therefore describes the supplied download; it does not claim byte-identical output across releases.

```bash
just rebuild-all
```

This produces ignored OSM clips, park boundary and north-up extent, prepared contours, contour-derived DEM and overviews, trails, named peaks, official trails, and hillshade classes. It does not fetch restricted aerial imagery, seed MapProxy, or create renders.

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
