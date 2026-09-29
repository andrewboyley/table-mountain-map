## Purpose

Defines where repository artifacts live so that directory names communicate their contents, every dataset has exactly one authoritative copy, and regenerable or orphaned files never enter the tracked tree.

## ADDED Requirements

### Requirement: The QGIS directory holds only project artifacts

The `qgis/` directory SHALL contain only project artifacts — the project file, styles, the presentation macro, the processing model and QGIS documentation — and SHALL NOT contain data layers.

#### Scenario: No data sources under qgis/

- **WHEN** the `qgis/` directory is listed
- **THEN** every file is a project artifact (project, styles, macro, model, documentation)
- **AND** no shapefile, GeoPackage or raster data source is tracked under `qgis/`

#### Scenario: The boundary lives in the data tree

- **WHEN** the DEM boundary mask is located
- **THEN** it resolves to `data/vector/bound/`
- **AND** no duplicate boundary files remain under `qgis/`

### Requirement: Every dataset has exactly one authoritative copy

Each dataset SHALL exist once at an authoritative path; duplicate or superseded copies SHALL be removed and SHALL NOT be resurrected.

#### Scenario: The park boundary exists once

- **WHEN** `data/vector/` is searched for the park boundary
- **THEN** the OSM relation GeoPackage is the single authoritative dataset
- **AND** the duplicate `tmnp` copy is absent

#### Scenario: Superseded rasters are not tracked

- **WHEN** the elevation data tree is inspected
- **THEN** no `_bgis` variant is present
- **AND** the verification inventory does not list it

### Requirement: Regenerable binary artifacts are not tracked

Raster sidecars and other files reproducible by documented commands SHALL NOT be committed.

#### Scenario: Overview sidecars are ignored

- **WHEN** overviews are generated for a raster
- **THEN** the `.ovr`/`.aux.xml`/`.wld` sidecars are regenerable by the documented overview commands
- **AND** none of them is tracked by git

#### Scenario: The inventory matches the tree

- **WHEN** the data verification script runs
- **THEN** its boundary, crop-extent and big-raster lists resolve against the actual tree
- **AND** nothing tracked is reported as missing

### Requirement: Every script is load-bearing

Each script under `scripts/` SHALL be referenced by a hook, by documentation, or by another script; orphaned tooling SHALL be removed.

#### Scenario: Scripts are referenced

- **WHEN** the scripts directory is cross-checked against hooks, READMEs and sibling scripts
- **THEN** every remaining script is named somewhere
- **AND** no script is unreferenced

#### Scenario: Orphaned tooling is not revived

- **WHEN** the repository is searched for the removed texture-pipeline scripts
- **THEN** they are absent
- **AND** nothing points at the renamed aerial input file

### Requirement: Working caches are ephemeral

Content under `cache/` SHALL be regenerable working state, clearable without breaking the build or the verification gates.

#### Scenario: Clearing the cache is safe

- **WHEN** `cache/` contents are cleared per its readme
- **THEN** the build and verification commands still succeed
- **AND** the regeneration commands are documented

#### Scenario: Cache content is not tracked

- **WHEN** the tracked tree is inspected
- **THEN** no file under `cache/` is committed
