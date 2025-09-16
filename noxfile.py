from pathlib import Path

import nox


package_path = Path.cwd()
nox.options.default_venv_backend = 'uv'


def uv_sync(session, group: str):
    session.run('uv', 'sync', '--active', '--frozen', '--only-group', group)


@nox.session
def tests(session: nox.Session):
    uv_sync(session, 'tests')
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
    uv_sync(session, 'pre-commit')
    session.run(
        'pre-commit',
        'run',
        '--all-files',
    )
