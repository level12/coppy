from contextlib import contextmanager
from pathlib import Path
import shutil

from coppy.utils import sub_run, sudo_run
from coppy.version import VERSION

from .os_prep import User
from .paths import dirs, tmp_dir


class UserBox:
    """
    Use a dedicated Linux user to isolate the test project from the current user's mise and uv
    setup.
    """

    # TODO: if needed, we could get this from the environment so a dev could use a different user
    # by setting it in mise.local.toml.
    username = 'coppy-tests'

    user = User(username)
    home_dpath = user.home_dir()
    tmp_dpath = home_dpath / 'tmp'
    local_bin_dpath = home_dpath / '.local/bin'
    sudo_PATH = f'{local_bin_dpath}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    pytest_tmppath = tmp_dir(tmp_dpath, 'pytest-run')

    def __init__(
        self,
        cwd: Path | None = None,
    ):
        self.cwd = cwd or self.home_dpath

    def exec(self, *args, **kwargs):
        kwargs.setdefault('cwd', self.cwd)
        return sudo_run(*args, sudo_user=self.username, env_path=self.sudo_PATH, **kwargs)

    def exec_stdout(self, *args, **kwargs) -> str:
        result = self.exec(*args, capture=True, **kwargs)
        return result.stdout.strip()

    def uv(self, *args, **kwargs):
        return self.exec(self.local_bin_dpath / 'uv', *args, **kwargs)

    def uv_run(self, *args, **kwargs):
        result = self.uv('run', '--', *args, **kwargs, capture=True)
        return result.stdout.strip()

    def uv_python(self, *args, **kwargs):
        return self.uv_run('python', '-c', *args, **kwargs)

    def mise(self, *args, **kwargs):
        return self.exec(self.local_bin_dpath / 'mise', *args, **kwargs)

    def mise_exec(self, *args, stderr=False, **kwargs):
        args = ('exec', '--', *args)
        result = self.mise(*args, capture=True, **kwargs)
        return (result.stderr if stderr else result.stdout).strip()

    def mise_env(self, *var_names):
        result = self.mise_exec(
            'printenv',
            *var_names,
            returns=(0, 1),
        )
        return result.splitlines()

    def __enter__(self):
        self.mise('trust')

        # Help keep tests from interfering with each other
        self.mise('--no-config', 'cache', 'clear')

        # uv_venv_auto detects projects by their uv.lock, so perform the same initial sync required
        # by the generated project's setup instructions before asking mise to activate the venv.
        self.uv('sync')

        # Mise exec should now read mise.toml and activate the uv-managed virtualenv.
        self.mise_exec('echo')

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def coppy_install(self) -> Path:
        version = VERSION
        sub_run('uv', 'build', '--wheel', '--out-dir', dirs.dist)
        wheel_name = f'coppy-{version}-py3-none-any.whl'
        wheel_fpath = dirs.dist / wheel_name

        sub_run('cp', wheel_fpath, self.tmp_dpath)

        user_wheel_fpath = self.tmp_dpath / wheel_name
        self.uv(
            'tool',
            'install',
            user_wheel_fpath,
            '--reinstall',
        )

    @contextmanager
    def place(self, src_fpath: Path, dest_fpath: str):
        if dest_fpath.startswith('~/'):
            dest_fpath: Path = self.home_dpath / dest_fpath.replace('~/', '', 1)
        else:
            dest_fpath: Path = Path(dest_fpath)
            assert dest_fpath.is_absolute()

        bak_fpath = Path(str(dest_fpath) + '~')

        # Move existing file to backup path
        if dest_fpath.exists():
            dest_fpath.replace(bak_fpath)
        else:
            dest_fpath.parent.mkdir(exist_ok=True, parents=True)

        # Copy source file to destination (that was just backed up)
        shutil.copy(src_fpath, dest_fpath)

        yield

        dest_fpath.unlink()

        # Restore the original
        if bak_fpath.exists():
            bak_fpath.replace(dest_fpath)
            bak_fpath.unlink()
