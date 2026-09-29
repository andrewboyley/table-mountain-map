## Why

The project file is a hand-edited binary artifact: QGIS rewrites the 3D terrain
binding and texture size on every save (requiring a regex re-patch each time),
commits are opaque `Bin X -> Y` diffs, and nothing machine-checks the project's
invariants. The CoCT aerial also drifted onto an XYZ stopgap because the
MapProxy WMS returned blank tiles — root cause now known (upstream serves real
imagery only in EPSG:32734; the cache grid was webmercator). This change makes
the project a reproducible, machine-verified artifact and restores the aerial
from the MapProxy WMS.

## What Changes

- **Prerequisite (landed)**: `docker-mapproxy` `coct_aerial_cache` now caches
  on a UTM 34S (`EPSG:32734`) grid covering the TMNP crop extent (upstream
  erdas WMS returns blank in 3857, imagery in 32734 — verified 2026-09-29),
  keeping `styles: ''`. Verify: MapProxy WMS GetMap in 32734 returns
  non-white imagery; commit `mapproxy.yaml` + README note.
- Adds `scripts/build_project.py`: an idempotent enforcement build that loads
  the project, applies canonical invariants (structured tree, categorized
  trail renderer from `trail_colors.csv`, map themes, project CRS, relative
  paths, basemap sources) and stamps the canonical 3D scene XML (terrain
  theme, `texture-size="512"`, bloom, colour grading, camera) with layer ids
  resolved by name. Repeated runs produce byte-identical output.
- Stores the project as **plain XML** `qgis/table_mountain_3D.qgs` so diffs
  are reviewable; removes the `.qgz` from the repo (its embedded aux DB is
  empty — verified).
- Adds `scripts/verify_project.py`: an offscreen gate that loads the project
  and asserts: CRS `EPSG:32734`, relative paths, exactly one categorized trail
  layer with palette-complete categories, themes present, the 3D stamp intact,
  atlas coverage/pages (172), basemap sources (OSM XYZ, CoCT WMS 32734), and
  that all layer sources resolve. Non-zero exit on failure.
- Wires `verify_project` into `.pre-commit-config.yaml` (runs on project
  changes and in pre-push) alongside the existing `verify_data` gate.
- CoCT aerial layer in the project returns to the MapProxy **WMS** endpoint
  (`EPSG:32734`, layer `coct_aerial`); OSM stays on MapProxy XYZ.
- Updates README / `qgis/README` / `docs` for: `.qgs` storage, single trail
  layer, WMS aerial, UTM cache grid; attribution and restricted-imagery flags
  retained.

## Capabilities

### New Capabilities
- `basemap-services`: cached OSM XYZ and CoCT aerial WMS (project CRS) served
  from the local MapProxy with the aerial cache in EPSG:32734.
- `project-build`: the project file is reproducible from a build script and
  machine-verified by an offscreen gate wired into pre-commit.

### Modified Capabilities
- `project-provenance`: documentation must describe the new storage format,
  service model and verification gate accurately.

## Impact

- `scripts/build_project.py`, `scripts/verify_project.py` (new; patterns
  borrowed from `scripts/apply_terrain_texture.py`).
- `.pre-commit-config.yaml`.
- `qgis/table_mountain_3D.qgz` → `qgis/table_mountain_3D.qgs` (storage
  change, **BREAKING** for paths referencing the `.qgz`).
- `docker-mapproxy/mapproxy_configuration/mapproxy.yaml` (UTM grid; landed).
- README, `qgis/README`, docs, pre-commit runners.
