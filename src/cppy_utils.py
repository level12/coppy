import base64
from collections.abc import Iterable
import copy
import os
from os import environ
import subprocess
import zlib

import msgpack


def reverse_mise_env(original_env):
    """Reverses the changes mise has made to the environment."""

    env = copy.deepcopy(original_env)  # Clone the environment

    mise_diff_encoded = env.get('__MISE_DIFF')
    if not mise_diff_encoded:
        return env  # No changes detected, return unchanged environment

    # Decode Base64 (handling missing padding)
    compressed_data = base64.b64decode(mise_diff_encoded + '==')

    # Decompress using Zlib
    decompressed_data = zlib.decompress(compressed_data)

    # Deserialize MessagePack data
    mise_diff = msgpack.unpackb(decompressed_data, raw=False)

    # Restore old environment variables
    for key, old_value in mise_diff.get('old', {}).items():
        env[key] = old_value  # Revert to original value

    # Remove new environment variables added by mise
    for key in mise_diff.get('new', {}):
        if key not in mise_diff.get('old', {}):  # Only remove if not previously existing
            env.pop(key, None)

    # Restore PATH by removing added paths
    if 'PATH' in env and mise_diff.get('path'):
        original_paths = env['PATH'].split(os.pathsep)
        paths_to_remove = set(mise_diff['path'])
        env['PATH'] = os.pathsep.join(p for p in original_paths if p not in paths_to_remove)

    # Remove mise tracking variables
    env.pop('__MISE_DIFF', None)
    env.pop('__MISE_SESSION', None)
    env.pop('__MISE_ORIG_PATH', None)

    return env


def min_env(**kwargs):
    return {
        'PATH': environ.get('__MISE_ORIG_PATH', environ['PATH']),
        'SHELL': '/bin/sh',
        'TERM': 'dumb',
        'USER': environ['USER'],
        'LOGNAME': environ['LOGNAME'],
        'LANG': environ['LANG'],
    }


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture)
    args = args + kwargs.pop('args', ())
    env = kwargs.pop('env', None)
    _min_env = kwargs.pop('min_env', None)

    if _min_env:
        kwargs['env'] = min_env(**_min_env)
    elif env:
        kwargs['env'] = environ | env

    if capture:
        kwargs.setdefault('text', True)

    try:
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            print(e.stderr)
        raise
