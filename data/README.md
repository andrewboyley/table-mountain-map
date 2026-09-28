# Data

## Subdirectories

- `osm/` — downloaded OpenStreetMap PBF files and future extracts.
- `terrain/` — raw and processed elevation rasters, contour surfaces, and height maps.
- `vector/` — COCT boundaries, contours, buildings, roads, and other context vectors. The offline COCT 2 m contour dataset is documented in `vector/coct/README.md`.
- `imagery/` — imagery and texture sources with recorded permissions.

## OSM source and attribution

The current `south-africa-latest.osm.pbf` is a Geofabrik South Africa extract. Its PBF header records a replication timestamp of `2026-09-24T20:21:20Z` and the source URL:

<https://download.geofabrik.de/africa/south-africa-updates>

Any published map, image, 3D render, or derived product must include suitable OpenStreetMap attribution. Do not treat the PBF as a terrain elevation source.

Keep raw downloads unchanged. Put filtered extracts and processing outputs in separate named files rather than overwriting the PBF.

## Table Mountain National Park extract

`table-mountain-national-park.osm.pbf` is a rectangular clip of the national park relation's WGS84 extent:

```text
18.30722,-34.35834,18.4979771,-33.9117846
```

It was created with Osmium's `complete_ways` strategy. This preserves complete ways and includes relations connected to the clipped area. The output header records the requested rectangle, while referenced complete geometries may extend beyond it.

`../vector/table-mountain-national-park.gpkg` is a GDAL `ogr2ogr` export of the clipped PBF. It contains five OSM-driver layers (`points`, `lines`, `multilinestrings`, `multipolygons`, and `other_relations`) in `EPSG:32734`, with 154,377 features in total.
