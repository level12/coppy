# Spec: Template Mise/UV Alignment


## Summary

- Mirror coppy's new `mise`/`uv`/Python setup in generated template projects.
- Standardize the template on `.python-version` as the project's Python version source of
  truth.
- Align template validation with the new `mise.toml` contract.


## Scope

- `template/mise.toml`
- `template/pyproject.toml.jinja`
- New `template/.python-version.jinja`
- `copier.yaml`
- `template/tasks/mise-uv-init.py`
- Template verification in `tests/coppy_tests/test_template.py`
- Sandbox verification in `tests/coppy_tests/test_sandbox.py`
- Changelog.d file for this spec


## Findings

- The latest commit moved coppy itself to a version-file-driven Python setup, but this
  spec should standardize template output on `.python-version`, not `.python-versions`.
- Coppy `mise.toml` now:
    - gets `UV_PROJECT_ENVIRONMENT` from `tasks/mise-uv-init.py` with no subcommand
    - sets `_.python.venv.create = true`
    - sets `UV_PYTHON` to the venv's `bin/python`
    - runs `uv sync` from a `[hooks].enter` hook
    - enables `idiomatic_version_file_enable_tools = ["python"]`
- The same commit already simplified `template/tasks/mise-uv-init.py` to the new
  no-argument contract.
- There are staged template changes in `template/tasks/mise-uv-init.py` to make
  centralized venv names include a short hash and support `COPPY_VENV_HASH_LEN`.
- `template/mise.toml` still uses the old contract:
    - `tasks/mise-uv-init.py proj-env`
    - `[tools].python = tasks/mise-uv-init.py py-ver`
- `copier.yaml` already has a `python_version` answer, so the template can render a
  version file directly.
- The template currently derives `requires-python` only from `python_version` via
  `~={{ python_version }}.0`.
- `gh-actions/uv-prep/action.yaml` already prefers `.python-version` or
  `.python-versions`, so standardizing on `.python-version` requires no CI action change.
- Template generation tests use `copier.run_copy(..., vcs_ref='HEAD')`, so
  generated-output assertions must be validated from a committed implementation.


## Decisions

- Generated projects will use `.python-version`; the earlier `.python-versions` plan was
  based on a misunderstanding and is superseded.
- Add a new Copier answer, `python_version_min`, defaulting to `python_version`.
- `requires-python` will remain `~={{ python_version }}.0` when
  `python_version_min == python_version`.
- If `python_version_min != python_version`, `requires-python` will render as
  `>={{ python_version_min }}`.
- `template/mise.toml` will mirror the new coppy root behavior instead of deriving Python
  via `[tools].python`.
- `template/tasks/mise-uv-init.py` will remain on the new no-argument contract introduced
  in the precursor commit.
- The staged `template/tasks/mise-uv-init.py` venv-hash changes are part of this spec and
  must be reflected in the changelog entry.
- Validation will focus on generated project behavior and sandbox behavior, not duplicate
  coppy-root-only checks.


## Implementation Plan

1. Add `python_version_min` to `copier.yaml`, defaulting to `python_version`.
2. Update `template/pyproject.toml.jinja` so `requires-python` renders:
    - `~={{ python_version }}.0` when `python_version_min == python_version`
    - `>={{ python_version_min }}` when they differ
3. Add `template/.python-version.jinja` with `{{ python_version }}`.
4. Update `template/mise.toml` to:
    - call `tasks/mise-uv-init.py` without subcommands
    - set `_.python.venv.create = true`
    - set `UV_PYTHON = "{{ env.UV_PROJECT_ENVIRONMENT }}/bin/python"`
    - add `[hooks] enter = "uv sync"`
    - add `[settings] idiomatic_version_file_enable_tools = ["python"]`
    - remove `[tools].python`
5. Carry forward the staged `template/tasks/mise-uv-init.py` change that appends a short
   hash to centralized venv names and supports `COPPY_VENV_HASH_LEN`.
6. Update template tests to cover both `requires-python` render paths and assert generated
   projects include `.python-version` with the chosen Python version.
7. Update sandbox assertions to verify `UV_PYTHON` points at the same interpreter as the
   active venv, with expectations updated for hashed centralized venv names where
   applicable.
8. Add a changelog entry covering both the `.python-version` standardization and the
   `mise-uv-init.py` venv-hash behavior.


## Validation Plan

- Validate generated template output in `tests/coppy_tests/test_template.py`.
- Validate both `requires-python` render modes in generated output.
- Validate sandboxed `mise`/`uv`/venv behavior in `tests/coppy_tests/test_sandbox.py`.
- Confirm centralized-venv behavior still matches `UV_PROJECT_ENVIRONMENT` expectations,
  including the hashed-name variant.


## Out of Scope

- Further changes to coppy root config; that precursor work is already committed.
- Documentation updates unless implementation reveals a mismatch in generated-project
  setup guidance.
