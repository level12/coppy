from pathlib import Path
import subprocess

import click
import pytest
import yaml

from coppy import utils
from coppy.migrate import Migrator, UvVersion
from coppy.utils import sub_run

from .libs import mocks


PRE_COMMIT_CONFIG = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml
      - id: check-json
""".lstrip()

RUMDL_CONFIG = """
[[repos]]
repo = 'https://github.com/rvben/rumdl-pre-commit'
rev = 'v0.2.55'
hooks = [
  { id = 'rumdl' },
]
""".lstrip()

UV_CONFIG = """
[[repos]]
repo = "https://github.com/astral-sh/uv-pre-commit"
rev = "0.12.3"
hooks = [
  { id = "uv-lock" },
]
""".lstrip()


class TestUvVersion:
    @pytest.mark.parametrize(
        'uv_output',
        [
            'uv 0.9.17',
            'uv 0.10.0',
            'uv 1.0.0',
            'uv 0.12.3 (x86_64-unknown-linux-gnu)',
        ],
    )
    def test_supported(self, uv_output: str):
        assert UvVersion.check(uv_output) is None

    def test_too_old(self):
        with pytest.raises(click.ClickException) as exc_info:
            UvVersion.check('uv 0.9.16')

        message = exc_info.value.message
        assert 'uv 0.9.16 is too old' in message
        assert 'uv 0.9.17 or newer is required' in message
        assert 'Upgrade uv then retry `coppy update`' in message

    @pytest.mark.parametrize(
        'uv_output',
        ['unexpected output', 'uv 0.9.17-alpha.1', 'uv 0.9.17garbage'],
    )
    def test_unrecognized(self, uv_output: str):
        with pytest.raises(click.ClickException) as exc_info:
            UvVersion.check(uv_output)

        assert exc_info.value.message == f'Could not determine uv version from: {uv_output}'

    def test_sub_run_uv_call(self):
        """
        The tests above all use uv_output to bypass sub_run().

        This test checks to make sure sub_run() is used to call uv correctly.
        """
        result = subprocess.CompletedProcess(('uv', '--version'), 0, 'uv 0.9.17\n', '')

        with mocks.patch('coppy.migrate.sub_run', return_value=result) as m_sub_run:
            UvVersion.check()

        m_sub_run.assert_called_once_with('uv', '--version', capture=True)


class TestMigrate:
    @pytest.fixture()
    def project_dpath(self, tmp_path: Path) -> Path:
        return tmp_path

    def test_converts_yaml_to_toml(self, project_dpath: Path):
        self.write_pre_commit_config(project_dpath)

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        migrator.after()

        assert not (project_dpath / '.coppy-prek.toml').exists()
        assert 'check-json' in (project_dpath / 'prek.toml').read_text()

    def test_before_reports_relative_conversion_paths(self, project_dpath: Path, capsys):
        self.write_pre_commit_config(project_dpath)

        Migrator(project_dpath).before()

        out = capsys.readouterr().out
        assert 'Converted `.pre-commit-config.yaml` → `.coppy-prek.toml`' in out
        assert project_dpath.as_posix() not in out

    def test_after_overwrites_templated_prek(self, project_dpath: Path):
        self.write_pre_commit_config(project_dpath)

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        (project_dpath / 'prek.toml').write_text('# curated template content\n')
        migrator.after()

        prek_text = (project_dpath / 'prek.toml').read_text()
        assert 'check-json' in prek_text
        assert 'curated template content' not in prek_text

    def test_after_adds_rendered_rumdl_before_uv(self, project_dpath: Path):
        converted_config = f"""
[[repos]]
repo = 'https://example.com/custom-hooks'

{UV_CONFIG}
""".lstrip()
        self.write_prek_configs(
            project_dpath,
            converted=converted_config,
            rendered=f'{RUMDL_CONFIG}\n{UV_CONFIG}',
        )

        Migrator(project_dpath, mise_lock=False).after()

        prek_config = (project_dpath / 'prek.toml').read_text()
        assert 'https://example.com/custom-hooks' in prek_config
        assert RUMDL_CONFIG in prek_config
        assert prek_config.index('rumdl-pre-commit') < prek_config.index('uv-pre-commit')

    def test_after_appends_rendered_rumdl_without_uv(self, project_dpath: Path):
        converted_config = """
