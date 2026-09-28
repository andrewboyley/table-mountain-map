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

## Changes

Work is planned as OpenSpec changes under `openspec/changes/`. A change is
proposed, specified and designed before it is applied, and tasks are tracked in
its `tasks.md`.
