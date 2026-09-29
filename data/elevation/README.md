# Elevation derivatives

## `table_mountain_contours_2m_interpolated_5m_within_bound.tif`

A **5 m contour-derived elevation surface** for the project boundary, made from
`data/vector/coct/contours_2m_within_bound.gpkg`—the City of Cape Town 2019
Ground Level Map 2 m contours. It is not the City’s original 2019 LiDAR DEM,
and it must not be described as a surveyed or measured DEM.

| Property | Value |
|---|---|
| Source | `contours_2m_within_bound`, field `ELVT` |
| Contour interval | 2 m |
| Output CRS | `EPSG:32734` |
| Output resolution | 5 m × 5 m |
| Band format | One `Float32` elevation band, metres |
| NoData | `-9999` |
| Boundary | `data/vector/bound/bound.shp`, using raster pixel-centre inclusion |
| Interpolation | Rasterized contour constraints followed by GDAL inverse-distance NoData fill, no smoothing |
| Provenance | 2019 City contours derived from the 2019 LiDAR 5 m DEM; height lineage is SA Land Levelling Datum with SAGEOID2010 |

## Build without QGIS

The pipeline uses GDAL command-line tools and the system Python GDAL bindings.
It never launches QGIS or uses its processing providers.

```bash
python scripts/build_contour_dem.py
```

It uses a fixed 5 m grid aligned outward from the boundary’s extent. The
contour clip does not extend fully to the west and south sides of `bound`, so
the configured inverse-distance search reaches all interior cells. This is
controlled extrapolation from the available contours, not new terrain
measurement.

The builder refuses to replace an existing final GeoTIFF. Regenerate only when
intended:

```bash
python scripts/build_contour_dem.py --overwrite
```

Intermediate inputs and diagnostic products live in `cache/contour_dem/`.
Both the intermediate data and final GeoTIFF are ignored by Git because they
are reproducible derivatives.

## Overviews after a clean checkout

The DEM's `.ovr` overview pyramid and `.aux.xml` sidecar are gitignored
(`data/elevation/*.{ovr,aux.xml,wld}`); they are regenerable and never
committed. After a fresh clone, rebuild the overview pyramid with the command
recorded in `data/README.md`:

```bash
gdaladdo -ro -r average \
  data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif \
  2 4 8 16 32
```

The source raster itself is never rewritten.

## Verify before use

```bash
python scripts/verify_contour_dem.py
```

The verification report is written to
`cache/contour_dem/contour_dem_5m_validation.json`. A successful report checks:

1. GeoTIFF structure: one `Float32` band, `EPSG:32734`, 5 m north-up grid,
   aligned extent, declared NoData, and provenance metadata.
2. Boundary mask: every pixel centre outside `bound` is `-9999`, and no
   interior cell remains unfilled.
3. Numerical sanity: finite values and no values outside the contour range
   `-14` to `1084` m beyond a 2 m tolerance.
4. Constraint preservation: the finished surface retains the exact elevation
   values at the rasterized contour cells used to build it.
5. Plausibility at Maclear’s Beacon against the recorded 1086 m OSM peak and
   1087.6 m NGI survey references.
6. Visual-inspection products: hillshade and slope GeoTIFFs in
   `cache/contour_dem/` for checking pits, spikes, contour striping, and edge
   extrapolation.

A passing report establishes a technically valid, reproducible raster and
internal agreement with its contour constraints. It **does not** prove the
accuracy of interpolated cells between contours, or make the raster equivalent
to the original LiDAR DEM. Independent accuracy validation still requires the
raw City DTM/DEM or independent ground-control data.
