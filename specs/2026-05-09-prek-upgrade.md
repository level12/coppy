
## Summary

- Migrate generated projects from `pre-commit` to `prek` as part of `coppy update`.
- The one non-static part is converting `.pre-commit-config.yaml` into `prek.toml`.
- Use a Copier update migration for this work; do not add custom update orchestration to `src/coppy/cli.py`.


## Decisions

- Use a Copier `_migrations` entry in `copier.yaml` for the transition.
- The conversion must run in the `before` stage so `.pre-commit-config.yaml` is still present when conversion runs.
- `coppy` itself must carry `prek` as a runtime dependency so the update path has the converter available.
- Do **not** rely on a bare `prek` executable being on `PATH` when `coppy` is installed as a uv tool.
  - `uv tool install` exposes executables from the installed package, not dependency executables.
  - The migration should invoke `prek` through Copier's Python environment instead of assuming the shell can find `prek` directly.

## Prior work

I've already converted a copier project to prek manually.  Use the commit as a reference point:

https://github.com/rsyring/agent-branch/commit/1b6202aa4b56bbdfd74ad4beb6a67741bdae0d7e

## Scope

### coppy package

- Update root `pyproject.toml` so `prek` is installed with `coppy`.
- Review any coppy-side references to `pre-commit` that should move to `prek`.

### Copier template

- Add the update migration in `copier.yaml`.
- Replace generated-project `pre-commit` references with `prek`, including at least:
  - `template/pyproject.toml.jinja`
  - `template/tasks/bootstrap`
  - `template/mise.toml`
- Review any other template files/docs that still assume `pre-commit`.

### Release notes

- Add a towncrier fragment under `changelog.d/`.
- Explain both:
  - the generated-project behavior change (`pre-commit` -> `prek`)
  - the expected update/upgrade flow for existing projects


## Test Plan

- Add an integration test that exercises the real `coppy update` flow under the isolated system user harness.
- Base the test on `tests/coppy_tests` infrastructure, especially:
  - `UserBox` for running as `coppy-tests`
  - `UserPackage` for a project owned/executed through that sandbox
  - the existing `coppy_install` fixture that builds a wheel and installs `coppy` for the test user
- The test should validate an actual upgrade scenario, not just a mocked CLI call.

### Procedure to verify

- Start from a project state that still has `.pre-commit-config.yaml` and old `pre-commit`-based template content.
- Run `coppy update` as the isolated system user.
- Assert at minimum:
  - the update succeeds
  - `.pre-commit-config.yaml` is converted before removal by the template update
  - `prek.toml` exists after update
  - generated project config/scripts now reference `prek` instead of `pre-commit`

### Important testing concern

- There is not currently an obvious existing test fixture for a two-version Copier update path.
- The test will likely need one of these setups:
  - a synthetic temporary git repo with an "old" tagged template state and a "new" tagged template state, or
  - a reliable existing tag/fixture that represents the old `pre-commit` state
- Prefer the synthetic repo/fixture if needed so the test is deterministic and not tied to long-term repo history.


## Changelog / Upgrade Notes to Cover

- `coppy` now ships with `prek` available for update migrations.
- Existing projects updated with `coppy update` will be moved from `pre-commit` config to `prek` config.
- If an existing Git `pre-commit` hook is present during update, the migration should replace it with
  the `prek` hook automatically.
- The upgrade note should call out that custom `.pre-commit-config.yaml` content will be translated by the migration and may be normalized/reformatted by the converter.
- If the migration cannot safely convert a project, the failure mode and expected manual recovery path should be documented.


## Questions / Comments / Concerns

1. Should the migration be gated to a specific template version threshold, or should it run on every update while `.pre-commit-config.yaml` is present?

No gate for now.  Run whenever `.pre-commit-config.yaml` is present.

2. Do we want generated projects to fully switch in one release, or keep any temporary compatibility layer for `pre-commit`-named dependency groups/tasks/session names?

Fully switch in one release.

3. If conversion fails, should the migration abort the update immediately, or is there a preferred degraded behavior?

