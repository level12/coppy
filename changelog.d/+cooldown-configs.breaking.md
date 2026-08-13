- Add project-local npm, pnpm, Bun, Yarn, and uv cooldown config files with a 3-day
  default for generated projects. Projects without a JavaScript build can opt out of the
  JavaScript package-manager configs.

The uv cooldown requires uv 0.9.17 or newer. Before updating an existing project, upgrade
Coppy itself with `uv tool upgrade coppy`. The updated `coppy update` checks the installed
uv version and stops with upgrade instructions when it is too old.
