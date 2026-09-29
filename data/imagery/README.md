# data/imagery

Local copies of aerial / photographic imagery, clipped to the model extent
(`../vector/osm/tmnp_extent_north_up.gpkg`).

Contents are gitignored (see the `data/imagery/*` rule plus the
`!data/imagery/README.md` exception in the root `.gitignore`). Everything here
is regenerable from the commands recorded below.

---

## `aerial_1m.tif` and `aerial_5m.tif`

Orthorectified colour aerial mosaic of the City of Cape Town, **January 2026
(version 2)**. The local rasters retain the former, larger raster footprint as
a superset of the north-up model extent; they are not re-cropped when the
model extent changes.

> Provenance: the orthophoto was formerly staged as `aerial.tif`; the current
> files are `aerial_1m.tif` (native grid) and `aerial_5m.tif` (averaged-down
> derivative). Nothing in the repository references the old `aerial.tif` name.

| Property | Value |
|---|---|
| Service | COCT WMS `GeoSpatial Datasets` |
| Service URL | `https://cityimg.capetown.gov.za/erdas-iws/ogc/wms/GeoSpatial Datasets` |
| Layer name | `Aerial Imagery_Aerial Imagery 2026Jan` |
| Native CRS / resolution | `EPSG:20482` at **0.05 m** |
| Stored CRS / resolution | `EPSG:32734` at **1.0 m** (`aerial_1m.tif`) and 5.0 m (`aerial_5m.tif`) |
| Extent | E 251408.358–270713.403, N 6195216.935–6246802.116 |
| Size | 19,305 × 51,585 px (1 m) and 4,041 × 10,427 px (5 m), four bands |
| Compression | tiled JPEG-compressed GeoTIFFs with external overview sidecars |

### Licensing — non-commercial only

The layer's own service abstract states:

> 2026 January orthorectified colour mosaic (version 2). Original imagery
> property of CCT. ... Planimetric fidelity expected within 0.3m. **No
> restrictions on the digital file for non-commercial purposes.** This is not
> the final image for 2026.

So local copying and use are permitted for **non-commercial** purposes. If this
project ever becomes commercial, written permission from CCT is required.

> Note this differs from the **2013** COCT aerial imagery, which is
> non-commercial *unless explicit permission is obtained*. Do not conflate the
> two.

### 3D texture derivative

`aerial_10m_terrain.tif` is a local, ignored 10 m terrain texture derived from
`aerial_5m.tif` with average resampling. The saved 3D terrain uses the dedicated
`3D terrain texture` map theme, which exposes only this raster; it never draws
the 1 m aerial or a WMS layer into terrain tiles. Terrain elevation remains the
5 m contour DEM. QGIS generates 512 px texture tiles from the 10 m raster.

`aerial_texture_3d.tif` is a separate small texture retained for the north-up
extent overlay. Regenerate either derivative from `aerial_5m.tif` in
`EPSG:32734` using a tiled compressed GeoTIFF and the appropriate model extent.

Notes:

- The service caps every request at **4000 x 4000 px**. A request must be
  tiled; a bare `gdal_translate` of a `WMS:` source does not work because the
  driver opens an impractically large virtual size.
- The layer advertises only `EPSG:20482`, `EPSG:4326` and `EPSG:3857`, but it
  **does** serve `EPSG:32734`. That matters, because it is the same request path
  the live `Aerial imagery (2026 Jan)` WMS layer uses (`dpiMode=7`), which is
  why the local copy and the live layer register on top of each other.
- Keep request concurrency low. It issues many requests to a public municipal
  service.

### Verification

Alignment was checked against live `EPSG:32734` GetMap requests of the same
windows, sampled onto the stored 1 m grid (1,000,000 px per window):

| Window | Band means, local vs live | Correlation | Mean abs. diff |
|---|---|---|---|
| Table Mountain | 130.17 vs 130.31 | 0.91 | 19.2 |
| City Bowl | 135.61 vs 135.68 | 0.93 | 10.6 |
| Sea Point | 90.39 vs 90.54 | 0.95 | 12.7 |
| Constantia | 122.45 vs 122.58 | 0.92 | 16.5 |
| Cape Point / SW corner / west margin | both blank | n/a | 0 |

Correlations are quoted after a best-fit **1 px** shift. That shift is not
misalignment: the stored grid origin is `250509.6`, not an integer, so windows
requested on integer coordinates land 0.4 m (0.4 px) off the stored grid and
round to a 1 px difference. Sub-metre agreement is well inside the source's
stated 0.3 m planimetric fidelity.

The residual mean-absolute-difference is JPEG: the source is served as JPEG and
the store re-encodes at quality 90 with YCbCr chroma subsampling, which is most
visible on high-frequency colour detail. It is not geometric error.

True 1 m detail, not an upsample — compared against a native 1 m GetMap of the
same window: correlation 0.94, and mean absolute horizontal gradient ratio
0.82 (a 4x upsample of the 4 m grid would be far lower).

Elapsed time for the full export: **724 s**, output **218 MB**.
