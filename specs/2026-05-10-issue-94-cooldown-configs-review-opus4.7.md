# Code Review — Issue #94 Cooldown Configs

Reviewer: Augment Agent (model: Claude Opus 4.7)
Spec: `specs/2026-05-10-issue-94-cooldown-configs.md`
Scope: working-tree changes (staged + unstaged + untracked) for issue #94.

## What was reviewed

- New template files: `template/.npmrc`, `template/.yarnrc.yml`,
  `template/aube-workspace.yaml`, `template/bunfig.toml`,
  `template/pnpm-workspace.yaml`, `template/uv.toml`.
- New repo-root `uv.toml`.
- `tests/coppy_tests/test_template.py` — added `test_supply_chain_configs`.
- `uv.lock` — updated (uv pinned dep bumped 0.9.5 → 0.11.11, new `[options]`
  block recording `exclude-newer-span = "P3D"`).
- `changelog.d/+cooldown-configs.changed.md`.
- `specs/2026-05-10-issue-94-cooldown-configs.md`.

Cross-checked against current upstream docs: npm v11 (`min-release-age`, days),
pnpm v11 (`minimumReleaseAge`, minutes), aube (`minimumReleaseAge`, minutes),
Bun 1.3 (`install.minimumReleaseAge`, seconds), Yarn berry (`npmMinimalAgeGate`,
duration string), uv ≥ 0.9.17 (`exclude-newer` accepts `"3 days"`). All keys,
locations and unit conversions in the diff are correct.

## High-priority findings

### 1. New test does not exercise template generation (test quality)

`test_supply_chain_configs` does not take the `gen_pkg` fixture and never
invokes `Package.generate()`. It just re-reads source files in `template/` and
asserts substrings the developer wrote moments earlier. That is close to
tautological and gives no signal that copier actually emits these files into
generated projects (it would still pass if a future `_exclude` rule, jinja
guard, or `_subdirectory` change silently dropped one).

The spec acknowledges the cause: `Package.generate()` uses `vcs_ref='HEAD'`,
so untracked files are invisible to the existing harness. The chosen
mitigation ("source-file test for now") locks in a test that cannot fail for
any realistic regression. Once these files are committed, reshape it to use
the same pattern as `test_static_files` (`gen_pkg.exists(...)` /
`gen_pkg.read_text(...)`), e.g.:

```python
def test_supply_chain_configs(self, gen_pkg: Package):
    for rel, expected in template_expected.items():
        assert expected in gen_pkg.read_text(rel)
```

That should be tracked explicitly (Open Question or follow-up issue), not
just left implicit in spec Findings.

### 2. `pnpm-workspace.yaml` shipped despite spec listing it as a blocker

The spec's Blockers section explicitly says: "If `pnpm-workspace.yaml` causes
unwanted behavior in single-package repos, we may need to revisit whether a
project `.npmrc` should carry pnpm's setting instead." The implementation
ships the file anyway without resolving the question.

