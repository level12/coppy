#!/usr/bin/env python
# [MISE] description="Prep OS user for testing"


import click
from coppy_tests.libs.os_prep import Mive, User, sudoers_write

from coppy import logs, utils
from coppy.utils import dd


log = logs.logger()

username = 'coppy-tests'
sudoers = """
# Permit passwordless sudo of coppy-tests user
%sudo ALL=({coppy_user}) NOPASSWD: ALL
""".lstrip()


@click.command()
@click.option('--systemd-skip', is_flag=True, default=False)
@click.option('--systemd-force', is_flag=True, default=False)
@click.option('--reinstall', is_flag=True, default=False)
@logs.opts_init
def main(systemd_skip: bool, systemd_force: bool, reinstall: bool):
    coppy_user = User(username)

    if reinstall and coppy_user.exists():
        result = utils.sudo_run('pkill', '-u', username, returns=(0, 1))
        if result.returncode == 0:
            # Wait for user's processes to exit or userdel will fail
            utils.sub_run('pidwait', '-u', username)
        utils.sudo_run('userdel', '-r', username)

        # Get rid of cache
        coppy_user = User(username)

    coppy_user.ensure()
    coppy_user_home = coppy_user.home_dir()

    if not coppy_user.is_current:
        curr_user = User.current()
        # This would clear them all (i.e. fix a mistake if you have one)
        utils.sub_run('sudo', 'setfacl', '-R', '-b', coppy_user_home)
        # utils.sudo_run('setfacl', '-R', '-m', f'u:{curr_user.name}:rwX', coppy_user_home)
        # utils.sudo_run('setfacl', '-R', '-d', '-m', f'u:{curr_user.name}:rwX', coppy_user_home)
        if coppy_user.name not in curr_user.groups():
            log.info(f'Adding your user to the user group: {coppy_user.name}')
            utils.sudo_run('usermod', '-aG', coppy_user.name, curr_user.name)
            log.warning(
                f'Please logout and then back in to enable access to the {coppy_user.name} group.',
            )
        else:
            log.info(f'Your user is already in the group: {coppy_user.name}')

        # Sticky group so files created by the dev's user can be accessed by coppy-tests user.
        utils.sudo_run('chmod', 'g+ws', coppy_user_home)

        # Needed for systemd files
        config_dpath = coppy_user_home / '.config/'
        config_dpath.mkdir(exist_ok=True)

    sudoers_write('coppy', sudoers.format(coppy_user=username))

    # Mise & uv
    mive = Mive(username)
    mive.install()

    coppy_user_home.joinpath('.gitconfig').write_text(
        dd("""
            [user]
            name = Foo
            email = foo@bar.com

            [safe]
            directory = *
        """),
    )

    if not systemd_skip:
        # I (RLS) think it's probably a good idea to keep mive and uv evergreen given their frequent
        # updates.  But, it does result in a number of other processes being started which are going
        # to be a, probably small, waste of resources:
        #
        #  $ pgrep -au coppy-tests
        #  106415 /usr/lib/systemd/systemd --user
        #  106416 (sd-pam)
        #  106428 /usr/bin/pipewire
        #  106429 /usr/bin/pipewire -c filter-chain.conf
        #  106430 /usr/bin/wireplumber
        #  106431 /usr/bin/pipewire-pulse
        #  106435 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile \
        #       --systemd-activation --syslog-only
        #
        # NOTE: checking status or logs on the systemd units is not starithstraightforward and
        # there are mise tasks (test-user-*) to help.
        mive.systemd(force=systemd_force)

        # This enables the update timer to run when the user doesn't have an active systemd session
        # going which is almost always since no one is likely to login with that user.  I presume
        # diagnostics would be done with `sudo -iu copppy-tests ...` which doesn't kick off the
        # systemd session.
        utils.sudo_run('loginctl', 'enable-linger', coppy_user.name)


if __name__ == '__main__':
    main()
