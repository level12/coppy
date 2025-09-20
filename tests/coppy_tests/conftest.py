import pytest

from coppy_tests.libs.click import CLIRunner
from coppy_tests.libs.sandbox import UserBox


@pytest.fixture(scope='session')
def coppy_install():
    return UserBox().coppy_install()


@pytest.fixture(scope='session')
def cli():
    return CLIRunner()
