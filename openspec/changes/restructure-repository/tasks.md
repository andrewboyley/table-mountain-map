## 1. Restore the deterministic project artifact

- [x] 1.1 Add `.qgs~` (and confirm the attachments zip stays covered) to `.gitignore`
- [x] 1.2 Delete the working-tree side files `qgis/table_mountain_3D.qgs~` and `qgis/table_mountain_3D_attachments.zip`
- [x] 1.3 Rebuild the project offscreen (`QT_QPA_PLATFORM=offscreen python3 scripts/build_project.py`), run it twice and confirm the second run leaves `qgis/table_mountain_3D.qgs` byte-identical (record the new sha256)
- [x] 1.4 Run `python3 scripts/verify_project.py` and `python3 scripts/verify_data.py all` — all checks pass
- [x] 1.5 Run `pre-commit run --all-files` — existing hooks pass on the restored artifact
- [x] 1.6 Add the GUI-save side-effect note to `qgis/README.md` (`.qgs~` backup + `_attachments.zip` are created by every GUI save in QGIS ≥ 3.22, not disableable; they are ignored; the committed `.qgs` is always the build output; a GUI save is reconciled by rebuilding)
- [x] 1.7 Commit `chore(qgis): restore deterministic project artifact; ignore GUI-save side-files`

## 2. Move the DEM boundary into the data tree

- [x] 2.1 `git mv qgis/bound.shp qgis/bound.shx qgis/bound.dbf qgis/bound.prj data/vector/bound/`
- [x] 2.2 Update `BOUNDARY = ROOT/"qgis/bound.shp"` to `data/vector/bound/bound.shp` in `scripts/build_contour_dem.py` and `scripts/verify_contour_dem.py`
- [x] 2.3 Update `verify_data.py`: `LEGACY_CROP_EXTENT` path and the "not qgis/bound.shp" check message
- [x] 2.4 Grep for `qgis/bound` across READMEs and docs and update every mention
- [x] 2.5 Run `python3 scripts/verify_contour_dem.py` — DEM bounds still match the moved boundary envelope
- [x] 2.6 Run `python3 scripts/verify_data.py all`, `python3 scripts/verify_project.py`, and `pre-commit run --all-files`
- [x] 2.7 Commit `refactor(data): move DEM boundary to data/vector/bound`

## 3. Drop duplicate, superseded and orphaned data

- [x] 3.1 `git rm data/vector/tmnp/` (the 7-file shapefile set whose extent equals `tmnp_relation_338191.gpkg`)
- [x] 3.2 `git rm` the `_bgis` DEM variant: `data/elevation/*_bgis.tif.ovr` and `data/elevation/*_bgis.wld`
- [x] 3.3 `git rm --cached` the DEM overview sidecars `table_mountain_contours_2m_interpolated_5m_within_bound.tif.{ovr,aux.xml}` (kept on disk for the gates)
- [x] 3.4 `git rm data/signal_hill_sunrise_4k.exr` (unreferenced render asset)
- [x] 3.5 Prune `docker-mapproxy/` upstream-only files: `.github/`, `docker-compose-s3.yml`, `mapproxy_configuration/log_*.ini`
- [x] 3.6 `.gitignore`: add raster-sidecar patterns; drop stale section comments (duckdb, table-mountain-national-park, pov-blend1)
- [x] 3.7 `verify_data.py`: remove `_bgis` from `BIG_RASTERS`; align `TOP_LEVEL_DIRS` and inventory constants with the actual tree
- [x] 3.8 `data/README.md`: remove the `tmnp.shp` line and the `_bgis` raster row; refresh the inventory (bound moved, sidecars untracked)
- [x] 3.9 `data/imagery/README.md`: one-line provenance note — the orthophoto now lives as `aerial_1m.tif`/`aerial_5m.tif` (renamed from `aerial.tif`)
- [x] 3.10 `data/elevation/README.md`: note that overview sidecars are regenerated with the recorded `gdaladdo -ro` command after a clean checkout
- [x] 3.11 Run `python3 scripts/verify_data.py all` and `pre-commit run --all-files` — all green
- [x] 3.12 Commit `chore(data): drop duplicate tmnp and superseded bGIS artifacts`

