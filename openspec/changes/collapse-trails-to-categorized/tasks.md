# Collapse Trails to Categorized

Implementation tasks.

## 1. Capture the palette baseline

- [x] Probe the live 172 layers and write `qgis/styles/trail_colors.csv`
      (`name,color,width`) from the captured renderers.
- **Verify**: 172 rows; colour values match the probe dump exactly.
      (`wc -l qgis/styles/trail_colors.csv` -> 173 with header; 12-colour
      repeating cycle preserved.)

## 2. Add the single categorized layer

- [x] Create `Hiking Trails` layer from
      `tm_hiking_trails_dissolved.gpkg|layername=hiking_trails`.
- [x] Apply 2D `QgsCategorizedSymbolRenderer` on `"name"` from the CSV.
- [x] Apply 3D `QgsCategorized3DRenderer` on `"name"` from the CSV with the
      `QgsLine3DSymbol` matching the current 3D look (metalrough, width 3.6,
      offset 20, terrain clamp, vertex binding, metalness 0.05, roughness
      0.55) and the renderer bound to the layer (`setLayer`), which is what
      lets the renderer survive a save/reload.
- [x] Port `Standard`/`Emphasis` named styles. No canvas labels: the old 172
      layers had labeling disabled and the atlas/legend already carries the
      names, so labels are intentionally skipped to preserve the current look.
- **Verify**: 172 categories; each colour equals the CSV row; the renderer is
  categorized on `name` after a fresh reload (checked headless and in the GUI).

## 3. Restructure the layer tree

- [x] Remove the `Hiking Trails` group (172 layers) and the
      `All named trails (3D)` node; insert `Hiking Trails` under `Paths`.
- **Verify**: tree contains exactly one named-trail layer; total layer count
  drops by 172 (183 -> 11).

## 4. Rewrite the presentation macro

- [x] Rewrite `qgis/trail_presentation_macro.py` for the single layer:
      `isolate(name)` (subset + best-effort zoom), `show_all()`,
      `show_single_part_trails()` (`"n_parts" = 1`),
      `show_aerial_imagery()`, preset rebuild (manual `MapThemeRecord`s).
- [x] Embed the rewritten macro into the project `Macros` section (stored
      under `Macros` / `pythonCode`; re-stamp the 3D terrain XML after the
      save that embeds it).
- **Verify**: macro runs idempotently (run twice, state unchanged);
  `isolate("Platteklip Gorge")` -> 1 feature; single-part -> 144 features;
  apostrophe names (`Smuts' Track`) quote correctly -> 1 feature;
  `Trail Inspection`, `Aerial Imagery`, `Single-part trails` presets exist.

## 5. Re-point the atlas coverage

- [x] Set the Named Trail Atlas coverage layer to `Hiking Trails`.
- **Verify**: `atlas.count() == 172`; page-name expression unchanged
  (`concat("name", ' — OSM ', "osm_ids")`); map item `trail_map` layer set is
  `[Hiking Trails, contours_2m_within_bound]` (XML `LayerSet`).

## 6. Save, re-stamp 3D, render-verify

- [x] Save the project.
- [x] Re-apply the 3D terrain binding (theme + `texture-size="512"`).
- [x] Render-verify a map view and the 3D view.
- **Verify**: no crash; terrain/scene XML patched (scene `<layers>` swap,
  `map-theme="3D terrain texture"`, `texture-size="512"`, terrain
  `layer=<DEM id>`); the categorized 2D render draws exact palette colours
  (checked numerically on a rendered image); the 3D categorized renderer (172
  categories on `name`) loads in the GUI after a fresh open;
  `blender/tmnp.blend` remains unstaged.

## 7. Commit

- [x] Run `pre-commit` and `python3 scripts/verify_data.py all`.
- [x] Conventional commit for the change.
- **Verify**: `git status` clean except `blender/tmnp.blend`.
