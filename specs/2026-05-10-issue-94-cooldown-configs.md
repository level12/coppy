# Spec: Issue 94 Cooldown Configs


## Summary

- Add project-local cooldown config files for package managers that support them.
- Apply JS package-manager configs in the copier template so generated projects inherit
  them.
- Keep coppy itself limited to project-local `uv.toml`.
- Use only repo-local config files; do not write user- or system-level config.


## Scope

- Repo root `uv.toml`.
- Template root config files.
- Minimal test coverage for the new files.
- Changelog entry for the generated-project behavior change.


## Findings

- The current template is Python-focused, but Coppy docs already treat Node tooling as
  reasonable in these projects.
- The following tools support a repo-local config file for a cooldown / age gate:
    - npm: project `.npmrc` with `min-release-age`
    - pnpm: project `pnpm-workspace.yaml` with `minimumReleaseAge`
    - Bun: project `bunfig.toml` with `install.minimumReleaseAge`
    - Yarn: project `.yarnrc.yml` with `npmMinimalAgeGate`
    - uv: project `uv.toml` with `exclude-newer`
- uv local config applies to project commands, but not `uv tool` commands.
- Coppy itself does not need the JS package-manager cooldown files at repo root.
- pnpm's current docs put `minimumReleaseAge` in `pnpm-workspace.yaml`; `.npmrc` is
  documented as auth/registry-only for pnpm v11.


## Decisions

- Use a 3-day default across tools, expressed in each tool's native units.
- Keep JS package-manager configs only in `template/`.
- Generate JS package-manager configs by default, with a Copier option for projects that
  have no JavaScript build to omit all four files.
- Keep `template/pnpm-workspace.yaml`; it is the documented project-local pnpm config
  surface for `minimumReleaseAge`.
- Keep `uv.toml` in both the repo root and `template/`.
- Do not add package allowlists/exclusions in this pass.


## Open Questions

- Should we later add trusted-package allowlists for fast-moving internal dependencies?


## Validation Outcomes

- Full `ruff format` / `ruff check` sequence passed.
- All nine `TestTemplateGen` tests passed.
- Generation coverage confirms the default includes all cooldown configs and opting out
  omits the four JavaScript package-manager files while retaining `uv.toml`.
