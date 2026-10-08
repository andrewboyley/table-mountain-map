# AGENTS.md

This file gives an AI agent the facts it needs to work in this repository without breaking its gates. Read it before you change code, data, or documentation.

## Project

This project prepares City of Cape Town elevation data, OpenStreetMap context, and a Blender scene for a metrically scaled Table Mountain model. The facts about data sources, access limits, and the QGIS project live in the `README.md` files and in `docs/`. Read them before you edit.

## The gates

Run both gates before you finish a task.

```bash
just verify
just check
```

`just verify` builds the contour-DEM intermediates first, then runs the three verification scripts. `just check` runs every pre-commit hook on all files. Use `just` as the single entry point for project commands. The `justfile` lists every recipe.

The QGIS project at `qgis/table_mountain_3D.qgs` is hand-edited in QGIS. `scripts/verify_project.py` loads it offscreen and fails on any broken invariant (CRS, layer existence, renderer coverage, relative paths).  There is no separate build step -- the `.qgs` file is the source of truth.  The project embeds no scripts or macros; presentation uses native QGIS features only.

## Verification scripts

- `scripts/verify_project.py` loads the QGIS project offscreen and fails on any broken invariant.
- `scripts/verify_data.py all` makes sure the data inventory, the documented paths, the raster performance, the trail outputs, and the named-summits outputs are correct.
- `scripts/build_contour_dem.py` and `scripts/verify_contour_dem.py` build and validate the contour DEM.
- `scripts/build_peak_manifest.py` writes the named-summits provenance manifest. `just rebuild-peaks` runs it; do not hand-edit the manifest.

`scripts/verify_data.py` scans four README files for path references: `README.md`, `data/README.md`, `renders/README.md`, and `cache/README.md`. Every path you name in those files must resolve in the current tree. The scanner treats every backticked token as a path, so do not backtick a bare command name such as `qgis_process` in those four files.

## Processing models

`qgis_process` resolves `model:<name>` from the active QGIS profile's `processing/models` directory, never from the repository. A model in `qgis/processing/` is inert until it is copied into that profile, so `qgis_process run model:trail_rebuild` fails on a fresh clone even though the file is present. `just install-models` does the copy; both `rebuild-trails` and `rebuild-peaks` depend on it. Do not hand-copy, and do not edit the copies in the profile -- edit the repository file and re-run the recipe.

Reading OSM peaks needs `osmium`, not the GDAL OSM driver. That driver drops the `ele` tag from both its field list and `other_tags`, so a peak read through it has no elevation and cannot be filtered on one. Any new pipeline that needs `ele` must read the extract with `osmium` first.

## Data rules

Large source and derived binaries are not tracked. Restore them from the sources recorded in the `data/` READMEs. Raster overview sidecars (`.ovr`, `.aux.xml`, `.wld`) are ignored and regenerable with the recorded `gdaladdo -ro` commands. The DEM pyramid rebuilds with `just build-overviews`. The COCT 2 m contour zip is user-handled. It is not in git and you do not fetch it.

`cache/` holds temporary files only. You can clear it. `renders/` holds final images and video.

The OSM data requires attribution in any published map, render, or export. The CoCT aerial imagery is restricted. Do not publish it until the intended use is confirmed.

## Configuration files

Keep both `.mcp.json` and `opencode.json` in the repository root. They serve different tool ecosystems and both are tracked. Do not remove either one. `opencode.json` also defines the project slash commands `/verify`, `/check`, `/gates`, and `/commit`, plus the shell permission rules for this repository.

## Commits

Use Conventional Commits. Make one logical change per commit. Never add binary data to a commit that also changes source. The `blender/*.blend` files are the one tracked binary exception. `CONTRIBUTING.md` records why.
