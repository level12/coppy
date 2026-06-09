from pathlib import Path
import subprocess

import pytest
import yaml

from coppy import utils
from coppy.migrate import Migrator
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

    def test_after_strips_legacy_ruff_target_version(self, project_dpath: Path, capsys):
        ruff_fpath = project_dpath / 'ruff.toml'
        ruff_fpath.write_text(
            "line-length = 100\ntarget-version = 'py313'\noutput-format = 'concise'\n",
        )

        Migrator(project_dpath, mise_lock=False).after()

        assert ruff_fpath.read_text() == "line-length = 100\noutput-format = 'concise'\n"
        assert 'Removed legacy `target-version` from `ruff.toml`' in capsys.readouterr().out

    def test_after_leaves_modern_ruff_toml_alone(self, project_dpath: Path, capsys):
        ruff_fpath = project_dpath / 'ruff.toml'
        original = "line-length = 100\noutput-format = 'concise'\n"
        ruff_fpath.write_text(original)

        Migrator(project_dpath, mise_lock=False).after()

        assert ruff_fpath.read_text() == original
        assert 'Removed legacy' not in capsys.readouterr().out

    def test_after_preserves_customized_target_version(self, project_dpath: Path):
        # Only the exact single-quoted form the template emitted is stripped.  Anything the user
        # has customized away from that form (different quoting, trailing comment, etc.) survives.
        ruff_fpath = project_dpath / 'ruff.toml'
        original = (
            'target-version = "py313"\n'
            "target-version = 'py313'  # pinned\n"
        )
        ruff_fpath.write_text(original)

        Migrator(project_dpath, mise_lock=False).after()

        assert ruff_fpath.read_text() == original

    def test_after_skips_when_ruff_toml_missing(self, project_dpath: Path):
        Migrator(project_dpath, mise_lock=False).after()

        assert not (project_dpath / 'ruff.toml').exists()

    def test_copier_wires_hidden_migrate_commands(self):
        copier_cfg = yaml.safe_load((utils.pkg_dpath / 'copier.yaml').read_text())

        assert copier_cfg['_migrations'] == [
            {'command': 'coppy migrate before', 'when': "{{ _stage == 'before' }}"},
            {'command': 'coppy migrate after', 'when': "{{ _stage == 'after' }}"},
        ]

    def write_pre_commit_config(self, project_dpath: Path):
        (project_dpath / '.pre-commit-config.yaml').write_text(PRE_COMMIT_CONFIG)

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
