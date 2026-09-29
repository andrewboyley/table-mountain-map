## ADDED Requirements

### Requirement: The committed project file is immune to GUI-save drift

QGIS GUI saves SHALL NOT corrupt the committed project artifact: their side files are never committed, and a rebuild restores the byte-identical canonical file.

#### Scenario: Save side files are never committed

- **WHEN** a GUI save creates a backup or an attachments archive next to the project file
- **THEN** those side files are ignored by git
- **AND** none of them appears in the tracked tree

#### Scenario: A drifted artifact is reconciled by rebuild

- **WHEN** the committed project file differs from a fresh build of the same inputs, for example after a GUI save
- **THEN** the offscreen build reproduces the canonical file byte-identically
- **AND** the verification gate passes on the rebuilt file
