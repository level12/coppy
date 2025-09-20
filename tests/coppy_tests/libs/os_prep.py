from __future__ import annotations

import contextlib
from dataclasses import dataclass
from functools import partial
import getpass
import grp
import logging
from pathlib import Path
import pwd
import tempfile

from coppy import utils

from .paths import dirs


USERDEL_MISSING_MSG = 'does not exist'

log = logging.getLogger(__name__)


class UserError(Exception):
    pass


@dataclass
class Group:
    name: str
    id: int
    members: list[str]

    @classmethod
    def all(cls) -> Group:
        g: grp.struct_group  # noqa: F842
        return [cls(g.gr_name, g.gr_gid, g.gr_mem) for g in grp.getgrall()]

    @classmethod
    def all_names(cls) -> set:
        return {g.gr_name for g in grp.getgrall()}


@dataclass
class User:
    name: str
    is_current: bool = False
    _info: pwd.struct_passwd | None = None
    _groups: set[str] | None = None

    def __post_init__(self):
        self.is_current = getpass.getuser() == self.name

    @property
    def info(self) -> pwd.struct_passwd:
        if not self._info:
            with contextlib.suppress(KeyError):
                self._info = pwd.getpwnam(self.name)

        return self._info

    @property
    def uid(self):
        if not self.info:
            return None

        return self.info.pw_uid

    @property
    def gid(self):
        if not self.info:
            return None

        return self.info.pw_gid

    @property
    def is_system(self):
        if not self.info:
            return None

        return self.uid < 1000

    @property
    def is_incus_admin(self):
        return 'incus-admin' in self.groups()

    def exists(self, refresh=False):
        if refresh:
            self._info = None

        return bool(self.info)

    def ensure(self):
        if not self.exists():
            group_args = ()
            if self.name in Group.all_names():
                group_args = ('-g', self.name)

            log.info(f'Creating user: {self.name}')
            utils.sudo_run(
                'useradd',
                '--system',
                '--create-home',
                '--shell=/bin/bash',
                *group_args,
                self.name,
            )
            log.info(f'User created: {self.name}')
            return

        log.info(f'User existed: {self.name}')

    def delete(self):
        assert not self.is_current
        # No current use case to delete users without juke prefix.  If that changes, add force arg.
        assert self.name.startswith('juke')

        result = utils.sudo_run('userdel', '-r', self.name, check=False, capture=True)

        if result.returncode == 0:
            log.info(f'Deleted: User({self.name})')
            return True

        if USERDEL_MISSING_MSG not in result.stderr:
            raise UserError(f'userdel of "{self.name}" failed: {result.stderr}')

        log.info(f"Delete: User({self.name}) didn't exist")

    def groups(self) -> set[str]:
        if self._groups is not None:
            return self._groups

        if not self.exists():
            return set()

        self._groups = {g.name for g in Group.all() if self.name in g.members or g.id == self.gid}

        return self._groups

    @classmethod
    def current(cls):
        return cls(getpass.getuser())

    @classmethod
    def with_prefix(cls, prefix):
        return [
            User(user_info.pw_name)
            for user_info in pwd.getpwall()
            if user_info.pw_name.startswith(prefix)
        ]

    def home_dir(self) -> Path:
        return Path(f'~{self.name}').expanduser()


def sudoers_write(fname: str, content: str):
    """Validate sudoers content using visudo"""
    sudoers_fpath = Path('/etc/sudoers.d') / fname
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sudoers') as temp_file:
        Path(temp_file.name).write_text(content)

        # Use visudo to check the syntax.  Exception thrown if not valid.
        utils.sub_run('/usr/sbin/visudo', '-c', '-f', temp_file.name, capture=True)

        utils.sudo_run('cp', temp_file.name, sudoers_fpath)
        utils.sudo_run('chmod', '0660', sudoers_fpath)

    log.info(f'Wrote to: {sudoers_fpath}')


class Mive:
    service_name = 'mise-uv-update.service'
    sysd_service = dirs.systemd.joinpath(service_name).read_text()

    timer_name = 'mise-uv-update.timer'
    sysd_timer = dirs.systemd.joinpath(timer_name).read_text()

    def __init__(self, username: str = ''):
        self.username = username

        curr_user = User.current().name
        if not username or username == curr_user:
            self.sudo = False
            self.run_func = utils.sub_run
            self.user_home: Path = Path('~').expanduser()
            self.systemctl_func = utils.systemctl
        else:
            self.sudo = True
            self.run_func = partial(utils.sudo_run, '-u', username)
            self.user_home: Path = Path(f'~{username}').expanduser()
            self.systemctl_func = partial(utils.systemctl, machine_user=username)

        self.install_dir: Path = self.user_home / '.local/bin'
        self.mise_bin: Path = self.install_dir / 'mise'
        self.uv_bin: Path = self.install_dir / 'uv'
        self.systemd_dir: Path = self.user_home / '.config/systemd/user/'

    def sh_install(self, script_url: str, creates_bin: Path, **script_env):
        bin_name = creates_bin.name

        if creates_bin.exists():
            log.info(f'{bin_name}: already installed')
            return

        log.info(f'{bin_name}: getting install script')
        with utils.curl_download(script_url, dir_mode=0o777) as script_fpath:
            script_fpath.chmod(0o444)

            sudo_args = ()
            if self.sudo and script_env:
                env_keys = ','.join(script_env)
                sudo_args = (f'--preserve-env={env_keys}',)

            log.info(f'{bin_name}: running install script')
            self.run_func(*sudo_args, 'sh', script_fpath, env=script_env)

    def install(self):
        self.sh_install(
            'https://mise.run',
            self.mise_bin,
        )

        self.sh_install(
            'https://astral.sh/uv/install.sh',
            self.uv_bin,
        )

    def systemd(self, force: bool = False):
        service_fpath = self.systemd_dir / self.service_name
        timer_fpath = self.systemd_dir / self.timer_name

        self.systemd_dir.mkdir(exist_ok=True, parents=True)

        service_changed = timer_changed = False
        if not service_fpath.exists() or force:
            log.info(f'{self.service_name}: writing systemd unit')
            service_fpath.write_text(self.sysd_service)
            service_changed = True
        else:
            log.info(f'{self.service_name}: unit existed')

        if not timer_fpath.exists() or force:
            log.info(f'{self.timer_name}: writing systemd unit')
            timer_fpath.write_text(self.sysd_timer)
            timer_changed = True
        else:
            log.info(f'{self.timer_name}: unit existed')

        if service_changed or timer_changed:
            log.info('systemd: reloading dameon')
            self.systemctl_func('daemon-reload')

        if timer_changed:
            log.info(f'{self.timer_name}: enabling and starting')
            self.systemctl_func('enable', '--now', self.timer_name)