Practical risk: dropping `pnpm-workspace.yaml` into a single-package repo
makes pnpm treat the directory as a workspace root, which can change
resolution / hoisting behavior even for users who never opt into pnpm. For a
Python-focused template, putting `minimum-release-age=4320` (minutes; the
key pnpm reads from `.npmrc` is `minimum-release-age` per pnpm's settings
docs and confirmed in pnpm issue #10008) in `template/.npmrc` and dropping
`pnpm-workspace.yaml` would avoid the workspace-root side effect. Either
take that path or close the blocker in the spec with an explicit decision
before merge.

### 3. Repo-root `uv.toml` silently changes coppy contributor workflow

`exclude-newer = "3 days"` at the repo root applies to every contributor's
`uv sync` / `uv lock` / `uv add`. That is reasonable as a default, but:

- The changelog entry says only "for generated projects". Contributors
  running the `upgrade-deps` task will silently get versions up to 3 days
  stale with no on-screen indication. The changelog should also call out
  the coppy-side effect (this commit is what bumped `uv` from 0.9.5 to
  0.11.11 in `uv.lock`, exactly fitting the 3-day window since 0.11.11's
  2026-05-06 upload).
- Spec Findings note that `uv tool` commands are not covered; that gap
  should appear in user-facing docs (changelog or README), not just the
  spec.
- `exclude-newer = "3 days"` (relative duration) requires uv ≥ 0.9.17. The
  template does not currently pin a minimum uv version via `required-version`
  in `pyproject.toml` / `uv.toml`. Generated projects whose contributors are
  on an older `uv` will see a parse warning and fall through to no cooldown,
  which silently defeats the feature. Add `required-version = ">=0.9.17"`
  (or whatever floor matches the doc you cite) in both `uv.toml`s, or
  document the requirement.
- `changelog.d/+cooldown-configs.changed.md` has no issue reference. Other
  entries link the issue (e.g. `pytest-ini.changed.md` references `#96`);
  add `(#94)` for consistency.

### 4. Aube inclusion is unmotivated

`template/aube-workspace.yaml` ships a config for a brand-new package
manager (`endevco/aube`) with negligible adoption today, on equal footing
with npm/pnpm/yarn/bun, and the changelog promotes it to top-level
capitalization ("Aube"). The cost is small but it is also pure clutter for
the realistic user base. Either justify the inclusion in the spec
("we're tracking aube because…") or drop it until the tool has traction. If
kept, note that aube already defaults `minimumReleaseAge` to 1440 (per its
settings doc and `crates/aube-settings/settings.toml`), so the file is only
overriding 1 day → 3 days; that's worth a one-line comment in the file.

## Medium-priority findings

### 5. Yarn config likely redundant against current default

Yarn berry PR #7092 sets the default `npmMinimalAgeGate` to `4320m` (3
days). For Yarn versions that include that change, our explicit `"3d"` is a
no-op. That is harmless, but if the intent is to *guarantee* 3 days even on
older Yarn, document it; if the intent is just to be explicit, say so in a
file comment so the next reader doesn't wonder.

### 6. Cooldown-window literal duplicated across 6 places

The same 3-day window is encoded as `3` (npm days), `4320` (pnpm minutes),
`4320` (aube minutes), `259200` (bun seconds), `"3d"` (yarn), and `"3 days"`
(uv, twice). The test then re-encodes the same six literals. Changing the
window means editing 7 locations in lockstep with no shared source of
truth. Acceptable for now, but worth either:

- a single-line comment block at the top of each file noting "global
  cooldown window: 3 days; update siblings on change", or
- factoring the test's `template_expected` dict into a small fixture so
  there's one place to update test side.

### 7. Comment style is uneven

`.npmrc` comment: "at least 3 days old" but does not annotate the unit.
`.yarnrc.yml` comment: "Supply-chain hardening for Yarn." with no unit or
window. pnpm/aube/bun comments correctly translate to "(N units)". Bring
all six files to the same shape — one line saying what the setting does,
one line annotating the value as "= 3 days" — for parity. Pure stylistic;
not blocking.

### 8. Spec hygiene

- "Validation Outcomes" claims the targeted pytest passes, but the test it
  validated is the source-file test that cannot fail in realistic ways.
  Note that limitation, or revalidate after reshaping per finding #1.
- The Blockers section still has two open items (untracked-files
  visibility, pnpm-workspace side-effects). Per `agent-specs.md` the spec
  should record the decision or move them to Open Questions before this is
  considered complete.
- Per `agent-specs.md`, keep the spec focused on decisions and outcomes;
  the per-tool unit table in Findings is fine while the configs are still
  in flight, but trim it once the code is the source of truth.

## Low-priority / nits (not blocking)

- `template/uv.toml` and `uv.toml` are byte-identical aside from the
  comment. Fine; do not symlink (copier would dereference and emit the
  link target).
- `template/.npmrc` uses `;` for comments; both `;` and `#` are accepted.
- The new test reads via `coppy.utils.pkg_dpath`. That is the established
  module-level constant (also used inside `tests/coppy_tests/libs/testing.py`
  via `utils.pkg_dpath.as_posix()`), so this is consistent with existing
  patterns. The duplicated import (`from coppy import utils` *and* `from
  coppy.utils import LazyDict`) could collapse to a single `from coppy import
  utils` plus `utils.LazyDict`, but that is purely a style nit.
- No `_exclude` change in `copier.yaml` was needed; default file selection
  picks these up. Worth a one-liner in spec Decisions for the next reader.

## Summary

The functional change is small, the keys/units are correct, and the
direction is right. Three things should change before this is considered
done: (1) make the test actually exercise generated output (after commit),
(2) close the open `pnpm-workspace.yaml` blocker with a decision (and
prefer `.npmrc` for pnpm in a Python-template default), and (3) make the
contributor-side impact (repo-root `uv.toml`, uv version floor, `uv tool`
gap) explicit in the changelog.
