# QGIS

`qgis/table_mountain_3D.qgs` is a hand-edited project file. Edit it directly in QGIS and run `just verify-project` to check that the invariants hold (CRS, layer existence, renderer coverage, relative paths). The project embeds no scripts or macros: every presentation behaviour is a native QGIS feature.

## Project CRS

**EPSG:2048** — Hartebeesthoek94 / Lo19 (Transverse Mercator, South Orientated, zone 19). All local data layers (trails, contours, DEM, boundary, crop extent, land) are stored in this CRS so on-the-fly reprojection is not needed for the TMNP extent.

## Run the project gate

```bash
just verify-project
```

This runs at commit and push time as the `verify-project` pre-commit hook. It exits non-zero with a named failure when an invariant is broken. Fix issues directly in QGIS.

## Processing models

Four models are checked in here:

| Model | Produces | Rebuild command |
|---|---|---|
| `trail_rebuild.model3` | the three trail GeoPackages | `just rebuild-trails` |
| `trail_official.model3` | `tm_hiking_trails_official.gpkg` | `just rebuild-trails-official` |
| `peak_extract.model3` | `tm_peaks_named_with_ele.gpkg` (layer `summits`) | `just rebuild-peaks` |
| `hillshade_classes.model3` | `data/vector/terrain/hillshade_classes.gpkg` | `just hillshade-classes` — eleven native steps; block-averages the hillshade onto an 80 m grid before thresholding so the classes come out as 116 blobs instead of 127,617 speckle regions |

`qgis_process` resolves `model:<name>` from the **active QGIS profile's** `processing/models` directory, not from this folder. A model that is not installed there cannot run, so a fresh clone cannot run any of them until it is copied across. Every rebuild recipe does that copy for you via the `install-models` recipe; run `just install-models` on its own if you only want the copy. A pre-commit hook validates that every `.model3` in this folder is a model QGIS can load.

`peak_extract.model3` takes a GeoJSON or GeoPackage of peak points, not the `.pbf` directly. Its input is produced by `osmium`, because the GDAL OSM driver that QGIS would otherwise use for a `.pbf` silently drops the `ele` tag from both the field list and `other_tags`. See the named-summits section in `../data/README.md`.

### `hillshade_classes.model3`

Turns an elevation raster into a thresholded hillshade as polygons. It takes the layer you select in QGIS, so you can run it from the Processing toolbox on whatever DEM is loaded, or headlessly through the rebuild recipe. The chain is eleven steps, all native QGIS or GDAL provider algorithms, so you can read every operation off the model instead of trusting a script:

1. `gdal:hillshade` — one sun, azimuth 315 and altitude 45 by default.
2. `gdal:warpreproject` — block-average the hillshade onto a `COARSE_RES` grid (80 m by default) using `RESAMPLING=5`, the average. This is the step that decides the look, and it has to happen *before* the threshold, not after.
3. `gdal:rastercalculator` — three mutually exclusive codes: 1 below `SHADOW_MAX`, 2 from `SHADOW_MAX` up to `MID_MAX`, 3 at `MID_MAX` and above. `RTYPE` is Byte and `NO_DATA` is 0, so the class codes 1, 2 and 3 stay unambiguous and NoData stays NoData instead of becoming a class.
4. `gdal:sieve` — absorb regions below `SIEVE_PIXELS` into their largest neighbour. This is a fragmentation control, not a cosmetic one: at `COARSE_RES` 80 and `SIEVE_PIXELS` 16 it takes the raw polygonize from 1,384 features to 116, and the median feature from 6,400 m² to 243,200 m². Set it to 0 to keep every region.
5. `gdal:polygonize` — one polygon per contiguous class region, field `class`.
6. `native:extractbyexpression` — drop `class = 0`. `gdal:polygonize` passes no mask band, so the NoData ring outside the mountain arrives as a real class 0 polygon; this removes it so NoData never becomes a class.
7. `native:smoothgeometry` — round off the staircase. `gdal:polygonize` traces cell edges, so every class boundary is a right-angle step. `SMOOTH_ITERATIONS`, `SMOOTH_OFFSET` and `SMOOTH_MAX_ANGLE` are exposed; the defaults are 12, 0.03 and 180.
8. `native:simplifygeometries` — drop the vertices the smoothed curve no longer needs. Chaikin multiplies the vertex count by about sixteen, so `SIMPLIFY_TOLERANCE` defaults to 20 m, a quarter of a coarse cell, which takes 175,000 vertices back down to about 11,000 with no visible change to the curve.
9. `native:fixgeometries` — repair the self-intersections Chaikin can introduce on narrow slivers.
10. `native:fieldcalculator` — add `class_name` (`shadow`, `midtone`, `lit`).
11. `native:orderbyexpression` — sort by `class` so repeated runs diff cleanly.

