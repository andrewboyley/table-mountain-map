# Terrain data findings

Research date: September 25, 2026.

This document records the data sources and access limits for the Table Mountain 3D project. A digital terrain model, or DTM, is a raster of ground height without buildings or trees. A raw GeoTIFF stores source height values without display colors. The preferred source is a raw 2025 2 m bare-earth DTM from the City of Cape Town. The public service exposes rendered images, so it is not a source for measured terrain geometry.

## COCT elevation services

The City of Cape Town catalog lists five elevation services. They are the 2025 2 m DTM, 2025 5 m DTM, 2025 10 m DTM, 2025 1 m height map, and 2019 5 m DEM. The 1 m height map is an above-ground surface for buildings and vegetation. It is not a bare-earth terrain model. The 2 m DTM service reports 2 m cells, a 32-bit floating-point raster, and meter units. Its reported native extent is approximately `-64028,-3803550` to `4000,-3705000`. The service reports ArcGIS code `20482`, which local QGIS and PROJ do not resolve as an EPSG code. Keep the service WKT or request output geometry in `EPSG:32734`.

A Web Map Service, or WMS, returns map pictures. A Representational State Transfer, or REST, service returns map data through a web interface. The WMS capabilities for the elevation layers support image formats such as JPEG, PNG, and WebP. The REST export endpoint supports an 8-bit TIFF response. The returned TIFF has three 8-bit color bands, not 32-bit elevation values. A Web Coverage Service, or WCS, provides raster coverage data, but no working public WCS endpoint was found. A WMS feature-information request returned an `InvalidFormat` error instead of source height values.

## ODP catalog findings

The City of Cape Town Open Data Portal catalog contains 258 datasets. The catalog includes elevation services, contour data, building footprints, tree canopies, and access documents. The 2019 5 m DEM item is `dfed46fcf1784aafacb146b14f01cd49`. The item is a document link and points to the raster service catalog. Its download API reports `Downloads are not supported for this item`.

The 2019 5 m DEM is the preferred fallback when a raw file becomes available. The City describes it as LiDAR-derived with about 0.30 m vertical accuracy. Its height reference is the SA Land Levelling Datum, and the City used SAGEOID2010 for the height conversion. The access guide says that the DEM and 2 m contours are available through the City Maps Office at no cost. Smaller study-area requests are available from that office.

The 2019 2 m contour item is `bbd5614ce9154e649265dae5e9d26018`. It provides public ArcGIS service access and an elevation field named `ELVT`. The contours have a 2 m interval. The City says the contours were interpolated from a 5 m LiDAR-derived DEM. It states a 1 m vertical accuracy standard for the final contours. The layer supports `Query` and `Extract`. It does not provide a measured height for every raster cell.

The newer 5 m contour item is `d179f9e0faf145a2957617da1b231892`. The live service describes LiDAR captured from November 2024 to March 2025. It reports 15 points per square metre and 0.10 m vertical accuracy at the 95 percent level. The contour interval is 5 m, and the height reference is the SA Land Levelling Datum. The item description still gives older 2021 and 2023 flight dates, so the provenance needs confirmation. A test query over a broad Table Mountain rectangle returned 2,985 contour features. The elevation field ranged from -10 m to 1,080 m. This confirms that the contour service works. It does not create a continuous digital terrain model.

The ArcGIS WorldElevation `1m or better` coverage layer returned no features over Table Mountain. The 2025 2 m DTM is the best continuous City source, but its public REST and WMS outputs are rendered 8-bit images. REST identify returns RGB values, not source elevations. The 2025 1 m Height Map contains building and tree heights above the ground, so it cannot replace a DTM. The highest-resolution public representation that we can use without a request is therefore the 2019 2 m contour layer. We can use it to build an approximate triangulated surface. The 2025 5 m contours are a newer alternative with less vertical detail.

## Access and license limits

The standard OpenStreetMap XYZ layer is a visual map reference. It is not an elevation source. OSM attribution is required. Standard XYZ tiles must not be bulk-downloaded for an offline model. The 2013 City aerial service is limited to non-commercial use. The final team must make sure that the intended use is non-commercial before using restricted imagery. Commercial use requires a separate source with explicit commercial permission.

The final animation style and the treatment of buildings and trees are not yet selected. The model must not use restricted imagery until the intended use is recorded. The project can use permitted OSM data and City vector data for context while the elevation source is resolved.

## Project state

