import subprocess


def sub_run(*args, **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', True)
    args = kwargs.pop('args', args)
    return subprocess.run(args, **kwargs)
