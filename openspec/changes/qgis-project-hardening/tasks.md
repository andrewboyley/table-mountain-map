## 1. Baseline and verification

- [ ] 1.1 Back up `qgis/table_mountain_3D.qgz` and record the backup path in the task log
- [ ] 1.2 Record source checksums for `aerial_1m.tif`, `aerial_5m.tif` and both contour rasters, for later comparison in 2.4
- [ ] 1.3 Create `scripts/verify_data.py` with a subcommand per spec area: `crop-extent`, `raster`, `trails`, `docs`
- [ ] 1.4 Implement `verify_data.py crop-extent`: check north-up axis alignment, single authoritative extent, and boundary containment with a maximum-excursion report
- [ ] 1.5 Implement `verify_data.py raster`: check overview presence above the 10,000,000 pixel threshold and report every raster that fails
- [ ] 1.6 Implement `verify_data.py trails`: check presence, non-zero feature counts, geometry validity, and per-feature part counts; content-based comparison only, never GeoPackage byte comparison
- [ ] 1.7 Implement `verify_data.py docs`: extract every file path from `README.md` and `data/README.md`, resolve each against the project root, and report unresolved paths and undocumented datasets
- [ ] 1.8 Run the full verification against the current state and record the baseline failures in the task log
- [ ] 1.9 Confirm `qgis_process` is on `PATH`; if absent, record the shell fallback that stage 4 will use

## 2. Raster performance

- [ ] 2.1 Record available free disk space and confirm it exceeds the expected sidecar requirement
- [ ] 2.2 Generate overviews for `aerial_1m.tif` at levels 2–64 with `average` resampling, as an external sidecar
- [ ] 2.3 Generate overviews for `aerial_5m.tif` at levels 2–32 with `average` resampling
- [ ] 2.4 Generate overviews for both contour rasters at levels 2–32 with `average` resampling
- [ ] 2.5 Re-check source checksums against 1.2 and confirm every source raster is byte-unchanged
- [ ] 2.6 Confirm each raster's pixel dimensions and geotransform are unchanged
- [ ] 2.7 Verify zoomed-out panning across the full crop area is interactive, and that full native resolution is still reachable
- [ ] 2.8 Record the overview levels and resampling method for each raster in `data/README.md`

## 3. Model crop extent

- [ ] 3.1 Compute the north-up envelope of OSM relation 338191 in `EPSG:32734` and confirm it measures 18,479.41 × 49,372.55 m and 912.3755 km²
- [ ] 3.2 Write the envelope to a GeoPackage under `data/vector/` with an explicit field list, avoiding any `fid` or `id` field that would break import
- [ ] 3.3 Read the written layer back and confirm its geometry matches the computed envelope
- [ ] 3.4 Verify every park boundary vertex is contained, reporting the maximum excursion
- [ ] 3.5 Add a raster-footprint divergence report to `verify_data.py`, identifying each raster as superset, equal, or partial
- [ ] 3.6 Repoint the project's crop extent layer to the new GeoPackage and remove the reference to `qgis/bound.shp`
- [ ] 3.7 Reopen the project and confirm the layer count is unchanged and the extent layer resolves
- [ ] 3.8 Retain `qgis/bound.shp` until the divergence report from 3.5 is reviewed; delete it only after review

## 4. Trail pipeline and layer presentation