Yes, abort the update immediately.

4. For the update test, is there already a preferred pattern in this repo for creating/tagging a temporary git-backed template fixture, or should I introduce one?

You'll need to introduce once.

## Notes

- `src/coppy_extensions.py` is only providing Jinja globals/filters today; it is not an update lifecycle hook and is not the right place for this migration behavior.
- `src/coppy/cli.py` already passes `--trust`, so Copier migrations/tasks are allowed during `coppy update`.
- `coppy update` also needed a runtime fix: when coppy is installed as a uv tool, dependency
  executables like `copier` are not exposed on `PATH`.  The implementation therefore runs Copier as
  `sys.executable -m copier`.
- A `before` migration alone was not sufficient because the new template's `prek.toml` overwrote the
  converted file during update.  The implementation uses:
  - a `before` migration to convert `.pre-commit-config.yaml` to temporary `.coppy-prek.toml`
  - an `after` migration to move that converted file into final `prek.toml`
  - an `after` migration step that uses `git rev-parse --git-path hooks/pre-commit` and, when a
    `pre-commit` hook is already present, replaces it with `prek install -f -t pre-commit`


## Validation Outcomes

- Added an isolated-user integration test that creates a synthetic git-tagged old/new template repo,
  generates a project from the old tag, customizes `.pre-commit-config.yaml`, runs `coppy update`,
  and verifies the custom hook survives in `prek.toml` after update.
- That update test coverage also verifies an existing Git `pre-commit` hook is replaced with the
  `prek` hook during update.
- Targeted validation passed:
  - `ruff format && ruff check --fix --extend-fixable F401 && ruff format`
  - `pytest -q tests/coppy_tests/test_update.py tests/coppy_tests/test_template.py tests/coppy_tests/test_coppy.py`


## Code Reviews and Guidance From Opus

Whenever you think you are finished, or if you get stuck and need input, request a code review or
advice from Opus.  Save Opus' code review or adivice verbatim to a new file next to the spec file
after each run (number them to avoid collisions).

Unless you strongly disagree with a finding, fix anything Opus finds wrong and/or follow it's advice.

If you disagree, note it here in the spec and I'll review with you.

Repeat Opus code reviews until it is satisfied or you reach an impass.

## Status update

Current status: implementation complete. Multiple Opus review passes were run and the material
findings were addressed.

Intentional non-fixes after Opus review:

- The Copier migration is intentionally **not** version-gated. Per the agreed plan it should run on
  any update while `.pre-commit-config.yaml` is still present, and become a no-op afterward.


# Phase II

My feedback after reviewing your changes:

- Let's move the logic for the migration out of copier.yaml to coppy itself
  - `coppy migrate [before|after]`
    - Make this a hidden command with click.  We don't want users to think they need to run it.
    - The first arg should be a `click.Choice`
    - Have two top-level functions, `migrate_before` and `migrate_after`.
      - If helpful, these functions should take arguments that make it easier for them to be tested.
      - E.g. a project root path or similar so can easily have them work on temporary paths during
        testing.
  - Adjust copier.yaml to call `coppy migrate ...` before and after with the correct argument to
    indicate the stage.
- As I indicated above, for the migration, we should treat the presence of `.pre-commit-config.yaml`
  as an indicator that we should migrate it.  It doesn't matter if it matches a baseline or not.
  - It often WON'T match the baseline because there are versions in the file which projects update.
  - The entire reason we are using prek's `yaml-to-toml` is so that we can convert what the project
    is actually using without risk.  If the project dosn't like the conversion, they will not commit
    the changes.
  - Get rid of the migration features, tests, and the baseline pre-commit-config.v1.yaml file related
    to this.


## GPT's Recommendation (which I like)

Once the migration logic is moved out of `copier.yaml` and into hidden `coppy migrate before|after`
commands, the simplest and cleanest test strategy is:

- Put almost all migration coverage on `migrate_before()` and `migrate_after()` directly.
  - Test them against temporary project roots.
  - Pass an explicit project path argument so the tests do not need to rely on cwd tricks.
