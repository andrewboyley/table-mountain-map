## Why

The project renders the same hiking trails 172 times: every one of the 172
"Hiking Trails" layers is a subset view of the *same* table
(`tm_hiking_trails_dissolved.gpkg|layername=hiking_trails|subset=name = '...'`,
verified live). Each carries a full style block in the project XML, which is
why the inner project document is 11.5 MB and every commit is an opaque
`Bin X -> Y` diff. The previous hardening design explicitly deferred collapsing
them ("needs its own change"). QGIS 4.2 has since added categorized 3D
symbolisation (`QgsCategorized3DRenderer`, confirmed present in this build),
which removes the old blocker: one layer can now carry both a 2D and a 3D
per-trail look.

## What Changes

- Removes the 172 per-trail subset layers and the `All named trails (3D)`
  composite layer node.
- Adds a single `Hiking Trails` layer backed by the same dissolved GeoPackage
  with a categorized renderer on `name` (172 categories) for 2D, and a
  categorized 3D renderer on `name` for the 3D scene.
- Introduces `qgis/styles/trail_colors.csv` as the deterministic palette,
  captured from the current 172 layers so the look is preserved.
- Replaces the mutually-exclusive-group isolation with expression-based
  isolation: the presentation macro gains `isolate(name)`,
  `show_single_part_trails()` and `show_aerial_imagery()` driven by a subset
  filter on the single layer plus the existing visibility presets.
- Ports the `Standard` / `Emphasis` named styles onto the single layer's style
  manager.
- Points the Named Trail Atlas coverage at the new single layer; page count
  stays 172.
- Rewrites `qgis/trail_presentation_macro.py` for the single-layer model and
  keeps it as the authoritative copy re-embedded into the project (**BREAKING**
  for macro users: the tree no longer lists per-trail checkboxes).

## Capabilities

### Modified Capabilities
- `trail-layer-presentation`: replaced per-trail-layer isolation and styling
  with a single categorized layer; isolation now uses an expression filter and
  presets instead of a mutually exclusive group. The Named Trail Atlas coverage
  moves to the new layer as an implementation detail (coverage remains the
  named trail data, 172 pages).

## Impact

- `qgis/table_mountain_3D.qgz` layer tree and 3D scene.
- `qgis/trail_presentation_macro.py` and the embedded macro.
- New `qgis/styles/trail_colors.csv` (canonical palette).
- Named Trail Atlas coverage layer.
- `openspec/changes/qgis-project-hardening` spec `trail-layer-presentation`
  is superseded by this delta.
