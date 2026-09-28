## Purpose

Lets a user isolate, restyle and switch individual named trails from the QGIS
layer tree using native QGIS features, instead of maintaining a large
proliferation of separately configured layers.

## ADDED Requirements

### Requirement: One trail can be isolated in a single action

A user SHALL be able to make exactly one named trail visible without changing
the visibility of any other trail, in a single action from the layer tree.

#### Scenario: Checking a trail clears its siblings

- **WHEN** the trail group is configured as mutually exclusive and a user
  checks one trail
- **THEN** every other trail in that group becomes unchecked
- **AND** the checked trail remains visible

#### Scenario: Isolation does not disturb other groups

- **WHEN** a user isolates a trail from the named trail group
- **THEN** the visibility of unnamed trails, tracks, rasters and all other
  layers is unchanged

#### Scenario: Unnamed bulk layers are unaffected

- **WHEN** a user isolates a named trail
- **THEN** the unnamed trail and track layers keep their previous visibility
  state

### Requirement: Alternative looks do not require duplicate layers

Different visual treatments of the same trail SHALL be selectable without
duplicating the underlying layer.

#### Scenario: Styles are named and switchable

- **WHEN** a trail group carries more than one style
- **THEN** each style has a distinct name shown in the layer context menu
- **AND** selecting a style applies it to the group without recreating layers

#### Scenario: One trail data source serves every style

- **WHEN** any style of the trail group is active
- **THEN** all styles read from the same trail data source
- **AND** no additional trail file is created to hold a style

### Requirement: Whole-map configurations switch in one action

Saved configurations of layer visibility SHALL be restorable in a single
action.

#### Scenario: Preset restores an exact configuration

- **WHEN** a user selects a saved visibility preset
- **THEN** every layer's visibility matches the state captured when the preset
  was saved
- **AND** layers absent from the preset take their recorded default state

#### Scenario: Presets cover the configurations that matter

- **WHEN** the presets are listed
- **THEN** a preset exists for the trail-inspection configuration and for the
  aerial-imagery configuration

### Requirement: Trails are identifiable by name

The layer tree or legend SHALL present each named trail with its OSM name so a
user can find a trail without knowing its layer identity.

#### Scenario: Legend lists trail names

- **WHEN** the trail group is expanded
- **THEN** each entry is labelled with the trail's OSM name
- **AND** no entry is labelled with a layer name or identifier alone

#### Scenario: Names are unique within the project

- **WHEN** trail names are collected
- **THEN** no two named trail layers share a display label
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
- **THEN** it can still be selected
- **AND** the fact that it is multi-part is visible before framing it
