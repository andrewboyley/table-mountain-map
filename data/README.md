# Data

## Subdirectories

- `osm/` — downloaded OpenStreetMap PBF files and future extracts.
- `elevation/` — raw and processed elevation rasters, contour surfaces, and height maps.
- `vector/` — COCT boundaries, contours, buildings, roads, and other context vectors. The offline COCT 2 m contour dataset is documented in `vector/coct/README.md`.
- `imagery/` — imagery and texture sources with recorded permissions.

## OSM source and attribution

The current `south-africa-latest.osm.pbf` is a Geofabrik South Africa extract. Its PBF header records a replication timestamp of `2026-09-24T20:21:20Z` and the source URL:

<https://download.geofabrik.de/africa/south-africa-updates>

Any published map, image, 3D render, or derived product must include suitable OpenStreetMap attribution. Do not treat the PBF as a terrain elevation source.

Keep raw downloads unchanged. Put filtered extracts and processing outputs in separate named files rather than overwriting the PBF.

## Table Mountain National Park extract

`table-mountain-bound-extent.osm.pbf` is a rectangular clip of the national park relation's WGS84 extent:

```text
18.30722,-34.35834,18.4979771,-33.9117846
```

It was created with Osmium's `complete_ways` strategy. This preserves complete ways and includes relations connected to the clipped area. The output header records the requested rectangle, while referenced complete geometries may extend beyond it.

The stable park-boundary product is `vector/osm/tmnp_relation_338191.gpkg`.
The authoritative north-up crop envelope is
`vector/osm/tmnp_extent_north_up.gpkg`; it contains the relation boundary and
measures 18,479.41 m × 49,372.55 m (912.3755 km²) in `EPSG:32734`.

## Trail datasets

The trail data (`vector/osm/tm_hiking_trails_dissolved.gpkg`,
`vector/osm/tm_hiking_trails_named.gpkg` and
`vector/osm/tm_trail_supplement.gpkg`) is derived from the park extract by one
Processing model, `qgis/processing/trail_rebuild.model3`, with no manual step
in between. The model clips the extract's `lines` to the park boundary,
promotes every way to `MultiLineString`, reprojects to `EPSG:32734`, keeps
only ways whose `highway` is `path`, `steps` or `footway`, splits them into
named, unnamed and track sets, dissolves the named ways by OSM name with
deterministic aggregates, and writes the three GeoPackages with their
canonical layer names. Every step is order-invariant: processing the extract
in a different feature order produces an identical result.

Rebuild everything from the extract with a single command (prerequisites: QGIS
4.2 with qgis_process on `PATH`, and the model registered in the Processing
models folder from the checked-in `qgis/processing/trail_rebuild.model3`):

```bash
qgis_process run model:trail_rebuild \
  --ELLIPSOID=EPSG:7030 \
  --INPUT_PBF=data/osm/table-mountain-bound-extent.osm.pbf \
  --INPUT_BOUNDARY=data/vector/osm/tmnp_relation_338191.gpkg \
  --HIGHWAY_VALUES=path,steps,footway \
  --output_named=data/vector/osm/tm_hiking_trails_named.gpkg \
  --output_dissolved=data/vector/osm/tm_hiking_trails_dissolved.gpkg \
  --output_supplement=data/vector/osm/tm_trail_supplement.gpkg
```

The same model runs from the Processing toolbox (Processing → Models →
`trail_rebuild`) with the same parameter values and produces identical
outputs; the command line is exactly the GUI model's parameter set.

Provenance (extract, boundary, filter, dissolve rule, CRS), per-dataset
feature counts, total length, the single-part trail count and informational
checksums are recorded in `vector/osm/trail_datasets.manifest.json`.
Verification compares content and geometry, never bytes — GeoPackage files
embed a save-time timestamp, so byte checksums are not an acceptance test; the
acceptance path is `../scripts/verify_data.py trails`.

## Raster performance

Every raster above 10,000,000 px has an external overview pyramid (`.ovr`
sidecar), so zoomed-out views read a small fraction of the source. The source
files themselves are never rewritten: `gdaladdo -ro` only writes the sidecar,
and the source checksum, pixel dimensions and geotransform are unchanged by
the operation.

| Raster | Pixels | Overview levels | Resampling | Sidecar |
|---|---|---|---|---|
| `imagery/aerial_1m.tif` | 19305 × 51585 | 2, 4, 8, 16, 32, 64 | average | `aerial_1m.tif.ovr` (1.3 GB) |
| `imagery/aerial_5m.tif` | 4041 × 10427 | 2, 4, 8, 16, 32 | average | `aerial_5m.tif.ovr` (56 MB) |
| `elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif` | 4042 × 10428 | 2, 4, 8, 16, 32 | average | `.tif.ovr` (58 MB) |

Regenerating any of them (all rasters above the threshold are processed the
same way, with the level list varying):

```bash
gdaladdo -ro -r average <raster.tif> 2 4 8 16 32      # 5 m sources
gdaladdo -ro -r average <raster.tif> 2 4 8 16 32 64   # 1 m source
```

Deleting a `.ovr` sidecar returns that raster to its previous, slow,
full-resolution-only rendering — no source data is lost.

## Additional local inventory

- `elevation/South_Africa_SRMT30meters.zip` is a retained SRTM 30 m source
  archive; it is not the terrain source for the saved 3D scene.
- `vector/coct/contours_2m_within_bound.gpkg` is the clipped COCT contour
  layer. `vector/coct/ground_level_map_2m_contours/Ground_Level_Map_2m_Contours.shp`
  is the extracted source shapefile retained for provenance.
- `vector/osm/land_coast_only.gpkg` supplies coastline context.
- `vector/tiles_grid.gpkg` supplies the map tile grid.
- `vector/bound/bound.shp` is the DEM boundary mask — the envelope that the
  contour-derived DEM is aligned and rasterized against (`bound`). It is
  distinct from the authoritative crop extent above.
