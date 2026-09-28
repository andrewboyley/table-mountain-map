## Purpose

Generates one framed map page per named trail from the trail extents, so that
per-trail outputs are produced by the project itself instead of being set up by
hand for each trail.

## ADDED Requirements

### Requirement: One page per trail without manual setup

The project SHALL generate one map page per named trail from a declared
coverage source, with no per-trail manual configuration.

#### Scenario: Page count matches trail count

- **WHEN** the atlas is previewed
- **THEN** the number of pages equals the number of named trails
- **AND** each page corresponds to a distinct trail

#### Scenario: Coverage source is the trail data

- **WHEN** the atlas coverage is configured
- **THEN** it is driven by the named trail dataset
- **AND** no separate hand-built list of trails is required

### Requirement: Each page identifies its trail

Every generated page SHALL name the trail it depicts, derived from the feature
being mapped.

#### Scenario: Title follows the feature

- **WHEN** a page is generated for a trail
- **THEN** the page title is that trail's OSM name
- **AND** the title is taken from the feature rather than typed per page

#### Scenario: Names with awkward characters render

- **WHEN** a trail name contains punctuation or non-ASCII characters
- **THEN** the page title renders without truncation or substitution

### Requirement: Page order is deterministic

Atlas output SHALL produce pages in a stable, reproducible order.

#### Scenario: Repeat runs match

- **WHEN** the atlas is exported twice from unchanged input
- **THEN** the page order is identical between the two exports
- **AND** the page count is identical

#### Scenario: Sort key is explicit

- **WHEN** the atlas sort is configured
- **THEN** the sorting field and direction are recorded
- **AND** no dependence on internal feature order remains

### Requirement: Multi-part trails are framed explicitly

A trail whose geometry has disconnected parts SHALL be framed so that all its
parts are shown, and the fact that it is multi-part SHALL be visible in the
output rather than being resolved silently.

#### Scenario: All parts are inside the frame

- **WHEN** a page is generated for a trail with disconnected parts
- **THEN** every part is within the page frame
- **AND** no part is cropped out

#### Scenario: Multi-part status is visible

- **WHEN** a page is generated for a multi-part trail
- **THEN** the page indicates that the trail is multi-part
- **AND** the part count is shown

#### Scenario: A camera run is not silently a single line

- **WHEN** a multi-part trail is used to drive a single continuous camera run
- **THEN** the run is refused or explicitly acknowledged as crossing between
  disconnected parts
- **AND** the output is not presented as one unbroken path

### Requirement: Atlas output is reproducible

Repeated atlas exports from unchanged inputs SHALL produce the same pages.

#### Scenario: Layout is saved with the project

- **WHEN** the project is opened
- **THEN** the atlas layout is present with its coverage configured
- **AND** it can be exported without reconstructing the layout

#### Scenario: Scale and frame are stable

- **WHEN** a page is regenerated
- **THEN** it frames the same trail to the same extent
- **AND** the margin around the trail is consistent between pages
