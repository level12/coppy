Make generated `ruff.toml` track `python_version_min` for `target-version`

Ruff can use syntax which would break in earlier Python versions so we need to track the min version
not the primary dev version.
