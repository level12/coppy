import nox


# NOTE: uv is much faster at creating venvs and generally compatible with pip.
# Pip compat: https://github.com/astral-sh/uv/blob/main/PIP_COMPATIBILITY.md
nox.options.default_venv_backend = 'uv'


@nox.session
def tests(session: nox.Session):
    session.install('-r', 'requirements/base.txt')
    session.run('pytest')
