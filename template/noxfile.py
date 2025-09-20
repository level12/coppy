from pathlib import Path

import nox


package_path = Path(__file__).parent
nox.options.default_venv_backend = 'uv'


@nox.session
def pytest(session: nox.Session):
    uv_sync(session, 'pytest')
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
    uv_sync(session, 'audit')
    session.run(
        'pip-audit',
        '--desc',
        '--skip-editable',
    )


def uv_sync(session: nox.Session, *groups, project=False, extra=None):
    if not groups:
        groups = (session.name,)
    project_args = () if project or session.name.startswith('pytest') else ('--no-install-project',)
    group_args = [arg for group in groups for arg in ('--group', group)]
    extra_args = ('--extra', extra) if extra else ()
    run_args = (
        'uv',
        'sync',
        '--active',
        '--no-default-groups',
        *project_args,
        *group_args,
        *extra_args,
    )
    session.run(*run_args)


def pytest_run(session: nox.Session, *args, **env):
    session.run(
        'pytest',
        '-ra',
        '--tb=native',
        '--strict-markers',
        '--cov',
        '--cov-config=.coveragerc',
        f'--junit-xml={package_path}/ci/test-reports/{session.name}.pytests.xml',
        f'--cov-report=xml:{package_path}/ci/coverage/{session.name}.xml',
        '--no-cov-on-fail',
        package_path / 'tests',
        *args,
        *session.posargs,
        env=env,
    )
