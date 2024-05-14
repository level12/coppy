import nox


@nox.session
def tests(session: nox.Session):
    session.install('-r', 'requirements/dev.in')
    session.run('pytest', 'tests.py')
