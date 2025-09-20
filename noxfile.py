from pathlib import Path

import nox


package_path = Path.cwd()
nox.options.default_venv_backend = 'uv'


@nox.session
def pytest(session: nox.Session):
    uv_sync(session)
    # TODO: no coverage because the far majority of the code in this project is just for testing.
    # But it wouldn't hurt to add it.
    session.run(
        'pytest',
        '-ra',
        '--tb=native',
        '--strict-markers',
        'tests',
        *session.posargs,
    )


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
        '--no-default-groups',
        *project_args,
        *group_args,
        *extra_args,
    )
    session.run(*run_args)
