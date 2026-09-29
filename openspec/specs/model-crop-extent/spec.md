# Model Crop Extent Specification

## Purpose

Defines the single north-up rectangle that every raster and vector derivative
in this project is cropped to, so that crop targets cannot diverge from one
another or from the data they describe.

## Requirements

### Requirement: Crop extent is north-up

The model crop extent SHALL be axis-aligned to grid north. A rotated
minimum-area bounding rectangle SHALL NOT be used as a crop target.

#### Scenario: Authoritative crop extent is axis-aligned

- **WHEN** the crop extent geometry is inspected
- **THEN** its edges are parallel to the grid axes of `EPSG:32734`
- **AND** no edge bearing differs from grid north or grid east

#### Scenario: Rotated rectangle is not produced

- **WHEN** the crop extent is regenerated from the park boundary
- **THEN** no rotated minimum-area rectangle is created
- **AND** the previously documented rotated rectangle is not reinstated

### Requirement: Exactly one authoritative crop extent

The project SHALL have exactly one authoritative crop extent. Consumers of the
crop extent SHALL reference that one layer, and no second rectangle may serve
as a crop target.

#### Scenario: Only one crop extent is authoritative

- **WHEN** the project is searched for crop targets
- **THEN** exactly one crop extent layer is found
- **AND** any other extent present is labelled as descriptive rather than
  authoritative

#### Scenario: No divergent rectangle is introduced

- **WHEN** a new extent layer is added to the project
- **THEN** it is not used as a crop target unless it replaces the
  authoritative extent
- **AND** the replacement is recorded in the project documentation

### Requirement: Crop extent contains the complete park boundary

The crop extent SHALL contain every vertex of the Table Mountain National Park
boundary from OSM relation 338191.

#### Scenario: Boundary is fully contained

- **WHEN** every vertex of the park boundary is tested against the crop extent
- **THEN** no vertex lies outside it
- **AND** the reported maximum excursion is no greater than 1 millimetre, which
  is within the precision the published coordinates are stated at

#### Scenario: Contained check is repeatable

- **WHEN** the containment check is run twice against the same files
- **THEN** both runs report the same vertex count and the same maximum
  excursion

### Requirement: Crop extent derives from a declared stable source

The crop extent SHALL be derived from a single declared source, which SHALL be
recorded alongside the extent. That source SHALL be the park boundary rather
than a data extract, so that re-clipping an extract cannot silently
invalidate the extent.

#### Scenario: Source is recorded

- **WHEN** the crop extent's derivation is read
- **THEN** it names the park boundary it was computed from, by relation
  identifier
- **AND** the boundary's measured area is recorded

#### Scenario: Re-clipping does not invalidate the extent

- **WHEN** the OSM extract is re-clipped with a different area
- **THEN** the crop extent is unchanged
- **AND** no stale-extent condition arises

#### Scenario: Extent is reproducible from its source

- **WHEN** the extent is recomputed from the declared boundary
- **THEN** the side lengths and area match the recorded values
- **AND** a difference beyond 0.01 m in length or 0.0001 km² in area fails

#### Scenario: An extract-derived extent is rejected

- **WHEN** a candidate crop extent is derived from the bounding box of a data
  extract rather than from the boundary
- **THEN** it is rejected as a crop target
- **AND** the reason is recorded

### Requirement: Raster footprint divergence is reported

Where an existing raster's footprint differs from the crop extent, the
difference SHALL be reported as a known condition rather than treated as
misalignment or silently ignored.

#### Scenario: Larger raster footprint is reported

- **WHEN** a raster's footprint is larger than the crop extent
- **THEN** the raster is identified as a superset of the crop extent
- **AND** the size difference is reported

#### Scenario: Superset is not a failure

- **WHEN** a raster fully contains the crop extent
- **THEN** no alignment failure is raised
- **AND** the raster remains usable without reprojection

#### Scenario: Partial overlap is a failure

- **WHEN** a raster's footprint only partly overlaps the crop extent
- **THEN** it is reported as not covering the crop extent
- **AND** the uncovered portion is quantified

### Requirement: Published dimensions match the layer

The dimensions, area and corner coordinates published in project documentation
SHALL be the measured values of the authoritative crop extent layer.

#### Scenario: Published table reflects the real geometry

- **WHEN** the documented side lengths and area are compared against the layer
- **THEN** they agree to within 0.01 m for lengths and 0.0001 km² for area
- **AND** the documented corner coordinates lie on the layer's ring

#### Scenario: Documented rotated values are withdrawn

- **WHEN** the documentation is checked for a rotated crop rectangle
- **THEN** no rotated side lengths, area or corner coordinates remain
- **AND** the north-up values appear in their place
