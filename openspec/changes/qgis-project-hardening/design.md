## Context

See `proposal.md` for motivation and the seven `specs/` for the behaviour
contracts. This document records the choices made to satisfy them.

Two facts from disk measurement shape everything below:

- `data/imagery/aerial_5m.tif` matches `qgis/bound.shp` to **+0.00 m** on
  both axes. The rasters were built against that rectangle, and the project has
  been internally consistent about it.
- `README.md`'s geographic claims are all accurate to four decimal places. The
  documentation's *knowledge* is sound; its *inventory* is stale. Corrections
  should therefore amend paths and values, not rewrite the reasoning.

Current QGIS version is 4.2.2, project CRS is `EPSG:32734`, and the project
already uses relative paths and GeoPackage spatial indexes. None of those
change.

## Goals / Non-Goals

**Goals:**

- One authoritative north-up crop extent, reproducible from a stable source.
- Interactive rendering of the 3.8 GB raster at every zoom.
- Per-trail isolation in one action, using native QGIS features.
- A trail pipeline that is both runnable from the GUI and verifiable by
  checksum.
- Documentation that names only files which exist.

**Non-Goals:**

- Replacing the PBF → `ogr2ogr` → GeoPackage workflow with vector tiles or
  QuickOSM. Offline, version-pinned, reproducible vector data is what this
  project needs; those alternatives suit basemap rendering and live queries.
- Initialising a git repository. Worth doing, but a repo-level decision
  unrelated to QGIS configuration.
- Collapsing the 172 trail layers into a single categorised layer. See the
  first decision — this is deliberately deferred, and doing it would require
  rewriting `trail-layer-presentation`, so it needs its own change.
- Reprojecting or re-cropping existing rasters. The new crop extent is smaller
  than the current raster footprint, which makes the rasters a superset, and
  that is explicitly allowed.

## Decisions

### 1. The 172 layers stay; isolation comes from a mutually exclusive group

The original request was one layer per trail, and it was reaffirmed after I
objected. The best-practices research then surfaced the feature that makes
that request work *natively*: a mutually exclusive group checks one child and
unchecks the rest. The trails are already in one group, so the stated goal —
isolate one trail without touching 171 other checkboxes — is satisfied in one
click with nothing removed.

**Alternatives considered:**

- *Collapse to one layer with a categorised renderer on `name`.* Cleaner, one
  legend node instead of 172, and a faster layer tree. Rejected as the
  committed path because it deletes the structure the user explicitly asked
  for, and it would invalidate most of `trail-layer-presentation`. If wanted,
  it belongs in a separate change that rewrites that spec.
- *Filter legend by map content.* Useful for decluttering, but it hides entries
  rather than isolating a trail, so it does not meet the requirement.
- *Continue with the layers as-is.* Leaves the user toggling 172 checkboxes by
  hand, which is the problem being solved.

### 2. Crop extent is the north-up envelope of the park boundary, not the extract

Two north-up rectangles are candidates, and they are not the same shape:

| Source | Dimensions | Area | Status |
|---|---|---|---|
| Park boundary 338191 | 18,479.41 × 49,372.55 m | 912.3755 km² | documented, never built |
| OSM extract contents | 20,203.79 × 52,136.38 m | 1053.3526 km² | on disk as `bound.shp` |

The boundary-derived rectangle is chosen, for four reasons:

- **Semantics.** A model crop extent should bound the model subject. Bounding
  an extract bounds whatever happened to be in the file.
- **Stability.** Derived from relation 338191, it cannot be invalidated by
  re-clipping. Derived from the extract, it *was*: `bound.shp` is 508.5 m short
  in northing because the extract was re-clipped 5 minutes after the rectangle
  was made. Choosing the boundary makes staleness impossible by construction
  rather than by re-checking.
- **Intent.** 912.3755 km² is the exact figure the README already documents as
  the north-up baseline the rotated rectangle was measured against, so this
  option continues the project's original reasoning.
- **Cost.** 15.5% fewer pixels than the current footprint.

**Consequence, stated plainly:** `aerial_1m.tif`, `aerial_5m.tif` and the
contour rasters keep their 1,053 km² footprint and will not match the new crop
extent. They become supersets, which `model-crop-extent` permits and requires
be reported. **No raster is reprojected or re-cropped.** This is the decision I
am least certain about, and it is the one most worth overriding if raster
footprint parity matters more than semantic correctness — the cost of
overriding is a `gdalwarp` per raster to shrink them to 912 km².