### Why the resample is there, and why the smoothing is tuned the way it is

Thresholding the source DEM directly does not produce a coverage, it produces confetti. On the 5 m contour DEM the raw polygonize yields **127,617 class regions, 127,073 of them under 0.01 km²**, because the class boundary is a one-pixel staircase and so every "region" is a handful of pixels. Averaging the hillshade before thresholding is a genuine low-pass filter: at 80 m the same DEM gives **116 features**, of which the shadow class is 37 blobs with a median area of 267,000 m² and a largest of 7.8 km².

Averaging is also the only one of the three ways to de-speckle that conserves area. `gdal:sieve` conserves area exactly at every threshold, but it merges by largest-neighbour and so builds ragged amoebas rather than blobs; `native:smoothgeometry` does not conserve area at all. The resample moves the class boundary onto a coarser grid instead of trying to repair it afterwards, and the polygons come out 1,052.7 km² over a 1,055.7 km² footprint.

The smoothing parameters are set the opposite way round to the obvious choice, and that is deliberate. The area a Chaikin pass removes goes as the **square of the offset**, while the number of passes only controls how far the curve is pulled off the grid. So many passes at a small offset rounds a boundary as well as few passes at a large one, for a fraction of the cost. Measured over the 1,055.7 km² footprint, with blockiness measured as the share of boundary length still lying on an 80 m grid line:

| `SMOOTH_ITERATIONS` / `SMOOTH_OFFSET` | boundary on grid | interior coverage lost | total area |
| --- | --- | --- | --- |
| none | 100% | 0 km² | 1,055.7 km² |
| 2 / 0.25 | 28.4% | 135.6 km² | 891.5 km² |
| 4 / 0.05 | 4.6% | 2.0 km² | 1,049.4 km² |
| 8 / 0.05 | 2.8% | 2.0 km² | 1,049.5 km² |
| 12 / 0.04 | 2.9% | 0.9 km² | 1,051.8 km² |
| **12 / 0.03** | **3.0%** | **0.3 km²** | **1,052.7 km²** |

Two passes at 0.25 is the setting that looks reasonable and is not: it leaves a quarter of the boundary on the grid and destroys 13% of the map's interior coverage. The 12/0.03 default leaves 3% on the grid and loses 0.03%.

GRASS `v.generalize` is the usual recommendation for raster-derived polygons, because it is a topological GIS and holds adjacency by construction. The native steps already hold the seams here, so the model stays on the QGIS and GDAL providers alone and takes no GRASS dependency.

`sieve` defaults to four-connectedness, which is what the counts above assume. Setting `EIGHT_CONNECTEDNESS` to true raises the feature count at the same threshold because diagonal touches stop merging regions.

Step 3 builds its formula as a model expression rather than a literal string, so the two cut points stay adjustable. The expression is written out in full in `hillshade_classes.model3`; a `static_value` there would hand `@SHADOW_MAX` to the calculator as literal text and fail to parse.

The two class cut points are exposed as `SHADOW_MAX` and `MID_MAX` rather than baked in, because the default breaks are not equally balanced on this terrain: over half the pixels sit on one near-flat hillshade value, so the defaults give 2.9% class 1, 90.4% class 2 and 6.7% class 3. Move the cut points if you want a different balance. `COARSE_RES` is exposed for the same reason: it is the one parameter that controls the character of the output, and 80 m is a measured choice rather than a round default. Rasterising the layer at 2000 px confirms the result is sparse: 3.2% of the frame is painted, 96.8% is blank, and no visible blob falls under 100 px.

