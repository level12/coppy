# Coppy

A [copier](https://copier.readthedocs.io/en/stable/) template to create a Python package.


## Host Prep

To run a project created by this template, you will also need [mise & uv installed](wiki/Mise).

To use Coppy, you will need:

```shell
# To generate a project: copier and the template extension library
uv tool install copier --with copier-templates-extensions

# To update a project to the latest Coppy version: the coppy cli utility
uv tool install --from https://github.com/level12/coppy coppy`

# Or, if wantin got use a local development version of Coppy
uv tool install --editable --from ~/projects/coppy-pkg coppy`
```

You can opt to use other methods to install `copier` and `coppy`.  Just make sure they are on the
`PATH` and up-to-date:

```shell
uv tool upgrade copier coppy
```


## Creating a Project

```shell
# Using the GH repo (recommended)
copier copy --trust gh:level12/coppy .../projects/some-new-pkg

# Or, from a local repo
copier copy --trust .../coppy-pkg .../projects/some-new-pkg

# If doing local development on coppy itself, the demo is the easiest way to generate a project
mise demo -- --help
```

The method you choose (local vs. GH) affects the `_src` value stored in the copier answers file and
will be used when updating the project.  Using a template stored on the local file system will save
a `_src` that probably won't be accurate for other users of `copier update`.

You can safely edit the `_src` value in a generated project's answers file to be the gh reference.
Just make sure the gh reference is accurate.

Once a project is generated, run the bootstrap task:

```shell
cd .../projects/some-new-pkg
mise bootstrap
```

## Upating a Project

To update a previously generated Coppy project to the latest version of Coppy, run:

* `coppy update`: for the latest tagged version in `_src` repo, OR
* `coppy upudate --head`: head of primary branch in `_src` repo

then review changes in git, modify changes if needed, and commit.

The update should be pretty safe and only apply changes from Coppy since the target repo was last
generated or updated from Coppy.  Any conflicts with local changes to the project will show up
as git conflicts to be resolved.

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
  - date based by default (`mise run bump --help`)
  - bumping automatically commits, tags, and (by default) pushes
- nox (tox alternative)
- pre-commit
- CircleCi config


## Development

* Project tasks: `mise tasks`
* Build a demo project to test functionality: `mise run demo [--help]`
* CI uses a custom image built just for this project
  - See `compose.yaml` and related
  - Use `mise docker-build` to rebuild manually if needed
* CI ran in GH actions, not CircleCI

### Versions & releases

Versions are date based.  Tools:

- Current version: `hatch version`
- Bump version based on date, tag, push: `mise bump`
   - Options: `mise bump -- --help`

There is no actual "release" for this project since it only lives on GitHub and no artifacts need to
be built.  But, the most recent tag is, by default, what is used by `copier update` and `uv tool
install`.
