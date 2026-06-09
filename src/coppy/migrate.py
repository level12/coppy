from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

import click

from coppy.utils import CalledProcessError, sub_run


# Matches the exact line older versions of the template emitted in ruff.toml:
#   target-version = 'py313'
# Stripping it lets ruff auto-derive the target from pyproject.toml's `requires-python`.
LEGACY_RUFF_TARGET_VERSION_RE = re.compile(r"^target-version = 'py\d+'\n", re.MULTILINE)


@dataclass(slots=True)
class Migrator:
    project_dpath: Path
    python_executable: str | Path = field(default_factory=lambda: sys.executable)
    mise_lock: bool = True

    @property
    def pre_commit_config_fpath(self) -> Path:
        return self.project_dpath / '.pre-commit-config.yaml'

    @property
    def temp_prek_fpath(self) -> Path:
        return self.project_dpath / '.coppy-prek.toml'

    @property
    def prek_fpath(self) -> Path:
        return self.project_dpath / 'prek.toml'

    @property
    def mise_lock_fpath(self) -> Path:
        return self.project_dpath / 'mise.lock'

    @property
    def ruff_toml_fpath(self) -> Path:
        return self.project_dpath / 'ruff.toml'

    def before(self) -> None:
        if not self.pre_commit_config_fpath.exists():
            self.temp_prek_fpath.unlink(missing_ok=True)
            return

        sub_run(
            self.python_executable,
            '-m',
            'prek',
            'util',
            'yaml-to-toml',
            '--force',
            '--output',
            self.temp_prek_fpath,
            self.pre_commit_config_fpath,
            cwd=self.project_dpath,
            capture=True,
        )
        click.echo(
            f'Converted `{self.pre_commit_config_fpath.name}` → `{self.temp_prek_fpath.name}`',
        )

    def after(self) -> None:
        converted = self.temp_prek_fpath.exists()
        if converted:
            self.temp_prek_fpath.replace(self.prek_fpath)
            click.echo(f'Saved `{self.temp_prek_fpath.name}` → `{self.prek_fpath.name}`')

        if converted and (hook_fpath := self.pre_commit_hook_fpath()) and hook_fpath.exists():
            sub_run(
                self.python_executable,
                '-m',
                'prek',
                'install',
                '-f',
                '-t',
                'pre-commit',
                cwd=self.project_dpath,
            )

        self.strip_legacy_ruff_target_version()

        if self.mise_lock:
            self.ensure_mise_lock()

    def strip_legacy_ruff_target_version(self) -> None:
        if not self.ruff_toml_fpath.exists():
            return

        old_text = self.ruff_toml_fpath.read_text()
        new_text = LEGACY_RUFF_TARGET_VERSION_RE.sub('', old_text)
        if new_text == old_text:
            return

        self.ruff_toml_fpath.write_text(new_text)
        click.echo(
            'Removed legacy `target-version` from `ruff.toml`; '
            "ruff will derive it from `pyproject.toml`'s `requires-python`",
        )

    def ensure_mise_lock(self) -> None:
        if self.mise_lock_fpath.exists() and self.mise_lock_fpath.read_text().strip():
            return

        click.echo('`mise.lock` missing or empty; running `mise lock`')

        try:
            result = sub_run(
                'mise',
                'lock',
                cwd=self.project_dpath,
                capture=True,
                check=False,
            )
        except CalledProcessError as e:
            click.echo(f'`mise lock` failed: {e}', err=True)
            return

        if result.returncode == 0:
            return

        click.echo(f'`mise lock` failed with exit code {result.returncode}', err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)

    def pre_commit_hook_fpath(self) -> Path | None:
        result = sub_run(
            'git',
            'rev-parse',
            '--git-path',
            'hooks/pre-commit',
            cwd=self.project_dpath,
            capture=True,
            returns=(0, 128),  # 128 means the cwd is not inside a git repo.
        )
        if result.returncode != 0:
            return None

        if not (hook_path := result.stdout.strip()):
            return None

        hook_fpath = Path(hook_path)
        if hook_fpath.is_absolute():
            return hook_fpath

        return self.project_dpath / hook_fpath
