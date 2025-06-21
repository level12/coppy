# Coppy Development

* Project tasks: `mise tasks`
* Build a demo project to test functionality: `mise demo [--help]`
* CI uses a custom image built just for this project
  - See `compose.yaml` and related
  - Use `mise docker-build` to rebuild manually if needed
* CI runs in GH actions, not CircleCI

## Coppy Demo Repo

* We have a demo of the default output at: https://github.com/level12/coppy-demo
* Devs should update this after bumping Coppy to a new version
  * Which should [get automated](https://github.com/level12/coppy/issues/54) at some point

## Test Run Times

- Test runs are longer than our typical projects.
- As of Feb 2025, 12 tests take 65s on my (RLS) laptop
- **Hung?**: The first run of a day can take minutes before the first test runs due to docker
  building the newest [ubuntu-mive](https://github.com/level12/ubuntu-mive) image. Watch the
  progress with `pytest -s` if you are concerned it is hung.
- See also: https://github.com/level12/coppy/issues/53

## Versions & releases

Versions are date based. Tools:

- Current version: `hatch version`
- Bump version based on date, tag, push: `mise bump`
   - Options: `mise bump -- --help`

There is no actual "release" for this project since it only lives on GitHub and no artifacts need to
be published. But, the most recent tag is, by default, what is used by `copier update` and `uv tool
install`.
