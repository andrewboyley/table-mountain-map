# Basemap Services Specification

## Purpose

Defines how the project consumes the local MapProxy: cached OpenStreetMap tiles
over XYZ and the restricted City of Cape Town aerial imagery over WMS in the
project CRS, with the aerial cache gridded in EPSG:32734 (UTM zone 34S)
because the upstream service returns blank imagery in web mercator.

## Requirements

### Requirement: CoCT aerial is served as WMS in the project CRS

The CoCT aerial imagery SHALL be loadable in the QGIS project from the
MapProxy WMS service in `EPSG:32734` and SHALL render real imagery, not blank
tiles.

#### Scenario: WMS GetMap returns imagery

- **WHEN** a WMS `GetMap` request for layer `coct_aerial` in `EPSG:32734` is
  made against the local MapProxy
- **THEN** the response contains non-white imagery for areas over land

#### Scenario: The layer's data source is WMS

- **WHEN** the project's aerial layer source is inspected
- **THEN** it references the MapProxy WMS service with layer `coct_aerial`
- **AND** it does not rely on a tile/XYZ endpoint

#### Scenario: Upstream is fetched in the native CRS

- **WHEN** MapProxy fetches from the upstream CoCT service
- **THEN** the request uses `EPSG:32734`
- **AND** the empty `styles` parameter is forwarded so the server default
  applies

### Requirement: Aerial tiles are cached on the project grid

MapProxy SHALL cache the aerial imagery on a grid aligned to the project CRS
covering the TMNP crop extent, so WMS requests in `EPSG:32734` hit the cache
directly.

#### Scenario: Cache grid is EPSG:32734

- **WHEN** the MapProxy cache configuration is inspected
- **THEN** the `coct_aerial_cache` grid is `utm34s` (`EPSG:32734`)
- **AND** its coverage includes the TMNP crop extent

#### Scenario: Requests outside the grid are not silently half-blank

- **WHEN** a WMS request's bounding box lies partly outside the grid coverage
- **THEN** the service still returns a coherent image for the covered area

### Requirement: OSM context is served as cached XYZ

The OpenStreetMap basemap SHALL be served from the local MapProxy as XYZ tiles
in web mercator, with attribution retained in the project documentation.

#### Scenario: XYZ endpoint serves tiles

- **WHEN** the project's OSM layer source is inspected
- **THEN** it references the MapProxy XYZ/TMS tile endpoint
- **AND** the layer renders tiles at the project's working scales

#### Scenario: Attribution is retained

- **WHEN** documentation describing published output is inspected
- **THEN** the OSM attribution requirement is still stated