[[repos]]
repo = 'https://example.com/custom-hooks'
""".lstrip()
        self.write_prek_configs(
            project_dpath,
            converted=converted_config,
            rendered=RUMDL_CONFIG,
        )

        Migrator(project_dpath, mise_lock=False).after()

        prek_config = (project_dpath / 'prek.toml').read_text()
        assert prek_config.index('https://example.com/custom-hooks') < prek_config.index(
            'rumdl-pre-commit',
        )
        assert prek_config.endswith("  { id = 'rumdl' },\n]\n")

    def test_after_does_not_add_rumdl_when_not_rendered(self, project_dpath: Path):
        converted_config = f"""
[[repos]]
repo = 'https://example.com/custom-hooks'

{UV_CONFIG}
""".lstrip()
        self.write_prek_configs(
            project_dpath,
            converted=converted_config,
            rendered=UV_CONFIG,
        )

        Migrator(project_dpath, mise_lock=False).after()

        assert (project_dpath / 'prek.toml').read_text() == converted_config

    def test_after_does_not_duplicate_converted_rumdl(self, project_dpath: Path):
        converted_config = f'{RUMDL_CONFIG}\n{UV_CONFIG}'
        self.write_prek_configs(
            project_dpath,
            converted=converted_config,
            rendered=f'{RUMDL_CONFIG}\n{UV_CONFIG}',
        )

        Migrator(project_dpath, mise_lock=False).after()

        prek_config = (project_dpath / 'prek.toml').read_text()
        assert prek_config == converted_config
        assert prek_config.count('rumdl-pre-commit') == 1

    def test_after_reports_temp_saved_to_prek(self, project_dpath: Path, capsys):
        self.write_pre_commit_config(project_dpath)

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        capsys.readouterr()

        migrator.after()

        out = capsys.readouterr().out
        assert 'Saved `.coppy-prek.toml` → `prek.toml`' in out

    def test_skips_when_yaml_missing(self, project_dpath: Path):
        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        migrator.after()

        assert not (project_dpath / '.coppy-prek.toml').exists()
        assert not (project_dpath / 'prek.toml').exists()

    def test_before_raises_on_invalid_yaml(self, project_dpath: Path):
        (project_dpath / '.pre-commit-config.yaml').write_text('repos: [\n')

        with pytest.raises(subprocess.CalledProcessError):
            Migrator(project_dpath).before()

    def test_replaces_existing_pre_commit_hook(self, project_dpath: Path):
        self.init_git_repo(project_dpath)
        self.write_pre_commit_config(project_dpath)
        hook_fpath = self.install_old_pre_commit_hook(project_dpath)

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        migrator.after()

        assert not (project_dpath / '.coppy-prek.toml').exists()
        assert hook_fpath.exists()
        assert hook_fpath.read_text()
        assert 'old-pre-commit' not in hook_fpath.read_text()

    def test_leaves_missing_hook_alone(self, project_dpath: Path):
        self.init_git_repo(project_dpath)
        self.write_pre_commit_config(project_dpath)
        hook_fpath = project_dpath / '.git/hooks/pre-commit'

        assert not hook_fpath.exists()

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        migrator.after()

        assert not (project_dpath / '.coppy-prek.toml').exists()
        assert (project_dpath / 'prek.toml').exists()
        assert not hook_fpath.exists()

    def test_after_is_noop_without_converted_file(self, project_dpath: Path):
        hook_fpath = self.install_old_pre_commit_hook(project_dpath)

        with mocks.patch('coppy.migrate.sub_run') as m_sub_run:
            Migrator(project_dpath, mise_lock=False).after()

        m_sub_run.assert_not_called()
        assert 'old-pre-commit' in hook_fpath.read_text()

    def test_before_cleans_stale_temp_without_yaml(self, project_dpath: Path):
        temp_prek_fpath = project_dpath / '.coppy-prek.toml'
        prek_fpath = project_dpath / 'prek.toml'
        temp_prek_fpath.write_text('stale converted content\n')
        prek_fpath.write_text('hand curated content\n')

        migrator = Migrator(project_dpath, mise_lock=False)
        migrator.before()
        migrator.after()

        assert not temp_prek_fpath.exists()
        assert prek_fpath.read_text() == 'hand curated content\n'

    def test_after_runs_mise_lock_when_lock_missing(self, project_dpath: Path, capsys):
        with mocks.patch('coppy.migrate.sub_run') as m_sub_run:
            m_sub_run.return_value = subprocess.CompletedProcess(('mise', 'lock'), 0, '', '')
            Migrator(project_dpath).after()

        m_sub_run.assert_called_once_with(
            'mise',
            'lock',
            cwd=project_dpath,
            capture=True,
            check=False,
        )
        assert '`mise.lock` missing or empty; running `mise lock`' in capsys.readouterr().out

    def test_after_runs_mise_lock_when_lock_blank(self, project_dpath: Path):
        self.write_mise_lock(project_dpath, content=' \n\t')

        with mocks.patch('coppy.migrate.sub_run') as m_sub_run:
            m_sub_run.return_value = subprocess.CompletedProcess(('mise', 'lock'), 0, '', '')
            Migrator(project_dpath).after()

        m_sub_run.assert_called_once_with(
            'mise',
            'lock',
            cwd=project_dpath,
            capture=True,
            check=False,
        )

    def test_after_skips_mise_lock_when_populated(self, project_dpath: Path):
        self.write_mise_lock(project_dpath)

        with mocks.patch('coppy.migrate.sub_run') as m_sub_run:
            Migrator(project_dpath).after()

        m_sub_run.assert_not_called()

    def test_after_reports_failed_mise_lock_without_raising(self, project_dpath: Path, capsys):
        with mocks.patch('coppy.migrate.sub_run') as m_sub_run:
            m_sub_run.return_value = subprocess.CompletedProcess(('mise', 'lock'), 1, '', 'boom\n')

            Migrator(project_dpath).after()

        out = capsys.readouterr()
        assert '`mise.lock` missing or empty; running `mise lock`' in out.out
        assert '`mise lock` failed with exit code 1' in out.err
        assert 'boom' in out.err

    def test_after_runs_prek_install_before_failed_mise_lock(self, project_dpath: Path, capsys):
        hook_fpath = project_dpath / '.git/hooks/pre-commit'
        hook_fpath.parent.mkdir(parents=True, exist_ok=True)
        hook_fpath.write_text('#!/bin/sh\n')
        (project_dpath / '.coppy-prek.toml').write_text('repos = []\n')
        migrator = Migrator(project_dpath)

        with (
            mocks.patch_obj(Migrator, 'pre_commit_hook_fpath', return_value=hook_fpath),
            mocks.patch('coppy.migrate.sub_run') as m_sub_run,
        ):
            m_sub_run.side_effect = [
                subprocess.CompletedProcess((migrator.python_executable, '-m', 'prek'), 0, '', ''),
                subprocess.CompletedProcess(('mise', 'lock'), 1, '', 'boom\n'),
            ]

            migrator.after()

        assert (project_dpath / 'prek.toml').exists()
        out = capsys.readouterr()
        assert '`mise lock` failed with exit code 1' in out.err
        assert m_sub_run.call_args_list[0].args[1:4] == ('-m', 'prek', 'install')
        assert m_sub_run.call_args_list[1].args == ('mise', 'lock')

    def test_copier_wires_hidden_migrate_commands(self):
        copier_cfg = yaml.safe_load((utils.pkg_dpath / 'copier.yaml').read_text())

        assert copier_cfg['_migrations'] == [
            {'command': 'coppy migrate before', 'when': "{{ _stage == 'before' }}"},
            {'command': 'coppy migrate after', 'when': "{{ _stage == 'after' }}"},
        ]

    def write_pre_commit_config(self, project_dpath: Path):
        (project_dpath / '.pre-commit-config.yaml').write_text(PRE_COMMIT_CONFIG)

    def write_prek_configs(self, project_dpath: Path, *, converted: str, rendered: str):
        (project_dpath / '.coppy-prek.toml').write_text(converted)
        (project_dpath / 'prek.toml').write_text(rendered)

    def write_mise_lock(self, project_dpath: Path, *, content: str = 'locked\n'):
        (project_dpath / 'mise.lock').write_text(content)

    def init_git_repo(self, project_dpath: Path):
        sub_run('git', 'init', cwd=project_dpath)
        sub_run('git', 'config', 'user.name', 'Coppy Tests', cwd=project_dpath)
        sub_run('git', 'config', 'user.email', 'coppy-tests@example.com', cwd=project_dpath)

    def install_old_pre_commit_hook(self, project_dpath: Path) -> Path:
        hook_fpath = project_dpath / '.git/hooks/pre-commit'
        hook_fpath.parent.mkdir(parents=True, exist_ok=True)
        hook_fpath.write_text('#!/bin/sh\necho old-pre-commit\n')
        hook_fpath.chmod(0o755)
        return hook_fpath
