#!/usr/bin/env python3
"""Validate the headless 5 m contour-derived elevation surface.

A passing report proves technical validity and agreement with the source
contours. It does not establish independent, survey-grade terrain accuracy.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr, osr

ROOT = Path(__file__).resolve().parents[1]
CONTOURS = ROOT / "data/vector/coct/contours_2m_within_bound.gpkg"
CONTOUR_LAYER = "contours_2m_within_bound"
BOUNDARY = ROOT / "qgis/bound.shp"
DEFAULT_DEM = (
    ROOT / "data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif"
)
CACHE = ROOT / "cache/contour_dem"
NODATA = -9999.0
RESOLUTION = 5.0
SOURCE_MIN = -14.0
SOURCE_MAX = 1084.0
RANGE_TOLERANCE_M = 2.0


def fail(message: str) -> None:
    raise RuntimeError(message)


def aligned_bounds(path: Path) -> tuple[float, float, float, float]:
    dataset = ogr.Open(str(path))
    if dataset is None:
        fail(f"Cannot open boundary: {path}")
    xmin, xmax, ymin, ymax = dataset.GetLayer(0).GetExtent()
    return (
        math.floor(xmin / RESOLUTION) * RESOLUTION,
        math.floor(ymin / RESOLUTION) * RESOLUTION,
        math.ceil(xmax / RESOLUTION) * RESOLUTION,
        math.ceil(ymax / RESOLUTION) * RESOLUTION,
    )


def rasterized_boundary_mask(dataset: gdal.Dataset) -> np.ndarray:
    mask = gdal.GetDriverByName("MEM").Create(
        "", dataset.RasterXSize, dataset.RasterYSize, 1, gdal.GDT_Byte
    )
    mask.SetGeoTransform(dataset.GetGeoTransform())
    mask.SetProjection(dataset.GetProjection())
    mask.GetRasterBand(1).Fill(0)
    options = gdal.RasterizeOptions(burnValues=[1], allTouched=False, layers=["bound"])
    result = gdal.Rasterize(mask, str(BOUNDARY), options=options)
    if result is None:
        fail("Unable to rasterize the boundary for validation")
    values = mask.GetRasterBand(1).ReadAsArray()
    mask = None
    return values.astype(bool)


def contour_constraint_residuals(
    dataset: gdal.Dataset, values: np.ndarray
) -> dict[str, float | int]:
    """Compare the output with the rasterized contour constraints.

    A five-metre pixel centre cannot in general lie exactly on a two-metre
    contour vertex. Comparing arbitrary vertices to pixel-centre values would
    therefore measure sampling offset, not whether the interpolation preserved
    its input. The burned contour raster is the actual discrete constraint set.
    """
    burned_path = CACHE / "contour_cells_5m.tif"
    burned = gdal.Open(str(burned_path))
    if burned is None:
        fail(f"Missing rasterized contour constraints: {burned_path}")
    source = burned.GetRasterBand(1).ReadAsArray().astype(np.float32, copy=False)
    constraints = source != NODATA
    if not np.any(constraints):
        fail("Rasterized contour constraints contain no valid cells")
    boundary_mask = rasterized_boundary_mask(dataset)
    # A small number of source contour pixels lie beyond the selected output
    # mask at its rasterized edge. They are deliberately NoData in the final
    # product, so only constraints inside the boundary are applicable.
    constraints &= boundary_mask
    sampled = values[constraints].astype(np.float64)
    expected = source[constraints].astype(np.float64)
    missing = sampled == NODATA
    residuals = sampled[~missing] - expected[~missing]
    if np.any(~np.isfinite(residuals)):
        fail("Output is invalid at one or more rasterized contour constraints")
    absolute = np.abs(residuals)
    return {
        "count": int(sampled.size),
        "missing_constraints": int(np.count_nonzero(missing)),
        "bias_m": float(np.mean(residuals)),
        "mae_m": float(np.mean(absolute)),
        "rmse_m": float(np.sqrt(np.mean(np.square(residuals)))),
        "p95_abs_m": float(np.percentile(absolute, 95)),
        "max_abs_m": float(np.max(absolute)),
        "within_1m_percent": float(np.mean(absolute <= 1.0) * 100),
        "within_2m_percent": float(np.mean(absolute <= 2.0) * 100),
        "method": "Output compared to the exact 5 m rasterized contour-cell constraints.",
    }


def maclear_beacon_sample(
    dataset: gdal.Dataset, values: np.ndarray
) -> dict[str, float | None]:
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromWkt(dataset.GetProjection())
    source.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    x, y, _ = osr.CoordinateTransformation(source, target).TransformPoint(
        18.4255552, -33.966832
    )
    origin_x, pixel_x, _, origin_y, _, pixel_y = dataset.GetGeoTransform()
    column = int((x - origin_x) / pixel_x)
    row = int((y - origin_y) / pixel_y)
    value: float | None = None
    if 0 <= row < dataset.RasterYSize and 0 <= column < dataset.RasterXSize:
        candidate = float(values[row, column])
        if candidate != NODATA and math.isfinite(candidate):
            value = candidate
    return {
        "x_epsg_32734": x,
        "y_epsg_32734": y,
        "dem_elevation_m": value,
        "osm_peak_reference_m": 1086.0,
        "ngi_survey_reference_m": 1087.6,
        "difference_from_osm_peak_m": None if value is None else value - 1086.0,
        "difference_from_ngi_survey_m": None if value is None else value - 1087.6,
        "interpretation": "Plausibility check only; these external reference values do not prove grid-cell accuracy.",
    }


def make_diagnostics(dem: Path) -> dict[str, str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    outputs = {
        "hillshade": CACHE / "contour_dem_5m_hillshade.tif",
        "slope_degrees": CACHE / "contour_dem_5m_slope_degrees.tif",
    }
    if shutil.which("gdaldem") is None:
        return {key: "gdaldem unavailable" for key in outputs}
    commands = [
        [
            "gdaldem",
            "hillshade",
            str(dem),
            str(outputs["hillshade"]),
            "-compute_edges",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
            "-co",
            "TILED=YES",
        ],
        [
            "gdaldem",
            "slope",
            str(dem),
            str(outputs["slope_degrees"]),
            "-compute_edges",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
            "-co",
            "TILED=YES",
        ],
    ]
    for command in commands:
        subprocess.run(command, check=True)
    return {key: str(path.relative_to(ROOT)) for key, path in outputs.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dem", type=Path, default=DEFAULT_DEM, help="GeoTIFF to verify"
    )
    parser.add_argument(
        "--report", type=Path, default=CACHE / "contour_dem_5m_validation.json"
    )
    parser.add_argument(
        "--skip-diagnostics",
        action="store_true",
        help="Do not create hillshade and slope diagnostics",
    )
    args = parser.parse_args()

    dem = args.dem.resolve()
    if not dem.exists():
        parser.error(f"DEM does not exist: {dem}")
    dataset = gdal.Open(str(dem))
    if dataset is None:
        fail(f"GDAL cannot open {dem}")

    errors: list[str] = []
    checks: dict[str, object] = {}
    checks["gdal_driver"] = dataset.GetDriver().ShortName
    checks["band_count"] = dataset.RasterCount
    band = dataset.GetRasterBand(1) if dataset.RasterCount else None
    if dataset.RasterCount != 1:
        errors.append(f"Expected one raster band, found {dataset.RasterCount}")
    if band is None:
        fail("Raster has no band to validate")
    checks["data_type"] = gdal.GetDataTypeName(band.DataType)
    if band.DataType != gdal.GDT_Float32:
        errors.append(f"Expected Float32, found {checks['data_type']}")
    checks["nodata"] = band.GetNoDataValue()
    if band.GetNoDataValue() != NODATA:
        errors.append(f"Expected NoData {NODATA}, found {band.GetNoDataValue()}")

    expected_bounds = aligned_bounds(BOUNDARY)
    geotransform = dataset.GetGeoTransform()
    actual_bounds = (
        geotransform[0],
        geotransform[3] + dataset.RasterYSize * geotransform[5],
        geotransform[0] + dataset.RasterXSize * geotransform[1],
        geotransform[3],
    )
    checks["dimensions"] = {"width": dataset.RasterXSize, "height": dataset.RasterYSize}
    checks["geotransform"] = list(geotransform)
    checks["expected_bounds"] = expected_bounds
    checks["actual_bounds"] = actual_bounds
    if not (
        abs(geotransform[1] - RESOLUTION) < 1e-9
        and abs(geotransform[5] + RESOLUTION) < 1e-9
    ):
        errors.append(
            f"Expected {RESOLUTION} m north-up pixels, found {geotransform[1]}, {geotransform[5]}"
        )
    if any(
        abs(expected - actual) > 1e-6
        for expected, actual in zip(expected_bounds, actual_bounds)
    ):
        errors.append("Output bounds do not match the aligned boundary envelope")

    expected_srs = osr.SpatialReference()
    expected_srs.ImportFromEPSG(32734)
    actual_srs = osr.SpatialReference()
    actual_srs.ImportFromWkt(dataset.GetProjection())
    checks["crs"] = actual_srs.GetAuthorityCode(None)
    if not actual_srs.IsSame(expected_srs):
        errors.append("Output CRS is not EPSG:32734")

    metadata = dataset.GetMetadata()
    checks["interpolation"] = metadata.get("INTERPOLATION")
    checks["limitation"] = metadata.get("LIMITATION")
    for key in ("SOURCE_ELEVATION_FIELD", "INTERPOLATION", "LIMITATION"):
        if not metadata.get(key):
            errors.append(f"Missing required provenance metadata: {key}")

    values = band.ReadAsArray().astype(np.float32, copy=False)
    mask = rasterized_boundary_mask(dataset)
    valid = values != NODATA
    finite = np.isfinite(values[valid])
    if not np.all(finite):
        errors.append("Valid cells include non-finite values")
    outside_valid = int(np.count_nonzero(valid & ~mask))
    inside_missing = int(np.count_nonzero(~valid & mask))
    valid_values = values[valid]
    checks["mask"] = {
        "inside_cells": int(np.count_nonzero(mask)),
        "valid_cells": int(np.count_nonzero(valid)),
        "outside_valid_cells": outside_valid,
        "inside_missing_cells": inside_missing,
        "interior_coverage_percent": float(np.mean(valid[mask]) * 100),
    }
    if outside_valid:
        errors.append(f"Found {outside_valid} valid cells outside the boundary mask")
    if inside_missing:
        errors.append(f"Found {inside_missing} unfilled cells inside the boundary mask")
    if valid_values.size == 0:
        errors.append("Raster contains no valid elevation cells")
        statistics = {}
    else:
        statistics = {
            "min_m": float(np.min(valid_values)),
            "max_m": float(np.max(valid_values)),
            "mean_m": float(np.mean(valid_values)),
            "stddev_m": float(np.std(valid_values)),
        }
        if (
            statistics["min_m"] < SOURCE_MIN - RANGE_TOLERANCE_M
            or statistics["max_m"] > SOURCE_MAX + RANGE_TOLERANCE_M
        ):
            errors.append(
                "Raster elevations exceed the contour range beyond the allowed 2 m tolerance"
            )
    checks["elevation_statistics"] = statistics

    consistency = contour_constraint_residuals(dataset, values)
    checks["contour_constraint_residuals"] = consistency
    if consistency["missing_constraints"] or consistency["max_abs_m"] > 1e-6:
        errors.append(
            "Output does not preserve the rasterized contour elevation constraints"
        )
    checks["maclear_beacon_plausibility"] = maclear_beacon_sample(dataset, values)

    diagnostics = {} if args.skip_diagnostics else make_diagnostics(dem)
    checks["diagnostics"] = diagnostics
    checks["classification"] = (
        "contour-derived elevation surface; not a measured LiDAR DEM"
    )
    checks["external_accuracy_statement"] = (
        "Technical validity and internal contour agreement passed only if errors is empty. "
        "Independent survey-grade accuracy requires the raw LiDAR DEM/DTM or independent checkpoints."
    )

    report = {
        "technical_valid": not errors,
        "errors": errors,
        "checks": checks,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Report: {args.report}")
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
