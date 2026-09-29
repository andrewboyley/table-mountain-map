# Raster Performance Specification

## Purpose

Keeps the project's large rasters interactive at every zoom level by ensuring
overview pyramids exist, so that drawing a view never requires reading a whole
multi-gigabyte source file.

## Requirements

### Requirement: Large rasters have overviews

Every raster in the project whose pixel count exceeds 10,000,000 SHALL have a
resolvable set of overviews, either as an external sidecar or built into the
file.

#### Scenario: Overview presence is verifiable

- **WHEN** a verification pass runs over every raster in the project
- **THEN** each raster above the pixel threshold reports a resolvable
  overview set
- **AND** any raster failing the check is named explicitly

#### Scenario: A large raster is added without overviews

- **WHEN** a raster above the threshold is added to the project
- **THEN** the verification pass reports it as failing
- **AND** the failure is not suppressed

### Requirement: Overview generation preserves the source

Generating overviews SHALL NOT alter the bytes, dimensions or geotransform of
the source raster.

#### Scenario: Source is untouched

- **WHEN** overviews are generated for a raster
- **THEN** the source raster's checksum is unchanged
- **AND** its pixel dimensions and geotransform are unchanged

#### Scenario: Overviews are external sidecars

- **WHEN** overview generation completes for a large raster
- **THEN** the overview data is stored outside the source raster file
- **AND** the source raster is not rewritten

### Requirement: Overview generation is reversible

Removing the overview data SHALL return the project to its previous rendering
behaviour with no loss of source data.

#### Scenario: Removing overviews restores prior behaviour

- **WHEN** the overview sidecars are deleted
- **THEN** the rasters still open and render
- **AND** no source data has been lost
- **AND** zoomed-out views become slow again, which is the documented prior
  state

### Requirement: Zoomed-out rendering stays interactive

With overviews present, panning and zooming at full project extent SHALL
remain interactive, and drawing a view SHALL NOT require reading the entire
source raster.

#### Scenario: Full extent is usable

- **WHEN** the project is opened at full extent and panned across the whole
  crop area
- **THEN** rendering remains interactive
- **AND** the read volume is a small fraction of the source file size

#### Scenario: Zoom to full resolution still works

- **WHEN** the view is zoomed to native resolution
- **THEN** full-resolution pixels are shown
- **AND** the overview pyramid does not cap the achievable detail

### Requirement: Raster structure is recorded

The overview configuration applied to each raster SHALL be recorded so the same
setup can be recreated.

#### Scenario: Configuration is documented

- **WHEN** the raster preparation is documented
- **THEN** the overview levels and the resampling method used are stated
- **AND** the command that produces them is recorded