## 4. Remove unreferenced Blender assets and orphaned texture scripts

- [x] 4.1 `git rm blender/lions_head.blend`
- [x] 4.2 `git rm scripts/build_texture_rasters.py scripts/apply_terrain_texture.py`
- [x] 4.3 Grep the repo for references to the deleted scripts/files — none remain
- [x] 4.4 Run `pre-commit run --all-files` (stale `end-of-file-fixer` excludes are trimmed in group 5; nothing here may reference removed paths)
- [x] 4.5 Commit `chore(blender): remove unreferenced render assets and orphaned texture scripts`

## 5. Add pre-commit gates

- [x] 5.1 Add `check-added-large-files` (`--maxkb=5120`) and `check-ast` (on `scripts/**/*.py`) from `pre-commit-hooks`; add `ruff` + `ruff-format` (astral-sh/ruff-pre-commit) scoped to `scripts/`
- [x] 5.2 Add the local validation hook: `QT_QPA_PLATFORM=offscreen qgis_process help qgis/processing/trail_rebuild.model3` with `pass_filenames: false` and `files: ^qgis/processing/trail_rebuild\.model3$`
- [x] 5.3 Trim stale `end-of-file-fixer` excludes: `tmnp.*`, `_bgis.wld`, `qgis/bound.prj`
- [x] 5.4 Run `ruff format` then `ruff check --fix` across `scripts/`; review the reformat diff (expected to be the largest diff of the change)
- [x] 5.5 `pre-commit validate-config` and `pre-commit run --all-files` — all hooks green, including the new model hook
- [x] 5.6 Ensure `scripts/__pycache__/` and `.ruff_cache/` are ignored; remove the on-disk `scripts/__pycache__` directory
- [x] 5.7 CONTRIBUTING: document the hook list, the large-file threshold, and the `autoupdate` / `migrate-config` / `validate-config` commands
- [x] 5.8 Commit `build(pre-commit): add large-file, ast, ruff, and qgis_process model hooks`

## 6. Refresh findings and README inventories

- [x] 6.1 `docs/terrain_data_findings.md` §Project state: replace the stale absolute path, the dead "COCT elevation" group and the "no scene/texture exists" claims with current facts (QGIS 4.2.2 project, map themes, DEM pipeline, MapProxy WMS basemaps)
- [x] 6.2 Root `README.md`: refresh the scripts table (drop the texture scripts, keep build/verify gates), add the one-line MCP note (both `.mcp.json` and `opencode.json` are kept — different tool ecosystems), update any remaining `qgis/bound` mentions
- [x] 6.3 `qgis/README.md`: add the per-layer native-feature mapping and the declined-features list (adopted per the design's decision 6: categorized 2D/3D renderers, themes, subset-string filters, atlas coverage, terrain theme texture, WMS/XYZ basemaps; declined: QGZ, gpkg styles, virtual layers, temporal, vector tiles, PostgreSQL storage, atlas current-feature-only, layer notes, skybox lighting)
- [x] 6.4 Confirm `renders/README.md` and `cache/README.md` still resolve every path they name under the docs gate
- [x] 6.5 Run `python3 scripts/verify_data.py all`, `python3 scripts/verify_project.py`, `pre-commit run --all-files` — all green
- [x] 6.6 Commit `docs: refresh findings and README inventories`

## 7. Clear working caches

- [x] 7.1 Delete `cache/*/` (including `cache/blender/`, `cache/qgz_backups/` and the contour-DEM validation dir) — nothing under `cache/` is tracked; `cache/README.md` sanctions clearing
- [x] 7.2 Final sweep: `git status` shows no stray changes; gates green; record the new canonical `.qgs` sha256 in the summary
