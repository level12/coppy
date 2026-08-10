# Spec: Mise Lock Migration


## Summary

- Add a blank `mise.lock` to the copier template root.
- During `coppy migrate after`, ensure the project root has a populated `mise.lock`.
- If `mise.lock` is missing, or exists but is blank after `strip()`, run `mise lock`.


## Scope

- Template root lockfile presence.
- After-migration behavior for existing projects.
- Focused migration and template test coverage.
- Review follow-up captured in `specs/2026-05-10-mise-lock-review1-opus.md`.


## Findings

- Existing generated projects may not have a root `mise.lock` yet.
- A blank template `mise.lock` gives newly generated projects the expected file shape.
- Existing projects still need post-update handling so the lockfile is created or
  repaired.
- The current migration hook runs on every `coppy update`, so this check must stay safe
  and idempotent.
- Review feedback raised follow-up questions around future copier-update conflicts,
  migration ordering, and version-gating.


## Decisions

- Keep the initial template change minimal: ship an empty `template/mise.lock`.
- Put the repair/ensure behavior in `Migrator.after()` so it applies to updated projects.
- Treat whitespace-only lockfiles the same as missing lockfiles.
- Cover the missing, blank, and template-generation paths with targeted tests.


## Open Questions

- Should `template/mise.lock` be excluded from future `copier update` merges to avoid
  conflicts once users have a populated lockfile?

No. We will never change the content of mise.lock and copier will therefore never try to
update it during an update operation.

- Should `ensure_mise_lock()` run after `prek install`, or otherwise avoid blocking
  existing post-migration behavior if `mise lock` fails?

Yes. ensure_mise_lock() should run at the end of the after() logic. If it fails, report
it, but don't throw an exception (`check=False`).

- Should this migration be version-gated so it does not run on every future update?

Nope. We are making the migration idempotent so that it can always run and only take
action when the action is reasonably desired.


## Validation Outcomes

- Targeted formatting/linting passed on the touched Python files.
- Targeted tests passed:
    - `tests/coppy_tests/test_migrate.py`
    - `tests/coppy_tests/test_template.py`
- Latest focused run result: `27 passed`.


## Review Feedback

This is feedback for the review1-opus.md file related to this spec:

1. Fix, addressed above in Open Questions
2. We'll commit the file eventually
3. Ignore, addressed above in open questions
4. Add a changelog entry
5. We address this by not throwing an exception if `mise lock` fails
6. Add a variable to Migrator(mise_lock=True). Set it to `False` in the tests. Remove all
   the pre-creates of mise.lock.
7. Pedantic, ignore
8. Agreed, add output for the user that `mise lock` was ran
9. Pedantic, ignore
10. Ignore
11. Agreed
12. Ignore, I like the current style

Ignore Tests -- coverage gaps and Nits/ Questions.

Accepted items #1, #4, #5, #6, #8, and #11 were implemented.
