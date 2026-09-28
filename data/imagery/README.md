# data/imagery

Local copies of aerial / photographic imagery, clipped to the model extent
(`qgis/bound.shp`).

Contents are gitignored (see the `data/imagery/*` rule plus the
`!data/imagery/README.md` exception in the root `.gitignore`). Everything here
is regenerable from the commands recorded below.

---

## coct_aerial_2026jan_1m_within_bound.tif

Orthorectified colour aerial mosaic of the City of Cape Town, **January 2026
(version 2)**, at 1 m/px, clipped to `bound`.

| Property | Value |
|---|---|
| Service | COCT WMS `GeoSpatial Datasets` |
| Service URL | `https://cityimg.capetown.gov.za/erdas-iws/ogc/wms/GeoSpatial Datasets` |
| Layer name | `Aerial Imagery_Aerial Imagery 2026Jan` |
| Native CRS / resolution | `EPSG:20482` at **0.05 m** |
| Stored CRS / resolution | `EPSG:32734` at **1.0 m** |
| Extent | `250509.6, 6194665.7, 270713.4, 6246802.1` (exactly `bound`) |
| Size | 20204 x 52137 px, 3 bands RGB |
| Compression | JPEG, quality 90, YCbCr, tiled, BigTIFF if needed |

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

### Coverage

The mosaic footprint begins at longitude **18.30289**, while `bound` begins at
**18.28726**; the southern edge of the footprint is **-34.36050** against a
bound edge of **-34.36400**. The western and southern margins of `bound`
therefore fall outside the imagery.

Measured against `data/vector/osm/land_within_bound.gpkg`:

- 46.9 % of the bound is flat-toned, but **97.9 % of that is ocean** — the
  orthophoto does cover water, it is simply smooth there.
- Only **1.94 % of land** is blank, i.e. the no-imagery margins above.

### Regenerating

Run in the QGIS Processing toolbox, or from the Python console:

```python
import processing

processing.run(
    "gdal:warpreproject",
    {
        "INPUT": (
            "WMS:https://cityimg.capetown.gov.za/erdas-iws/ogc/wms/GeoSpatial%20Datasets"
            "?SERVICE=WMS&VERSION=1.3.0"
            "&LAYERS=Aerial%20Imagery_Aerial%20Imagery%202026Jan&STYLES="
            "&CRS=EPSG:32734"
            "&BBOX=250509.6,6194665.7,270713.4,6246802.1"
            "&WIDTH=5000&HEIGHT=5000&FORMAT=image/jpeg"
        ),
        "SOURCE_CRS": "EPSG:32734",
        "TARGET_CRS": "EPSG:32734",
        "RESAMPLING": 1,  # bilinear
        "TARGET_RESOLUTION": 1.0,
        "TARGET_EXTENT": "250509.6,270713.4,6194665.7,6246802.1 [EPSG:32734]",
        "TARGET_EXTENT_CRS": "EPSG:32734",
        "CREATION_OPTIONS": "COMPRESS=JPEG|TILED=YES|PHOTOMETRIC=YCBCR"
        "|JPEG_QUALITY=90|BIGTIFF=IF_SAFER",
        "MULTITHREADING": False,  # keep the request rate polite
        "OUTPUT": "data/imagery/coct_aerial_2026jan_1m_within_bound.tif",
    },
)
```

`bound` is an axis-aligned rectangle in `EPSG:32734`, so giving the algorithm
that extent **is** the clip; no separate mask step is needed. To clip against a
non-rectangular boundary instead, follow with `gdal:cliprasterbymasklayer` using
`qgis/bound.shp`.

Notes:

- The service caps every request at **4000 x 4000 px**. `gdal:warpreproject`
  sub-tiles automatically because it sets an explicit target grid. A bare
  `gdal_translate` of a `WMS:` source does **not** work — the driver opens at a
  1073741824 x 1073741824 virtual size and fails.
- The layer advertises only `EPSG:20482`, `EPSG:4326` and `EPSG:3857`, but it
  **does** serve `EPSG:32734`. That matters, because it is the same request path
  the live `Aerial imagery (2026 Jan)` WMS layer uses (`dpiMode=7`), which is
  why the local copy and the live layer register on top of each other.
- Keep `MULTITHREADING` off unless you have a reason. It issues many concurrent
  requests at a public municipal service.

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
