# Project Build Specification

## Purpose

Defines the project file as a reproducible, machine-verified artifact: a build
script enforces canonical invariants and stamps the 3D scene XML, and an
offscreen verification gate checks the result. The project is stored as plain
XML so changes are reviewable in git.

## Requirements

### Requirement: The project file is reproducible

A build script SHALL reproduce the project file from curated inputs (data
sources, the trail colour palette, and the canonical 3D scene settings), such
that running the build twice produces byte-identical output.

#### Scenario: Repeated builds match

- **WHEN** the build runs twice against unchanged inputs
- **THEN** the two output files are identical under checksum

#### Scenario: The 3D scene settings survive a save cycle

- **WHEN** the project is saved and reopened in QGIS
- **THEN** the terrain theme binding, texture size and the bloom / colour
  grading / camera settings are still present

### Requirement: Project invariants are machine-verified

A single command SHALL load the saved project offscreen and verify its
invariants, exiting non-zero when any check fails.

#### Scenario: Gate detects a broken project

- **WHEN** the project is edited so that a trail category no longer matches
  the palette or the 3D stamp is missing
- **THEN** the verification command exits non-zero with a message naming the
  failed check

#### Scenario: Gate asserts the structural contract

- **WHEN** the verification command runs against a healthy project
- **THEN** it confirms the project CRS, relative paths, single categorized
  trail layer with palette-complete categories, the map themes, the 3D stamp,
  the atlas coverage and page count, and that all layer sources resolve

### Requirement: Project storage is reviewable

The committed project file SHALL be plain XML with readable diffs, without
requiring a binary archive or an auxiliary database to open correctly.

#### Scenario: Diffs are human-readable

- **WHEN** the project file changes
- **THEN** the diff shows the edited XML elements rather than an opaque binary
  change

#### Scenario: The file opens without auxiliary state

- **WHEN** the project file is loaded on a clean checkout
- **THEN** the project opens with the same layers, themes and layout
- **AND** no auxiliary storage database is required

### Requirement: The presentation macro embeds from a single source

The macro stored in the project SHALL be reproduced from its authoritative
file in the repository during the build, so the two can never drift.

#### Scenario: Embedded macro matches the file

- **WHEN** the build runs
- **THEN** the project `Macros` section contains exactly the contents of
  `qgis/trail_presentation_macro.py`
