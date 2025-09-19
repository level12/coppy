# Coppy Development

* Project tasks: `mise tasks`
* Build a demo project to test functionality: `mise demo [--help]`
* CI runs in GH Actions


## OS Test User Required

Tests use a dedicated system user to run tests isolated from the developer's mise/uv config.

- Create/prep user: `mise run test-user-prep [--systemd-skip]`
- Systemd:
  - Without `--systemd-skip` a service and timer will be installed to keep mise and uv current
  - Diagnostic help with tasks: `test-user-systemctl` and `test-user-journalctl`
- Current task is Ubuntu centric.  Fix & submit a PR for other systems if needed.


## Coppy Demo Repo

* We have a demo of the default output at: https://github.com/level12/coppy-demo
* Devs should update this after bumping Coppy to a new version
  * Which should [get automated](https://github.com/level12/coppy/issues/54) at some point


## Versions & releases

Versions are date based. Tools:

- Current version: `hatch version`
- Bump version based on date, tag, push: `mise bump`
   - Options: `mise bump -- --help`

There is no actual "release" for this project since it only lives on GitHub and no artifacts need to
be published. But, the most recent tag is, by default, what is used by `copier update` and `uv tool
install`.
