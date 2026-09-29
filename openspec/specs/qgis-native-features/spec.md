# QGIS Native Features Specification

## Purpose

Keeps the saved QGIS project expressive through native QGIS mechanisms — categorized renderers, map themes, filters, atlas coverage and theme-driven 3D terrain texture — so no scripted or file-based workaround stands in for a built-in feature, and records which features were deliberately declined.

## Requirements

### Requirement: Layer behaviour is expressed with native QGIS features

Each layer's rendering and interaction SHALL use the native QGIS feature that fits it, and the mapping of layer to feature SHALL be documented.

#### Scenario: The feature mapping is documented

- **WHEN** the QGIS documentation is read
- **THEN** for each project layer it names the native QGIS feature the layer uses
- **AND** the mapping covers trails, boundary, crop extent, DEM, rasters, basemaps, atlas and the 3D scene

#### Scenario: Declined features are recorded

- **WHEN** the QGIS documentation is read
- **THEN** features evaluated but not adopted are listed with the reason
- **AND** no layer relies on a non-native workaround where a native feature exists

#### Scenario: Trails stay one categorized layer

- **WHEN** the trail layer is inspected
- **THEN** it is a single categorized layer in 2D and 3D
- **AND** isolation and single-part filtering use subset-string filters and map themes rather than extra layers

### Requirement: Headless QGIS is the canonical validation path

Project artifacts SHALL be validated and rebuilt with headless QGIS tooling, not by manual GUI inspection alone.

#### Scenario: The project gate runs offscreen

- **WHEN** the project verification gate runs
- **THEN** it loads the project offscreen and exits non-zero on any failed invariant

#### Scenario: The model check runs headless

- **WHEN** the processing model is validated
- **THEN** validation runs through the headless QGIS process tool
- **AND** opening the GUI is not required
