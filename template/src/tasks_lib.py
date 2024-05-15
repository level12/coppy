import subprocess


def sub_run(*args, capture=False, **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', True)
    kwargs.setdefault('capture_output', capture)
    args = kwargs.pop('args', args)
    return subprocess.run(args, **kwargs)
