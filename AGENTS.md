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

`just verify` builds the contour-DEM intermediates first, then runs the three verification scripts. `just check` runs every pre-commit hook on all files. You can run them without `just`, but `just` is the documented way. The `justfile` lists every recipe.

The QGIS project at `qgis/table_mountain_3D.qgs` is a build artifact. Do not hand-edit it. If it drifts, rebuild it with `just build` and commit the byte-identical output.

## Verification scripts

- `scripts/build_project.py` rebuilds `qgis/table_mountain_3D.qgs` headlessly.
- `scripts/verify_project.py` loads the project offscreen and fails on any broken invariant.
- `scripts/verify_data.py all` makes sure the data inventory, the documented paths, the raster performance, and the trail outputs are correct.
- `scripts/build_contour_dem.py` and `scripts/verify_contour_dem.py` build and validate the contour DEM.

`scripts/verify_data.py` scans four README files for path references: `README.md`, `data/README.md`, `renders/README.md`, and `cache/README.md`. Every path you name in those files must resolve in the current tree.

## Data rules

Large source and derived binaries are not tracked. Restore them from the sources recorded in the `data/` READMEs. Raster overview sidecars (`.ovr`, `.aux.xml`, `.wld`) are ignored and regenerable with the recorded `gdaladdo -ro` commands. The COCT 2 m contour zip is user-handled. It is not in git and you do not fetch it.

`cache/` holds temporary files only. You can clear it. `renders/` holds final images and video.

The OSM data requires attribution in any published map, render, or export. The CoCT aerial imagery is restricted. Do not publish it until the intended use is confirmed.

## Configuration files

Keep both `.mcp.json` and `opencode.json` in the repository root. They serve different tool ecosystems and both are tracked. Do not remove either one.

## Commits

Use Conventional Commits. Make one logical change per commit. Never add binary data to a commit that also changes source. The `blender/*.blend` files are the one tracked binary exception. `CONTRIBUTING.md` records why.
