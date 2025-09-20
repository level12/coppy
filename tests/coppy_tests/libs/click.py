import click.testing

from coppy import cli


class CLIRunner(click.testing.CliRunner):
    def invoke(self, *args, check=True, **kwargs):
        # Letting Click catch the exception makes it harder to troubleshoot, just let the
        # exception surface.
        kwargs.setdefault('catch_exceptions', False)
        # assign invoke's args to the args variable to give better ergonomics.  i.e.:
        # invoke('foo', 'bar') vs invoke(args=('foo', 'bar'))
        result = super().invoke(cli.cli, args, **kwargs)
        if result.exit_code != 0 and check:
            raise Exception(
                f'Non-zero exit code: {result.exit_code}\n'
                f'STDOUT: {result.stdout}\n'
                f'STDERR: {result.stderr}',
            )
