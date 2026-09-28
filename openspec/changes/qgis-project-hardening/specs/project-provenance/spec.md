## Purpose

Keeps project documentation and derived data honest about what actually exists
on disk, so that a reader is never sent to a file that is absent and no dataset
appears without a recorded origin.

## ADDED Requirements

### Requirement: Documented file paths exist

Every file or directory path named in project documentation SHALL exist at the
path given, or the documentation SHALL be corrected.

#### Scenario: Paths are checkable

- **WHEN** a verification pass extracts paths from the project documentation
- **THEN** each extracted path is resolved relative to the project root
- **AND** any path that does not resolve is reported by name

#### Scenario: Absent paths are corrected, not assumed

- **WHEN** verification finds a documented path that does not exist
- **THEN** the documentation is corrected to name the file that is actually
  present
- **AND** no placeholder is left standing in for the missing file

#### Scenario: Real files are documented

- **WHEN** verification completes
- **THEN** every derived dataset present in the data directory is named in the
  documentation
- **AND** datasets that exist but are undocumented are reported

### Requirement: Directory names match reality

Documentation SHALL name directories as they exist on disk.

#### Scenario: Mismatched directory name is corrected

- **WHEN** documentation names a directory that does not exist while a
  similarly named one does
- **THEN** the documented name is corrected to the directory present

#### Scenario: Documented subdirectory exists

- **WHEN** documentation refers to a subdirectory's own readme
- **THEN** that readme is present, or the reference is removed

### Requirement: Stale recorded values are refreshed

Where documentation records a size, timestamp, feature count or checksum for a
file, the recorded value SHALL match the file as it currently is.

#### Scenario: Recorded size matches

- **WHEN** a documented byte size is compared against the file
- **THEN** they agree
- **AND** a mismatch fails the check

#### Scenario: Recorded timestamp matches

- **WHEN** a documented data timestamp is compared against the file's recorded
  source timestamp
- **THEN** they agree
- **AND** a mismatch fails the check

#### Scenario: Recorded count matches

- **WHEN** a documented feature count is compared against the dataset
- **THEN** they agree
- **AND** a mismatch fails the check

### Requirement: Derived data records its origin

Every derived dataset SHALL be traceable to the command or process that
produced it.

#### Scenario: Trail datasets name their build

- **WHEN** a trail dataset is inspected
- **THEN** the documentation states how it was produced
- **AND** the extract, boundary and filter used are named

#### Scenario: Rasters name their preparation

- **WHEN** a large raster's preparation is documented
- **THEN** the overview and tiling steps applied to it are recorded
- **AND** the resulting configuration is stated

### Requirement: Attribution requirements are preserved

The project's OSM attribution obligations SHALL remain stated wherever
published output is described.

#### Scenario: Attribution survives editing

- **WHEN** documentation describing a published output is edited
- **THEN** the OSM attribution requirement remains present
- **AND** the imagery permission restriction remains stated

#### Scenario: Restricted imagery still flagged

- **WHEN** the documentation mentions the restricted city imagery
- **THEN** it remains flagged as unusable until the intended use is confirmed
