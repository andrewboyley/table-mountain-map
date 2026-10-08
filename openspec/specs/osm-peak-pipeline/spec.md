# OSM Peak Pipeline Specification

## Purpose

Makes the named-summits dataset rebuildable from the OSM extract by a single
documented command, and verifiable against recorded provenance, so that
derived peak data is never an unexplained artefact on disk.

The dataset holds the officially named peaks that carry an elevation:
`natural=peak` features with both a non-blank `name` and a non-blank `ele`.

## Requirements

### Requirement: Peaks are rebuildable by one command

The named-summits dataset SHALL be rebuildable from the OSM extract by a
single documented command, with no manual step in between.

#### Scenario: Full rebuild from the extract

- **WHEN** the documented rebuild command is run against the project
- **THEN** the named-summits GeoPackage is produced
- **AND** no intermediate file has to be prepared by hand first

#### Scenario: The command is discoverable

- **WHEN** a user reads the project documentation
- **THEN** the exact rebuild command is stated
- **AND** its prerequisites are stated

### Requirement: Elevation is exposed as a number

The dataset SHALL carry a numeric elevation field alongside the verbatim OSM
string, because OSM elevations arrive as text from GeoJSON and a renderer or
expression that expects a number will otherwise classify the text instead.

#### Scenario: The OSM string is preserved

- **WHEN** the dataset is inspected
- **THEN** `ele` holds the value as OSM recorded it

#### Scenario: A numeric measure accompanies it

- **WHEN** the dataset is inspected
- **THEN** `ele_m` is a real-valued field
- **AND** it is set on every feature

#### Scenario: The two agree

- **WHEN** `ele` and `ele_m` are compared feature by feature
- **THEN** they agree to within floating-point tolerance

#### Scenario: Styling the string field is a defect, not a warning

- **WHEN** a graduated renderer is built on the String `ele` field
- **THEN** the classes are derived by lexicographic order
- **AND** the gate makes the numeric `ele_m` field mandatory instead

### Requirement: Elevation is read with a tag-faithful reader

The pipeline SHALL read the OSM extract with a reader that preserves every
node tag, and SHALL NOT rely on the GDAL OSM driver, because that driver drops
the `ele` tag from both its field list and its `other_tags` field.

#### Scenario: A peak read through the GDAL OSM driver has no elevation

- **WHEN** a `natural=peak` node carrying `ele` is read through the GDAL OSM
  driver
- **THEN** the `ele` tag appears neither as a field nor inside `other_tags`
- **AND** the elevation is unrecoverable from that reading

#### Scenario: The extract is read with osmium

- **WHEN** the extract is read with `osmium tags-filter` and `osmium export`
- **THEN** `ele` is present on every peak that has it
- **AND** the output GeoPackage carries an `ele` value for every feature

### Requirement: Only named peaks with an elevation are kept

The dataset SHALL contain a feature only when the node is `natural=peak`, its
`name` is non-null and non-blank, and its `ele` is non-null and non-blank.

#### Scenario: An unnamed peak is excluded

- **WHEN** a `natural=peak` node has no name
- **THEN** it is not in the dataset

#### Scenario: A named peak without an elevation is excluded

- **WHEN** a `natural=peak` node has a name but no `ele`
- **THEN** it is not in the dataset

#### Scenario: A named peak with an elevation is kept

- **WHEN** a `natural=peak` node has both a name and an `ele`
- **THEN** it is in the dataset with that name and that elevation

#### Scenario: Every feature carries both values

- **WHEN** the dataset is inspected
- **THEN** no feature has a blank name
- **AND** no feature has a blank or unparseable `ele`

### Requirement: Feature provenance is recorded

Each feature SHALL carry the OSM node id it came from, and the dataset SHALL
ship a manifest naming the OSM nodes it contains, so a feature can be traced
back to its source.

#### Scenario: The node id survives the rebuild

- **WHEN** the dataset is inspected
- **THEN** each feature carries an `osm_id` holding its OSM node id

#### Scenario: The id set is recorded

- **WHEN** the manifest is read
- **THEN** it lists the `osm_id` of every feature in the dataset

#### Scenario: The id set is checked on verification

- **WHEN** the dataset is compared against the manifest
- **THEN** a mismatch in the `osm_id` set fails verification

### Requirement: Rebuild is deterministic

Given the same OSM extract, a rebuild SHALL produce the same features,
attributes, geometry and order.

#### Scenario: Feature-level equality

- **WHEN** the dataset is rebuilt from an unchanged extract
- **THEN** the feature count is unchanged
- **AND** the per-feature attributes are unchanged

#### Scenario: Ordering does not affect output

- **WHEN** the extract is processed in a different feature order
- **THEN** the resulting dataset is identical

#### Scenario: Features are stored in a fixed order

- **WHEN** the dataset is inspected
- **THEN** features are stored sorted by `osm_id` ascending
- **AND** the rebuild fails if they are not

#### Scenario: Node ids are unique

- **WHEN** the dataset is inspected
- **THEN** no two features share an `osm_id`

### Requirement: The output is in the project CRS

The dataset SHALL be written in the project CRS, EPSG:32734.

#### Scenario: Written in project CRS

- **WHEN** the dataset is inspected
- **THEN** its CRS is EPSG:32734
- **AND** the manifest records the same CRS

### Requirement: The model runs from the QGIS profile

The rebuild SHALL install the Processing model into the active QGIS profile
before invoking it, because `qgis_process` resolves `model:<name>` from the
profile rather than from the repository.

#### Scenario: Model is installed automatically

- **WHEN** the rebuild command is run on a machine where the model is not yet
  installed in the QGIS profile
- **THEN** the model is copied into the profile's models directory
- **AND** `qgis_process` finds it without a manual step

#### Scenario: Installation is idempotent

- **WHEN** the rebuild command is run repeatedly
- **THEN** re-installing the model does not change the result

### Requirement: Verification is content-based, not byte-based

Verification SHALL compare content and attributes rather than file bytes,
because the GeoPackage writer embeds a modification timestamp that changes on
every save even when the data is identical.

#### Scenario: Byte checksum is not the acceptance test

- **WHEN** a verification pass runs on the named-summits GeoPackage
- **THEN** acceptance is decided by feature count, attributes and CRS
- **AND** a changed byte checksum alone does not fail verification

#### Scenario: The recorded digest is informational

- **WHEN** the manifest records a digest of the GeoPackage
- **THEN** the manifest states that the digest describes the file as committed
- **AND** not the acceptance criterion
