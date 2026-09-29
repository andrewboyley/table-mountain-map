## Context

See `proposal.md` for motivation and the five `specs/` for the behaviour contracts. Three facts from the audit shape everything below:

- `qgis/bound.shp` is the **DEM boundary mask** — the envelope the contour-derived DEM is mesh-aligned and rasterized against — not the crop extent. `scripts/build_contour_dem.py` and `scripts/verify_contour_dem.py` read it as `BOUNDARY`; `verify_data.py` reads it as `LEGACY_CROP_EXTENT` to assert nothing still treats it as the authoritative crop rectangle (that role moved to `tmnp_extent_north_up.gpkg`).
- `build_project.py` does **not** reference `bound.shp` (only the contours GeoPackage and the DEM raster), so the `.qgs` rebuild is independent of the boundary move. The committed `.qgs` at HEAD is canonical (`sha256 45d126fd…`); the working tree carries a GUI-save drift whose fingerprints include an **absolute** `contours_2m_within_bound.gpkg` datasource next to the relative one.
- Tracked binaries today are entirely redundant: `data/elevation/*{ovr,aux.xml,wld}` (~115 MB, regenerable via the documented `gdaladdo`), `data/signal_hill_sunrise_4k.exr` (18.8 MB, referenced by no tracked Blender scene), `data/vector/tmnp/*` (7 files whose extent equals `tmnp_relation_338191.gpkg`), `blender/lions_head.blend` (4.5 MB, unreferenced), and `qgis/bound.*` (moving, not deleting).

QGIS research used below (Context7 against the official docs + visual changelogs): the installed **QGIS 4.2.2** is the current release line (4.2, July 2026). Relevant 4.x facts: categorized renderers for 3D symbols (4.2), MSAA / light bloom / colour grading (4.2), a camera-controls dialog that positions the 3D camera in map coordinates (4.2), `qgis_process help <model-file>` as the headless equivalent of Validate Model (needs `QT_QPA_PLATFORM=offscreen`), atlas option to limit coverage rendering to the current feature (4.0), Qt6 migration (4.0).

## Goals / Non-Goals

**Goals:**

- Every directory's name communicates its contents; the tracked tree contains only authoritative data, project artifacts, and load-bearing tooling.
- The `.qgs` is byte-deterministic again, GUI-save side effects are ignored and documented, and all existing gates stay green on every commit of this change.
- Commit-time gates catch the failure classes this repo has actually hit (oversized binaries, unparsable/unformatted Python, invalid Processing models).
- Each layer's QGIS presentation uses the native feature that fits it; adopted and declined features are written down so nothing is gratuitous.

**Non-Goals:**

- Rebuilding the DEM raster, reprojecting rasters, or changing the crop extent or raster footprints.
- Converting `bound.shp` to GeoPackage (see Open Questions — deliberately deferred, needs no spec change).
- Reinitialising git history, changing the trail pipeline, the MapProxy configuration, or the OSM attribution / CoCT imagery restriction statements.
- Writing a Blender scene build script (`scripts/blender/` still does not exist; `tmnp.blend` stays tracked per CONTRIBUTING, and the render pipeline stays non-reproducible).

## Decisions

### 1. The boundary shapefile moves to `data/vector/bound/` and keeps its name

`qgis/bound.*` → `data/vector/bound/bound.{shp,shx,dbf,prj}` via `git mv`. Keeping the basename `bound` is load-bearing: `build_contour_dem.py` and `verify_contour_dem.py` pass `layers=["bound"]` to `gdal.RasterizeOptions`, which selects the shapefile's (layer-name) basename. No geometry touches this rectangle; it stays distinct from the crop extent and remains the DEM mask.

**Alternatives:** *Merge into the crop-extent GeoPackage* — rejected: different semantics (DEM mask vs north-up crop), and it would rewrite the scripts and `model-crop-extent` reasoning. *Leave in `qgis/`* — rejected: `qgis/` is project artifacts only (`repository-layout`).

Script/verify/doc updates ride in the same commit so `verify_data.py` (whose `README.md` docs-gate scans `README.md`, `data/README.md`, `renders/README.md`, `cache/README.md`) stays green atomically: `BOUNDARY` in the two DEM scripts, `LEGACY_CROP_EXTENT` + the "not `qgis/bound.shp`" check message in `verify_data.py`, and any README path mentions.

