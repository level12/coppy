# Code Review: `ensure_mise_lock` migration

Scope: staged changes to `src/coppy/migrate.py`, `template/mise.lock`,
`tests/coppy_tests/test_migrate.py`, `tests/coppy_tests/test_template.py`.

Reviewer model: Claude Opus 4.7 (Augment Agent).


## High


### 1. Failure of `mise lock` aborts `prek install` (regression risk)

`src/coppy/migrate.py` lines 53–79: `ensure_mise_lock()` is called between the prek
file rename and the `prek install` step. `sub_run` defaults to `check=True`, so any
non‑zero exit from `mise lock` (mise missing, network failure, lockfile error, etc.)
raises and prevents `prek install` from running. Previously, `coppy migrate after`
would always reinstall the prek hook when applicable; that guarantee is now lost.

Fix: move `self.ensure_mise_lock()` to the end of `after()` (after the `prek install`
block), so a `mise lock` failure cannot regress the existing prek behavior.


### 2. `template/mise.lock` is not yet committed — `test_static_files` will fail

`tests/coppy_tests/libs/testing.py` calls `copier.run_copy(..., vcs_ref='HEAD')`,
which generates the project from the committed tree, not the working/staged tree.
`template/mise.lock` is staged as a new file but not in HEAD, so the new assertion
`assert gen_pkg.exists('mise.lock')` in `test_template.py::test_static_files` will
fail when run against the current working tree until the staged change is
committed. Verify CI runs the test post‑commit, or note this expectation.


## Medium


### 3. `copier update` will likely conflict on `mise.lock`

`template/mise.lock` is shipped as an empty, non-templated static file. After first
generation, `coppy migrate after` runs `mise lock` and populates the user's
`mise.lock`. On a subsequent `copier update`, copier renders the template version
(still empty) and diffs against the user's now-populated file. Depending on
copier's three-way merge, this is at minimum noisy and at worst will prompt to
overwrite the user's real lock contents.

Suggested fixes:

- Add `mise.lock` to a top-level `_exclude:` in `copier.yaml` so copier never
  touches it on update, and let `ensure_mise_lock()` create it on first run
  instead of shipping the empty placeholder.
- Or make `template/mise.lock` a no-op placeholder that is intentionally
  regenerated and document the conflict resolution.


### 4. Missing changelog entry

The repo uses `changelog.d/` (towncrier-style); the only existing fragment is
`+prek.breaking.md`. The migration now invokes `mise lock` on every `coppy update`
for users without a populated `mise.lock`. That is a user‑visible behavior change
(new dependency on `mise` being on PATH at update time, network/cache implications).
Add a changelog fragment describing it.


### 5. `mise` becomes a hard prerequisite for `coppy update`

`ensure_mise_lock()` will hard‑fail with `FileNotFoundError` (wrapped as
`CalledProcessError` by `sub_run`) if `mise` is not installed. Coppy targets
mise‑based projects, so this is defensible, but consider:

- A clearer error message ("mise is required to populate mise.lock"), or
- Skipping with a warning when `shutil.which('mise')` is `None`.

At minimum, document the new requirement in the changelog/readme.


## Low


### 6. `after()` now unconditionally invokes a real subprocess; tests work around

it with manual file-writing in 7 places

Adding `self.ensure_mise_lock()` to `Migrator.after()` means every test that calls
`after()` must pre-create `mise.lock` to avoid invoking `mise` for real. The diff
repeats `self.write_mise_lock(project_dpath)` in 7 tests. This is a leaky
abstraction and a fixture smell. Prefer a shared fixture.

Two cleaner options:

- Add an `autouse=True` fixture on `TestMigrate` that pre-creates `mise.lock`.
- Or split the mise-lock concern into its own helper invoked separately from
  `after()`, so the conversion tests do not need to know about it at all.


### 7. New tests don't isolate `project_dpath` from real `mise` invocation paths

`test_after_runs_mise_lock_when_lock_missing` and `..._when_lock_blank` mock
`coppy.migrate.sub_run`, so `mise` is never executed — good. However they don't
assert that no real `mise.lock` ends up on disk, and they share `project_dpath`
(tmp_path) with prior fixture state semantics. They are fine as written, but
consider adding `assert not (project_dpath / 'mise.lock').exists()` for the
"missing" case to make the precondition explicit.


### 8. `ensure_mise_lock` provides no user-visible feedback

