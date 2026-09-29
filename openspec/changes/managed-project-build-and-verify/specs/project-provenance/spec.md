## MODIFIED Requirements

### Requirement: Project facts are documented accurately

The repository SHALL document how the QGIS project is stored, how it is built
and verified, and which services supply its basemaps, so that a reader can
reproduce the project and understand its data provenance from the repository
alone.

#### Scenario: Storage format is documented

- **WHEN** the QGIS documentation is read
- **THEN** it names the project file format and its location in the repository

#### Scenario: Build and verification are documented

- **WHEN** the QGIS documentation is read
- **THEN** it names the build script and the verification gate and how to run
  them

#### Scenario: Basemap services are documented

- **WHEN** the QGIS documentation is read
- **THEN** it states that OSM is served as cached XYZ tiles and the CoCT
  aerial imagery as WMS in `EPSG:32734` from the local MapProxy

### Requirement: Published-output restrictions are documented

Documentation SHALL retain the OSM attribution requirement and the flag that
CoCT aerial imagery is restricted and not for publication, unchanged by this
change.

#### Scenario: Restrictions are still stated

- **WHEN** documentation describing published output or the basemaps is
  inspected
- **THEN** the OSM attribution requirement is stated
- **AND** the CoCT aerial imagery is flagged as restricted, not for
  publication
