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
        *pip_audit_ignore_args(),
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


def pip_audit_ignore_args() -> list | tuple:
    ignore_fpath = package_path / 'pip-audit-ignore.txt'

    if not ignore_fpath.exists():
        return ()

    vuln_ids = [
        line for line in ignore_fpath.read_text().strip().splitlines() if not line.startswith('#')
    ]

    return [arg for vuln_id in vuln_ids for arg in ('--ignore-vuln', vuln_id)]
