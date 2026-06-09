Generated `ruff.toml` no longer pins `target-version`

Ruff now auto-derives its target from `pyproject.toml`'s `requires-python`, so edits to the
project's supported Python versions stay in sync with ruff without re-running copier.
`copier update` will strip the legacy `target-version = 'py3XX'` line from existing projects.
