Modify the uv/mise/Python integration.

- Standardize on `.python-version` for Python version selection.
    - It works for mise, uv, and GitHub's `setup-python` action.
    - If a project removes it, mise and uv will stay synced due to mise's `UV_PYTHON` setup.
- mise
    - Is again responsible for venv creation. It will tell uv to use the version from
      `.python-version` when creating the venv.
    - Sets `UV_PYTHON` to the mise-managed venv `/bin` so uv always uses the venv mise created.
      This works for in-repo and centralized venvs.
    - Gets its Python tool spec from `.python-version`.
    - Uses an `enter` hook to run `uv sync`
- Add a `python_version_min` Copier template setting so the `pyproject.toml` Python spec can be
  different from the interpreter version used for local development.
    - This is useful for library projects that want to test on a given version but may support
      older or newer versions.
    - Applications should keep `python_version_min = python_version`.
- `mise-uv-init.py`
    - Simplify it by removing code for work that mise now does.
    - For centralized venvs, add a hash to the venv name to avoid collisions.
    - Customize the number of hash characters with `COPPY_VENV_HASH_LEN`.
