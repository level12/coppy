#!/usr/bin/env python
# [MISE] description="Run towncrier to build the changelog"

import datetime as dt

import click

from coppy_tasks_lib import sub_run


def current_version():
    result = sub_run('hatch', 'version', capture=True)
    return result.stdout.strip()


def date_version(current: str):
    major, _, patch, *_ = current.split('.')
    version = f'{major}.' + dt.date.today().strftime(r'%Y%m%d')

    patch = int(patch) + 1 if current.startswith(version) else 1

    return f'{version}.{patch}'


@click.command()
@click.option('--keep', is_flag=True, help='Keep changelog.d fragements')
def main(keep: bool):
    keep_args = ('--keep',) if keep else ()
    version = sub_run('hatch', 'version', capture=True).stdout.strip()

    sub_run('towncrier', 'build', *keep_args, '--version', version)


if __name__ == '__main__':
    main()
