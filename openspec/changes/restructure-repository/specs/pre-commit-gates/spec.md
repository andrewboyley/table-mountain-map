## Purpose

Enforces repository quality at commit time with checks that catch the failure classes this project has hit — oversized binaries, unparsable scripts, unformatted Python and invalid Processing models — and documents how to maintain the gate set.

## ADDED Requirements

### Requirement: Large binaries are blocked at commit

Commits SHALL be refused when they add a file above the configured size threshold, unless the file is explicitly allowed.

#### Scenario: An oversized file is refused

- **WHEN** a commit tries to add a file above the configured maximum size
- **THEN** the commit fails with a message naming the file and the threshold

#### Scenario: The threshold is documented

- **WHEN** the contribution guide is read
- **THEN** it states the large-file threshold and how to adjust it

### Requirement: Python scripts are syntactically valid and lint-clean

Every Python file under `scripts/` SHALL parse and SHALL pass the configured linter and formatter checks before commit.

#### Scenario: Unparsable scripts are refused

- **WHEN** a Python file with a syntax error is staged
- **THEN** a syntax check fails the commit

#### Scenario: Lint and format are enforced

- **WHEN** a script violates a lint rule or the configured formatter
- **THEN** the lint or format hook reports the violation
- **AND** the violation fails the commit

### Requirement: Processing models are validated headlessly

Changes to the trail-rebuild Processing model SHALL be validated with the headless QGIS process tool before commit.

#### Scenario: A valid model passes

- **WHEN** an unchanged or validly edited trail-rebuild model is committed
- **THEN** the headless model validation succeeds
- **AND** the commit proceeds

#### Scenario: An invalid model is refused

- **WHEN** the model file cannot be loaded by QGIS Processing
- **THEN** the headless validation fails
- **AND** the commit is refused

### Requirement: Gate maintenance is documented

The contribution guide SHALL document the gate list and the commands to update and validate the hook configuration.

#### Scenario: Gate commands are documented

- **WHEN** the contribution guide is read
- **THEN** it names the commands to autoupdate hook versions, migrate legacy configuration and validate the hook config
- **AND** it lists which gates run at commit and which run at push
