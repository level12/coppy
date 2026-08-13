from pathlib import Path
import subprocess
import sys

import pytest

from coppy import cli as cli_mod
from coppy import utils

from .libs import mocks
from .libs.click import CLIRunner
from .libs.sandbox import UserBox


pytestmark = pytest.mark.usefixtures('coppy_install')


class TestCoppy:
    def test_coppy_install(self):
        sb = UserBox()
        version = sb.exec_stdout('coppy', 'version')
        assert version.startswith('coppy version: ')

    def test_pytest_config_matches_template(self):
        boundary = '    #----------------------------------------------------------'
        coppy_lines = (utils.pkg_dpath / 'pytest.ini').read_text().splitlines()
        template_lines = (utils.template / 'pytest.ini').read_text().splitlines()

        coppy_boundary = coppy_lines.index(boundary)
        template_boundary = template_lines.index(boundary)

        assert coppy_lines[: coppy_boundary + 1] == template_lines[: template_boundary + 1]


@mocks.patch_obj(cli_mod, 'sub_run')
class TestCoppyCLI:
    @pytest.fixture(autouse=True)
    def uv_version_check(self):
        with mocks.patch_obj(cli_mod.UvVersion, 'check'):
            yield

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


class TestCoppyCLIUvVersion:
    def test_supported_reaches_copier(self, cli: CLIRunner):
        uv_result = subprocess.CompletedProcess(('uv', '--version'), 0, 'uv 0.9.17\n', '')

        with (
            mocks.patch('coppy.migrate.sub_run', return_value=uv_result) as m_uv_sub_run,
            mocks.patch_obj(cli_mod, 'sub_run') as m_copier_sub_run,
        ):
            cli.invoke('update')

        m_uv_sub_run.assert_called_once_with('uv', '--version', capture=True)
        m_copier_sub_run.assert_called_once_with(
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

    @pytest.mark.parametrize(
        ('uv_output', 'expected_error'),
        [
            (
                'uv 0.9.16\n',
                (
                    'uv 0.9.16 is too old for Coppy cooldown configuration; '
                    'uv 0.9.17 or newer is required. Upgrade uv then retry `coppy update`.'
                ),
            ),
            ('unexpected output\n', 'Could not determine uv version from: unexpected output'),
        ],
    )
    def test_rejected_stops_before_copier(
        self,
        cli: CLIRunner,
        uv_output: str,
        expected_error: str,
    ):
        uv_result = subprocess.CompletedProcess(('uv', '--version'), 0, uv_output, '')

        with (
            mocks.patch('coppy.migrate.sub_run', return_value=uv_result) as m_uv_sub_run,
            mocks.patch_obj(cli_mod, 'sub_run') as m_copier_sub_run,
        ):
            result = cli.invoke('update', check=False)

        assert result.exit_code == 1
        assert result.output == f'Error: {expected_error}\n'
        m_uv_sub_run.assert_called_once_with('uv', '--version', capture=True)
        m_copier_sub_run.assert_not_called()


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
