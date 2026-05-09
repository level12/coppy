from pathlib import Path
import sys

import pytest

from coppy import cli as cli_mod

from .libs import mocks
from .libs.click import CLIRunner
from .libs.sandbox import UserBox


pytestmark = pytest.mark.usefixtures('coppy_install')


class TestCoppy:
    def test_coppy_install(self):
        sb = UserBox()
        version = sb.exec_stdout('coppy', 'version')
        assert version.startswith('coppy version: ')


@mocks.patch_obj(cli_mod, 'sub_run')
class TestCoppyCLI:
    def test_defaults(self, m_sub_run, cli: CLIRunner):
        cli.invoke('update')

        m_sub_run.assert_called_once_with(
            sys.executable,
            '-m',
            'copier',
            'update',
            '--answers-file',
            '.copier-answers-py.yaml',
            '--trust',
            '--skip-answered',
            Path.cwd(),
        )

    def test_path(self, m_sub_run, cli: CLIRunner):
        cli.invoke('update', '/tmp')

        m_sub_run.assert_called_once_with(
            sys.executable,
            '-m',
            'copier',
            'update',
            '--answers-file',
            '.copier-answers-py.yaml',
            '--trust',
            '--skip-answered',
            Path('/tmp'),
        )

    def test_opt_head(self, m_sub_run, cli: CLIRunner):
        cli.invoke('update', '--head')

        m_sub_run.assert_called_once_with(
            sys.executable,
            '-m',
            'copier',
            'update',
            '--answers-file',
            '.copier-answers-py.yaml',
            '--trust',
            '--skip-answered',
            '--vcs-ref',
            'HEAD',
            Path.cwd(),
        )


class TestCoppyMigrateCLI:
    def test_before(self, cli: CLIRunner):
        with mocks.patch_obj(cli_mod, 'Migrator') as m_migrator:
            cli.invoke('migrate', 'before')

        m_migrator.assert_called_once_with(project_dpath=Path.cwd())
        m_migrator.return_value.before.assert_called_once_with()
        m_migrator.return_value.after.assert_not_called()

    def test_after(self, cli: CLIRunner):
        with mocks.patch_obj(cli_mod, 'Migrator') as m_migrator:
            cli.invoke('migrate', 'after')

        m_migrator.assert_called_once_with(project_dpath=Path.cwd())
        m_migrator.return_value.before.assert_not_called()
        m_migrator.return_value.after.assert_called_once_with()
