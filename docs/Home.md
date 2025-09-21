# Documentation

All our docs are here in the GH wiki. See the nav `-->` for additional documentation.

# Getting Started

## Host Prep

To run a project created with Coppy, you will need [mise & uv installed](wiki/Mise).

To use Coppy itself, you will need:

```shell
# To generate a project: copier and the template extension library
uv tool install copier --with copier-templates-extensions

# To update a project to the latest Coppy version: the coppy cli utility
uv tool install --from https://github.com/level12/coppy coppy

# Or, if wanting to use a local development version of Coppy
uv tool install --editable --from ~/projects/coppy-pkg coppy
```

You can opt to use other methods to install `copier` and `coppy`. Just make sure they are on the
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
will be used when updating the project. Using a template stored on the local file system will save
a `_src` that probably won't be accurate for other users of `copier update`.

You can safely edit the `_src` value in a generated project's answers file to be the gh reference.
Just make sure the gh reference is accurate.

Once a project is generated, run the bootstrap task:

```shell
cd .../projects/some-new-pkg
mise bootstrap
```


## Updating a Project

Before updating, check the [Changelog] for breaking changes!  We'll do our best to keep them
relatively minor and provide clear instructions when manual invervention is needed.

To update a previously generated Coppy project to the latest version of Coppy, run:

* `coppy update`: for the latest tagged version in `_src` repo, OR
* `coppy update --head`: head of primary branch in `_src` repo

then review changes in git, modify changes if needed, and commit.

The update should be pretty safe and only apply changes from Coppy since the target repo was last
generated or updated from Coppy. Any conflicts with local changes to the project will show up
as git conflicts to be resolved.

[Changelog]: https://github.com/level12/coppy/blob/main/changelog.md
