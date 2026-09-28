# COCT vector data

## Offline 2 m contours

The source archive is `../../../GLM_2m_-1536768105596229130.zip` at the project root. It was extracted to `ground_level_map_2m_contours/` without modifying the archive.

- Dataset: City of Cape Town Ground Level Map 2 m contours
- Geometry: 73,245 `LineString` features
- Elevation field: `ELVT`
- Contour interval: 2 m
- Native CRS: `ESRI:102562` (Hartebeesthoek94 / Lo19, WGS 84 Transverse Mercator, central meridian 19°)
- Archive SHA-256: `adf09db8b963e6814eae2aec63240bf870d31bfcaade46d8db96f50f65c3f880`

The source metadata says these contours were derived from a 2019 LiDAR-derived 5 m DEM. It states an approximately 1 m vertical accuracy standard for the 2 m contours. This is a contour-derived surface source, not a continuous measured DTM.

The QGIS project uses `EPSG:32734` and reprojects this native-CRS layer on the fly. For metric terrain exports, reproject a working copy to `EPSG:32734`; do not change the source layer CRS in place. The layer is named `COCT 2m contours (offline)` in the `COCT elevation` group.
