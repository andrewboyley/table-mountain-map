#!/usr/bin/env python3
"""Build a 5 m contour-derived DEM without opening QGIS.

TODO: move this pipeline into a QGIS Processing model, like the trail, peak
and hillshade pipelines in `qgis/processing/`. Until then this script is the
record of the build.

The raster is a model surface interpolated from the City of Cape Town 2 m
contours. It is not the City's original LiDAR DEM and must never be described
as surveyed or measured raster elevation data.
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
from pathlib import Path

from osgeo import gdal, ogr

ROOT = Path(__file__).resolve().parents[1]
CONTOURS = ROOT / "data/vector/coct/contours_2m_within_bound.gpkg"
CONTOUR_LAYER = "contours_2m_within_bound"
BOUNDARY = ROOT / "data/vector/bound/bound.shp"
OUTPUT = (
    ROOT / "data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif"
)
CACHE = ROOT / "cache/contour_dem"
NODATA = -9999.0
RESOLUTION = 5.0
# The contour clip is incomplete at the western and southern sides of `bound`.
# 11,000 five-metre cells (55 km) spans the full output diagonal so every
# interior target cell can be estimated, while the final mask still controls
# the exact analysis area.
FILL_DISTANCE_PIXELS = 11000


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def aligned_bounds(path: Path, resolution: float) -> tuple[float, float, float, float]:
    dataset = ogr.Open(str(path))
    if dataset is None:
        raise RuntimeError(f"Cannot open boundary: {path}")
    layer = dataset.GetLayer(0)
    xmin, xmax, ymin, ymax = layer.GetExtent()
    return (
        math.floor(xmin / resolution) * resolution,
        math.floor(ymin / resolution) * resolution,
        math.ceil(xmax / resolution) * resolution,
        math.ceil(ymax / resolution) * resolution,
    )


def ensure_input() -> None:
    for path in (CONTOURS, BOUNDARY):
        if not path.exists():
            raise FileNotFoundError(path)

    dataset = ogr.Open(str(CONTOURS))
    if dataset is None:
        raise RuntimeError(f"Cannot open contours: {CONTOURS}")
    layer = dataset.GetLayerByName(CONTOUR_LAYER)
    if layer is None:
        raise RuntimeError(f"Missing contour layer: {CONTOUR_LAYER}")
    if layer.GetFeatureCount() == 0:
        raise RuntimeError("Contour layer is empty")
    if layer.FindFieldIndex("ELVT", True) < 0:
        raise RuntimeError("Contour layer does not contain the ELVT elevation field")


def set_metadata(path: Path, bounds: tuple[float, float, float, float]) -> None:
    dataset = gdal.Open(str(path), gdal.GA_Update)
    if dataset is None:
        raise RuntimeError(f"Cannot write metadata to {path}")
    dataset.SetMetadata(
        {
            "TITLE": "Table Mountain 5 m contour-derived elevation surface",
            "SOURCE_DATASET": str(CONTOURS.relative_to(ROOT)),
            "SOURCE_LAYER": CONTOUR_LAYER,
            "SOURCE_ELEVATION_FIELD": "ELVT",
            "SOURCE_CONTOUR_INTERVAL_M": "2",
            "SOURCE_VERTICAL_LINEAGE": (
                "COCT 2019 2 m contours derived from the 2019 LiDAR 5 m DEM; "
                "SA Land Levelling Datum using SAGEOID2010."
            ),
            "INTERPOLATION": (
                "GDAL rasterize contour lines (ALL_TOUCHED) followed by "
                "GDALFillNodata inverse-distance interpolation; no smoothing."
            ),
            "GRID_RESOLUTION_M": "5",
            "BOUNDARY_MASK": str(BOUNDARY.relative_to(ROOT)),
            "NODATA_VALUE": str(int(NODATA)),
            "LIMITATION": (
                "This is an interpolated surface from contours, not the original "
                "measured LiDAR DEM. Contour source vertical accuracy is about 1 m."
            ),
            "BUILD_TOOL": f"GDAL {gdal.VersionInfo('RELEASE_NAME')}",
            "GRID_BOUNDS_EPSG_32734": ",".join(f"{value:.3f}" for value in bounds),
        }
    )
    band = dataset.GetRasterBand(1)
    band.SetDescription("Interpolated elevation (m)")
    band.SetNoDataValue(NODATA)
    band.FlushCache()
    dataset = None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Final GeoTIFF path (default: project elevation output)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Rebuild the final GeoTIFF even when it is current",
    )
    parser.add_argument(
        "--fill-distance-pixels",
        type=int,
        default=FILL_DISTANCE_PIXELS,
        help="Maximum inverse-distance search distance in pixels (default: %(default)s)",
    )
    args = parser.parse_args()

    if args.fill_distance_pixels <= 0:
        parser.error("--fill-distance-pixels must be positive")

    ensure_input()
    output = args.output.resolve()

    # Freshness of the final surface is judged against the inputs it depends
    # on: the contour source, the boundary mask (with its shapefile sidecars),
    # and this build script itself.
    inputs = [CONTOURS, BOUNDARY, Path(__file__).resolve()]
    for suffix in ("dbf", "shx", "prj"):
        sidecar = BOUNDARY.with_suffix(f".{suffix}")
        if sidecar.exists():
            inputs.append(sidecar)
    inputs_mtime = max(path.stat().st_mtime for path in inputs)

    rasterized = CACHE / "contour_cells_5m.tif"
    filled = CACHE / "contour_cells_5m_filled.tif"
    masked = CACHE / "contour_cells_5m_masked.tif"
    final_fresh = output.exists() and output.stat().st_mtime >= inputs_mtime
    intermediates_fresh = all(
        path.exists() and path.stat().st_mtime >= inputs_mtime
        for path in (rasterized, filled)
    )

    if final_fresh and intermediates_fresh:
        print(f"Up to date: {output} and validation intermediates", flush=True)
        return 0

    for executable in ("gdal_rasterize", "gdal_fillnodata", "gdalwarp"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required GDAL command is not available: {executable}")

    CACHE.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_final = not final_fresh or args.overwrite
    for path in (rasterized, filled, masked):
        if path.exists():
            path.unlink()
    bounds = aligned_bounds(BOUNDARY, RESOLUTION)
    xmin, ymin, xmax, ymax = bounds
    width = round((xmax - xmin) / RESOLUTION)
    height = round((ymax - ymin) / RESOLUTION)
    print(
        f"Grid: {width} x {height} cells at {RESOLUTION:g} m; "
        f"EPSG:32734 bounds {xmin:g},{ymin:g},{xmax:g},{ymax:g}",
        flush=True,
    )

    creation_options = ["TILED=YES", "COMPRESS=LZW", "BIGTIFF=IF_SAFER"]
    run(
        [
            "gdal_rasterize",
            "-l",
            CONTOUR_LAYER,
            "-a",
            "ELVT",
            "-at",
            "-init",
            str(int(NODATA)),
            "-a_nodata",
            str(int(NODATA)),
            "-te",
            str(xmin),
            str(ymin),
            str(xmax),
            str(ymax),
            "-tr",
            str(RESOLUTION),
            str(RESOLUTION),
            "-tap",
            "-a_srs",
            "EPSG:32734",
            "-ot",
            "Float32",
            "-of",
            "GTiff",
            *[item for option in creation_options for item in ("-co", option)],
            str(CONTOURS),
            str(rasterized),
        ]
    )
    run(
        [
            "gdal_fillnodata",
            "-interp",
            "inv_dist",
            "-md",
            str(args.fill_distance_pixels),
            "-si",
            "0",
            "-of",
            "GTiff",
            *[item for option in creation_options for item in ("-co", option)],
            str(rasterized),
            str(filled),
        ]
    )
    run(
        [
            "gdalwarp",
            "-overwrite",
            "-r",
            "near",
            "-cutline",
            str(BOUNDARY),
            "-dstnodata",
            str(int(NODATA)),
            "-te",
            str(xmin),
            str(ymin),
            str(xmax),
            str(ymax),
            "-tr",
            str(RESOLUTION),
            str(RESOLUTION),
            "-tap",
            "-t_srs",
            "EPSG:32734",
            "-ot",
            "Float32",
            "-of",
            "GTiff",
            *[item for option in creation_options for item in ("-co", option)],
            str(filled),
            str(masked),
        ]
    )

    # gdalwarp uses the source's NoData value when resampling, which can leave
    # a few contour constraints where overlapping input lines were rasterized
    # in a different order. Restore every burned contour cell explicitly so
    # the final surface honours its discrete elevation constraints exactly.
    final_dataset = gdal.Open(str(masked), gdal.GA_Update)
    constraint_dataset = gdal.Open(str(rasterized))
    if final_dataset is None or constraint_dataset is None:
        raise RuntimeError("Cannot reopen interpolation output and contour constraints")
    final_band = final_dataset.GetRasterBand(1)
    constraint_band = constraint_dataset.GetRasterBand(1)
    boundary_mask = gdal.GetDriverByName("MEM").Create(
        "", final_dataset.RasterXSize, final_dataset.RasterYSize, 1, gdal.GDT_Byte
    )
    boundary_mask.SetGeoTransform(final_dataset.GetGeoTransform())
    boundary_mask.SetProjection(final_dataset.GetProjection())
    boundary_mask.GetRasterBand(1).Fill(0)
    mask_options = gdal.RasterizeOptions(
        burnValues=[1], layers=["bound"], allTouched=False
    )
    if gdal.Rasterize(boundary_mask, str(BOUNDARY), options=mask_options) is None:
        raise RuntimeError("Cannot rasterize boundary mask")
    mask_band = boundary_mask.GetRasterBand(1)
    for row in range(0, final_dataset.RasterYSize, 512):
        rows = min(512, final_dataset.RasterYSize - row)
        surface = final_band.ReadAsArray(0, row, final_dataset.RasterXSize, rows)
        constraints = constraint_band.ReadAsArray(
            0, row, final_dataset.RasterXSize, rows
        )
        inside = mask_band.ReadAsArray(0, row, final_dataset.RasterXSize, rows).astype(
            bool
        )
        constraint_cells = (constraints != NODATA) & inside
        surface[~inside] = NODATA
        surface[constraint_cells] = constraints[constraint_cells]
        final_band.WriteArray(surface, 0, row)
    final_band.FlushCache()
    final_dataset = None
    constraint_dataset = None
    if not write_final:
        # The final surface is already current, so keep it untouched. Only
        # the validation intermediates were missing or outdated.
        if masked.exists():
            masked.unlink()
        print(f"Validation intermediates rebuilt; kept {output}", flush=True)
        return 0

    if output.exists():
        output.unlink()
    masked.replace(output)
    set_metadata(output, bounds)
    print(f"Wrote {output}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
