Mise is used for at least:

- Dev [tools]: Python, Node, Terraform, etc.
- Static [Environment variables](https://mise.jdx.dev/environments/)
- Python [venv activation] and creation using uv
  - See also [Mise: Python Cookbook]
- [Tasks]: scripts used to manage the project that, usually, need the project's tooling and/or environment setup to function correctly


[uv]: https://docs.astral.sh/uv/
[mise]: https://mise.jdx.dev/
[tools]: https://mise.jdx.dev/dev-tools/
[tasks]: https://mise.jdx.dev/tasks/
[venv activation]: (https://mise.jdx.dev/lang/python.html#automatic-virtualenv-activation)
[Mise: Python Cookbook]: https://mise.jdx.dev/mise-cookbook/python.html


## Host Prep

Coppy projects assume [mise] and [uv] are installed on a developer's host system

We **recommend** installing both mise and uv directly for your OS user account.

We **no longer recommend** installing uv through mise as uv should be available as a tool without
going through mise to get access.

[mise]: https://mise.jdx.dev/installing-mise.html
[uv]: https://docs.astral.sh/uv/getting-started/installation/


### Host Updates

Given the frequency of releases to mise and uv, we recommend updating them frequently.  See our
[systemd folder](https://github.com/level12/coppy/tree/main/systemd) for service and timer units
that update these tools nightly.

```
# mise

 ❯ mise self-update
 ❯ mise up
 ❯ mise reshim

# Keep mise & uv Pythons in-sync with:

 ❯ mise sync python --uv

# uv

 ❯ uv self update
 ❯ uv tool upgrade --all
```


## Virtualenv Location

By default, the project's venv will be located in the project directory at `.venv`.

You can use centralized virtualenvs by ensuring a cache directory exists: `~/.cache/uv-venvs/`.
E.g.:

```
mkdir ~/.cache/uv-venvs/
```

Mise tasks can use a [uv shebang](https://mise.jdx.dev/mise-cookbook/python.html#uv-scripts) so they
can function without mise being active.  But:

- This won't work if using centralized virtualenvs b/c UV_PROJECT_ENVIRONMENT is activated by
  mise.  So when the script runs, it will want to use `.venv`.
- A workaround, until uv gets [support for centralized
  venvs](https://github.com/astral-sh/uv/issues/1495#issuecomment-3073898354), is to symlink
  `.venv` to the central one.


## Design Notes

1. Smooth integration between mise & uv is a high priority
1. Our repos will operate as [uv projects](https://docs.astral.sh/uv/concepts/projects/) including
   defining requirements in `pyproject.toml` and using `uv.lock`
1. Developers will manually run `uv sync` to update the, presumably mise activated, active
   virtualenv
