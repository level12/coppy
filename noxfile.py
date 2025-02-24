from pathlib import Path

import nox


package_path = Path.cwd()
nox.options.default_venv_backend = 'uv'


@nox.session
def tests(session: nox.Session):
    session.run('uv', 'sync', '--active', '--no-dev', '--group', 'tests')
    session.run(
        'pytest',
        '-ra',
        '--tb=native',
        '--strict-markers',
        f'--junit-xml={package_path}/ci/test-reports/{session.name}.pytests.xml',
        *session.posargs,
    )


@nox.session
def standards(session: nox.Session):
    session.run('uv', 'sync', '--active', '--only-group', 'pre-commit')
    session.run(
        'pre-commit',
        'run',
        '--all-files',
    )
