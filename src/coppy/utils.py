from collections.abc import Iterable
from json import loads as json_loads
from pathlib import Path
import re
import subprocess

from blazeutils import containers


src_dpath = tests_dpath = Path(__file__).parent.parent
pkg_dpath = src_dpath.parent


class LazyDict(containers.LazyDict):
    def __getattr__(self, attr):
        val = super().__getattr__(attr)
        if isinstance(val, dict) and not isinstance(val, LazyDict):
            return LazyDict(val)
        return val


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    json: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture or json)
    args = args + kwargs.pop('args', ())

    if capture:
        kwargs.setdefault('text', True)

    try:
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])

        if json:
            return json_loads(result.stdout)

        if capture and result.stderr:
            print('STDERR', result.stderr)

        return result
    except subprocess.CalledProcessError as e:
        if capture:
            print('STDOUT:', e.stdout)
            print('STDERR:', e.stderr)
        raise


slug_re_keep = re.compile(r'[^\/a-zA-Z0-9_ \\-]')
slug_re_replace = re.compile(r'[\/ \\_]+')


def slug(s, length=None, replace_with='-'):
    # $slug = str_replace("&", "and", $string);
    # only keep alphanumeric characters, underscores, dashes, and spaces
    s = slug_re_keep.sub('', s)
    # replace forward slash, back slash, underscores, and spaces with dashes
    s = slug_re_replace.sub(replace_with, s)
    # make it lowercase
    s = s.lower()
    if length is not None:
        return s[: length - 1].rstrip(replace_with)

    return s
