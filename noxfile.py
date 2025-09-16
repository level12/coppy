from pathlib import Path

import nox


package_path = Path.cwd()
nox.options.default_venv_backend = 'uv'


def uv_sync(session, group: str, project: bool = False):
    # NOTE: not sure why, but sys.path doesn't get correctly configured to include the coppy pkg's
    # `src` directory when using '--only-group'.  But, in a templated generated app, like the
    # coppy demo, '--only-group' works just fine.  I spent some time trying to debug but am punting
    # for now since the problem/solution seem convoluted to me.
    groups_args = ('--no-default-groups', '--group') if project else ('--only-group',)
    session.run('uv', 'sync', '--active', '--frozen', *groups_args, group)


@nox.session
def tests(session: nox.Session):
    uv_sync(session, 'tests', project=True)
    session.run(
        'pytest',
        '-ra',
        '--tb=native',
        '--strict-markers',
        f'--junit-xml={package_path}/ci/test-reports/{session.name}.pytests.xml',
        'src/tests',
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
