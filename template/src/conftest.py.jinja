import warnings


# Filters for warnings that are triggered during import go at the top level.  Filters for warnings
# thrown during test runs goes in pytest_configure() below.

# Any errors not noted here should cause pytest to throw an error. It seems like this should be
# last in the list, but warnings that match multiple lines will apply the last line matched.
warnings.filterwarnings('error')
# Examples:
# warnings.filterwarnings(
#     'ignore',
#     "'cgi' is deprecated and slated for removal in Python 3.13",
#     category=DeprecationWarning,
#     module='webob.compat',
# )
# warnings.filterwarnings(
#     'ignore',
#     "'crypt' is deprecated and slated for removal in Python 3.13",
#     category=DeprecationWarning,
#     module='passlib.utils',
# )


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
    # Example:
    # config.addinivalue_line(
    #     'filterwarnings',
    #     # Note the lines that follow are implicitly concatinated, no "," at the end
    #     "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this will be"
    #     ' mandatory in wtforms 3.2'
    #     ':DeprecationWarning'
    #     ':wtforms.meta',
    # )
