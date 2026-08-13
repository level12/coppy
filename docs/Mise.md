Mise is used for at least:

- Dev [tools]: Python, Node, Terraform, etc.
- Static [Environment variables](https://mise.jdx.dev/environments/)
- Python [venv activation] and creation using uv
    - See also [Mise: Python Cookbook]
- [Tasks]: scripts used to manage the project that, usually, need the project's tooling
  and/or environment setup to function correctly

[tools]: https://mise.jdx.dev/dev-tools/
[tasks]: https://mise.jdx.dev/tasks/
[venv activation]: (<https://mise.jdx.dev/lang/python.html#automatic-virtualenv-activation>)
[Mise: Python Cookbook]: https://mise.jdx.dev/mise-cookbook/python.html


## Host Prep

Coppy projects assume [mise] and [uv] are installed on a developer's host system

We **recommend** installing both mise and uv directly for your OS user account.

We **no longer recommend** installing uv through mise as uv should be available as a tool
without going through mise to get access.

[mise]: https://mise.jdx.dev/installing-mise.html
[uv]: https://docs.astral.sh/uv/getting-started/installation/


### Host Updates

Given the frequency of releases to mise and uv, we recommend updating them frequently. See
our [systemd folder](https://github.com/level12/coppy/tree/main/systemd) for service and
timer units that update these tools nightly.

```text
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

By default, uv creates the project environment at `.venv`.

[Centralized project environments](https://docs.astral.sh/uv/concepts/projects/layout/#centralized-project-environments)
can be enabled with an environment variable, e.g. in your user-level mise config,
typically `~/.config/mise/config.toml`:

```toml
[env]
UV_PREVIEW_FEATURES = "centralized-project-envs"
```

When enabled by a developer, uv stores the environment in its cache and maintains `.venv`
as a compatibility link for the project.


## Design Notes

1. Smooth integration between mise & uv is a high priority
1. Our repos will operate as [uv projects](https://docs.astral.sh/uv/concepts/projects/)
   including defining requirements in `pyproject.toml` and using `uv.lock`
1. Developers will manually run `uv sync` to update the, presumably mise activated, active
   virtualenv
