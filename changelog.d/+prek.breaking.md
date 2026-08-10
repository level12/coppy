Use `prek` instead of `pre-commit`.

Coppy now requires Copier 9.5+.

Upgrade path for existing projects:

- Run `coppy update` like normal.
- Coppy's migrations will
    - Convert your `.pre-commit-config.yaml` into `prek.toml`.
    - Replace an existing Git `pre-commit` hook with a `prek` hook

If the conversion step fails, `coppy update` aborts immediately. Restore a clean working
tree, fix the hook config, and rerun the update.

**Manual Updates**:

- update any custom CI/scripts/docs that still run `nox -s precommit`; the session is now
  `nox -s prek`
- replace any direct use of the old Python `pre-commit` API (for example
  `pre_commit.main`)
