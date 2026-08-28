- Project tasks: `mise tasks`
- Build a demo project to test functionality: `mise run demo-gen [-- --help]`
- CI runs in GH Actions


## OS Test User Required

Tests use a dedicated system user to run tests isolated from the developer's mise/uv
config.

- Create/prep user: `mise run test-user-prep [--systemd-skip]`
- Systemd:
    - Without `--systemd-skip` a service and timer will be installed to keep mise and uv
      current
    - Diagnostic help with tasks: `test-user-systemctl` and `test-user-journalctl`
- Current task is Ubuntu centric. Fix & submit a PR for other systems if needed.


## Coppy Demo Repo

- We have a demo of the default output at: <https://github.com/level12/coppy-demo>
- Devs should update this after bumping Coppy to a new version
    - Which should [get automated](https://github.com/level12/coppy/issues/54) at some
      point


## Versions

Versions are date based. The latest tag is used by `copier update` and `uv tool install`.


## Release checklist

- Push `main`, confirm CI is passing
- `mise run version -- bump` to commit, sign, tag, and push
    - Bumping first since `changelog` task uses the current version
- `mise run changelog`
    - `rumdl fmt docs/Changelog.md`
    - Review, commit and push the changelog
- `mise run demo-update` to update [coppy-demo](https://github.com/level12/coppy-demo)
  locally
    - commit & push that repo
