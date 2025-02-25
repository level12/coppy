#!/usr/bin/env -S uv run --script
# mise description="Show sandbox env details"

from pathlib import Path

import click

from coppy.sandbox import Container
from tasks_lib import demo_dest_default


@click.command()
@click.argument(
    'project_path',
    type=click.Path(path_type=Path),
    default=demo_dest_default(),
)
@click.option('--bash', is_flag=True)
@click.option('--doctor', is_flag=True)
@click.option('--bash', 'bash_on_enter', is_flag=True)
def main(project_path: Path, bash: bool, doctor: bool, bash_on_enter: bool):
    with Container(project_path, bash_on_enter=bash_on_enter) as sb:
        sb.exec('printenv')
        sb.exec('pwd')
        sb.exec('ls')
        print('mise python vars:', sb.mise_env('USER', 'VIRTUAL_ENV'))
        if doctor:
            sb.exec('mise', 'doctor', returns=(0, 1))
            sb.exec('mise', 'ls')
            sb.exec('mise', 'exec', '--', 'python', '--version')
        if bash:
            sb.exec('bash')


if __name__ == '__main__':
    main()
