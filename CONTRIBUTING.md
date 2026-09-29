# Contributing

## Commit messages

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification, version 1.0.0.

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

A `!` before the `:` marks a breaking change. The body must state the migration path.

### Rules

- The description is imperative mood, lowercase, and has no trailing period: `fix: correct crop extent derivation`, not `Fixed the crop extent`.
- Make one logical change per commit. A commit that touches layers, rasters, and docs for unrelated reasons must be three commits.
- Reference issues or changes in the footer. For example: `Refs: openspec/changes/qgis-project-hardening`.
- Never add binary data to a commit that also changes source. Data updates and code changes are separate commits.

### What this repository considers committable

Per `.gitignore`, the tracked tree is the reproducible definition of the project. It holds documentation, scripts, the QGIS project, READMEs, and the small boundary layers the project references. Large geospatial binaries are regenerable and stay out of history.

`blender/*.blend` is the deliberate exception. Those scenes are tracked while `scripts/blender/` does not exist, because they are not currently reproducible from this repository. If a scene build script is added, ignore the blends at that point.

## Hooks

Install [pre-commit](https://pre-commit.com/), then install this repository's commit and push hooks:

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

`pre-commit install` installs both hook stages. The config declares them with `default_install_hook_types: [pre-commit, pre-push]`.

### The commit hooks

- added files stay under the 5120 KB large-file threshold (`check-added-large-files`), which is why the largest tracked binary, `data/vector/tiles_grid.gpkg` at 4.4 MB, stays in history.
- Python files parse (`check-ast`) and pass formatting and linting with [ruff](https://docs.astral.sh/ruff/) (`ruff-format` then `ruff`) across `scripts/`.
- JSON and YAML files parse (`check-json`, `check-yaml`).
- no changed file carries a private key (`detect-private-key`).
- no merge-conflict markers remain, and line endings, end-of-file newlines, and trailing whitespace are consistent.
- the QGIS project artifact (`verify-project`) loads headlessly and keeps the invariants documented in `qgis/README.md`.
- the `qgis/processing/trail_rebuild.model3` Processing model validates headlessly (`validate-processing-model`, via `QT_QPA_PLATFORM=offscreen qgis_process help qgis/processing/trail_rebuild.model3`).

### The push hooks

The push hooks run the complete data verifier:

```bash
just verify-data
```

It uses the GDAL-enabled `/usr/bin/python3` supplied by the QGIS installation and needs the local geospatial inputs documented in `data/README.md`. That is why it is a pre-push hook, not a requirement for every commit. Run the complete configured set manually with:

```bash
just check
just check-push
```

You can run the same gates with `just`. `just check` runs every pre-commit hook on all files. `just verify` runs `verify-data`, `verify-project`, and `verify-dem` in order, building the contour-DEM intermediates first. Bare `just` runs `build` then `verify`. Every project command routes through the `justfile`.

### Working with pre-commit

- Run one hook: `pre-commit run <hook-id>`.
- Run on specific files: `pre-commit run --files <path>`.
- Run on the files changed between two refs: `pre-commit run --from-ref <ref> --to-ref <ref>`. Use this in CI or before a merge.
- Run `pre-commit run --show-diff-on-failure` after a failed fixer hook. The hook prints the diff it wants to apply. If `ruff-format` or `end-of-file-fixer` fails, use this flag to see the intended change.
- Bypass hooks for one run: `SKIP=hook-id1,hook-id2 pre-commit run`. Use this only for a documented reason.
- Test a hook before adopting it: `pre-commit try-repo <repo> <hook-id> [--all-files]`. This runs the hook from a remote or local repository without changing `.pre-commit-config.yaml`. Use it to evaluate a candidate hook.

### Maintaining the hook configuration

- `pre-commit autoupdate`: bump the pinned hook revisions to their latest tags. Review the resulting `.pre-commit-config.yaml` diff before committing.
- `pre-commit migrate-config`: migrate the config to the current pre-commit schema, for example when upgrading from an older pre-commit major version.
- `pre-commit validate-config`: parse and validate the config without running hooks.
- `pre-commit clean`: remove every cached hook environment. They re-install on the next run.
- `pre-commit gc`: remove unused cached hook repositories.
- `pre-commit sample-config`: print an example config.

### Considered and not adopted

- `no-commit-to-branch`: this project commits directly to `main`. The hook blocks the normal flow.
- `check-toml`: the repository has no TOML files today.
- `debug-statements`: ruff already lints `scripts/`.
- `check-xml`: `verify-project` loads the `.qgs` project in QGIS, which is a stronger gate than XML parsing.
- Full secret scanners such as gitleaks or detect-secrets: no secrets are tracked. `detect-private-key` covers accidental key commits today.
- A commit-msg hook that enforces Conventional Commits: the convention is documented but not yet enforced by a hook. Adopt one if you want it enforced.
- `fail_fast`: you want the full gate result, not the first failure.

## Changes

Work is planned as OpenSpec changes under `openspec/changes/`. A change is proposed, specified, and designed before it is applied. Tasks are tracked in its `tasks.md`.
