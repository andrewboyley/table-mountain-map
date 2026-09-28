#!/usr/bin/env python3
"""Build Blender-ready texture rasters from the COCT aerial orthophoto.

Produces two derivatives in cache/blender/:

  tex_base_3p2.tif   3.2 m, full land extent, RGB
  tex_massif_1m.tif  1 m, massif window, RGB + a feathered alpha band

The alpha band is not transparency -- it is a blend mask. The shader keys the
1 m detail over the coarse base with it, so the transition needs no extra nodes
and cannot open a seam. Interior alpha is a uniform 255; it ramps to 0 over
FEATHER_M at the window border.

Why the base is 3.2 m and not 2 m
---------------------------------
The base exists to keep the far field from looking soft, not to be inspected
up close. 2 m gave a 996 MB texture, and with 1 m detail on top the pair needs
~1.7 GB of VRAM once mip chains are counted, against ~1.9 GB free on this
RX 6500 -- EEVEE dies allocating it. 3.2 m is the finest size whose height
still clears the 16384 px GPU texture limit: 51586 m / 3.0 = 17195 rows, which
does not, while 51586 / 3.2 = 16121 does. The 1 m massif, which is what the
camera actually flies over, is untouched by this.

Read path is chunked ReadAsArray against the source raster. gdalwarp is
deliberately never used: warp OUTPUTS are what exhibit the windowed-RasterIO
fault on this imagery (see docs/), and chunked reads of the original
data/imagery/aerial.tif are clean at every row. The source grid is
0.9999898 m, not exactly 1 m, so the target grids below are snapped and the
true geotransform is carried through rather than assumed.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from osgeo import gdal

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/imagery/aerial.tif"
CACHE = ROOT / "cache/blender"

# Rows read per RasterIO call. 256 full-width rows across all four bands
# completes without error on the 20204 x 52136 source.
CHUNK_ROWS = 256

# Interior alpha is opaque; the ramp at the border hides the resolution change.
FEATHER_M = 150

_NP_TYPES = {
    gdal.GDT_Byte: np.uint8,
    gdal.GDT_UInt16: np.uint16,
    gdal.GDT_Int16: np.int16,
    gdal.GDT_UInt32: np.uint32,
    gdal.GDT_Int32: np.int32,
    gdal.GDT_Float32: np.float32,
    gdal.GDT_Float64: np.float64,
}


@dataclass(frozen=True)
class Grid:
    """A north-up, axis-aligned target grid snapped to whole metres."""

    x0: int  # west edge, EPSG:32734
    y0: int  # north edge, EPSG:32734
    px: float  # pixel size, metres
    width: int
    height: int

    @property
    def geotransform(self) -> tuple[float, float, float, float, float, float]:
        return (
            float(self.x0),
            float(self.px),
            0.0,
            float(self.y0),
            0.0,
            -float(self.px),
        )

    @property
    def extent(self) -> tuple[float, float, float, float]:
        return (
            self.x0,
            self.x0 + self.width * self.px,
            self.y0 - self.height * self.px,
            float(self.y0),
        )


# 19306 x 51586 m, covering data/vector/osm/land_coast_only.gpkg with a little
# slack. 3.2 m is the finest size that keeps the height under the 16384 px GPU
# texture limit: 51586 / 3.0 = 17195 rows (over), 51586 / 3.2 = 16121 (under).
BASE = Grid(x0=251408, y0=6246802, px=3.2, width=6034, height=16121)

# 500 m of margin around all seven trail landmarks, snapped to 100 m.
# NOTE the north-south span is 13.4 km, not 7 km: the landmarks run from
# Sea Point (N 6229781) up to Lion's Head (N 6242097). Both dimensions stay
# under the 16384 px GPU texture limit, so EEVEE can bind this one directly.
MASSIF = Grid(x0=258400, y0=6242600, px=1, width=5400, height=13400)


def np_type(band: gdal.Band) -> type:
    return _NP_TYPES.get(band.DataType, np.uint8)


def src_window(tgt_gt, src_gt, src_size, px0: int, py0: int, w: int, h: int):
    """Source pixel window covering target-grid window (px0, py0, w, h).

    The two grids are not aligned -- the cutline crop offsets the DEM by a
    fraction of a pixel -- so a stride-and-slice decimation would be wrong.
    """
    sx0 = (tgt_gt[0] + px0 * tgt_gt[1] - src_gt[0]) / src_gt[1]
    sx1 = (tgt_gt[0] + (px0 + w) * tgt_gt[1] - src_gt[0]) / src_gt[1]
    sy0 = (tgt_gt[3] + py0 * tgt_gt[5] - src_gt[3]) / src_gt[5]  # north, smaller row
    sy1 = (tgt_gt[3] + (py0 + h) * tgt_gt[5] - src_gt[3]) / src_gt[5]
    src_w, src_h = src_size
    x0 = max(0, min(math.floor(sx0), src_w - 1))
    y0 = max(0, min(math.floor(sy0), src_h - 1))
    x1 = max(x0 + 1, min(math.ceil(sx1), src_w))
    y1 = max(y0 + 1, min(math.ceil(sy1), src_h))
    return x0, y0, x1 - x0, y1 - y0


def read_grid(
    band,
    src_ds,
    tgt_gt,
    width: int,
    height: int,
    *,
    row0: int = 0,
    chunk: int = CHUNK_ROWS,
) -> np.ndarray:
    """Read `band` onto the target grid, area-averaged, in row chunks.

    `row0` is the target row that `height` starts at, so successive chunks
    tile the grid correctly.
    """
    sgt = src_ds.GetGeoTransform()
    size = (src_ds.RasterXSize, src_ds.RasterYSize)
    out = np.zeros((height, width), dtype=np_type(band))
    for i, py in enumerate(range(row0, row0 + height, chunk)):
        rows = min(chunk, row0 + height - py)
        x, y, w, h = src_window(tgt_gt, sgt, size, 0, py, width, rows)
        out[i : i + rows] = band.ReadAsArray(x, y, w, h, width, rows, gdal.GRA_Average)
    return out


def write_rgb(dataset, source, grid: Grid) -> None:
    gt = grid.geotransform
    for index, colour in (
        (1, gdal.GCI_RedBand),
        (2, gdal.GCI_GreenBand),
        (3, gdal.GCI_BlueBand),
    ):
        band = dataset.GetRasterBand(index)
        band.SetColorInterpretation(colour)
        done = 0
        while done < grid.height:
            rows = min(CHUNK_ROWS, grid.height - done)
            band.WriteArray(
                read_grid(
                    source.GetRasterBand(index), source, gt, grid.width, rows, row0=done
                ),
                0,
                done,
            )
            done += rows
        print(f"    band {index} done", flush=True)


def write_blend_mask(dataset, grid: Grid) -> None:
    """Alpha = 255 in the interior, ramping to 0 across the outer feather."""
    band = dataset.GetRasterBand(4)
    band.SetColorInterpretation(gdal.GCI_AlphaBand)
    px, width, height = grid.px, grid.width, grid.height
    for row0 in range(0, height, 512):
        row1 = min(height, row0 + 512)
        y = (np.arange(row0, row1) + 0.5)[:, None] * px
        x = (np.arange(width) + 0.5)[None, :] * px
        edge = np.minimum(np.minimum(x, width * px - x), np.minimum(y, height * px - y))
        ramp = np.clip(edge / FEATHER_M, 0.0, 1.0)
        band.WriteArray((ramp * 255.0 + 0.5).astype(np.uint8), 0, row0)


def build(name: str, grid: Grid, *, feather: bool) -> Path:
    source = gdal.Open(str(SOURCE))
    if source is None:
        raise FileNotFoundError(f"cannot open source raster: {SOURCE}")

    west, east, south, north = grid.extent
    print(f"  {name}  {grid.width}x{grid.height} @ {grid.px} m")
    print(f"    extent E {west:.0f}..{east:.0f}  N {south:.0f}..{north:.0f}")
    print(f"    bands  {'RGB + blend-mask alpha' if feather else 'RGB'}")

    output = CACHE / name
    # classic TIFF (BIGTIFF=NO): Tyf, which BlenderGIS' raster importer uses,
    # cannot read BigTIFF. bpy.data.images.load copes either way, but keeping
    # one convention avoids a surprise later.
    dataset = gdal.GetDriverByName("GTiff").Create(
        str(output),
        grid.width,
        grid.height,
        4 if feather else 3,
        gdal.GDT_Byte,
        options=[
            "TILED=YES",
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "ZLEVEL=6",
            "BIGTIFF=NO",
            "NUM_THREADS=ALL_CPUS",
        ],
    )
    dataset.SetGeoTransform(grid.geotransform)
    dataset.SetProjection(source.GetProjection())
    write_rgb(dataset, source, grid)
    if feather:
        write_blend_mask(dataset, grid)
    dataset.FlushCache()
    dataset = None

    magic = output.read_bytes()[:4].hex()
    if magic != "49492a00":
        raise RuntimeError(f"{output} is not a classic TIFF (magic {magic})")
    print(
        f"    wrote {output.relative_to(ROOT)} "
        f"({output.stat().st_size / 1e6:.0f} MB, classic TIFF)"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "base", "massif"],
        help="which raster to build (default: all)",
    )
    args = parser.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"source: {SOURCE.relative_to(ROOT)}")
    if args.target in ("all", "massif"):
        build("tex_massif_1m.tif", MASSIF, feather=True)
    if args.target in ("all", "base"):
        build("tex_base_3p2.tif", BASE, feather=False)
    return 0


if __name__ == "__main__":
    gdal.UseExceptions()
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
