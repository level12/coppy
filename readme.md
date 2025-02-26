# Coppy

A [copier](https://copier.readthedocs.io/en/stable/) template to create a Python package.

**Getting Started** & other docs are in the [GH Wiki](https://github.com/level12/coppy/wiki).

## Features

- pyproject.toml package config
    - [Hatch](https://hatch.pypa.io/latest/) build backend
    - [uv project](https://docs.astral.sh/uv/guides/projects/) for dependencies, etc.
- [Ruff](https://docs.astral.sh/ruff/) linting & formatting
  - Enforce single quotes
  - Sane(ish) linting rules including safe fixes
- [mise](https://mise.jdx.dev/)
    - Manage [Python version](https://mise.jdx.dev/lang/python.html) and local dev
      [virtualenv activation](https://mise.jdx.dev/lang/python.html#automatic-virtualenv-activation)
    - Static [environment variables](https://mise.jdx.dev/environments.html)
    - Other tools when needed (e.g. npm, Terraform)
    - Project [tasks](https://mise.jdx.dev/tasks/)
- Versioning
  - date based by default (`mise bump --help`)
  - bumping automatically commits, tags, and (by default) pushes
- nox (tox alternative) test runner
- pre-commit & [pre-commit-uv](https://github.com/tox-dev/pre-commit-uv)
- CircleCi config
