## Why

The audit shows the repository carrying artifacts that contradict its own documented structure and tooling contract: a data layer (`qgis/bound.*`) living in the QGIS project directory, a duplicate boundary set in `data/vector/tmnp/`, a superseded `_bgis` DEM variant with ~115 MB of regenerable raster sidecars (`.ovr`/`.aux.xml`/`.wld`) tracked in git, and two orphaned Blender-texture scripts whose input file was renamed months ago. QGIS GUI saves also drift the deterministic project artifact (`.qgs~` backup + `_attachments.zip` side files). At the same time QGIS 4.2 — the installed version — ships native features the project under-uses (headless `qgis_process`, camera dialogs, atlas refinements), and pre-commit best practices (large-file guard, ruff, AST checks, model validation) would have caught several of these regressions before they landed.

## What Changes

- **BREAKING** Move `qgis/bound.*` → `data/vector/bound/` (the DEM boundary mask, distinct from the crop-extent GeoPackage); update every script, verification path, README and docs reference.
- Delete duplicates and superseded artifacts: `data/vector/tmnp/*` (its extent equals `tmnp_relation_338191.gpkg` exactly), the `_bgis` DEM variant (+ `.wld`), `blender/lions_head.blend` (unreferenced scene), and tracked raster sidecars (`.ovr`/`.aux.xml`).
- Delete the orphaned Blender-texture scripts (`build_texture_rasters.py`, `apply_terrain_texture.py`): their input `data/imagery/aerial.tif` no longer exists (renamed `aerial_1m.tif`), and nothing in the repo references them or consumes their outputs; record a one-line provenance note in `data/imagery/README.md`.
- Untrack and ignore regenerable sidecars; add `.qgs~` and raster sidecar patterns (`.ovr`/`.aux.xml`/`.wld`) to `.gitignore`; remove stale ignore comments; keep both `.mcp.json` and `opencode.json` tracked and document why.
- Pre-commit: add `check-added-large-files`, `check-ast`, ruff + ruff-format on `scripts/`, and a local `qgis_process help qgis/processing/trail_rebuild.model3` validation hook; trim stale `end-of-file-fixer` excludes; document `autoupdate`/`migrate-config`/`validate-config` in CONTRIBUTING.
- Rebuild `qgis/table_mountain_3D.qgs` deterministically offscreen to remove GUI-save drift, then re-run all gates.
- Docs: refresh `docs/terrain_data_findings.md` §Project state, `data/README.md` inventory, README paths in elevation/imagery/contour docs, the root `README.md` scripts table and MCP note, and `qgis/README.md` (GUI-save side-effect note + per-layer QGIS feature mapping).
- Adopt QGIS-native features per layer where they earn their keep (map themes, categorized 2D/3D renderers, subset-string filters, atlas coverage, terrain theme texture, WMS/XYZ basemaps, headless `qgis_process` model validation) and record deliberately declined features so none are used gratuitously.
- Prune `docker-mapproxy/` upstream-only files (`.github/`, `docker-compose-s3.yml`, `log_*.ini`), keeping runtime files and LICENSE.
- Clear working `cache/*/` directories (2.6 GB, incl. `qgz_backups`) and the QGIS save side-files; `cache/README.md` already sanctions this.

Unchanged: OSM attribution and restricted-CoCT-imagery flags stay in the docs; the `.qgs` stays the deterministic, byte-identical build artifact; existing `{verify-data, verify-project}` hooks keep passing; `qgis/processing/trail_rebuild.model3` stays the processing-model source of truth.

## Capabilities

### New Capabilities

- `repository-layout`: where artifacts live and why — directories mean what they say, every dataset has exactly one authoritative copy, regenerable binaries are never tracked, every script is load-bearing, and working caches are ephemeral.
- `pre-commit-gates`: the repo's commit-time contract — large binaries, unparsable Python, unformatted Python, and invalid Processing models are all refused before commit, with the gates documented.
- `qgis-native-features`: the saved project expresses each layer's behaviour with native QGIS mechanisms (categorized renderers, themes, filters, atlas coverage, terrain theme texture, WMS/XYZ) and uses headless QGIS tooling as the canonical validation path; adopted and declined features are documented.

### Modified Capabilities

- `project-build`: the committed project file is immune to GUI-save drift — side files are never committed and a rebuild restores the byte-identical canonical artifact.
- `project-provenance`: findings analyses describe the current on-disk state — stale paths, dead absolute paths and vanished artifacts named as present are corrected.

## Impact

- **scripts/**: `verify_data.py` (BOUNDARY/LEGACY_CROP_EXTENT paths, `_bgis` out of `BIG_RASTERS`, inventory reflects the new tree), `build_contour_dem.py` + `verify_contour_dem.py` (BOUNDARY path), `build_project.py` (boundary source path, deterministic rebuild); the two texture scripts are deleted.
- **qgis/**: `table_mountain_3D.qgs` rebuilt deterministically; `README.md` gains the GUI-save note and per-layer feature mapping; styles, macro and processing model unchanged in content.
- **data/**: `vector/bound/` added; `vector/tmnp/` removed; `elevation/` loses `_bgis`; README inventories refreshed.
- **blender/**: `lions_head.blend` removed; `tmnp.blend` retained.
- **Root**: `.gitignore`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, `README.md`, `docs/terrain_data_findings.md`, `docker-mapproxy/` pruning.
- **No change** to rendering behaviour, raster footprints, the crop extent, trail data, or the MapProxy service; the OSM attribution and CoCT imagery restriction statements are preserved verbatim.