### 2. Duplicate, superseded and orphaned binaries leave the tree

`git rm` (not just `--cached`, these are genuinely dead):

- `data/vector/tmnp/*` — its extent was verified identical to `tmnp_relation_338191.gpkg` (ogrinfo), so it is a true duplicate.
- `data/elevation/*_bgis.{tif.ovr,wld}` + the `_bgis` rows in `verify_data.py` `BIG_RASTERS` and `data/README.md` — superseded DEM variant.
- `data/signal_hill_sunrise_4k.exr` — no tracked `.blend` references it (`strings` on both scenes found zero path refs); it is the last big binary of the dormant render pipeline.
- `blender/lions_head.blend` — unreferenced scene, superseded by `tmnp.blend`.

`git rm --cached` (file stays on disk for the gates, disappears from git):

- `data/elevation/table_mountain_contours_2m_interpolated_5m_within_bound.tif.{ovr,aux.xml}` — regenerable by the documented `gdaladdo -ro`; ignored going forward so overview checks keep passing locally while clean checkouts document regeneration.

**Alternatives:** *Keep `signal_hill_sunrise_4k.exr` "just in case"* — rejected: 18.8 MB of tracked binary with no consumer, contradicting CONTRIBUTING; it is recoverable as a stock HDR if the Blender pipeline is revived. *Convert sidecars to internal overviews* — rejected in the earlier hardening change; external sidecars are the documented, reversible choice (`raster-performance`).

### 3. The two orphaned Blender-texture scripts are deleted with a provenance breadcrumb

`build_texture_rasters.py` (`SOURCE = data/imagery/aerial.tif`, a file renamed to `aerial_1m.tif` in September) and `apply_terrain_texture.py` (expects a ~21.5 M-vertex terrain mesh that no tracked scene contains) cannot run as written, are referenced by nothing, and their outputs feed no tracked file. `data/imagery/README.md` gains one line recording that the orthophoto now lives as `aerial_1m.tif`/`aerial_5m.tif`, so a future texture-pipeline rewrite starts from the right source.

**Alternatives:** *Keep as intent documentation* — rejected: they are misleading (document a non-existent input) and unreferenced (`repository-layout`: every script is load-bearing). *Park under `cache/`* — rejected: cache is being cleared. Git history retains them.

### 4. QGIS GUI-save side effects are contained, then the artifact is rebuilt

QGIS ≥ 3.22 writes a `<name>.qgs~` backup and a `<name>_attachments.zip` on every GUI save, and this cannot be disabled — so containment is `.gitignore` + documentation + deterministic rebuild:

1. Add `.qgs~` (and the attachments zip via the existing `*.zip` rule) to `.gitignore`; delete the two working-tree side files.
2. Re-run `QT_QPA_PLATFORM=offscreen python3 scripts/build_project.py` to erase the drift (including the stray absolute datasource), then `verify_project.py` and `pre-commit` must pass.
3. `qgis/README.md` documents the side-effect, why ignoring it is safe (the committed `.qgs` is always the build output), and how to reconcile a future GUI save.

This becomes **task group 1**, before any move: the drifted working tree would otherwise fail `verify-project` on every subsequent commit.

**Alternatives:** *Switch to `.qgz` to avoid side files* — rejected: `.qgz` is a zip; reviewable diffs and `verify_project.py` XML checks depend on plain `.qgs` (`project-build`: storage is reviewable). *Patch the drift by hand-editing XML* — rejected: not reproducible; rebuild is the canonical fix.

### 5. Pre-commit gates are added in one commit

`.pre-commit-config.yaml` gains, alongside the existing `verify-project` (pre-commit) and `verify-data` (pre-push):

