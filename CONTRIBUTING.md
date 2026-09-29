# Contributing

## Commit messages

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
specification, version 1.0.0.

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Use for |
|---|---|
| `feat` | A new capability a user can observe |
| `fix` | A correction of existing behaviour |
| `perf` | A change made for performance, not behaviour |
| `docs` | Documentation only |
| `refactor` | Restructuring with no behaviour change |
| `build` | Build system, packaging, dependencies |
| `chore` | Maintenance that fits nothing else |
| `ci` | Continuous integration configuration |
| `test` | Adding or correcting tests |
| `revert` | Reverting a prior commit |

A `!` before the `:` marks a breaking change, and the body **must** state the
migration path.

### Rules

- The description is imperative mood, lowercase, no trailing period:
  `fix: correct crop extent derivation`, not `Fixed the crop extent`.
- One logical change per commit. A commit that touches layers, rasters and docs
  for unrelated reasons should be three commits.
- Reference issues or changes in the footer, e.g. `Refs: openspec/changes/qgis-project-hardening`.
- Binary data is never added in a commit that also changes source. Data
  updates and code changes are separate commits.

### What this repository considers committable

Per `.gitignore`, the tracked tree is the *reproducible definition* of the
project: documentation, scripts, the QGIS project, READMEs, and the small
boundary layers the project references. Large geospatial binaries are
regenerable and stay out of history.

The exception, and it is deliberate: `blender/*.blend` **is** tracked while
`scripts/blender/` does not exist, because those scenes are not currently
reproducible from this repository. If a scene build script is added, the
ignore rule should be added at that point.

## Local hooks

Install [pre-commit](https://pre-commit.com/), then install this repository's
commit and push hooks:

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

The commit hooks check:

- added files stay under the 5120 KB large-file threshold
  (`check-added-large-files`), which is why the largest tracked binary,
  `data/vector/tiles_grid.gpkg` at 4.4 MB, stays in history;
- Python AST validity (`check-ast`) and formatting plus linting with
  [ruff](https://docs.astral.sh/ruff/) (`ruff-format` then `ruff`) across
  `scripts/`;
- structured files, merge-conflict markers, line endings, end-of-file
  newlines, and trailing whitespace;
- the QGIS project artifact (`verify-project` — loads headlessly and checks
  the invariants documented in `qgis/README.md`);
- the `qgis/processing/trail_rebuild.model3` Processing model
  (`validate-processing-model` — runs
  `QT_QPA_PLATFORM=offscreen qgis_process help qgis/processing/trail_rebuild.model3`
  as a headless model validation).

The push hooks run the complete data verifier:

```bash
python3 scripts/verify_data.py all
```

It uses the GDAL-enabled `/usr/bin/python3` supplied by the QGIS installation
and needs the local geospatial inputs documented in `data/README.md`, so it is
intentionally a pre-push hook rather than a requirement for every commit. Run
the complete configured set manually with:

```bash
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

### Maintaining the hook configuration

- `pre-commit autoupdate` — bump the pinned hook revisions to their latest
  tags. Review the resulting `.pre-commit-config.yaml` diff before committing.
- `pre-commit migrate-config` — migrate the config to the current pre-commit
  schema (e.g. when upgrading from an older pre-commit major version).
- `pre-commit validate-config` — parse and validate the config without
  running hooks.

## Changes

Work is planned as OpenSpec changes under `openspec/changes/`. A change is
proposed, specified and designed before it is applied, and tasks are tracked in
its `tasks.md`.
