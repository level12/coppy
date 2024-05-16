from pathlib import Path

import nox


package_path = Path.cwd()

# NOTE: uv is much faster at creating venvs and generally compatible with pip.
# Pip compat: https://github.com/astral-sh/uv/blob/main/PIP_COMPATIBILITY.md
nox.options.default_venv_backend = 'uv'


@nox.session
def tests(session: nox.Session):
    session.install('-r', 'requirements/base.txt')
    session.run(
        'pytest',
        # use our pytest.ini for warning management
        '-c=ci/pytest.ini',
        '-ra',
        '--tb=native',
        '--strict-markers',
        '--cov={{py_module}}',
        '--cov-config .coveragerc',
        '--cov-report xml',
        '--no-cov-on-fail',
        f'--junit-xml={package_path}/ci/test-reports/{session.name}.pytests.xml',
        'src',
    )