- `check-added-large-files` with `--maxkb=5120` — above the largest legitimate tracked file (`data/vector/tiles_grid.gpkg`, 4.4 MB) and far below every oversized offender (`.ovr` 56–58 MB each, `_bgis`/`.exr` 18.8 MB+). Threshold documented in CONTRIBUTING.
- `check-ast` on `scripts/**/*.py`.
- `ruff` + `ruff-format` (astral-sh/ruff-pre-commit) on `scripts/`, format first, then lint.
- Local hook: `QT_QPA_PLATFORM=offscreen qgis_process help qgis/processing/trail_rebuild.model3` with `pass_filenames: false`, `files: ^qgis/processing/trail_rebuild\.model3$`.
- Trim stale `end-of-file-fixer` excludes (`tmnp.*`, `_bgis.wld`, `qgis/bound.prj` no longer exist after decisions 1–2).

CONTRIBUTING documents the hook list, the large-file threshold, and the maintenance commands: `pre-commit autoupdate`, `pre-commit migrate-config`, `pre-commit validate-config`. The config is already v4 style (no migration needed), and repo pins are current (`pre-commit-hooks` v6, ruff from its own repo).

**Alternatives:** *Shell-level guards in CI instead* — out of scope; this repo's contract lives in pre-commit hooks, and CONTRIBUTING already directs contributors there.

### 6. Per-layer QGIS features: adopted and declined

The saved project already expresses most presentation natively; this change writes that down (in `qgis/README.md`) and only adjusts what is genuinely off. Mapping (`qgis-native-features`):

| Layer / group | Data source | Native feature |
|---|---|---|
| Named trails | `tm_hiking_trails_dissolved.gpkg` | Single categorized layer; 2D + 3D categorized renderer (a 4.2 feature); subset-string filter macros for isolation and single-part filtering; named styles; map themes |
| Park boundary | `tmnp_relation_338191.gpkg` | Styled vector layer; clip source for the Processing rebuild model |
| Crop extent | `tmnp_extent_north_up.gpkg` | Styled layer; 3D-only textured overlay |
| Contours | `contours_2m_within_bound.gpkg` | Styled layer within themes |
| Terrain / DEM | `table_mountain_contours_2m_interpolated_5m_within_bound.tif` | 3D terrain elevation source; theme-driven terrain texture (`map-theme`, `texture-size=512`); overview sidecars |
| Basemaps | MapProxy `coct_aerial` WMS (EPSG:32734) + OSM XYZ | WMS / XYZ providers with local cache |
| Inspection rasters + raw OSM layers | unresolved-layers group | `Trail Inspection` map theme |
| Per-trail output | atlas coverage from trails | Print-layout Atlas, coverage-driven pages, data-defined titles, feature scaling |
| 3D scene | project | Terrain, camera pose (editable in the 4.2 camera dialog), MSAA / bloom / colour grading, categorized 3D line symbols |

Declined, each with a recorded reason (no feature used for its own sake):

- `.qgz` storage — breaks reviewable diffs.
- GeoPackage-embedded styles (`gpkg_style`) — would split the palette truth from `trail_colors.csv`.
- Virtual layers / embedded-layers list — no aggregate-query need; data is on disk.
- Temporal rendering — the scene is static.
- Vector tiles — offline, version-pinned GeoPackage data is the point; XYZ already serves OSM context.
- PostgreSQL project storage / project versioning (4.0) — git is the version system.
- Atlas "limit coverage rendering to current feature" (4.0) — pages intentionally show trail context; re-evaluate only if per-page isolation is wanted (Open Questions).
- Layer notes for provenance — provenance lives in `trail_datasets.manifest.json` + READMEs.
- Skybox-environment lighting (4.2) — not Python-bound in 4.2.2; current bloom/colour-grading/MSAA look suffices.

**Alternatives:** *Adopt every listed feature* — rejected by the user's own constraint: features must earn their keep.

### 7. Both MCP configs stay, and `.gitignore` comments are cleaned

`.mcp.json` (VS Code/Cline and other MCP clients) and `opencode.json` (OpenCode) serve different tools; both stay tracked, and the root README gains one line stating that. `.gitignore` keeps both, drops stale section comments (duckdb, table-mountain-national-park, pov-blend1) that describe abandoned experiments, and adds `.qgs~` plus `data/elevation/*.{ovr,aux.xml,wld}`.

### 8. `docker-mapproxy/` drops upstream-only files

