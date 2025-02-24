from os import environ
from pathlib import Path
import shutil
import tempfile

from coppy.utils import slug, sub_run


def has_lib64():
    usr_lib64 = Path('/usr/lib64')

    return usr_lib64.is_dir()


def has_merged_usr():
    _bin = Path('/bin')
    usr_bin = Path('/usr/bin')

    return _bin.resolve() == usr_bin


class Sandbox:
    """
    Use bubblewrap to run subprocesses in a sandboxed filesystem and environment.

    When testing mise and uv it ensures the developer's mise config(s) are not impacting the
    tests and that running mise/uv for the tests doesn't change the dev's system.
    """

    sb_home_dpath = Path('/home/picard')
    sb_home_bin_dpath = sb_home_dpath / 'bin'
    sb_proj_dpath = sb_home_dpath / 'project'

    def __init__(self, project_path: Path, mise_verbose=False):
        self.project_path = project_path

        # Ensure we have paths to the bins we use
        bwrap_bin = shutil.which('bwrap')
        self.mise_bin = shutil.which('mise')
        self.uv_bin = shutil.which('uv')

        assert bwrap_bin, f'bwrap bin not found: {environ["PATH"]}'
        assert self.mise_bin, f'mise bin not found: {environ["PATH"]}'
        assert self.uv_bin, f'uv bin not found: {environ["PATH"]}'

        self.base_args = [
            bwrap_bin,
            '--unshare-all',
            '--dev',
            '/dev',
            '--proc',
            '/proc',
            '--share-net',
        ]
        self.add_usr_args()
        self.add_etc_args()
        self.add_mise_args()

    def add_etc_args(self):
        """Get the arguments related to /etc"""
        self.base_args.extend(
            [
                # hosts
                '--ro-bind',
                '/etc/hosts',
                '/etc/hosts',
                # resolve.conf
                '--ro-bind',
                '/etc/resolv.conf',
                '/etc/resolv.conf',
                # ssl
                '--ro-bind',
                '/etc/ssl',
                '/etc/ssl',
            ],
        )

    def add_usr_args(self):
        """Get the arguments related to /usr"""
        self.base_args.extend(
            [
                '--ro-bind',
                '/usr',
                '/usr',
            ],
        )
        dirs = ['/bin', '/sbin', '/lib']

        if has_lib64():
            dirs.append('/lib64')

        if has_merged_usr():
            for dest in dirs:
                src = f'/usr{dest}'
                self.base_args.extend(['--symlink', src, dest])

        else:
            for dest in dirs:
                src = dest
                self.base_args.extend(['--ro-bind', src, dest])

    def add_mise_args(self):
        mise_bin = shutil.which('mise')
        self.base_args.extend(
            [
                '--ro-bind',
                mise_bin,
                mise_bin,
            ],
        )

    def run(self, *args, **kwargs):
        print('sandbox.run:', *args)
        args = (*self.base_args, *self.session_args, *args)
        env = self.session_env | kwargs.pop('env', {})
        return sub_run(args=args, env=env, **kwargs)

    def mise(self, *args, **kwargs):
        return self.run('mise', *args, **kwargs)

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

    def mise_config(self, host_fpath: Path):
        self.session_args.extend(
            (
                '--ro-bind',
                host_fpath,
                self.sb_home_dpath / '.config/mise/config.toml',
            ),
        )

    def uv(self, *args, **kwargs):
        return self.run('uv', *args, **kwargs)

    def home_overlays(self, *rel_paths):
        args = []
        for rel_path in rel_paths:
            path_slug = slug(rel_path)

            src_dpath: Path = Path.home() / rel_path
            src_dpath.mkdir(exist_ok=True)

            rw_dpath = self.sess_dpath / f'home-overlay-{path_slug}-rw'
            rw_dpath.mkdir()
            work_dpath = self.sess_dpath / f'home-overlay-{path_slug}-workdir'
            work_dpath.mkdir()

            args.extend(
                (
                    '--overlay-src',
                    src_dpath,
                    '--overlay',
                    rw_dpath,
                    work_dpath,
                    self.sb_home_dpath / rel_path,
                ),
            )
        return args

    def proj_rw_path(self, relpath: Path) -> Path:
        return self.proj_rw_dpath.joinpath(relpath)

    def __enter__(self):
        # Have to keep this around or it will get cleaned up when the method ends.
        self.sess_dir = tempfile.TemporaryDirectory()
        self.sess_dpath = Path(self.sess_dir.name)

        self.sess_home = self.sess_dpath / 'home'
        self.sess_user = self.sess_home / 'picard'
        user_bin_dpath = self.sess_home / 'picard/bin'
        user_bin_dpath.mkdir(parents=True)

        self.sess_tmp = self.sess_dpath / 'tmp'
        self.sess_tmp.mkdir()

        self.proj_rw_dpath = self.sess_dpath / 'proj-overlay-rw'
        self.proj_rw_dpath.mkdir()
        proj_work_dpath = self.sess_dpath / 'proj-overlay-work'
        proj_work_dpath.mkdir()

        self.session_args = [
            # /home
            '--bind',
            self.sess_home,
            '/home',
            # /home/picard/bin/mise
            '--ro-bind',
            shutil.which('mise'),
            self.sb_home_bin_dpath / 'mise',
            # /home/picard/bin/uv
            '--ro-bind',
            shutil.which('uv'),
            self.sb_home_bin_dpath / 'uv',
            # /home/picard/project
            '--overlay-src',
            self.project_path,
            '--overlay',
            self.proj_rw_dpath,
            proj_work_dpath,
            self.sb_proj_dpath,
            # chdir
            '--chdir',
            self.sb_proj_dpath,
            # /tmp
            '--bind',
            self.sess_tmp,
            '/tmp',
            *self.home_overlays(
                '.local/share/mise',
                '.local/share/uv',
                '.cache/uv',
            ),
        ]

        self.session_env = {
            'PATH': '/home/picard/bin:/home/picard/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',  # noqa
            'SHELL': '/bin/bash',
            'TERM': 'dumb',
            'USER': 'picard',
            'HOME': self.sb_home_dpath,
            'LOGNAME': 'picard',
            'LANG': environ['LANG'],
            'RUST_BACKTRACE': '1',
            # Hardlinks don't work inside the sandbox, presumably due to overlays & mounting.
            'UV_LINK_MODE': 'copy',
        }

        self.mise('trust')
        self.uv('python', 'install')
        self.mise('sync', 'python', '--uv')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sess_dir.cleanup()
        self.sess_home = None
        self.ses_tmp = None
        self.session_args = []
