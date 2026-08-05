# ib-pyrelease-utils

THIS CODE IS NOT CURRENTLY FINISHED.

These are programs and utility functions to assist with creating consistent releases from a project's build tooling. Primarily they are aimed at Python projects, but should (eventually) be useful for other languages as well.

The release model is the familiar two-phase *prepare* then *perform* cycle: `prepare` tags the current version, bumps the repository to the next one, and records the result in `release.properties`; `perform` checks that tag out into an isolated directory, validates it by running the project's own `clean` and `build` targets, and publishes it.

## Features

### Console scripts

| Command | Purpose |
| --- | --- |
| `ib-prepare [next_version]` | Tag the current version and bump the repo to the next one. Defaults to a patch increment. |
| `ib-perform [checkout_path] [--build-tool TOOL]` | Check the release tag out, validate it, and publish to PyPI. |
| `ib-check-release <directory>` | Fail if a directory still has a `release.properties`, meaning a prepared release is pending. |

All three accept `--help`.

### Configurable build tool

`ib-perform` validates the isolated checkout by running `<tool> clean build` inside it. Any command exposing those two targets works — `just`, `make`, `task`, or a wrapper script.

Resolution order is **explicit argument → `$IB_BUILD_TOOL` → `just`**:

```bash
ib-perform --build-tool make          # explicit
IB_BUILD_TOOL=make ib-perform         # environment
just release-perform target/checkout make
```

### Environment

| Variable | Purpose |
| --- | --- |
| `UV_PUBLISH_TOKEN` | PyPI token used by `ib-perform`. Redacted from error output. |
| `UV_PUBLISH_INDEX` | Optional target index (e.g. `testpypi`). |
| `IB_BUILD_TOOL` | Build tool used inside the release checkout. |

## Development

This project is driven by [`just`](https://just.systems) and [`uv`](https://docs.astral.sh/uv/).
Run `just` to see every recipe.

```bash
just dev-install     # install dev dependencies
just check           # ruff + black + mypy
just test            # run the test suite
just test-cov        # run tests with coverage
just build           # lint, format, test, then build the package
```

## Library use

The release primitives are importable directly:

```python
from ib_pyrelease_utils import get_current_version, release_prepare, resolve_build_tool
```

## License

Apache-2.0