The QGIS project is `qgis/table_mountain_3D.qgs` (QGIS 4.2.2), hand-edited
in QGIS and verified on every commit and push by `scripts/verify_project.py`.
It uses `EPSG:2048` (Hartebeesthoek94 / Lo19) and organises the layer tree as
`Paths` / `Elevation` / `Shapes` / `Basemaps`. The basemaps are served from the
MapProxy deployment in `docker-mapproxy`: the COCT January 2026 aerial as a
WMS endpoint (layer `coct_aerial`, cache grid `EPSG:3857`,
fetched upstream in `EPSG:32734`), the CoCT hillshade (layer `coct_hillshade`,
cache grid `EPSG:3857`), the CoCT basemap raster (layer `coct_basemap`, cache
grid `EPSG:3857`), and OSM as cached XYZ tiles. None of the CoCT layers is
clipped to the park: each serves its full upstream extent. Four map themes
(`3D terrain texture`, `Aerial Imagery`, `Trail Inspection`,
Single-part trails`) drive the 2D/3D views and the named Trail Atlas layout.
See `qgis/README.md` for the full inventory and the adopted/declined QGIS
features.

The terrain surface is
`data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif`,
a 5 m GDAL inverse-distance interpolation from the COCT 2 m contours, aligned
to the boundary mask `data/vector/bound/bound.shp`. It is a contour-derived
elevation surface, not a measured City LiDAR DEM. Its technical validation
(`scripts/verify_contour_dem.py`) cannot establish independent grid-cell
accuracy. The aerial texture used by the 3D terrain is derived from
`data/imagery/aerial_1m.tif` and `aerial_5m.tif` (permitted COCT WMS
downloads, see `data/imagery/README.md`). The Blender scene
`blender/tmnp.blend` and the `renders/` directory hold the animation work.
The project-local OpenCode configuration remains at `opencode.json`.

## Next action

Request a small study-area subset from the City Maps Office. The request must ask for a GeoTIFF, the source CRS, horizontal and vertical units, the vertical reference, the nodata value, and the permitted use. The contact address is `city.maps@capetown.gov.za`. The telephone number is `021 487 2826`.

Ask for the 2025 2 m bare-earth DTM first. Ask for the 2019 5 m DEM as a second choice. If no raw raster becomes available, use the 2 m contours for an approximate model. Use the 5 m contours when newer coverage matters more than vertical detail. Do not label either contour model as a measured DEM.

The 2 m contour service can return geometry directly in `EPSG:32734` (for
MapProxy WMS caching). For the project display, request output in `EPSG:2048`
(Hartebeesthoek94 / Lo19). Use the `EPSG:32734` contour geometry for the first
working surface. When a raw file arrives, read its metadata with `gdalinfo`.
Compare sample heights with known points and inspect the edge and nodata areas.
Reproject a working copy to `EPSG:2048` before creating the Blender heightmap.
Then prepare the texture and context layers and build the scene.

## Source links

The City elevation service catalog is at <https://cityimg.capetown.gov.za/erdas-iws/esri/GeoSpatial%20Datasets/rest/services/>.

The elevation WMS capabilities are at <https://cityimg.capetown.gov.za/erdas-iws/ogc/wms/GeoSpatial%20Datasets?service=WMS&request=getcapabilities&version=1.3.0>.

The City Open Data Portal is at <https://odp-cctegis.opendata.arcgis.com>.

The GLM access guide is at <https://www.arcgis.com/sharing/rest/content/items/99defafc0b354579a544855947eed8f4/data>.

The 5 m contour service is at <https://esapqa.capetown.gov.za/agsext/rest/services/Theme_Based/ODP_SPLIT_2/FeatureServer/0>.

The 2019 2 m contour item is at <https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::city-of-cape-town-ground-level-map-2m-contours-cct-glm-2019>.

The 2019 2 m contour service is at <https://services6.arcgis.com/nyYfO9SxHU2ChQd9/arcgis/rest/services/GLM_2m/FeatureServer/1>.

The 2025 2 m DTM metadata is at <https://cityimg.capetown.gov.za/erdas-iws/esri/GeoSpatial%20Datasets/rest/services/Elevation_DTM_2m/MapServer?f=pjson>.

The 2025 1 m Height Map metadata is at <https://cityimg.capetown.gov.za/erdas-iws/esri/GeoSpatial%20Datasets/rest/services/Elevation_Height_Map_1m/MapServer?f=pjson>.

The ArcGIS WorldElevation coverage layer is at <https://elevation.arcgis.com/arcgis/rest/services/WorldElevation/DataExtents/MapServer/1>.
