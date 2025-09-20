from collections.abc import Iterable, Iterator
from contextlib import contextmanager
import datetime as dt
from json import loads as json_loads
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap

from blazeutils import containers

from .logs import logger


log = logger()

src_dpath = tests_dpath = Path(__file__).parent.parent
pkg_dpath = src_dpath.parent


class LazyDict(containers.LazyDict):
    def __getattr__(self, attr):
        val = super().__getattr__(attr)
        if isinstance(val, dict) and not isinstance(val, LazyDict):
            return LazyDict(val)
        return val


class CalledProcessError(subprocess.CalledProcessError):
    @classmethod
    def from_cpe(cls, exc: subprocess.CalledProcessError):
        return cls(
            returncode=exc.returncode,
            cmd=exc.cmd,
            output=exc.output,
            stderr=exc.stderr,
        )

    def __str__(self):
        return super().__str__() + f'\nSTDOUT: {self.stdout}' + f'\nSTDERR: {self.stderr}'


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    json=False,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture or json)
    args = args + kwargs.pop('args', ())
    env = kwargs.pop('env', None)

    if env:
        kwargs['env'] = os.environ | env

    if capture:
        kwargs.setdefault('text', True)

    try:
        log.debug(f'Running: {" ".join(str(a) for a in args)}\nkwargs: {kwargs}')
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])

        if capture and result.stderr:
            log.debug('Captured STDERR', result.stderr)

        if json:
            return json_loads(result.stdout)

        return result
    except subprocess.CalledProcessError as e:
        if capture:
            raise CalledProcessError.from_cpe(e) from e
        raise
    except Exception as e:
        raise CalledProcessError('n/a', args, '', '') from e


def sudo_run(*args, sudo_user=None, env_path=None, **kwargs):
    user_args = ('-u', sudo_user, f'HOME=/home/{sudo_user}') if sudo_user else ()
    # Sudo only looks for bins in: $ sudo grep secure_path /etc/sudoers
    # If we want to adjust the path, then we need to use `env` to do it.
    env_args = ('env', f'PATH={env_path}') if env_path else ()
    return sub_run('sudo', *user_args, *env_args, args=args, **kwargs)


def systemctl(*args, machine_user=None, **kwargs):
    user_args = ()
    sudo_args = ()
    if machine_user is True:
        user_args = ('--user',)
    elif machine_user:
        user_args = ('--user', f'--machine={machine_user}@.host')
        sudo_args = ('sudo',)

    return sub_run(*sudo_args, 'systemctl', *user_args, *args, **kwargs)


def loginctl(*args, machine_user=None, **kwargs):
    user_args = ()
    if machine_user is True:
        user_args = ('--user',)
    elif machine_user:
        user_args = ('--user', f'--machine={machine_user}@.host')

    return sub_run('systemctl', *user_args, *args, **kwargs)


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


@contextmanager
def curl_download(url: str, dir_mode=None) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        if dir_mode:
            tmp_dir.chmod(dir_mode)
        dest = tmp_dir / 'downloaded.bin'
        sub_run(
            'curl',
            '--fail',  # fail on http status codes
            '--silent',
            '--show-error',  # show errors even though --silent
            '--location',  # follow redirects
            '--output',
            dest,
            url,
        )
        yield dest


def utc_now():
    return dt.datetime.now(dt.UTC)


def dd(s: str):
    """
    A visually minimal dedent function that strips the left most whitespace.  Designed to
    make it easy to indent text in source code and have the result not be indented.

        myvar = dd('''
            [some config]
            with-indenting = 'is helpful'
        ''')

    """
    return textwrap.dedent(s).lstrip()
