from contextlib import contextmanager
import os
from unittest import mock


@contextmanager
def environ(**kwargs):
    with mock.patch.dict(os.environ, **kwargs):
        yield


def patch_obj(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch.object(*args, **kwargs)


def patch(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch(*args, **kwargs)
