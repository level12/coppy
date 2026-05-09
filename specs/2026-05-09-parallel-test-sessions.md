## Summary

- Allow multiple local test sessions to run at the same time for one developer/machine.
- Keep the existing dedicated test OS user model, but stop treating that user's real home, cache, tool install, and temp paths as globally shared mutable state.
- Introduce session-scoped runtime directories and env overrides so each test run is isolated even when all runs execute as `coppy-tests`.


## Findings

- `tests/coppy_tests/libs/sandbox.py`
  - `UserBox.username`, `home_dpath`, `tmp_dpath`, `cache_uv_venvs`, and `pytest_tmppath` are class-level globals.
  - `pytest_tmppath = tmp_dir(...)` runs at import time, so directory allocation and cleanup happen before any explicit session boundary exists.
- `tests/coppy_tests/libs/paths.py:tmp_dir()` is not concurrency-safe.
  - It scans a shared directory, picks the next numeric suffix, rewrites a shared `*-current` symlink, and deletes older runs.
  - Two processes can pick the same next directory, or one process can delete another still-active run.
- `tests/coppy_tests/libs/testing.py`
  - `UserPackage('test-sandbox')` and `UserPackage('template-with-sandbox')` resolve to stable shared paths under `UserBox.pytest_tmppath`.
  - `Package.generate(rm_first=True)` will delete and recreate those paths, which can clobber another concurrent session.
- `tests/coppy_tests/libs/sandbox.py:UserBox.__enter__()` mutates shared user state.
  - Non-centralized runs delete `~coppy-tests/.cache/uv-venvs`.
  - Every sandbox run calls `mise --no-config cache clear`, which clears a shared cache for the whole test user.
- `src/coppy/utils.py:sudo_run()` hardcodes `HOME=/home/{sudo_user}`.
  - That blocks session-specific `HOME`, `XDG_*`, `MISE_*`, and `UV_*` isolation unless the helper is refactored.
- `tests/coppy_tests/conftest.py:coppy_install()` plus `tests/coppy_tests/libs/sandbox.py:UserBox.coppy_install()` use shared install/build state.
  - `hatch build --clean` writes to repo-local `tmp/dist` (see `hatch.toml`), which is shared by concurrent runs in the same checkout.
  - `uv tool install --reinstall` installs `coppy` for the shared `coppy-tests` user, so one session can replace the tool another session is using.
- Hard-coded path assertions assume one fixed home.
  - Examples: `tests/coppy_tests/test_sandbox.py`, `tests/coppy_tests/test_template.py`, and `tests/coppy_tests/data/mise-config.toml` embed `/home/coppy-tests/...`.
- `tasks/test-user-prep.py` and `tests/coppy_tests/libs/os_prep.py` are machine-global setup.
  - Fixed username/group/sudoers entry/systemd unit names all assume one shared prepared user.
  - `--reinstall` is explicitly destructive: it `pkill`s all processes for `coppy-tests`, waits, then `userdel -r`s the user.
- `tests/coppy_tests/test_template.py` already contains a TODO noting sandbox/package isolation is insufficient when a test mutates the generated package.
- Lower-priority latent issue: `UserBox.place()` uses a fixed `~` backup suffix, so concurrent use against the same target would not be safe.


## Decision

- Keep one prepared OS user: `coppy-tests`.
- Add a first-class test session concept and make all mutable runtime state session-scoped.
- Treat machine prep (`tasks/test-user-prep.py`) as an infrequent shared bootstrap step, not something that provides per-run isolation.


## Proposed Design

### 1) Add a session model

- Introduce a small `TestSession`/`SandboxSession` object used by `UserBox` and `UserPackage`.
- Required fields:
  - `session_id`
  - `username`
  - `base_home_dpath` = real passwd home for `coppy-tests`
  - `session_root_dpath`
  - `session_home_dpath`
  - `session_tmp_dpath`
  - `session_cache_dpath`
  - `session_config_dpath`
  - `session_data_dpath`
  - `session_tool_bin_dpath`
