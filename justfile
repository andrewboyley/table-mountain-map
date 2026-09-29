# Rebuild the QGIS project offscreen, then run every verification gate
default: build verify

# Rebuild qgis/table_mountain_3D.qgs offscreen (byte-identical across runs)
build:
    QT_QPA_PLATFORM=offscreen python3 scripts/build_project.py

# Verify the QGIS project offscreen (backs the verify-project pre-commit hook)
verify-project:
    QT_QPA_PLATFORM=offscreen python3 scripts/verify_project.py

# Verify data contracts for one subcommand or 'all' (crop extent, rasters, trails, docs)
verify-data subcommand='all':
    python3 scripts/verify_data.py {{ subcommand }}

# Rebuild the trail GeoPackages from the OSM extract
rebuild-trails:
    qgis_process run model:trail_rebuild \
      --ELLIPSOID=EPSG:7030 \
      --INPUT_PBF=data/osm/table-mountain-bound-extent.osm.pbf \
      --INPUT_BOUNDARY=data/vector/osm/tmnp_relation_338191.gpkg \
      --HIGHWAY_VALUES=path,steps,footway \
      --output_named=data/vector/osm/tm_hiking_trails_named.gpkg \
      --output_dissolved=data/vector/osm/tm_hiking_trails_dissolved.gpkg \
      --output_supplement=data/vector/osm/tm_trail_supplement.gpkg

# Rebuild the contour DEM from the boundary mask (skips when up to date)
build-dem:
    python3 scripts/build_contour_dem.py

# Force a rebuild of a current DEM surface (build-dem skips when up to date)
build-dem-force:
    python3 scripts/build_contour_dem.py --overwrite

# Rebuild the DEM overview pyramid and sidecars (never rewrites the raster)
build-overviews:
    gdaladdo -ro -r average \
      data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif \
      2 4 8 16 32

# Verify the contour DEM bounds against the boundary envelope
verify-dem: build-dem
    python3 scripts/verify_contour_dem.py

# Every verification gate: data, project, DEM
verify: verify-data verify-project verify-dem

# Run all pre-commit hooks across every file
check:
    pre-commit run --all-files

# Run pre-commit hooks on staged files only
check-staged:
    pre-commit

# Run the pre-push stage hooks (full data verifier and project gate)
check-push:
    pre-commit run --hook-stage pre-push --all-files

# Clear the temporary cache (all contents are regenerable)
cache-clear:
    rm -rf cache/*

# Format scripts with ruff (mirrors the ruff-format pre-commit hook)
format:
    ruff format scripts/

# Lint scripts with ruff (mirrors the ruff pre-commit hook); fix with lint-fix
lint:
    ruff check scripts/

lint-fix:
    ruff check --fix scripts/

# Validate the trail_rebuild Processing model headlessly
model-validate:
    QT_QPA_PLATFORM=offscreen qgis_process help qgis/processing/trail_rebuild.model3

# Bump pinned pre-commit hook revisions; review the diff before committing
hooks-update:
    pre-commit autoupdate

# Parse and validate .pre-commit-config.yaml
hooks-validate:
    pre-commit validate-config