- Remove the synthetic tagged template repo setup that copies large parts of the coppy repo just to
  exercise migration behavior.
  - That should also allow removing everything in `tests/coppy_tests/data/template-v1/`.
- Remove the baseline comparison approach and delete `src/coppy/migrations/pre-commit-config.v1.yaml`.
  - If `.pre-commit-config.yaml` exists, convert it.
- Keep the migration tests focused on behavior that is actually owned by coppy:
  - `.pre-commit-config.yaml` present -> converts to `prek.toml`
  - `.pre-commit-config.yaml` absent -> no conversion
  - existing git `pre-commit` hook -> replaced in `after`
  - no hook -> no-op
- Keep at most one thin integration test around the Copier wiring if needed, but it should only prove
  that `copier.yaml` invokes `coppy migrate before` and `coppy migrate after` correctly.
  - If that thin integration test still needs any old/new template fixture data, keep only the minimum
    needed for the wiring test rather than preserving the current `template-v1` fixture set.

In short: move the logic into Python, unit-test that Python directly, and stop using the synthetic
template-history test for behavior that no longer belongs in Copier shell migrations.


## Handoff Notes For Next Agent

- The operator has explicitly directed a Phase II redesign:
  - move migration logic out of `copier.yaml` shell snippets and into hidden `coppy migrate before|after`
    commands
  - use a `click.Choice` arg for the stage
  - expose top-level Python functions `migrate_before` and `migrate_after`
  - make those functions easy to test directly, ideally by accepting a project-root path argument
- The operator explicitly does **not** want baseline comparison logic.
  - Presence of `.pre-commit-config.yaml` alone should trigger conversion.
  - Remove `src/coppy/migrations/pre-commit-config.v1.yaml`.
- The operator also wants the old migration-specific synthetic test setup removed.
  - Remove the related `tests/coppy_tests/data/template-v1/` fixtures unless a tiny remainder is
    still needed for a thin Copier wiring test.
  - Prefer direct Python tests of `migrate_before()` / `migrate_after()` over synthetic tagged-template
    history tests.
- Fresh-project docs/bootstrap were intentionally changed back to plain `prek install` (no `-f`).
  - Do not reintroduce `-f` there unless the operator asks.
- `tests/coppy_tests/test_coppy.py` was intentionally simplified to inline repeated mock assertions.
  - Do not reintroduce the removed `assert_update_call()` helper unless requested.
- If the next agent continues implementation, they should re-run the focused validation for any touched
  files/tests and keep this spec updated with outcomes/decisions.


## Phase II Implementation Outcome

- Migration behavior now lives in `src/coppy/migrate.py` with top-level `migrate_before()` and
  `migrate_after()` functions backed by a small `Migrator` class.
- `src/coppy/cli.py` now exposes hidden `coppy migrate before|after` commands using a
  `click.Choice` stage argument.
- `copier.yaml` now delegates update-stage migration work to `coppy migrate before` and
  `coppy migrate after`.
- Baseline-comparison migration logic was removed.
  - Deleted `src/coppy/migrations/pre-commit-config.v1.yaml`.
  - Presence of `.pre-commit-config.yaml` alone now triggers conversion.
- The synthetic tagged-template update test setup was removed.
  - Deleted `tests/coppy_tests/test_update.py` and the related `tests/coppy_tests/data/template-v1/`
    fixtures.
  - Added direct migration coverage in `tests/coppy_tests/test_migrate.py`.


## Phase II Validation Outcome

- Targeted Ruff format/lint passed for the touched Python files.
- `tests/coppy_tests/test_coppy.py` passed.
- `tests/coppy_tests/test_migrate.py` passed.

## Phase II Operator Feedback

- cli.py: is it safe to assume Path.cwd() is the target project's base repo directory?
- migrate.py
  - Migrator.migrate_before() -> .before()
  - Migrator.migrate_after() -> .after()
  - Remove migrate_before() and migrate_after() as top-level functions
  - Adjust cli.py and tests to use Migrator(...).before() | .after() directly.


## Phase II Follow-up Outcome

