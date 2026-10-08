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

### The one manual data source

The COCT 2 m contour archive is 753 MB and is not in git. Get it from the [City of Cape Town Open Data Portal](https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::city-of-cape-town-ground-level-map-2m-contours-cct-glm-2019) and save it as `data/vector/coct/GLM_2m_-1536768105596229130.zip`. Then run the checksum command:

```bash
echo adf09db8b963e6814eae2aec63240bf870d31bfcaade46d8db96f50f65c3f880 \
  data/vector/coct/GLM_2m_-1536768105596229130.zip | sha256sum -c -
```

If the portal is unreachable, request the dataset from `city.maps@capetown.gov.za`.

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
