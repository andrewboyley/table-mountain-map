## ADDED Requirements

### Requirement: Findings analyses describe the current state

Where an analysis document records the state of the project or its data, the record SHALL match the repository as it currently is.

#### Scenario: The findings document matches the tree

- **WHEN** the terrain-data findings document is read
- **THEN** every path and directory name it names resolves in the current repository
- **AND** no vanished artifact is named as present and no dead absolute path remains

#### Scenario: Aerial source names are current

- **WHEN** documentation names the aerial orthophoto source
- **THEN** it names the file actually present on disk
- **AND** it does not name the renamed original file
