# OSM PBF inspection

Inspection date: 2026-09-25.

## File

- Path: `data/osm/south-africa-latest.osm.pbf`
- Size: 420,911,514 bytes
- Source: Geofabrik South Africa extract
- Replication timestamp: `2026-09-24T20:21:20Z`
- Source updates: <https://download.geofabrik.de/africa/south-africa-updates>
- Raw PBF header extent: longitude 14.373284 to 40.2702, latitude -48.464971 to -21.775433

The PBF must retain OpenStreetMap attribution in any published map, render, or derived product.

## DuckDB setup

- DuckDB: 1.5.5
- Spatial extension: loaded
- Community `osmium` extension: loaded
- Python support package: `pytz` 2026.4

Use `osmium_read()` explicitly. Loading both extensions and using a bare PBF replacement scan can select DuckDB Spatial's native OSM reader, which does not return the community extension's reconstructed geometry schema.

The `osmium_read()` schema contains `kind`, `type`, `id`, `tags`, `geometry`, OSM metadata fields, and relation member arrays. Its `kind` values are `node`, `line`, `area`, and `relation`.

## Counts

`osmium fileinfo -e` reports the raw PBF contents:

| Object | Count |
|---|---:|
| Nodes | 81,432,122 |
| Ways | 7,020,077 |
| Relations | 40,744 |

DuckDB's `osmium_read()` emits reconstructed rows rather than every raw node:

| Reconstructed kind | Rows |
|---|---:|
| area | 4,630,690 |
| line | 7,015,608 |
| node | 1,191,216 |
| relation | 19,254 |

The DuckDB type counts are 1,191,216 nodes, 11,624,808 ways, and 40,744 relations. Closed ways can be emitted as both a line and an area, and untagged nodes that are not needed to construct another geometry may not be emitted. Do not treat the DuckDB kind counts as raw PBF object counts.

## Cape Town features

| OSM object | Interpretation | Geometry summary | WGS84 centroid |
|---|---|---|---|
| Way `112264998` | Table Mountain cliff (`natural=cliff`) | LineString, 34 vertices | `POINT (18.40430439568989 -33.959012555210926)` |
| Node `282699448` | Table Mountain / Maclear's Beacon (`natural=peak`) | Point; `ele=1086` | `POINT (18.4255552 -33.966832)` |
| Node `7204435025` | NGI survey point; `ele=1087.6` | Point | `POINT (18.4255528 -33.9668304)` |
| Relation `338191` | Table Mountain National Park | MultiPolygon, 5,398 vertices | `POINT (18.406628125246158 -34.13768918926714)` |
| Way `26543847` | MCSA Table Mountain Hut | Closed way; line and polygon interpretations | `POINT (18.398550281284425 -33.97266585693516)` |
| Node `10106877818` | Table Mountain Aerial Cableway information point | Point | `POINT (18.4006449 -33.9461094)` |

The cliff way's WGS84 bounds are approximately longitude `18.4026934` to `18.407219` and latitude `-33.9612038` to `-33.9568938`. The national park relation's bounds are approximately longitude `18.30722` to `18.4979771` and latitude `-34.35834` to `-33.9117846`.

For metric project work, DuckDB Spatial can transform the WGS84 geometries to `EPSG:32734`:

```sql
SET geometry_always_xy = true;
SELECT ST_Transform(
    ST_Centroid(geometry)::GEOMETRY('EPSG:4326'),
    'EPSG:32734'
);
```

The cliff centroid becomes approximately `POINT (260146.98 6239352.45)`, and the national-park centroid becomes approximately `POINT (260864.37 6219538.79)` in `EPSG:32734`.

## Name collision

Node `1927594806` is also named `Table Mountain`, but it is a locality at longitude `30.6009535`, latitude `-29.6101133` in KwaZulu-Natal. It is not the Cape Mountain target. Use the Cape Town coordinates, the cliff way, the peak node, or the national-park relation instead.

## Table Mountain National Park clip

The clipped file is:

```text
data/osm/table-mountain-national-park.osm.pbf
```

It was extracted from the South Africa PBF with:

```bash
osmium extract \
  --bbox 18.30722,-34.35834,18.4979771,-33.9117846 \
  --strategy complete_ways \
  --set-bounds \
  --output data/osm/table-mountain-national-park.osm.pbf \
  data/osm/south-africa-latest.osm.pbf
```

The output is 8,100,239 bytes and contains 922,382 nodes, 123,917 ways, and 2,752 relations. Its header records the requested park extent. Because `complete_ways` preserves referenced geometries, the complete object data bounding box is wider than the header rectangle. The national park relation `338191`, the cliff way `112264998`, and Maclear's Beacon node `282699448` were verified in the extract with DuckDB.

This is a rectangular extent clip, not a polygon cut exactly along the national park boundary. Keep the relation geometry if the legal boundary is needed.

## GeoPackage export

The clipped PBF was converted with GDAL 3.13.3 `ogr2ogr` and the GDAL OSM driver to:

```text
data/vector/table-mountain-national-park.gpkg
```

The reproducible command is:

```bash
ogr2ogr \
  -f GPKG \
  -t_srs EPSG:32734 \
  -oo TAGS_FORMAT=JSON \
  data/vector/table-mountain-national-park.gpkg \
  data/osm/table-mountain-national-park.osm.pbf
```

The GeoPackage contains five layers. All layers use `EPSG:32734` (WGS 84 / UTM zone 34S), have the geometry column `geom`, and store the full remaining tag set in the JSON text field `other_tags`:

| Layer | Geometry | Features |
|---|---|---:|
| `points` | Point | 31,172 |
| `lines` | LineString | 55,815 |
| `multilinestrings` | MultiLineString | 184 |
| `multipolygons` | MultiPolygon | 65,946 |
| `other_relations` | GeometryCollection | 1,260 |

The total is 154,377 GDAL OSM-driver features. This is different from the earlier DuckDB reconstructed-row count because the GDAL OSM driver groups objects by geometry interpretation and does not emit every raw or reconstructed OSM row as a separate feature.

The national park relation `338191` is in `multipolygons`, the cliff way `112264998` is in `lines`, and Maclear's Beacon node `282699448` is in `points`. They were verified after the reprojection.

GDAL reported several non-closed-ring warnings while building polygon geometries. The default conversion accepted those rings, so review the affected areas before using the GeoPackage as a strict topological boundary. The source remains a rectangular `complete_ways` clip, so referenced complete ways can extend beyond the requested rectangle.

## Reproduction

The clip and the GeoPackage are rebuilt by `scripts/bootstrap.sh`, which is
idempotent. The park clip is pinned by SHA-256 and rebuilds byte-identically:

```text
8e8147222953741a0b379b77b0271a2b95fd98a51aa50c922d7baafcf3ca6f63  data/osm/table-mountain-national-park.osm.pbf
```

The GeoPackage is not checksum-pinned. GDAL writes a `last_change` timestamp
into `gpkg_contents` on every save, so its bytes differ on each build even when
the data is identical. Rebuilds are therefore checked semantically, by feature
count and by the area of relation 338191:

```text
multipolygons: 65946 features
relation 338191: 1 feature, 249913922.120323 m2 (249.91 km2)
```

Run `python3 scripts/verify_data.py` to confirm both.

To inspect the PBF directly:

```bash
uv pip install --python .venv/bin/python -r scripts/duckdb/requirements.txt
.venv/bin/python scripts/duckdb/inspect_pbf.py --name-like "Table Mountain"
```

The inspection script prints the schema, reconstructed kind/type counts, and concise geometry summaries for matching names.