- Session ID source:
  - prefer explicit env var like `COPPY_TEST_SESSION`
  - otherwise auto-generate from `PYTEST_XDIST_WORKER`/pid/timestamp or a UUID

### 2) Make sandbox env fully session-scoped

- Refactor `sudo_run()` so callers can pass command env vars through `sudo`, not only `PATH`.
- Every sandboxed command should run with session overrides at minimum:
  - `HOME`
  - `TMPDIR`
  - `XDG_CACHE_HOME`
  - `XDG_CONFIG_HOME`
  - `XDG_DATA_HOME`
  - `MISE_CACHE_DIR`
  - `MISE_CONFIG_DIR`
  - `MISE_DATA_DIR`
  - `UV_CACHE_DIR`
  - `UV_TOOL_DIR`
  - `UV_TOOL_BIN_DIR`
- Keep using the shared installed `mise` and `uv` executables from the prepared user's real `~/.local/bin` unless testing proves those binaries themselves need session isolation.

### 3) Remove shared temp path allocation

- Delete the import-time `UserBox.pytest_tmppath = tmp_dir(...)` pattern.
- Stop using numeric `pytest-run-*` directories and the shared `*-current` symlink.
- Use session-owned directories created with `tempfile.mkdtemp()` or a UUID-based path under a stable parent such as:
  - `/home/coppy-tests/tmp/sessions/<session-id>/...`
- Only clean up directories owned by the current session.

### 4) Make project/package paths session-local

- `UserPackage` paths should include the session root so fixed identifiers like `test-sandbox` and `template-with-sandbox` stop colliding across sessions.
- Tests may still use stable per-test identifiers, but only within the current session namespace.

### 5) Make coppy tool install session-local

- `coppy_install()` must stop reinstalling into the shared default uv tool directory.
- Install `coppy` into the current session's `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` instead.
- Avoid shared repo build artifacts while preparing that install.
  - The current `hatch build --clean` -> `tmp/dist` flow is not safe for concurrent runs in the same checkout.
  - Build or stage wheels in a session-owned directory instead.

### 6) Update tests to use dynamic paths

- Replace literal `/home/coppy-tests/...` assertions with values derived from `UserBox`/session paths.
- Remove or update any fixture data that bakes in the real home path.

### 7) Guard destructive machine-prep actions

- `tasks/test-user-prep.py --reinstall` should remain an explicit maintenance action.
- Add a lock or at least clear documentation that it must not run while any test session is active.
- Normal test execution should not require rewriting sudoers, deleting the test user, or resetting shared home state.


## Implementation Plan

1. Add the session abstraction and env plumbing in `UserBox`/`sudo_run()`.
2. Refactor temp/package path creation so all test artifacts live under the session root.
3. Refactor `coppy_install()` so build + tool-install state is session-local.
4. Update sandbox tests and fixtures to assert against session-derived paths.
5. Add lightweight documentation for local usage, including how to set `COPPY_TEST_SESSION` when desired.
6. Add a safety guard for destructive prep/reinstall flows.


## Validation Plan

- Existing targeted tests after implementation:
  - `tests/coppy_tests/test_sandbox.py`
  - `tests/coppy_tests/test_template.py`
  - `tests/coppy_tests/test_coppy.py`
- Add at least one explicit concurrency smoke test/procedure:
  - start two pytest runs concurrently with different `COPPY_TEST_SESSION` values
  - ensure both can create sandboxes, create/generated packages, and install/use `coppy` without deleting or replacing each other's state
- Success criteria:
  - no shared-path collisions
  - no global cache clears affecting sibling runs
  - no tool reinstall cross-talk
  - no fixed-home assertions left in the sandboxed integration tests


## Scope Notes

- This spec is about concurrent local test sessions for this repo.
- It does not attempt to make destructive machine bootstrap (`test-user-prep --reinstall`) concurrent-safe.
- It also does not address two agents editing the same checkout at the same time; the focus here is test/runtime isolation.
