## Context

The 172 "Hiking Trails" layers are presentation copies of a single GeoPackage
table. Live probe (2026-09-29): every layer's source is

```
tm_hiking_trails_dissolved.gpkg|layername=hiking_trails|subset=name = '...'
```

(`storageType = GPKG`, no per-layer data). The atlas coverage layer
`All named trails (3D)` is the same table unfiltered and counts **172
features**. Collapsing is therefore a pure renderer/tree change: zero data
migration, and the atlas coverage simply moves to the new layer.

The old per-trail 3D blocker is gone: the installed QGIS 4.2.2 exposes
`QgsCategorized3DRenderer`, `QgsRuleBased3DRenderer` and `Qgs3DRendererCategory`
in `qgis._3d` (verified).

## Current colour baseline

The 172 layers repeat a cycle of six colours, all at width 0.26:

- `#e8718d #e77148 #e15989 #beb297 #85b66f #729b6f` (first 18 trails)
- `#c43c39 #7d8b8f #d5b43c #8d5a99 #b7484b #becf50` (thereafter)

These are captured verbatim into `qgis/styles/trail_colors.csv`
(`name,color,width_mm`) by a one-off probe. The categorized renderer consumes
the CSV so a rebuild can never drift the palette.

## Decision 1 — one layer, two renderers

Introduce layer `Hiking Trails` on the dissolved source:

- 2D: `QgsCategorizedSymbolRenderer` on `"name"`, 172 categories read from the
  CSV (exact colour, width 0.26 mm).
- 3D: `QgsCategorized3DRenderer` on `"name"` with one `QgsLine3DSymbol` per
  trail, coloured from the same CSV, line width replicated from the current
  "All named trails (3D)" symbol (probed during implementation).
- Labels: a single rule labelling `"name"`, replacing the per-layer labels;
  duplicate display names are reported by the macro rather than merged.

The `Standard` and `Emphasis` named styles move onto this layer's style
manager (Emphasis = 203,24,24 at 1.8 mm, matching the old macro).

## Decision 2 — isolation moves from mutex group to filter + presets

A mutually exclusive group only works with multiple layers. With one layer,
"exactly one trail visible" becomes a feature filter on the single layer:

- `isolate(name)`  → `layer.setSubsetString("name" = '<name>')` then applies
  the Inspection preset (context layers on, imagery off).
- `show_all()`    → clears the subset.
- `show_single_part_trails()` → `"n_parts" = 1`; the single-part count (144 in
  the current project) is asserted by the macro and the verification script,
  not hard-coded.

The three presets (`Trail Inspection`, `Aerial Imagery`, `Single-part trails`)
are rebuilt as manual `MapThemeRecord`s — the capture API
(`createThemeFromCurrentState`/`applyTheme`) hard-crashes QGIS 4.2.2
(reproduced in the hardening change), so preset state is written node by node,
exactly as the current macro already does.

## Decision 3 — macro is the single source of truth

`qgis/trail_presentation_macro.py` is rewritten for the single-layer model and
remains both a repo file and the embedded project macro body. The build script
(managed-project-build-and-verify change) re-embeds the file contents into the
project `Macros` section on every build, so the embedded copy can never fall
out of sync.

## Decision 4 — atlas and 3D scene

- Atlas coverage: `layout.atlas().setCoverageLayer(<Hiking Trails>)`.
  `pageNameExpression` (`concat("name", ' — OSM ', "osm_ids")`) and the
  172-page count are unchanged and verified after the swap.
- 3D scene: the old `All named trails (3D)` layer node is removed and the
  `Hiking Trails` layer id is added to the scene's terrain `<layers>` list
  (the build script resolves ids by name at stamp time — see the
  managed-project-build change).
- The `3D terrain texture` theme (10 m aerial only) is untouched.

## Repro checks

1. Atlas page count == 172 after coverage swap.
2. Categorized categories == 172 == CSV rows; every colour equals the CSV.
3. 3D scene categorised renderer present and palette-complete.
4. Rendering a trail isolation shows exactly one trail.
5. `verify_data.py` stays green.

## Non-goals

- Keeping per-trail layer checkboxes (replaced by filter isolation).
- Rebuilding the print layout from scratch (authored in QGIS; the build change
  enforces, not regenerates, layout state).
