import click

from coppy.utils import sub_run
from coppy.version import VERSION


@click.group()
def cli():
    pass


@cli.command()
def version():
    print('coppy version:', VERSION)


@cli.command()
@click.option('--head', 'use_head', is_flag=True, help='Use HEAD instead of latest version tag')
def update(use_head: bool):
    """
    Update project from coppy template
    """
    vcs_ref = ('--vcs-ref', 'HEAD') if use_head else ()

    sub_run(
        'copier',
        'update',
        '--answers-file',
        '.copier-answers-py.yaml',
        '--trust',
        '--skip-answered',
        *vcs_ref,
    )


if __name__ == '__main__':
    cli()
