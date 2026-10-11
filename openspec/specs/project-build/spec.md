# Project Build Specification

## Purpose

Defines the QGIS project file as a hand-edited, machine-verified artifact.
The project is stored as plain XML so changes are reviewable in git. An
offscreen verification gate checks that the essential invariants hold after
each manual edit.

## Requirements

### Requirement: Project invariants are machine-verified

A single command SHALL load the saved project offscreen and verify its
invariants, exiting non-zero when any check fails.

#### Scenario: Gate detects a broken project

- **WHEN** the project is edited so that the CRS is wrong, a trail category
  no longer matches the palette, or the 3D renderer is missing
- **THEN** the verification command exits non-zero with a message naming the
  failed check

#### Scenario: Gate asserts the structural contract

- **WHEN** the verification command runs against a healthy project
- **THEN** it confirms the project CRS (`EPSG:32734`), relative paths, single
  categorized trail layer with palette-complete categories, the 3D renderer,
  and that all local layer sources resolve

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

### Requirement: The project embeds no scripts or macros

The project file SHALL NOT contain a `Macros` / `pythonCode` entry or any other
embedded script. Presentation is expressed with native QGIS features: map
themes, layer visibility, renderers, and the subset-string provider on the
trail layer.

#### Scenario: No macro is stored

- **WHEN** the project file is inspected
- **THEN** it contains no `Macros` properties block and no `pythonCode` entry

#### Scenario: The project loads with no macro

- **WHEN** the project is loaded offscreen
- **THEN** `readEntry("Macros", "/pythonCode")` reports the entry as absent
- **AND** the layers, map themes and layouts are unchanged

### Requirement: The committed project file is hand-edited

QGIS GUI saves SHALL be committed directly after verification. There is no
rebuild step that overwrites the working tree. Side files (`.qgs~`,
`_attachments.zip`) are never committed.