- `src/coppy/migrate.py`
  - Renamed `Migrator.migrate_before()` -> `Migrator.before()`.
  - Renamed `Migrator.migrate_after()` -> `Migrator.after()`.
  - Removed the top-level `migrate_before()` / `migrate_after()` wrappers.
  - Gated hook replacement in `after()` on actual conversion work so later updates are a no-op.
  - Switched `python_executable` to a dataclass `default_factory`.
- `src/coppy/cli.py`
  - Hidden `coppy migrate` now uses `Migrator(...).before()` / `.after()` directly.
- Verified Copier's migration working-directory contract instead of adding extra path plumbing.
- Tests
  - Updated CLI tests to assert construction and use of `Migrator` directly.
  - Added migration coverage for:
    - converted `prek.toml` winning over templated `prek.toml`
    - invalid YAML aborting conversion
    - idempotent `after()` behavior when no converted temp file is present
  - Relaxed the hook replacement assertion so it no longer depends on prek's exact hook header.
- Docs / notes
  - Removed the stale changelog note about raw-SHA `_commit` values skipping migrations.
  - Removed the stale `prek.toml` sync comment now that the repo root file is a symlink.


## Phase II Follow-up Validation Outcome

- Targeted Ruff format/lint passed for `src/coppy/migrate.py`, `src/coppy/cli.py`,
  `tests/coppy_tests/test_coppy.py`, and `tests/coppy_tests/test_migrate.py`.
- `pytest -q tests/coppy_tests/test_coppy.py tests/coppy_tests/test_migrate.py` passed (`15 passed`).


## Phase II.2 Outcome

- The `Path.cwd()` question is closed.
  - Verified from Copier documentation that migration commands run in the destination project root by
    default.
  - `copier.yaml` therefore calls the hidden command simply as `coppy migrate before|after`.
  - `coppy update <project_dpath>` remains safe because Copier executes migrations with cwd set to the
    destination project directory.


## Phase II.3 Final (I hope) cleanup

> In light of the Opus concerns, my plan
> 1. Keep the temp-file design
> I would keep .coppy-prek.toml.
>
> It is the simplest way to preserve the converted YAML while still letting Copier finish rendering the project.
>
> 2. Treat the stale-temp regression as the main real issue
> The important review concern was:
>
> if one update aborts after writing .coppy-prek.toml
> and a later update runs with no .pre-commit-config.yaml
> the stale temp file could wrongly overwrite a hand-edited prek.toml
> The right fix is the one already identified in review and reflected in the current migration shape:
>
> in before(), if .pre-commit-config.yaml is absent, proactively delete stale .coppy-prek.toml
> That makes the next after() a no-op instead of clobbering prek.toml.
>
> 3. Keep hook replacement gated on actual conversion
> Another good concern was avoiding reinstalling the prek hook on every later update.
>
> So the plan is:
>
> only run hook replacement in after() when a conversion actually happened for that update
> That keeps later no-op updates clean.

Agreed.

> Opus earlier suggested preserving the curated template prek.toml for stock configs.
>
> I would not do that

Agreed.  Do not do that.

> So the current intent is:
>
> converted project state wins
> not the curated template file

Agreed.


## Phase II.3 Outcome

- Review4's stale-temp regression concern is addressed.
  - `Migrator.before()` now removes a stale `.coppy-prek.toml` when
    `.pre-commit-config.yaml` is absent.
  - That prevents a later update from clobbering a hand-edited `prek.toml` with temp
    output left behind by an earlier aborted update.
- The Copier wiring test was hardened.
  - `tests/coppy_tests/test_migrate.py` now parses `copier.yaml` structurally instead of
    asserting raw YAML substrings.
- The stale empty leftover directories from earlier migration approaches were removed.


## Phase II.3 Validation Outcome

- Added direct regression coverage in `test_before_cleans_stale_temp_without_yaml` for
  the stale-temp cleanup path.
- `pytest -q tests/coppy_tests/test_coppy.py tests/coppy_tests/test_migrate.py` passed
  with `15 passed`.
