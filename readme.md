# Coppy
[![Nox](https://github.com/level12/coppy/actions/workflows/nox.yaml/badge.svg)](https://github.com/level12/coppy/actions/workflows/nox.yaml)
[![Docs <-> Wiki](https://github.com/level12/coppy/actions/workflows/docs.yaml/badge.svg)](https://github.com/level12/coppy/actions/workflows/docs.yaml)


A [copier](https://copier.readthedocs.io/en/stable/) template to create a Python package.

**Getting Started** & other docs are in the [GH Wiki](https://github.com/level12/coppy/wiki).


## Template Updates

[Copier], the project Coppy is built on, enables code lifecycle management for generated projects.
That means, it's much easier to keep your project [in-sync with the upstream template] even when you
have made changes to the template files post-generation.

Before [updating] your Coppy based project, check the [Changelog] for breaking changes.  We'll do our
best to keep them relatively minor and provide clear instructions when manual invervention is
needed.

[Copier]: https://copier.readthedocs.io
[in-sync with the upstream template]: https://copier.readthedocs.io/en/stable/updating/
[updating]: https://github.com/level12/coppy/wiki#updating-a-project
[Changelog]: https://github.com/level12/coppy/blob/main/changelog.md


## Features

- `pyproject.toml` package config
    - [Hatch](https://hatch.pypa.io/latest/) build backend
    - [uv project](https://docs.astral.sh/uv/guides/projects/) for dependencies, etc.
- [Ruff](https://docs.astral.sh/ruff/) linting & formatting
  - Enforce single quotes
  - Sane(ish) linting rules including safe fixes
- [mise](https://mise.jdx.dev/)
    - Manage [Python version](https://mise.jdx.dev/lang/python.html)
    - Local dev [virtualenv activation](https://mise.jdx.dev/lang/python.html#automatic-virtualenv-activation)
    - Static [environment variables](https://mise.jdx.dev/environments.html)
    - Other [tools](https://mise.jdx.dev/dev-tools/) when needed (e.g. npm, Terraform)
    - Project [tasks](https://mise.jdx.dev/tasks/)
- Versioning
  - Date based by default (`mise bump --help`)
  - Bumping automatically commits, tags, and (by default) pushes
- Testing
  - Nox (tox alternative) test runner
  - [`pytest`](https://docs.pytest.org/en/stable/) with [integrated](https://pypi.org/project/pytest-cov/) code [coverage](https://coverage.readthedocs.io/)
- pre-commit & [pre-commit-uv](https://github.com/tox-dev/pre-commit-uv) for speed
- CI: GitHub Actions & CircleCi integration using nox