### 3. The crop extent becomes a GeoPackage in the data tree

`qgis/bound.shp` currently lives in the QGIS directory, which is where project
files live, not data. It also carries an `id` field, and a sibling shapefile in
this project has already broken a GeoPackage import with a `fid` field of
incompatible type — so the write is done with an explicit field list and
verified by reading back, not by conversion.

**Alternatives considered:** *Keep the shapefile.* Rejected: it is the reason
the extent was hard to find, being outside the data tree and under a different
name than the documentation used.

### 4. Overviews are external sidecars

`gdaladdo` writing `.ovr` sidecars, never internal overviews. The source rasters
are not rewritten, which matters most for `aerial_1m.tif` at 3.8 GB, and the
change is reversible by deleting the sidecar. Internal tiling would make each
file self-contained but would rewrite 3.8 GB with no way back.

Levels 2–64 for the 1 m raster, 2–32 for the 5 m rasters, resampling
`average` — correct for both continuous elevation and imagery when reducing.
Sidecar size is expected at roughly 10–15% of source, so budget disk before
starting.

### 5. The pipeline's source of truth is a Processing model, with `qgis_process` as the one command

`osm-trail-pipeline` requires both "one documented command" and "runnable from
QGIS". One implementation satisfies both: a Processing model invoked through
the `qgis_process` CLI. A shell script and a model that each implement the
steps would drift, which is the failure mode that produced the current
situation.

This also restores the register the project started in — the lost rotated
rectangle was computed by `native:orientedminimumboundingbox`, so the original
pipeline lived in Processing. The trail work drifted to shell plus individual
API calls, and that drift is where reproducibility went.

**Alternative considered:** *Shell script primary, model as a wrapper.* Fewer
moving parts in CI, but the model becomes a second-class citizen and the GUI
path stops being authoritative.

### 6. Layer-tree configuration runs as one project macro, never as 172 API calls

QGIS crashed once during remove/re-add churn at this layer count. That was
almost certainly the churn rather than the count, but the lesson stands: the
whole group configuration is applied by a single saved macro, executed once.
It is faster, it leaves a reviewable artefact inside the project, and it is
re-runnable if it half-completes.

### 7. One verification entry point

The README references `scripts/verify_data.py`, which does not exist. Rather
than adding several narrow checkers, one script implements the verification
scenarios across `model-crop-extent`, `raster-performance`, `osm-trail-pipeline`
and `project-provenance`. The spec scenarios are already written as
WHEN/THEN checks, so the script is a direct transcription of them, and the
specs and the script stay legible to each other.

Verification is **content-based for GeoPackages, not byte-based**: GDAL writes
a `last_change` timestamp into `gpkg_contents` on every save, so bytes always
differ even when data is identical. The README already documents this
reasoning; the requirement now has an executable check behind it.

### 8. The saved 3D scene uses the contour DEM and a local-coordinate camera

The `Point of View` scene is saved in `qgis/table_mountain_3D.qgz`. Its terrain
source is `table_mountain_contours_2m_interpolated_5m_within_bound`, band 1,
with a 100 m tile resolution, 5 m maximum ground error and 3 px maximum screen
error in `EPSG:32734`. The all-trails overview is a 3D-only, unchecked layer
categorised by `n_parts`; the north-up extent is a textured 3D-only overlay.

`QgsCameraPose` stores coordinates relative to the saved 3D origin. The
persisted origin is the crop-extent centre at 190 m elevation, and the camera
target is therefore stored as map coordinates `262848.06182320754,
6221403.2117594285, 90` with heading 38°, pitch 58° and distance 7,800 m.
This avoids the QGIS 4.2.2 canvas-save behaviour that double-offsets an
absolute pose.

QGIS 4.2.2 exposes MSAA through Python but does not bind the colour-grading,
bloom, or skybox settings classes. The saved scene consequently configures
MSAA through the API and persists bloom plus colour grading in the project's
native `<qgis3d>` XML (`bloom enabled="1"`, exposure `0.15`). The project was
reopened to confirm the terrain, pose, lights, materials, 3D renderers and
MSAA. The MCP 3D screenshot helper crashes this QGIS build, so it is not used
as scene evidence.

