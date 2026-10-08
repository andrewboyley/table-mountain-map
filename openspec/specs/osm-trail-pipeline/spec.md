# OSM Trail Pipeline Specification

## Purpose

Makes the trail datasets rebuildable from the OSM extract by a single
documented command, and verifiable against recorded provenance, so that
derived trail data is never an unexplained artefact on disk.

## Requirements

### Requirement: Trails are rebuildable by one command

The trail datasets SHALL be rebuildable from the OSM extract by a single
documented command, with no manual step in between.

#### Scenario: Full rebuild from the extract

- **WHEN** the documented rebuild command is run against the project
- **THEN** the named trail dataset and the supplement datasets are produced
- **AND** no intermediate file has to be prepared by hand first

#### Scenario: The command is discoverable

- **WHEN** a user reads the project documentation
- **THEN** the exact rebuild command is stated
- **AND** its prerequisites are stated

### Requirement: Rebuild is deterministic

Given the same OSM extract, park boundary and filter, a rebuild SHALL produce
the same features, attributes and geometry.

#### Scenario: Feature-level equality

- **WHEN** a dataset is rebuilt from an unchanged extract
- **THEN** the feature count is unchanged
- **AND** the per-feature attributes are unchanged
- **AND** the geometry is geometrically equal to within 1 millimetre

#### Scenario: Aggregate measures are stable

- **WHEN** a rebuilt named trail dataset is measured
- **THEN** the total length agrees with the recorded value
- **AND** the trail count agrees with the recorded value

#### Scenario: Ordering does not affect output

- **WHEN** the extract is processed in a different feature order
- **THEN** the resulting dataset is identical

### Requirement: Verification is content-based, not byte-based

Verification SHALL compare content and geometry rather than file bytes, because
the GeoPackage writer embeds a modification timestamp that changes on every
save even when the data is identical.

#### Scenario: Byte checksum is not the acceptance test

- **WHEN** a verification pass runs on a GeoPackage output
- **THEN** acceptance is decided by feature count, attributes and geometry
- **AND** a byte-level difference caused only by a save timestamp does not fail
  the check

#### Scenario: Real data change is detected

- **WHEN** a feature, attribute or coordinate is altered
- **THEN** verification fails
- **AND** the differing feature is identified

### Requirement: Provenance is recorded

Each trail dataset SHALL record the source extract, the clip boundary, the tag
filter, the dissolve rule and the output CRS it was produced with.

#### Scenario: Source extract is named

- **WHEN** a trail dataset's provenance is read
- **THEN** it names the specific OSM extract file used
- **AND** the extract's size and modification time are recorded

#### Scenario: Clip boundary is named

- **WHEN** a trail dataset's provenance is read
- **THEN** it names the park boundary used for clipping, by relation
  identifier
- **AND** it records the boundary's measured area

#### Scenario: Tag filter is explicit

- **WHEN** a trail dataset's provenance is read
- **THEN** the accepted highway values are listed
- **AND** whether unnamed features were kept is stated
- **AND** the accept strategy is stated

#### Scenario: Dissolve rule is explicit

- **WHEN** a trail dataset's provenance is read
- **THEN** the grouping attribute is named
- **AND** the geometric operator used to combine segments is stated

#### Scenario: CRS is recorded

- **WHEN** a trail dataset's provenance is read
- **THEN** the output coordinate reference system is named
- **AND** its axis units are confirmed linear

### Requirement: Pipeline is runnable from QGIS

The rebuild SHALL be expressible as a QGIS Processing model,
so it runs from the application rather than only from a shell.

#### Scenario: Model is discoverable in Processing

- **WHEN** the QGIS Processing toolbox is opened
- **THEN** the trail rebuild is listed as a runnable model
- **AND** its parameters are exposed rather than hard-coded

#### Scenario: Model and shell entry point agree

- **WHEN** the model is run
- **THEN** it produces the same output as the documented shell command
- **AND** the two paths are documented as equivalent

### Requirement: Outputs are identified in the project

A verification pass SHALL be able to confirm that every expected trail dataset
is present, with a non-empty feature count and a valid geometry on every
feature.

#### Scenario: Expected datasets are present

- **WHEN** the expected output list is checked
- **THEN** every listed dataset is present
- **AND** each reports a non-zero feature count

#### Scenario: Invalid geometry is reported

- **WHEN** geometry validity is checked across a dataset
- **THEN** any invalid feature is named
- **AND** a non-zero invalid count fails the check
