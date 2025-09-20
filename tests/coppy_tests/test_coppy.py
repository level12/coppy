from pathlib import Path

import pytest

from coppy import cli

from .libs import mocks
from .libs.click import CLIRunner
from .libs.sandbox import UserBox


pytestmark = pytest.mark.usefixtures('coppy_install')


class TestCoppy:
    def test_coppy_install(self):
        sb = UserBox()
        version = sb.exec_stdout('coppy', 'version')
        assert version.startswith('coppy version: ')


@mocks.patch_obj(cli, 'sub_run')
class TestCoppyCLI:
    def test_defaults(self, m_sub_run, cli: CLIRunner):
        cli.invoke('update')

        m_sub_run.assert_called_once_with(
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
