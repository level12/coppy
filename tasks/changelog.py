#!/usr/bin/env python
# [MISE] description="Run towncrier to build the changelog"

import click

from coppy.version import VERSION
from coppy_tasks_lib import sub_run


@click.command()
@click.option('--keep', is_flag=True, help='Keep changelog.d fragments')
def main(keep: bool):
    keep_args = ('--keep',) if keep else ()
    sub_run('towncrier', 'build', *keep_args, '--version', VERSION)


if __name__ == '__main__':
    main()
