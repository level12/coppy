#!/usr/bin/env -S uv run --script
# mise description="Show isolated environment used by tests"

from pathlib import Path

import click

from coppy.sandbox import Sandbox


@click.command()
@click.argument(
    'project_path',
    type=click.Path(path_type=Path),
    default='/tmp/copier-py-package-demo',
)
@click.option('--bash', is_flag=True)
@click.option('--doctor', is_flag=True)
def main(project_path: Path, bash: bool, doctor: bool):
    with Sandbox(project_path) as sb:
        sb.run('printenv')
        sb.run('pwd')
        sb.run('ls')
        print('mise python vars:', sb.mise_env('USER', 'VIRTUAL_ENV'))
        if doctor:
            sb.run('mise', 'doctor', returns=(0, 1))
            sb.run('mise', 'ls')
            sb.run('mise', 'exec', '--', 'python', '--version')
        if bash:
            sb.run('bash')


if __name__ == '__main__':
    main()
