#!/usr/bin/env python3
"""
#MISE hide=true

PURPOSE - this script, in combination with mise.toml, facilitates:

- Sync mise Python installs with uv Python installs so mise uses the same Python install as uv
  (not just the same version).
- Provides for a centralized venv instead of `./venv`
    - Used automatically if `~/.cache/uv-venvs/` exists

RUN CONTEXT:

- This script runs with the system python without a venv.  So nothing but stdlib available.
- It's not intended to be ran with `mise run`.  It's ran by mise.toml's exec()s.


LOGGING:

- Logs will show up in /tmp: `tail /tmp/*-mise-uv-init.log`
- Logs may not show up as expected due to caching.  In which case, see next item.


MISE CACHING:

- Mise is configured to cache values from this script for an hour
- This is for performance reasons assuming a mise shell integration
- Can be cleared with: `mise cache clear`

"""

import datetime as dt
import functools
from os import environ
from pathlib import Path
import re
import subprocess
import sys
import tempfile


class paths:
    project = Path(__file__).parent.parent
    venv_cache = Path.home() / '.cache' / 'uv-venvs'

    @classmethod
    @functools.cache
    def project_slug(cls) -> str:
        return slugify(cls.project.name)

    @classmethod
    @functools.cache
    def log(cls):
        return Path(tempfile.gettempdir()) / f'{cls.project_slug()}-mise-uv-init.log'

    @classmethod
    @functools.cache
    def project_venv(cls):
        if cls.venv_cache.exists():
            return cls.venv_cache / cls.project_slug()

        return cls.project / '.venv'


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]+', '-', text)  # replace non-alphanum (except dashes) with dash
    text = re.sub(r'-{2,}', '-', text)  # replace multiple dashes with one
    return text.strip('-')


def print_log(*args, **kwargs):
    with paths.log().open('a') as fo:
        print(*args, file=fo, **kwargs)


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    print_log(*args, **kwargs)


def sub_run(*args, env=None) -> str:
    if env:
        env = environ | env

    try:
        result = subprocess.run(args, check=True, text=True, capture_output=True, env=env)
        if result.stderr:
            print_err(args, '\n', result.stderr)
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print_err(args, '\n', e.stderr)
        raise

    return result.stdout.strip()


def main():
    print_log(dt.datetime.now(), 'proj-venv:', paths.project_venv())

    # Sync mise & uv Python versions so that neither tool spends time downlaoding/installing the
    # same version that's already present locally.
    sub_run('mise', '--no-config', 'sync', 'python', '--uv')

    print(paths.project_venv().as_posix(), end='')


if __name__ == '__main__':
    main(*sys.argv[1:])
