# import warnings


# # Filters for warnings that are triggered during import go at the top level.  Filters for warnings
# # thrown during test runs goes in pytest_configure() below.

# # Any errors not noted here should cause pytest to throw an error. It seems like this should be
# # last in the list, but warnings that match multiple lines will apply the last line matched.
# warnings.filterwarnings('error')
# # Examples:
# warnings.filterwarnings(
#     'ignore',
#     'Dirty template changes.*',
#     module='copier.errors',
# )


# # warnings.filterwarnings(
# #     'ignore',
# #     "'crypt' is deprecated and slated for removal in Python 3.13",
# #     category=DeprecationWarning,
# #     module='passlib.utils',
# # )


import pytest

from coppy.utils import sub_run


def pytest_configure(config):
    """
    At some point during testing, pytest does something to the warnings module which clears out
    any previously setup filters, like the one set above, and creates its own filters from
    the config.

    The pytest warnings docs say that any previously setup filters should be respected but that's
    not the observed behavior.
    """
    # Comment above explains why error comes first and not last.
    config.addinivalue_line('filterwarnings', 'error')
    config.addinivalue_line(
        'filterwarnings',
        'ignore:.*',
    )


@pytest.fixture(autouse=True, scope='session')
def build_docker():
    # Normally, no files change and the build should take less than a second to run due to docker
    # layer caching.  If it starts taking longer than that, something has probably changed in the
    # Dockerfile.  There is a comment there with further details.
    sub_run('mise', 'docker-build')
