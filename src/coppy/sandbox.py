from contextlib import contextmanager
from pathlib import Path

from coppy.utils import sub_run


class Container:
    c_image = 'copierpy-tests'
    c_name = 'copierpy-tests'
    c_home_dpath = Path('/home/ubuntu')
    c_home_bin_dpath = c_home_dpath / 'bin'
    c_proj_dpath = c_home_dpath / 'project'

    def __init__(self, proj_dpath: Path, bash_on_enter: bool = False, mise_verbose=False):
        self.host_proj_dpath = proj_dpath
        self.break_on_enter = bash_on_enter

    def docker(self, *args, **kwargs):
        return sub_run('docker', *args, **kwargs)

    def exec(self, *args, **kwargs):
        is_bash = args == ('bash',)
        it_args = ('-it',) if is_bash else ()
        return self.docker('exec', *it_args, self.c_name, *args, **kwargs)

    def mise(self, *args, **kwargs):
        return self.exec('mise', *args, **kwargs)

    def mise_exec(self, *args, **kwargs):
        args = ('exec', '--', *args)
        return self.mise(*args, **kwargs)

    def mise_env(self, *var_names):
        result = self.mise_exec(
            'printenv',
            *var_names,
            capture=True,
            returns=(0, 1),
        )
        return result.stdout.strip().splitlines()

    @contextmanager
    def place(self, host_fpath: Path, c_fpath: str):
        if c_fpath.startswith('~'):
            c_fpath = c_fpath.replace('~', '/home/ubuntu', 1)
        self.docker('cp', host_fpath, f'{self.c_name}:{c_fpath}')
        yield
        self.exec('rm', c_fpath)

    def uv(self, *args, **kwargs):
        return self.exec('uv', *args, **kwargs)

    def proj_vol_args(self):
        """This can be used to mount the project read-only."""
        args = []
        for path in self.host_proj_dpath.iterdir():
            if path.name == '.venv':
                continue
            args.extend(
                ('--volume', f'{path}:{self.c_proj_dpath / path.name}:ro'),
            )
        return args

    def docker_rm(self):
        result = self.docker(
            'ps',
            '--all',
            '--quiet',
            '--filter',
            f'name={self.c_name}',
            capture=True,
        )
        if result.stdout.strip():
            self.docker('rm', '--force', self.c_name, capture=True)

    def path_exists(self, path: str):
        path = path if Path(path).is_absolute() else self.c_proj_dpath / path
        result = self.exec('ls', path, returns=(0, 2), capture=True)
        return result.returncode == 0

    def __enter__(self):
        self.docker_rm()

        self.docker(
            'run',
            '--detach',
            '--name',
            self.c_name,
            # *self.proj_vol_args(),
            '--volume',
            f'{self.host_proj_dpath}:{self.c_proj_dpath}',
            '--workdir',
            self.c_proj_dpath,
            self.c_image,
            'infinity',
            capture=True,
        )

        if self.break_on_enter:
            self.exec('bash')

        self.mise('trust')
        self.uv('python', 'install')
        self.mise('sync', 'python', '--uv')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.docker_rm()