The neighboring conversion path in `after()` uses `click.echo(...)` to tell the
user what happened. `ensure_mise_lock()` runs `mise lock` silently from coppy's
side. Consider an echo such as `Generating mise.lock...` or
`mise.lock missing/empty; running mise lock` so the migration step is
self-explanatory in the copier output.


### 9. `ensure_mise_lock` runs on every update, unconditionally

The `_migrations` entries in `copier.yaml` have no version gating, so this code
path runs on every `coppy update`. That is idempotent when the lock is non‑blank,
but it does mean the check happens forever, not just for a one‑shot migration.
If the intent is a one‑time migration for existing projects, gate it on
`_copier_conf.old_commit` / migration version. If the intent is "always ensure a
non‑blank lock exists," consider moving this out of `migrate.py` (which is
semantically about migrations) into a post‑generation step or a `mise.lock.jinja`
that runs `mise lock` itself.


### 10. Empty `template/mise.lock` is a load‑bearing marker

Shipping an empty file purely to be overwritten by `mise lock` is fragile and
non‑obvious. A short comment in the template (e.g., a sibling note in
`template/mise.toml` or a brief `readme`/`tasks` mention) — or generating the lock
directly during template render — would make the intent clearer. Not a blocker.


### 11. No explicit test for the populated-lock skip path

Add a direct test like `test_after_skips_mise_lock_when_populated` so the intended
`exists() and read_text().strip()` skip behavior stays explicit and protected.


### 12. Style nit: redundant existence check

`mise_lock_fpath.exists() and mise_lock_fpath.read_text().strip()` can be reduced
to `try: ... except FileNotFoundError: ...` or `read_text(...)` guarded once. Not
required; current form is readable.


## Tests — coverage gaps

- No test asserts ordering: that `prek install` still runs when `mise lock`
  succeeds, nor that `prek install` is skipped when `mise lock` fails (related to
  finding #1). If finding #1 is addressed, add a regression test asserting
  `prek install` runs even when `ensure_mise_lock` would invoke `mise lock`.
- No test asserts the `before()` path is unaffected by mise (it is not, but a
  one‑liner test would lock that in).


## Nits / questions

- `write_mise_lock` default content `'locked\n'` is fine; consider a constant at
  module top to avoid magic strings if reused further.
- The new property `mise_lock_fpath` matches the existing naming convention
  (`*_fpath`) — good consistency.


## Things that look correct

- The skip semantics correctly treat empty or whitespace-only files as needing
  `mise lock`, which matches the empty `template/mise.lock` shipped to fresh
  projects.
- `ensure_mise_lock()` is invoked before the `if not converted: return` early
  exit, so it runs for non-conversion updates too.
- `m_sub_run.assert_called_once_with('mise', 'lock', cwd=project_dpath)`
  correctly asserts both args and kwargs.
- The new `test_static_files` assertion is consistent with the rest of that test.
- Style conforms to the project conventions.
- Migrations only run on `copier update`, not initial copy, so shipping the empty
  `template/mise.lock` will not trigger `mise lock` during template-generation
  tests.


## Recommended next actions

1. Decide on the `_exclude` (or equivalent) strategy for `template/mise.lock` to
   avoid `copier update` conflicts and document the choice.
2. Refactor the repeated `self.write_mise_lock(project_dpath)` setup into an
   autouse fixture, or split `ensure_mise_lock` out of `after()`.
3. Add an explicit test for the populated-lock skip branch.
4. Add a `click.echo` or log call inside `ensure_mise_lock` for visibility.
5. Optionally pin the migration to a `version:` so it does not run on every
   update.


## Spec feedback disposition

Accepted from `specs/2026-05-10-mise-lock-migration.md` review feedback:

- #1: move `ensure_mise_lock()` to the end of `after()`.
- #4: add a changelog entry.
- #5: do not abort the migration if `mise lock` fails; report the failure.
- #6: add `mise_lock=True` on `Migrator` and disable it in non-mise migration
  tests instead of pre-creating `mise.lock` repeatedly.
- #8: add user-visible output when `mise lock` is run.
- #11: add an explicit populated-lock skip test.

Not adopted per spec feedback:

- #3, #7, #9, #10, #12.
- "Tests — coverage gaps" and "Nits / questions" sections.

---

LGTM aside from finding #1 (ordering/regression) and #2 (commit `template/mise.lock`
before relying on the new `test_static_files` assertion). Findings #3–#4 should be
addressed before release.
