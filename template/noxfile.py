from os import environ
from pathlib import Path

import nox


package_path = Path(__file__).parent
is_circleci = 'CIRCLECI' in environ

nox.options.default_venv_backend = 'uv'


@nox.session
def pytest(session: nox.Session):
    uv_sync(session)
    pytest_run(session)


@nox.session
def precommit(session: nox.Session):
    uv_sync(session, 'pre-commit')
    session.run(
        'pre-commit',
        'run',
        '--all-files',
    )


@nox.session
def audit(session: nox.Session):
    # Much faster to install the deps first and have pip-audit run against the venv
    uv_sync(session)
    session.run(
        'pip-audit',
        '--desc',
        '--skip-editable',
    )


def pytest_run(session: nox.Session, *args, **env):
    """
    Using functions for pytest and uv enables more advanced uses cases.  Examples:

    py_all = ['3.10', '3.11', '3.12', '3.13']

    @session(py=py_all)
    @parametrize('db', ['pg', 'sqlite'])
    def pytest(session: Session, db: str):
        uv_sync(session)
        pytest_run(session, WEBTEST_DB=db)


    @session(py=py_single)
    def pytest_mssql(session: Session):
        uv_sync(session, 'pytest', 'mssql')
        pytest_run(session, WEBTEST_DB='mssql')


    @session(py=py_single)
    def pytest_i18n(session: Session):
        uv_sync(session, extra='i18n')
        pytest_run(session, WEBTEST_DB='sqlite')

    """
    # CircleCI will give additional info in the UI about tests if junit-xml is output.
    junit_opt = f'--junit-xml={package_path}/ci/test-reports/{session.name}.pytests.xml'
    junit_args = (junit_opt,) if is_circleci else ()

    session.run(
        'pytest',
        '-ra',
        '--tb=native',
        '--strict-markers',
        '--cov',
        '--cov-report=xml',
        '--no-cov-on-fail',
        *junit_args,
        package_path / 'tests',
        *args,
        *session.posargs,
        env=env,
    )


def uv_sync(session: nox.Session, *groups, project=False, extra=None):
    # If no group given, assume group shares name of session.
    if not groups:
        groups = (session.name,)

    # At least pytest needs the project installed.
    project_args = () if project or session.name.startswith('pytest') else ('--no-install-project',)

    group_args = [arg for group in groups for arg in ('--group', group)]
    extra_args = ('--extra', extra) if extra else ()

    run_args = (
        'uv',
        'sync',
        '--active',
        '--frozen',
        '--exact',
        # Use --no-default-groups instead of --only-group as the latter implies
        # --no-install-project.
        '--no-default-groups',
        *project_args,
        *group_args,
        *extra_args,
    )
    session.run(*run_args)
