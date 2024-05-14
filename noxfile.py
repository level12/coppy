import nox


nox.options.default_venv_backend = 'uv'


@nox.session
def tests(session: nox.Session):
    session.install('-r', 'requirements/dev.txt')
    session.run('pytest', 'tests.py')
