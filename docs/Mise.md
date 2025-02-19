# Mise (& uv)

Mise is used for at least:

- Dev [tools]: Python, Node, Terraform, etc.
- Static [Environment variables](https://mise.jdx.dev/environments/)
- Python [venv activation] and creation using uv
  - See also [Python Cookbook]
- Task [tasks]: scripts used to manage the project that, usually, need the project's tooling and/or environment setup to function correctly


[uv]: https://docs.astral.sh/uv/
[mise]: https://mise.jdx.dev/
[tools]: https://mise.jdx.dev/dev-tools/
[tasks]: https://mise.jdx.dev/tasks/
[venv activation]: (https://mise.jdx.dev/lang/python.html#automatic-virtualenv-activation)
[Python Cookbook]: https://mise.jdx.dev/mise-cookbook/python.html

## Host Prep

CPyP projects assume [mise] and [uv] are installed on a developer's host system.

For mise, see: https://mise.jdx.dev/installing-mise.html

Once mise is installed, the uv install can be managed with mise:

```
 ❯ mise use -g ubi:astral-sh/uv
mise Installed executable into ~/.local/share/mise/installs/ubi-astral-sh-uv/0.6.0/uv
mise ubi:astral-sh/uv@0.6.0 ✓ installed
mise ~/.config/mise/config.toml tools: ubi:astral-sh/uv@0.6.0

 ❯ which uv
~/.local/share/mise/installs/ubi-astral-sh-uv/0.6.0/uv
```

### Host Updates

All dev tooling, including anything installed with uv, can be updated with:

```
 ❯ mise self-update
 ❯ mise up
 ❯ uv tool upgrade --all
```


Keep mise & uv Python's in-sync with:

```
 ❯ mise sync python --uv
```

### Nightly Updates

See [systemd](https://github.com/level12/copier-py-package/tree/main/systemd) for units to run nightly updates.


## Virtualenv Location

By default, the project's venv will be located in the project directory at `.venv`.

To set a different location, define `UV_PROJECT_ENVIRONMENT` as a mise env var:

```toml
# Put this in a config that is used by all your projects, e.g. ~/.config/mise/config.toml or ~/mise.toml
[env]
UV_PROJECT_ENVIRONMENT = { value='{% if env.PROJECT_SLUG %}~/.cache/uv-venvs/{{ env.PROJECT_SLUG }}{% endif %}', tools = true }
```

### `uv_venv_auto`

We can use `uv_venv_auto` when mise respects `UV_PROJECT_ENVIRONMENT`.  Tracking in [#26](https://github.com/level12/copier-py-package/issues/26).


## Design Notes

1. Smooth integration between mise & uv is a high priority
1. Our repos will operate as [uv projects](https://docs.astral.sh/uv/concepts/projects/) including defining requirements in `pyproject.toml` and using `uv.lock`
1. Use `.python-version` so [mise](https://mise.jdx.dev/configuration.html#idiomatic-version-files) & [uv](https://docs.astral.sh/uv/concepts/python-versions/#python-version-files) share the version spec file
1. Developers will manually run `uv sync` to update the active virtualenv (but see [#27](https://github.com/level12/copier-py-package/issues/27))
1. Python tasks should use a [uv shebang](https://mise.jdx.dev/mise-cookbook/python.html#uv-scripts) so they can function without mise being active.