- [ ] 4.1 Build the trail pipeline as a QGIS Processing model, exposing the extract path, boundary, tag filter and output paths as parameters rather than hard-coded values
- [ ] 4.2 Confirm the model reproduces the existing named trail dataset: same feature count, same attributes, geometry equal within 1 mm
- [ ] 4.3 Confirm the model output aggregate measures match the recorded trail count and total length
- [ ] 4.4 Confirm the model output is identical when the extract is processed in a different feature order
- [ ] 4.5 Record provenance for each trail dataset: extract file with size and mtime, boundary relation identifier and area, accepted highway values, named-only rule, dissolve grouping attribute and geometric operator, and output CRS
- [ ] 4.6 Record checksums for the trail datasets in a manifest
- [ ] 4.7 Document the single `qgis_process` rebuild command, its prerequisites, and its equivalence to the GUI model path
- [ ] 4.8 Write a project macro that applies the trail group configuration in one invocation: mutually exclusive group, named styles, and a legend labelling each layer by OSM name
- [ ] 4.9 Run the macro once, then confirm the layer count is unchanged and the bulk unnamed and track layers were not affected
- [ ] 4.10 Verify isolating a single named trail leaves all other layers' visibility unchanged
- [ ] 4.11 Verify no two named trail layers share a display label, and surface any OSM name collision rather than merging it
- [ ] 4.12 Create visibility presets for the trail-inspection and aerial-imagery configurations, and verify each restores its exact recorded state
- [ ] 4.13 Verify the part-count filter shows exactly the recorded number of single-part trails, and that multi-part trails remain reachable

## 5. Terrain and 3D scene

- [ ] 5.1 Configure the 3D view terrain from the project DEM and record the elevation source layer and band
- [ ] 5.2 Set terrain tiling parameters in metres and confirm terrain detail refines when the view approaches the ground
- [ ] 5.3 Set a camera pose as explicit map coordinates and heading
- [ ] 5.4 Configure surface materials with independent base colour, metalness and roughness, and bind an image texture to the base colour
- [ ] 5.5 Select an environment lighting source
- [ ] 5.6 Enable colour grading, bloom and anti-aliasing
- [ ] 5.7 Configure categorised 3D symbols where a 3D symbol layer is rendered
- [ ] 5.8 Save the project, reopen it, and confirm the terrain source, camera pose, materials, lighting and post-processing are all restored

## 6. Trail atlas

- [ ] 6.1 Create an Atlas layout driven by the named trail dataset as coverage
- [ ] 6.2 Bind the page title to the feature's name expression
- [ ] 6.3 Set an explicit sort field and direction
- [ ] 6.4 Preview the atlas and confirm the page count equals the named trail count
- [ ] 6.5 Verify every generated page frames its full trail, including trails with disconnected parts
- [ ] 6.6 Add a visible multi-part indicator showing the part count on pages for multi-part trails
- [ ] 6.7 Make a single continuous camera run across disconnected parts either refuse or require explicit acknowledgement
- [ ] 6.8 Export twice from unchanged input and confirm page order, page count and framing are identical
- [ ] 6.9 Verify trail names containing punctuation and non-ASCII characters render without truncation

## 7. Documentation

- [ ] 7.1 Replace the rotated crop-rectangle table in `README.md` with the north-up dimensions measured in 3.1
- [ ] 7.2 Remove the rotated rectangle's corner coordinates and its comparison percentage
- [ ] 7.3 Correct `data/README.md`: `terrain/` to `elevation/`
- [ ] 7.4 Correct the OSM extract identity in `data/README.md` to the real file name, size and timestamp
- [ ] 7.5 Remove or correct the reference to the absent five-layer park GeoPackage and its recorded feature count
- [ ] 7.6 Remove or create the referenced `vector/coct/README.md`
- [ ] 7.7 Add the trail datasets to the documented data inventory, with their build command and provenance
- [ ] 7.8 Confirm the OSM attribution requirement and the restricted-imagery flag are still present after editing

## 8. Final verification

- [ ] 8.1 Run `verify_data.py` across all four subcommands and confirm every check passes
- [ ] 8.2 Confirm no documented path remains unresolved
- [ ] 8.3 Confirm no dataset present in the data directory is undocumented
- [ ] 8.4 Reopen the project and confirm the expected layer count, group configuration, presets and 3D scene
- [ ] 8.5 Record the final measured crop-extent values, trail counts and raster overview configuration in the task log
