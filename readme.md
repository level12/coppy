# Copier Python Package Template

A [copier](https://copier.readthedocs.io/en/stable/) template to create a Python package.

## Usage

```
# From GH repo
copier copy --trust gh:level12/copier-py-package .../projects/some-new-pkg

# OR from local repo*
copier copy --trust .../copier-py-package .../projects/some-new-pkg

# Then bootstrap...assuming mise activates when changing into pkg directory
cd .../projects/some-new-pkg
mise run bootstrap
```

*NOTE: the method you choose (local vs. GH) affects the `_src` value stored in the copier answers
file and will be used by `copier update`.  Using a template stored on the local file system will
save a `_src` that may not be accurate for other users of `copier update`.

## Features

- pyproject.toml package config
    - [Hatch](https://hatch.pypa.io/latest/) build backend w/ [support for requirements files](https://github.com/repo-helper/hatch-requirements-txt)
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
  - date based by default (`mise run bump --help`)
  - bumping automatically commits, tags, and (by default) pushes
- [reqs](https://github.com/level12/reqs) for Python dependencies
- nox (tox alternative)
- pre-commit
- CircleCi config

Todo:

- env-config for environment profiles and 1password integration
- pre-commit
- badges
- review keg-app-cookiecutter


## System Dependencies

To use a project generated by this template, you will need to have the following tools installed and
available on the path:

- copier
  - with copier-templates-extensions (`pipx inject copier copier-templates-extensions`)
- mise
- [reqs](https://github.com/level12/reqs)

## Why ...?

TODO