### 9. The named-trail Atlas is coverage-driven and makes disconnections explicit

The saved `Named Trail Atlas` layout uses the 172-feature `All named trails
(3D)` layer as coverage, not a hand-maintained list. Its explicit ascending
sort key is `concat("name", '|', "osm_ids")`: OSM names are not guaranteed to
be unique, so the numeric source identifiers make order and internal page names
unique without changing the visible title, which remains the feature's OSM
`name`.

The atlas map has automatic feature scaling with a 15% margin. A dynamic
notice labels every multi-part page with its part count and the statement that
the frame includes every part but is **not** a continuous camera run. This
prevents a disconnected geometry being presented as one traversable line.

Two independent `qgis_process native:atlaslayouttopdf` runs at 24 DPI each
produced 172 pages. Their PDF metadata differs, but all 172 corresponding
rendered PNG pages are pixel-identical, which proves identical order and
framing. Punctuation was exercised by `580m Devil's Peak Traverse`; no
coverage feature contains non-ASCII characters, and the saved dynamic title
uses the Unicode-capable Noto Sans font.

## Risks / Trade-offs

**Overviews on a 3.8 GB raster is long-running and disk-hungry** → Start it
first and in the background, since nothing else depends on it. Budget roughly
500 MB of sidecar. Sidecars are deletable, so it is fully reversible.

**Applying the mutually exclusive setting to 172 layers could crash QGIS
again** → Do it in one macro invocation, not 172 calls. Back up the `.qgz`
first; it is a single file, so the rollback is one copy.

**Changing the crop extent could silently misalign already-built rasters** →
Mitigated by decision 2: the new extent is a *subset* of the current raster
footprint, so no existing alignment changes. The verification script reports
the divergence explicitly rather than assuming parity.

**A `.qgz` written by a crashed or mid-macro session may be corrupt** → Back
up before the macro, and validate the reopened project reports the expected
layer count before trusting it.

**`qgis_process` may not be on `PATH` in every environment** → The design
assumes it ships with QGIS 4.2; if absent, the model is still runnable from
the GUI and the shell command falls back to invoking the steps directly. Task
ordering puts this check early so the fallback is known before it is needed.

**The verification script becomes a new dependency with no prior existence** →
It is the first thing built, so the rest of the work can be checked against a
known-good baseline, and it is the artefact that makes the "before" state
measurable rather than assumed.

## Migration Plan

Each stage is independently reversible and verified before the next begins.

1. **Baseline.** Back up `qgis/table_mountain_3D.qgz`. Build the verification
   script and run it against the current state, recording what fails. This
   captures the "before" numbers that later stages are judged against.
2. **Overviews** (long pole, start early, in background). Generate sidecars;
   verify source checksums unchanged; confirm zoomed-out interaction improves.
   *Rollback: delete the `.ovr` files.*
3. **Crop extent.** Compute the north-up envelope of relation 338191, write it
   as a GeoPackage under `data/vector/`, verify it against the recorded
   dimensions, and repoint the project layer. `qgis/bound.shp` is retained
   until the raster-divergence report is reviewed. *Rollback: restore the
   `.qgz` backup.*
4. **Trail presentation.** Apply group mutuality, styles and visibility
   presets via a single macro. Verify layer count is unchanged and that
   isolating one trail leaves the bulk layers alone.
5. **3D scene.** Configure terrain, camera, materials, lighting and
   post-processing; save; reopen and confirm the scene is reproduced.
6. **Atlas.** Build the layout and coverage, preview, and check the page count
   against the trail count and the multi-part handling.
7. **Documentation.** Correct the four absent-path references, the
   `terrain/` → `elevation/` mismatch, the PBF identity, and replace the
   rotated crop table with north-up values. Final verification pass.

Stages 3–6 all touch the project file, so the stage 1 backup is what makes
the whole sequence safe to re-run.

## Open Questions

- **Should the 172 layers eventually collapse to one categorised layer?** This
  is not deferrable within this change: it would rewrite
  `trail-layer-presentation` and the task breakdown, so it needs its own
  change and a decision from the user. The mutually exclusive group meets the
  stated requirement today without it.
- **Is the 508.5 m of OSM extract north of the current rectangle worth
  investigating as data?** It lies outside the park and is already excluded by
  the boundary clip. Answering it would not change any spec or task, so it is
  safe to defer indefinitely.