Remove `.github/`, `docker-compose-s3.yml`, and `mapproxy_configuration/log_*.ini` (upstream CI/configuration clutter). Keep Dockerfile, compose files, `mapproxy.yaml`, `web/`, `sites-enabled/`, and LICENSE — the runtime surface.

## Risks / Trade-offs

**[Ruff-format rewrites every script]** → Isolated in the pre-commit commit (group 5); formatting runs first, lint second, both green before commit; diff reviewable as pure reformatting.

**[`git rm --cached` sidecars make clean checkouts temporarily slow for the DEM]** → Documented in `data/elevation/README.md` — regenerate with the recorded `gdaladdo -ro` command; `raster-performance` already treats sidecars as regenerable, reversible state.

**[Rebuilding `.qgs` changes the canonical checksum]** → Expected; the guarantee is *build-twice → byte-identical*, not pinning the historical `45d126fd…` blob. After group 1, run the build twice and confirm zero diff; record the new sha for verification.

**[Docs-gate coupling]** → `verify_data.py` scans the root/data/renders/cache READMEs. Every commit touching those trees updates the README in the same commit; groups are ordered so the gate never fails mid-change.

**[Boundary move breaks DEM scripts if paths are missed]** → The three script files and both READMEs are updated in the same commit; `verify_contour_dem.py` + `verify_data.py` run before commit prove the moved rectangle reproduces identical bounds.

**[Deleting `cache/*/` (≈2.6 GB) is irreversible]** → Nothing under `cache/` is tracked; every product is regenerable by documented commands or user-supplied data (SRTM zip was user-handled). `cache/README.md` sanctions clearing.

## Migration Plan

Each group is one commit, `verify_data.py` + `verify_project.py` + `pre-commit` green before and after, with its own rollback.

1. **chore(qgis): restore deterministic project artifact; ignore GUI-save side-files** — `.gitignore` (`.qgs~`), delete `table_mountain_3D.qgs~` + `_attachments.zip`, rebuild `.qgs` offscreen (twice, confirm identical), `qgis/README.md` side-effect note. *Rollback: `git revert`; a GUI save can always reproduce the side files.*
2. **refactor(data): move DEM boundary to `data/vector/bound`** — `git mv qgis/bound.*`, update `BOUNDARY`/`LEGACY_CROP_EXTENT`/messages in the three scripts, update README path mentions; run DEM verification + data verification. *Rollback: `git revert`.*
3. **chore(data): drop duplicate tmnp, superseded bGIS and orphaned binaries** — remove `data/vector/tmnp/`, `_bgis.{ovr,wld}`, the DEM `.ovr`/`.aux.xml` from git (`--cached`), `signal_hill_sunrise_4k.exr`, prune `docker-mapproxy/` upstream files; `verify_data.py` `BIG_RASTERS` + `data/README.md` inventory; `.gitignore` raster-sidecar patterns; imagery README provenance line. *Rollback: `git revert` (sidecars re-tracked if desired).*
4. **chore(blender): remove unreferenced render assets** — delete `lions_head.blend` and the two texture-pipeline scripts. *Rollback: `git revert`.*
5. **build(pre-commit): add large-file, ast, ruff, and qgis_process model hooks** — config + CONTRIBUTING gate documentation; `ruff format` then `ruff check` across `scripts/`; validate-config passes. *Rollback: `git revert`.*
6. **docs: refresh findings and README inventories** — `docs/terrain_data_findings.md` §Project state, root README (scripts table, MCP note), `data/README.md`, elevation/imagery/contour READMEs, CONTRIBUTING pre-commit guidance. *Rollback: `git revert`.*
7. **chore(cache): clear working caches** — delete `cache/*/` incl. `qgz_backups`; no git change; `cache/README.md` already sanctions it.

## Open Questions

- **Should `data/vector/bound` hold a GeoPackage instead of the shapefile?** Deferred: the move keeps the basename-layered shapefile to avoid churn; converting later is a mechanical `ogr2ogr` + path update and changes no spec.
- **Adopt QGIS 4.0's atlas "current feature only" rendering?** Deferred: pages currently show trail context deliberately; adopting would change `trail-atlas-outputs` scenarios, so it needs its own change if wanted.
