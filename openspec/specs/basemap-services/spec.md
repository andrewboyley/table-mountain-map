# Basemap Services Specification

## Purpose

Defines how the project consumes the local MapProxy: cached OpenStreetMap tiles
over XYZ and the City of Cape Town GeoSpatial Datasets imagery and hillshade
over WMS. Every cache is stored on the webmercator grid (`EPSG:3857`), the one
grid the web clients speak, so those clients are served natively. The QGIS
project CRS is `EPSG:32734` (WGS 84 / UTM zone 34S) and is not cached, so QGIS
reads through a per-request reprojection out of the webmercator grid. The
upstream CoCT erdas WMS serves real imagery only in `EPSG:32734`; MapProxy
fetches upstream in `EPSG:32734` and reprojects to `EPSG:3857` for caching.

## Requirements

### Requirement: CoCT aerial is served as WMS in the project CRS

The CoCT aerial imagery SHALL be loadable in the QGIS project from the
MapProxy WMS service in `EPSG:32734` (the project CRS) and SHALL render real
imagery, not blank tiles. MapProxy fetches the upstream erdas WMS in its native
`EPSG:32734`, reprojects to the cached `EPSG:3857` grid, and reprojects again
on the way out to the `EPSG:32734` the project asks for.

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



### Requirement: CoCT hillshade is served as WMS

The CoCT 2 m hillshade SHALL be served from the local MapProxy WMS service so
it can be overlaid on the aerial layer for terrain context.
The layer is cached on the shared webmercator grid, and QGIS reprojects to the
project CRS (`EPSG:32734`) on the fly.

#### Scenario: Hillshade WMS GetMap returns imagery

- **WHEN** a WMS `GetMap` request for layer `coct_hillshade` is made against
  the local MapProxy
- **THEN** the response contains hillshade shading for areas within the
  requested bounding box

#### Scenario: Hillshade cache grid is webmercator

- **WHEN** the MapProxy cache configuration is inspected
- **THEN** the `coct_hillshade_cache` grid is `webmercator` (`EPSG:3857`)

### Requirement: CoCT basemap raster is served as WMS

The CoCT basemap raster (`Backdrops_Basemap_Raster`) SHALL be served from the
local MapProxy WMS service so it can be toggled on in the QGIS project as a
streetmap-style backdrop. It is cached on the shared webmercator grid, and QGIS
reprojects to the project CRS (`EPSG:32734`) on the fly.

#### Scenario: Basemap raster WMS GetMap returns imagery

- **WHEN** a WMS `GetMap` request for layer `coct_basemap` is made against
  the local MapProxy
- **THEN** the response contains basemap raster features for areas within the
  requested bounding box

#### Scenario: Basemap raster cache grid is webmercator

- **WHEN** the MapProxy cache configuration is inspected
- **THEN** the `coct_basemap_cache` grid is `webmercator` (`EPSG:3857`)

### Requirement: Every cache is on the webmercator grid

MapProxy SHALL cache every layer on the single `webmercator` grid (`EPSG:3857`),
so web clients read every layer natively and no cache needs an extent of its
own. The trade is that a client in any other CRS, QGIS included, is served by
reprojecting out of that grid per request rather than from a cache in its own
CRS. Measured on a warm cache that costs roughly 6 ms extra per tile, which is
not the reason to prefer it, but the single shared grid is.

#### Scenario: Aerial cache grid is webmercator

- **WHEN** the MapProxy cache configuration is inspected
- **THEN** the `coct_aerial_cache` grids are `webmercator` (`EPSG:3857`)

#### Scenario: No second grid is declared

- **WHEN** the `grids` block of the MapProxy configuration is inspected
- **THEN** it declares only `webmercator`

#### Scenario: QGIS still reads real imagery

- **WHEN** a WMS `GetMap` request for layer `coct_aerial` in `EPSG:32734` is made
- **THEN** the response contains non-white imagery for areas over land

### Requirement: WMS layers are not clipped to the park

The CoCT WMS sources SHALL NOT declare a `coverage` block, so MapProxy serves
the full upstream extent of each layer instead of stopping at the park boundary.
The webmercator grid SHALL NOT declare a `bbox`, because the grid has to stay
global for one cache to serve every layer. The upstream extent is bounded where
it actually costs something instead: the seeding walk.

#### Scenario: No source clips the extent

- **WHEN** the MapProxy source configuration is inspected
- **THEN** `coct_aerial_wms`, `coct_hillshade_wms` and `coct_basemap_wms` have no
  `coverage` block

#### Scenario: The grid is not narrowed to a local extent

- **WHEN** the grid configuration is inspected
- **THEN** the `webmercator` grid declares no `bbox`

#### Scenario: Seeding is bounded by the land mask

- **WHEN** the seed configuration is inspected
- **THEN** every task carries a `coverages` entry, because the grid is global
- **AND** each cache's coarse task uses the land mask as its coverage, so the
  seeder walks land rather than the world or the open ocean

#### Scenario: The park is seeded finer than the land around it

- **WHEN** the seed configuration is inspected
- **THEN** each cache has a second task clipped to the park polygon, at deeper
  levels than the coarse task, and the two level ranges do not overlap

#### Scenario: Serving past the park is not an error

- **WHEN** a WMS `GetMap` request covers an area outside the park but inside the
  upstream layer's extent
- **THEN** the response contains real imagery, not a blank or an error

#### Scenario: Seeding does not limit serving

- **WHEN** seeding is limited to the park boundary and a request arrives outside
  it
- **THEN** MapProxy fetches the tile from the upstream and caches it on demand

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
