Modify the uv/mise/Python integration.

- Standardize on `.python-version` for Python version selection.
    - It works for mise, uv, and GitHub's `setup-python` action.
- mise
    - Uses `python.uv_venv_auto = "create|source"` to create and activate uv's project environment.
    - Gets its Python tool spec from `.python-version`.
    - Uses an `enter` hook to run `uv sync`
- Add a `python_version_min` Copier template setting so the `pyproject.toml` Python spec can be
  different from the interpreter version used for local development.
    - This is useful for library projects that want to test on a given version but may support
      older or newer versions.
    - Applications should keep `python_version_min = python_version`.
- Remove the custom `mise-uv-init.py` task and its `UV_PROJECT_ENVIRONMENT` and `UV_PYTHON`
  overrides.
- Centralized environments are now an optional developer-level uv setting rather than project
  configuration.
