# Run the pre-commit gate
default: check

# QGIS Processing models are COPIES in the active profile's models directory.
# qgis_process resolves `model:<name>` from there, never from the repo, so a
# model that is not installed cannot run. Resolved at parse time from the
# highest-numbered QGIS profile so it tracks the installed QGIS version.
QGIS_MODEL_DIR := `ls -d "$HOME"/.local/share/QGIS/QGIS*/profiles/default/processing/models 2>/dev/null | sort -V | tail -1`

# Copy the repo's Processing models into the active QGIS profile (idempotent)
install-models:
    @test -n "{{QGIS_MODEL_DIR}}" || { echo "no QGIS profile models directory found; is QGIS installed?" >&2; exit 1; }
    for model in qgis/processing/*.model3; do install -D -m 0644 "$model" "{{QGIS_MODEL_DIR}}/$(basename "$model")"; done
    @echo "installed into {{QGIS_MODEL_DIR}}"

# Fetch the two upstream source files into data/ (Geofabrik PBF, COCT 2 m
# contour zip). See REPRODUCTION.md for the verification each download gets
# and for every step that derives from these two sources.
fetch-sources *args:
    python3 scripts/fetch_sources.py {{ args }}

# Clip the rolling South Africa extract to the fixed Table Mountain extent.
prepare-osm:
    mkdir -p data/osm
    osmium extract --strategy complete_ways \
      -b 18.30722,-34.35834,18.4979771,-33.9117846 \
      data/osm/south-africa-latest.osm.pbf -O \
      -o data/osm/table-mountain-bound-extent.osm.pbf

# Derive the OSM park relation and its north-up crop extent.
prepare-boundary: prepare-osm install-models
    mkdir -p data/vector/osm
    QT_QPA_PLATFORM=offscreen qgis_process run model:boundary_extract \
      '--INPUT_PBF=data/osm/table-mountain-bound-extent.osm.pbf|layername=multipolygons' \
      --boundary_geopackage=data/vector/osm/tmnp_relation_338191.gpkg \
      --northup_extent_geopackage=data/vector/osm/tmnp_extent_north_up.gpkg

# Reproject and clip the user-supplied CoCT contour Shapefile to TMNP.
prepare-contours: prepare-boundary
    mkdir -p data/vector/coct
    QT_QPA_PLATFORM=offscreen qgis_process run model:contour_prepare \
      --INPUT_CONTOURS=data/vector/coct/ground_level_map_2m_contours/Ground_Level_Map_2m_Contours.shp \
      --INPUT_BOUNDARY=data/vector/osm/tmnp_relation_338191.gpkg \
      --prepared_contours_geopackage=data/vector/coct/contours_2m_within_bound.gpkg

# Rebuild the trail GeoPackages from the OSM extract
rebuild-trails: prepare-boundary
    qgis_process run model:trail_rebuild \
      --ELLIPSOID=EPSG:7030 \
      --INPUT_PBF=data/osm/table-mountain-bound-extent.osm.pbf \
      --INPUT_BOUNDARY=data/vector/osm/tmnp_relation_338191.gpkg \
      --HIGHWAY_VALUES=path,steps,footway \
      --output_named=data/vector/osm/tm_hiking_trails_named.gpkg \
      --output_dissolved=data/vector/osm/tm_hiking_trails_dissolved.gpkg \
      --output_supplement=data/vector/osm/tm_trail_supplement.gpkg

# Rebuild the named-summits GeoPackage from the OSM extract.
# osmium reads the PBF, not the GDAL OSM driver that QGIS would use: that
# driver drops the `ele` tag from both its field list and other_tags, so peaks
# read through it arrive with no elevation. The cache/ intermediates are
# regenerable and gitignored; the model applies the name+ele filter.
rebuild-peaks: prepare-osm install-models
    mkdir -p cache data/vector/osm
    osmium tags-filter data/osm/table-mountain-bound-extent.osm.pbf \
      n/natural=peak -O -o cache/peaks.osm.pbf
    osmium export cache/peaks.osm.pbf --add-unique-id=type_id -f geojson \
      -O -o cache/peaks.geojson
    qgis_process run model:peak_extract \
      --INPUT_PEAKS=cache/peaks.geojson \
      --output_peaks=data/vector/osm/tm_peaks_named_with_ele.gpkg

# Rebuild the vector thresholded hillshade classes from the contour DEM.
# Every model parameter is passed explicitly here, so the recipe is the record
# of the exact settings and does not drift if a model default changes.
# Every step is a native QGIS or GDAL provider algorithm: inspect it in
# Processing > Models > hillshade_classes, or read
# qgis/processing/hillshade_classes.model3.
#
# The COARSE_RES step is what decides the look. Thresholding the 5 m DEM
# directly gives 127617 regions, 127073 of them under 0.01 km2: every class
# boundary is a one-pixel staircase, so the result is speckle. Averaging the
# hillshade onto an 80 m grid before thresholding is a true low-pass filter; it
# collapses those 127617 regions to a few hundred large ones and conserves
# total area, where sieving or smoothing afterwards does not.
#
# The last three model steps then round the 80 m staircase the same way:
# Chaikin smoothing, vertex reduction, and a geometry repair for the
# self-intersections smoothing can introduce. Smoothing is tuned to many passes
# at a small offset rather than few passes at a large one, because the area a
# pass removes goes as the square of the offset while the pass count only
# controls how far the curve is pulled off the grid. Measured over this DEM's
# 1055.7 km2 footprint: 2 passes at 0.25 leaves 28% of the boundary on the cell
# grid and loses 136 km2 of interior coverage; 12 passes at 0.03 leaves 3% and
# loses 0.3 km2, for 1052.7 km2 of polygons in 116 features. The simplify
# tolerance is a quarter of a cell, which drops the vertex count that Chaikin
# inflates by about sixteenfold without moving the curve.
#
# This recipe needs two libraries that GDAL's own drivers link against but
# CachyOS does not install by default: podofo (libpodofo.so.2, for the PDF
# driver) and mariadb-libs (libmariadb.so.3, for the MySQL driver). Without
# them QGIS aborts with SIGABRT the moment it has to invent a name for a
# temporary raster, because enumerating the broken drivers raises inside a
# PyQt6 virtual call. QGIS overwrites GDAL_SKIP with an empty string at
# startup, so there is no environment variable that works around it:
#   sudo pacman -S podofo mariadb-libs
hillshade-classes: build-dem
    mkdir -p data/vector/terrain
    qgis_process run model:hillshade_classes \
      --INPUT=data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif \
      --AZIMUTH=315 \
      --ALTITUDE=45 \
      --Z_FACTOR=1 \
      --COMPUTE_EDGES=false \
      --COARSE_RES=80 \
      --SHADOW_MAX=128 \
      --MID_MAX=192 \
      --SIEVE_PIXELS=16 \
      --EIGHT_CONNECTEDNESS=false \
      --SMOOTH_ITERATIONS=12 \
      --SMOOTH_OFFSET=0.03 \
      --SMOOTH_MAX_ANGLE=180 \
      --SIMPLIFY_TOLERANCE=20 \
      --output_classes=data/vector/terrain/hillshade_classes.gpkg

# Rebuild the officially acknowledged trail set from the named trails.
# Depends on rebuild-trails, which produces the layer this filters. The model
# carries its own copy of the reviewed name list, so no side script runs here.
rebuild-trails-official: rebuild-trails
    qgis_process run model:trail_official \
      '--INPUT_NAMED=data/vector/osm/tm_hiking_trails_named.gpkg|layername=hiking_trails_named' \
      --output_official=data/vector/osm/tm_hiking_trails_official.gpkg

# Rebuild the contour-derived 5 m DEM through the QGIS Processing model.
build-dem: prepare-contours
    mkdir -p data/elevation
    QT_QPA_PLATFORM=offscreen qgis_process run model:contour_dem \
      '--INPUT_CONTOURS=data/vector/coct/contours_2m_within_bound.gpkg|layername=contours_2m_within_bound' \
      --INPUT_BOUNDARY=data/vector/osm/tmnp_relation_338191.gpkg \
      --ELEVATION_FIELD=ELVT \
      --CELL_SIZE=5 \
      --FILL_DISTANCE=11000

# Rebuild the DEM overview pyramid and sidecars (never rewrites the raster)
build-overviews:
    gdaladdo -ro -r average \
      data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif \
      2 4 8 16 32

# Recreate all GIS vector and terrain outputs from the two local sources.
rebuild-all: prepare-osm prepare-boundary prepare-contours build-dem build-overviews rebuild-trails rebuild-peaks rebuild-trails-official hillshade-classes

# Run all pre-commit hooks across every file
check:
    pre-commit run --all-files

# Run pre-commit hooks on staged files only
check-staged:
    pre-commit

# List the MapProxy seed tasks and their tile counts without fetching anything
seed-mapproxy-list:
    docker compose -f docker-mapproxy/docker-compose.yml exec -T mapproxy \
      gosu mapproxy mapproxy-seed \
        -f /multi_mapproxy/mapproxy.yaml -s /multi_mapproxy/seed.yaml \
        -n --summary

# Uncached WMS tiles cost an upstream round-trip each, so a cold view fills in
# slowly and QGIS abandons the slow requests. Seeding makes every tile a local
# cache hit. This puts real load on the CoCT WMS; keep jobs modest.
#
# Parameter is named jobs, not concurrency: `concurrency` is a reserved just
# keyword and would expand to the literal "concurrency=N" instead of the value.
#
# tasks=ALL, or a comma-separated task list.
# Pass BOTH positionally: `just seed-mapproxy <tasks> <jobs>`.
# This just version (1.58.0) binds `name=value` positionally too, so
# `jobs=4` would be taken as the literal string "jobs=4".
#
# Seed as the same user the service runs as, so the cache needs no special
# permissions and no repair after seeding.
#
# Why gosu: the image declares no USER, so a bare `docker compose exec` lands on
# root, and root-owned 0644 tiles are unwritable by the unprivileged service
# (PermissionError Errno 13 on every cache write). That is the whole origin of
# the old chown-after-seed. `gosu mapproxy` is the image's own privilege-drop
# mechanism -- the entrypoint uses it for uwsgi via `exec gosu "$USER" uwsgi` --
# so the seeder and the service share one uid and MapProxy's stock 0644/0755
# output is already correct. No chmod, no chown, no file_permissions override.
#
# MAPPROXY_USER_ID in docker-compose.yml stays the single source of truth: gosu
# resolves the name `mapproxy`, which the entrypoint creates with that uid, so
# changing the uid there needs no edit here.
seed-mapproxy tasks='ALL' jobs='4':
    docker compose -f docker-mapproxy/docker-compose.yml exec -T mapproxy \
      gosu mapproxy mapproxy-seed \
        -f /multi_mapproxy/mapproxy.yaml -s /multi_mapproxy/seed.yaml \
        -c {{ jobs }} --seed={{ tasks }}

# Report any cache entry the service cannot write. Runs as the service uid so
# `find -writable` answers the real question -- can MapProxy write here -- rather
# than proxying it with an ownership test. Ownership is deliberately not the
# check: a root-owned file the service can still write is not a problem.
#
# A fresh cache always passes, since seeding now runs as the service uid. This
# gate is for caches seeded by the old root-based recipe, which is the only way
# unwritable entries can still appear.
seed-mapproxy-checkperm:
    docker compose -f docker-mapproxy/docker-compose.yml exec -T mapproxy sh -c '\
      bad=$(find /cache_data/mapproxy ! -writable | wc -l); \
      if [ "$bad" -ne 0 ]; then \
        echo "FAIL: $bad cache entries are not writable by the service"; \
        echo "      seeded as root before the seeder dropped privileges?"; \
        echo "      repair with: just seed-mapproxy-fixperm"; \
        exit 1; \
      fi; \
      echo "PASS: every cache entry is writable by the service"'

# Repair a cache left unwritable by the old root-based seeding recipe. Handing
# the files to the service uid is the same fix the chown used to do, and it also
# covers entries that root created inside directories the service cannot enter.
# Only needed for a pre-existing cache; a freshly seeded one never needs it.
seed-mapproxy-fixperm:
    docker compose -f docker-mapproxy/docker-compose.yml exec -T mapproxy sh -c '\
      u=$(stat -c %u /cache_data/mapproxy); g=$(stat -c %g /cache_data/mapproxy); \
      chown -R $u:$g /cache_data/mapproxy && echo "cache ownership set to $u:$g"'

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

# Validate every checked-in Processing model headlessly. This does not require data.
model-validate:
    for model in qgis/processing/*.model3; do QT_QPA_PLATFORM=offscreen qgis_process help "$model" >/dev/null; done

# Bump pinned pre-commit hook revisions; review the diff before committing
hooks-update:
    pre-commit autoupdate

# Parse and validate .pre-commit-config.yaml
hooks-validate:
    pre-commit validate-config
