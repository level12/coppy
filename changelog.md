# Changelog

**Unreleased** changes are documented in [changelog.d].

[changelog.d]: https://github.com/level12/coppy/tree/main/changelog.d

<!-- towncrier release notes start -->

## [1.20250622.1](https://github.com/level12/coppy/releases/tag/v1.20250622.1) - 2025-10-14

### Breaking

- Moderate: Adjust mise/uv Python bootstrap mechanism and change install recommendations in docs.
    - If using centralized venvs, ensure `~/.cache/uv-venvs/` exists.  Project venvs will now be
      configured in that location.
    - The new init method which uses a custom task in the project and adjusted `mise.toml` config
      should "just work".  It's tested, but it's also new, so YMMV.
    - Docs: we now recommend installing uv directly as the OS user and not through Mise.
    - Remove `UV_PROJECT_ENVIRONMENT` from `~/.config/mise/config.toml` which will be a breaking
      change for existing projects not updated to at least this version of the Coppy template.

      For existing projects that aren't ready to be updated, you should add the
      `UV_PROJECT_ENVIRONMENT` definition to a project specific `mise.local.toml` file:

        ```toml
        [env]
        UV_PROJECT_ENVIRONMENT = '{% if env.PROJECT_SLUG %}~/.cache/uv-venvs/{{ env.PROJECT_SLUG }}{% endif %}'
        ```

        When the project updates to at least this version of the Coppy template, that definition
        should be removed. ([#56](https://github.com/level12/coppy/issues/56))
- Moderate: move project's tests from `./src` to `./tests`
    - Advantages: test directory is top-level and more obvious, provides more flexibility if wanting
      to test a generated wheel and not the code in `./src`.  See related issue for example.
    - Actions **required**: move `conftest.py` and your tests from `./src/` to `./tests` ([#75](https://github.com/level12/coppy/issues/75))
- Minor: `env-config.yaml` changed HATCH_INDEX_AUTH 1password secret reference

  - From: 'op://my/private/pypi.python.org/api-token'
  - To: 'op://my/private/pypi.org/api-token'

  ([#78](https://github.com/level12/coppy/issues/78))
- Minor: change python dependency group and nox session name from "tests" to pytest.  Also, enhance
  noxfile with improved `uv_sync()` and `pytest_run()`.
      - "tests" -> "pytest" dependency group: mostly for clarity.  While technically breaking, most
        projects won't need to manually change anything unless they've customized that group already.
      - The functions serve as a foundation for more complicated setups with multiple pytest runs,
        potentially using different environment variables, and paramiterization.  Example of such
        usage in Webgrid's [`noxfile.py`](https://github.com/level12/webgrid/blob/master/noxfile.py). ([#82](https://github.com/level12/coppy/issues/82))

### Changed

- `.editorconfig`: move `charset = utf-8` to global as it seems like a sensible modern default. ([#68](https://github.com/level12/coppy/issues/68))
- Remove "From Coppy" and "App Specific" from pyproject.toml dependency groups.  They didn't stay
  organized with `uv add` and aren't likely to be necessary. ([#72](https://github.com/level12/coppy/issues/72))
- Use uv's `--frozen` in CI and testing scenarios to help ensure dependency updates are handled
  explicitly by the developer. ([#74](https://github.com/level12/coppy/issues/74))
- Nox pytest command should not specify the module to cover.  Since we specify the paths in
  `.coveragerc`, the pytest option should be just `--cov`, not e.g. `--cov=webgrid`. ([#76](https://github.com/level12/coppy/issues/76))
- nox uv now uses `--only-group` instead of `--no-dev` since the intention behind our usage
  is to only install the group the nox session needs.  `--only-group` is more appropriate
  since it's possible that the dev group is not the default group.  Also DRY refactor uv calls in nox. ([#77](https://github.com/level12/coppy/issues/77))
- Noxfile and nox GH action updates
    - Use uv's --exact and --frozen to help ensure environments contain only expected packages
    - noxfile: enhance pytest() and uv_sync() functions
    - pytest: only include junit xml for CircleCI
    - pytest: remove `--cov-config=.coveragerc` because it's the default
    - GitHub action: use separate jobs and a matrix to parallelize the runs
    - GitHub action: use Coppy's GH actions to DRY the config; drop dependency on ubuntu-mive
    - GitHub action: add codecov integration ([#82](https://github.com/level12/coppy/issues/82))
- - Change mise task comment headers ([discussion](https://github.com/jdx/mise/discussions/6139)) ([#83](https://github.com/level12/coppy/issues/83))
- Update pre-commit versions
