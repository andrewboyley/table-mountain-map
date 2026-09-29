## MODIFIED Requirements

### Requirement: One trail can be isolated in a single action

A user SHALL be able to make exactly one named trail visible without changing
the visibility of any other trail, in a single action, using a filter on the
single trail layer combined with a saved preset.

#### Scenario: Isolating a trail shows only it

- **WHEN** the user runs the isolation action for a trail name
- **THEN** the trail layer's filter restricts the visible features to that
  trail
- **AND** every other named trail is not shown

#### Scenario: Isolation does not disturb other groups

- **WHEN** a user isolates a trail
- **THEN** the visibility of unnamed trails, tracks, rasters and all other
  layers is unchanged

#### Scenario: The filter can be cleared

- **WHEN** the user runs the clear action
- **THEN** all named trails are visible again

### Requirement: Alternative looks do not require duplicate layers

Different visual treatments of the trails SHALL be selectable without
duplicating the underlying layer.

#### Scenario: Styles are named and switchable

- **WHEN** the trail layer carries more than one style
- **THEN** each style has a distinct name shown in the layer context menu
- **AND** selecting a style changes the rendering without creating layers

#### Scenario: One trail data source serves every style

- **WHEN** any style of the trail layer is active
- **THEN** all styles read from the same trail data source
- **AND** no additional trail file is created to hold a style

### Requirement: Whole-map configurations switch in one action

Saved configurations of layer visibility SHALL be restorable in a single
action.

#### Scenario: Preset restores an exact configuration

- **WHEN** a user selects a saved visibility preset
- **THEN** every layer's visibility matches the state captured when the preset
  was saved

#### Scenario: Presets cover the configurations that matter

- **WHEN** the presets are listed
- **THEN** a preset exists for the trail-inspection configuration and for the
  aerial-imagery configuration

### Requirement: Trails are identifiable by name

The layer tree or legend SHALL present each named trail with its OSM name so a
user can find a trail without knowing its layer identity.

#### Scenario: Legend lists trail names

- **WHEN** the trail layer's legend is expanded
- **THEN** each category is labelled with the trail's OSM name
- **AND** no category is labelled with a layer name or identifier alone

#### Scenario: Names are unique within the project

- **WHEN** trail categories are collected
- **THEN** no two categories share a display label
- **AND** any OSM name collision is surfaced rather than silently merged

### Requirement: Continuous trails can be selected alone

The user SHALL be able to restrict the trail set to those forming a single
unbroken line, excluding trails whose parts are disconnected.

#### Scenario: Filtering to single-part trails

- **WHEN** the trail set is filtered on the part count
- **THEN** only trails with a part count of one are shown
- **AND** the number shown matches the recorded count of single-part trails

#### Scenario: Multi-part trails remain reachable

- **WHEN** a user needs a trail whose parts are disconnected
- **THEN** it can still be selected by clearing the single-part filter

## ADDED Requirements

### Requirement: All named trails come from one layer

The entire named-trail set SHALL be served by a single layer whose data source
is the dissolved trail GeoPackage table, and whose classification field is the
trail name.

#### Scenario: One layer, all trails

- **WHEN** the layer tree is inspected
- **THEN** exactly one layer serves the named trails
- **AND** its source is `tm_hiking_trails_dissolved.gpkg` layer `hiking_trails`

#### Scenario: Categories match the trail inventory

- **WHEN** the categorized renderer is expanded
- **THEN** the number of categories equals the number of distinct named trails
- **AND** every category corresponds to one named trail

### Requirement: Trail colours are deterministic

Trail colours SHALL come from a committed, machine-readable palette so that a
rebuilt project reproduces the same legend.

#### Scenario: Palette is the source of truth

- **WHEN** the project is rebuilt
- **THEN** each trail category's colour equals the row for that trail in
  `qgis/styles/trail_colors.csv`

#### Scenario: The palette is complete

- **WHEN** the palette is compared with the trail inventory
- **THEN** every named trail has exactly one colour row

### Requirement: Named trails are categorised in 3D

The 3D scene SHALL colour each named trail according to the same palette by
varying a 3D line symbol per category, without needing per-trail layers.

#### Scenario: 3D symbols follow the palette

- **WHEN** the 3D scene renders named trails
- **THEN** each trail's colour matches its `trail_colors.csv` entry

#### Scenario: Categories are retained in the project

- **WHEN** the project is saved and reopened
- **THEN** the categorized 3D renderer is still applied
