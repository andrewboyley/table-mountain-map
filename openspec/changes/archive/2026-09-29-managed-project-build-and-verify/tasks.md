# Managed Project Build and Verify

Implementation tasks. Prerequisite already landed on disk: MapProxy `utm34s`
cache grid + restart + cache clear, WMS verified non-white in `EPSG:32734`.

## 1. Commit the MapProxy grid fix

- [x] Commit `docker-mapproxy/mapproxy_configuration/mapproxy.yaml` (`emm`)
      as `fix(data): cache CoCT aerial on UTM 34S grid` with a README note.
- **Verify**: commit contains only mapproxy.yaml + note; `git status` shows
  `blender/tmnp.blend` and the qgz as expected.

## 2. Write the build script

- [x] `scripts/build_project.py`: enforcement build (load, enforce tree /
      categories / themes / CRS / relative paths / basemap sources, stamp 3D
      XML from the template with ids resolved by name, re-embed macro, write
      `qgis/table_mountain_3D.qgs`).
- [x] Extract the canonical 3D stamp template from the current project.
- **Verify**: two consecutive runs produce identical sha256; output opens in
  QGIS.

## 3. Switch storage to .qgs

- [x] Build writes `qgis/table_mountain_3D.qgs`; remove `table_mountain_3D.qgz`
      from the repo; update any paths/docs referencing the `.qgz`.
- **Verify**: fresh offscreen load of the `.qgs` shows the same layers,
  themes, layout; no `.qgz` in `git ls-files`.

## 4. Write the verification gate

- [x] `scripts/verify_project.py` with the assertions in design.md, exit 0/1.
- **Verify**: healthy project -> exit 0; breaking a check (e.g. missing 3D
  stamp) -> non-zero with a named failure.

## 5. Restore the aerial layer to WMS

- [x] Set the CoCT aerial layer source to the MapProxy WMS endpoint
      (`EPSG:32734`, layer `coct_aerial`) in the project; keep OSM on XYZ.
- **Verify**: WMS GetMap in 32734 non-white; QGIS canvas renders the aerial
  layer via WMS (screenshot); `verify_project.py` checks the source.

## 6. Wire pre-commit

- [x] Add `verify-project` local hook to `.pre-commit-config.yaml`
      (system interpreter, on `qgis/**` changes and pre-push).
- **Verify**: `pre-commit run --all-files` green (verify-data + others).

## 7. Update docs

- [x] README, `qgis/README`, relevant `docs/`: `.qgs` storage, single trail
      layer, build + verify commands, basemap service model (OSM XYZ, CoCT
      WMS 32734), attribution + restricted-imagery flags retained.
- **Verify**: doc prose matches `verify_project.py` assertions; no stale
  references to 172 layers / XYZ aerial remain in prose.

## 8. Commit

- [x] Commit `scripts/`, `.pre-commit-config.yaml`, project `.qgs`, docs.
- **Verify**: `python3 scripts/verify_data.py all` green; `git status` clean
  except `blender/tmnp.blend`.