This model needs two libraries that GDAL's own drivers link against but that are not installed by default: `podofo` and `mariadb-libs`. Without them the `PDF` and `MySQL` drivers raise when QGIS enumerates raster formats, and because that happens inside a PyQt6 virtual call QGIS dies with `SIGABRT` (exit 134) with no message. QGIS overwrites `GDAL_SKIP` with an empty string at startup, so no environment variable can suppress it:

```bash
sudo pacman -S podofo mariadb-libs
```


## GUI saves and side files

Every GUI save in QGIS 3.22 or later writes a `<name>.qgs~` backup file and a `<name>_attachments.zip` archive next to the project. You cannot disable either one. Both are regenerable, so they are gitignored (`*.qgs~`, `*_attachments.zip`) and never committed.

## Map themes

The project ships four map themes (visibility presets):

- `3D terrain texture` — nothing visible; base state for the 3D scene.
- `Aerial Imagery` — the CoCT 2026 January aerial only.
- `Trail Inspection` — trails, OSM, boundary, crop extent, hillshade (for shadow context).
- `Single-part trails` — filter-driven single-part trail view.

## Basemaps and attribution

- `OpenStreetMap`: cached XYZ tiles from the local MapProxy (`tiles/1.0.0/osm/webmercator`). OSM attribution is required in any published map, render, or export.
- `City of Cape Town Aerial Photography (2026 January)`: restricted CoCT imagery served locally through MapProxy WMS (`coct_aerial`, fetched in `EPSG:32734`). Do not publish restricted imagery until the intended commercial or non-commercial use is confirmed.
- `City of Cape Town Hillshade 2m DEM`: 2 m hillshade derived from 2017–2019 CoCT LiDAR, served locally through MapProxy WMS (`coct_hillshade`, fetched in `EPSG:3857`). No restrictions on non-commercial use.
- `Basemap_Raster`: City of Cape Town basemap raster (streetmap-style backdrop) served locally through MapProxy WMS (`coct_basemap`, fetched in `EPSG:3857`). No restrictions on non-commercial use.

## Native QGIS features per layer

Each layer expresses its rendering and interaction with the native QGIS feature that fits it. Nothing is emulated by scripts or extra layers.

| Layer / group | Data source | Native feature |
|---|---|---|
| Named trails | `../data/vector/osm/tm_hiking_trails_dissolved.gpkg` | Single categorized layer. 2D and 3D categorized renderer (QGIS 4.2). Subset-string provider filter for isolation and single-part filtering. Named styles. Map themes |
| Named summits | `../data/vector/osm/tm_peaks_named_with_ele.gpkg` (layer `summits`) | In the `Elevation` group. Graduated renderer on the numeric `ele_m` field over 6 classes, simple labelling on `name`. Not a member of any map theme |
| Park boundary | `../data/vector/osm/tmnp_relation_338191.gpkg` | Styled vector layer. Clip source for the Processing rebuild model |
| Crop extent | `../data/vector/osm/tmnp_extent_north_up.gpkg` | Styled layer. Textured overlay in the 3D scene |
| Contours | `../data/vector/coct/contours_2m_within_bound.gpkg` | Styled layer included in themes |
| Hillshade bands | `../data/vector/terrain/hillshade_classes.gpkg` | Categorized renderer on `class_name` where only `shadow` carries a fill. `midtone` and `lit` are given an empty symbol, so the layer paints the dark ground and leaves the rest of the map clear. Rebuild with `just hillshade-classes` |
| Terrain / DEM | `../data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif` | 3D terrain elevation source. Theme-driven terrain texture (`map-theme`, `texture-size="512"`). Overview sidecars |
| Basemaps | MapProxy `coct_aerial` WMS (cached in `EPSG:3857`, fetched upstream in `EPSG:32734`, reprojected to the project `EPSG:2048` on request) + `coct_hillshade` (`EPSG:3857`) + `coct_basemap` (`EPSG:3857`) + OSM XYZ | WMS / XYZ providers with a local cache |
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
