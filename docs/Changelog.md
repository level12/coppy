**Unreleased** changes are documented in [changelog.d].

[changelog.d]: https://github.com/level12/coppy/tree/main/changelog.d

<!-- towncrier release notes start -->

## [1.20260812.2](https://github.com/level12/coppy/releases/tag/v1.20260812.2)


### Changed

- Switch the rumdl prek hook to check Markdown without formatting it.


## [1.20260812.1](https://github.com/level12/coppy/releases/tag/v1.20260812.1)


### Breaking

- Add project-local npm, pnpm, Bun, Yarn, and uv cooldown config files with a 3-day
  default for generated projects. Projects without a JavaScript build can opt out of the
  JavaScript package-manager configs.

  The uv cooldown requires uv 0.9.17 or newer. Before updating an existing project,
  upgrade Coppy itself with `uv tool upgrade coppy`. The updated `coppy update` checks the
  installed uv version and stops with upgrade instructions when it is too old.
- Add a `pytest.ini` to generated project roots and move pytest warning configuration
  there from `tests/conftest.py` so the filters apply during every pytest lifecycle phase,
  including configuration and collection
  ([#96](https://github.com/level12/coppy/issues/96)).

  This makes the intended warnings-as-errors policy effective. After updating, warnings
  that previously appeared only in pytest's warning summary may fail the test run.

  **Manual update required:** migrate any project-specific `warnings.filterwarnings()`
  calls from `tests/conftest.py` to `pytest.ini`'s `filterwarnings` list. Put the general
  `error` rule first and more specific `ignore` rules afterward because the last matching
  rule takes precedence.
- Get rid of dependency on hatch cli and related

  This is a breaking change if a project:

    - Uses Hatch environments or other Hatch CLI functionality
    - Customizes the old `bump` task or has built automations on it
    - Depends on a "v" prefix in the version in `version.py` (a "v" is still present in
      the Git tag added by version bumping)

  CLI replacements:

    - `hatch build` → `mise run build`
    - `hatch version` → `mise run version show`
    - `mise run bump` → `mise run version bump`
- Use `prek` instead of `pre-commit`.

  Coppy now requires Copier 9.5+.

  Upgrade path for existing projects:

    - Run `coppy update` like normal.
    - Coppy's migrations will
        - Convert your `.pre-commit-config.yaml` into `prek.toml`.
        - Replace an existing Git `pre-commit` hook with a `prek` hook

  If the conversion step fails, `coppy update` aborts immediately. Restore a clean working
  tree, fix the hook config, and rerun the update.

  **Manual Updates**:

    - update any custom CI/scripts/docs that still run `nox -s precommit`; the session is
      now `nox -s prek`
    - replace any direct use of the old Python `pre-commit` API (for example
      `pre_commit.main`)


### Fixed

- Ignore blank lines in `pip-audit-ignore.txt` when building `pip-audit` ignore arguments


### Added

- Add rumdl Markdown linting and formatting behind a `use_rumdl` Copier option.
- Projects can omit the Codecov upload and OIDC permissions from the GitHub nox workflow.


### Changed

- Add `mise lock` support by placing a `mise.lock` file.

  `copy update`: if `mise.lock` is blank, coppy runs `mise lock`.
- Generated `ruff.toml` no longer pins `target-version`

  Ruff now auto-derives its target from `pyproject.toml`'s `requires-python`, so edits to
  the project's supported Python versions stay in sync with ruff without re-running
  copier.

  <https://docs.astral.sh/ruff/configuration/#inferring-the-python-version>
- Modify the uv/mise/Python integration.

    - Standardize on `.python-version` for Python version selection.
        - It works for mise, uv, and GitHub's `setup-python` action.
    - mise
        - Uses `python.uv_venv_auto = "create|source"` to create and activate uv's
          project environment.
        - Gets its Python tool spec from `.python-version`.
        - Uses an `enter` hook to run `uv sync`
    - Add a `python_version_min` Copier template setting so the `pyproject.toml` Python
      spec can be different from the interpreter version used for local development.
        - This is useful for library projects that want to test on a given version but may
          support older or newer versions.
        - Applications should keep `python_version_min = python_version`.
    - Remove the custom `mise-uv-init.py` task and its `UV_PROJECT_ENVIRONMENT` and
      `UV_PYTHON` overrides.
    - Centralized environments are now an optional developer-level uv setting rather than
      project configuration.
- The `upgrade-deps` task now refreshes `mise.lock` so tools using fuzzy version selectors
  such as `latest` advance to the latest published matching version.


## [1.20251025.1](https://github.com/level12/coppy/releases/tag/v1.20251025.1)


### Changed

- Remove pip-audit ignore for vulnerability fixed by pip 25.3 release. You will need to
  `uv sync --upgrade` to get the pip update which will then satisfy pip-audit.
  ([#91](https://github.com/level12/coppy/issues/91))


## [1.20251024.2](https://github.com/level12/coppy/releases/tag/v1.20251024.2)


### Fixed

- Fix nox GitHub actions permission ([#90](https://github.com/level12/coppy/issues/90))


### Added

- Add ignore file for pip-audit & ignore pip vulnerability


## [1.20251024.1](https://github.com/level12/coppy/releases/tag/v1.20251024.1)


### Breaking

- Moderate: Adjust mise/uv Python bootstrap mechanism and change install recommendations
  in docs ([#56](https://github.com/level12/coppy/issues/56)).
    - The new init method which uses a custom task in the project and adjusted `mise.toml`
      config should "just work". It's tested, but it's also new, so YMMV.
    - If using centralized venvs:
        - ensure `~/.cache/uv-venvs/` exists. Project venvs will now be
          configured in that location.
        - Remove `UV_PROJECT_ENVIRONMENT` from `~/.config/mise/config.toml` which will be
          a breaking
  change for existing projects not updated to at least this version of the Coppy template.

        - For existing projects that aren't ready to be updated to the latest Coppy
          version, you
  should add the `UV_PROJECT_ENVIRONMENT` definition to a project specific
  `mise.local.toml` file:

          ```toml
          [env]
          UV_PROJECT_ENVIRONMENT = '{% if env.PROJECT_SLUG %}~/.cache/uv-venvs/{{ env.PROJECT_SLUG }}{% endif %}'
          ```

  When the project updates to at least this version of the Coppy template, that definition
  should be removed.
- Moderate: move project's tests from `./src` to `./tests`
  ([#75](https://github.com/level12/coppy/issues/75))
    - Advantages: test directory is top-level and more obvious, provides more flexibility
      if wanting to test a generated wheel and not the code in `./src`. See related issue
      for example.
    - Actions **required**: move `conftest.py` and your tests from `./src/` to `./tests`
- Minor: `env-config.yaml` changed HATCH_INDEX_AUTH 1password secret reference
  ([#78](https://github.com/level12/coppy/issues/78))

    - From: 'op://my/private/pypi.python.org/api-token'
    - To: 'op://my/private/pypi.org/api-token'
- Minor: change python dependency group and nox session name from "tests" to pytest. Also,
  enhance noxfile with improved `uv_sync()` and `pytest_run()`
  ([#82](https://github.com/level12/coppy/issues/82)).

    - "tests" -> "pytest" dependency group: mostly for clarity. While technically
      breaking, most
  projects won't need to manually change anything unless they've customized that group
  already.
    - The functions serve as a foundation for more complicated setups with multiple pytest
      runs,
  potentially using different environment variables, and parameterization. Example of such
  usage in Webgrid's
  [`noxfile.py`](https://github.com/level12/webgrid/blob/master/noxfile.py).


### Changed

- Docs: we now recommend installing uv directly as the OS user and not through Mise.
- `.editorconfig`: move `charset = utf-8` to global as it seems like a sensible modern
  default. ([#68](https://github.com/level12/coppy/issues/68))
- Remove "From Coppy" and "App Specific" from pyproject.toml dependency groups. They
  didn't stay organized with `uv add` and aren't likely to be necessary.
  ([#72](https://github.com/level12/coppy/issues/72))
- Use uv's `--frozen` in CI and testing scenarios to help ensure dependency updates are
  handled explicitly by the developer. ([#74](https://github.com/level12/coppy/issues/74))
- Nox pytest command should not specify the module to cover. Since we specify the paths in
  `.coveragerc`, the pytest option should be just `--cov`, not e.g. `--cov=webgrid`.
  ([#76](https://github.com/level12/coppy/issues/76))
- nox uv now uses `--only-group` instead of `--no-dev` since the intention behind our
  usage is to only install the group the nox session needs. `--only-group` is more
  appropriate since it's possible that the dev group is not the default group. Also DRY
  refactor uv calls in nox. ([#77](https://github.com/level12/coppy/issues/77))
- Noxfile and nox GH action updates
    - Use uv's --exact and --frozen to help ensure environments contain only expected
      packages
    - noxfile: enhance pytest() and uv_sync() functions
    - pytest: only include junit xml for CircleCI
    - pytest: remove `--cov-config=.coveragerc` because it's the default
    - GitHub action: use separate jobs and a matrix to parallelize the runs
    - GitHub action: use Coppy's GH actions to DRY the config; drop dependency on
      ubuntu-mive
    - GitHub action: add codecov integration
      ([#82](https://github.com/level12/coppy/issues/82))
- Change mise task comment headers
  ([discussion](https://github.com/jdx/mise/discussions/6139))
  ([#83](https://github.com/level12/coppy/issues/83))
- Update pre-commit versions
