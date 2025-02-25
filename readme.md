# Copier Python Package Template

A [copier](https://copier.readthedocs.io/en/stable/) template to create a Python package.


## Host Prep

To use this copier template, you will need copier & template extensions installed:

`uv tool install copier --with copier-templates-extensions`

To run a project created by this template, you will also need [mise & uv installed](wiki/Mise).


## Usage

From GH repo (preferred):
```
copier copy --trust gh:level12/copier-py-package .../projects/some-new-pkg
```

Or, from local repo (mainly for local dev):
```
copier copy --trust .../copier-py-package .../projects/some-new-pkg
```

The method you choose (local vs. GH) affects the `_src` value stored in the copier answers file and
will be used by `copier update`.  Using a template stored on the local file system will save a
`_src` that may not be accurate for other users of `copier update`.  You can safely edit the local
reference to be the gh reference even though that answers file warns against editing it. Just make
sure the gh reference is accurate.

Then run the bootstrap task:

```
cd .../projects/some-new-pkg
mise bootstrap
```

### Updates

To update a project from the `_src` repo in the copier answers file:

* `mise copier-update`: latest tagged version in `_src` repo, OR
* `mise copier-update --head`: head of master in `_src` repo

then review changes in git, modify changes if needed, and commit.

The update should be pretty safe and only apply changes from the upstream repo that have happened
since this project was last updated.  Any conflicts with local changes to the project will show up
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
  - Publish image changes to docker hub manually using: `mise run publish-ci-img`
* Simulate CI run locally: `mise run docker-nox`

### Versions & releases

Versions are date based.  Tools:

- Current version: `hatch version`
- Bump version based on date, tag, push: `mise run bump`
   - Options: `mise run bump -- --help`

There is no actual "release" for this project since it only lives on GitHub and no artifacts need
to be built.  But, the most recent tag is, by default, used by `copier update`.
