from dataclasses import dataclass, field
from pathlib import Path
import sys

from coppy.utils import sub_run


@dataclass(slots=True)
class Migrator:
    project_dpath: Path
    python_executable: str | Path = field(default_factory=lambda: sys.executable)

    @property
    def pre_commit_config_fpath(self) -> Path:
        return self.project_dpath / '.pre-commit-config.yaml'

    @property
    def temp_prek_fpath(self) -> Path:
        return self.project_dpath / '.coppy-prek.toml'

    @property
    def prek_fpath(self) -> Path:
        return self.project_dpath / 'prek.toml'

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
        )

    def after(self) -> None:
        converted = self.temp_prek_fpath.exists()
        if converted:
            self.temp_prek_fpath.replace(self.prek_fpath)

        if not converted:
            return

        if not (hook_fpath := self.pre_commit_hook_fpath()):
            return

        if not hook_fpath.exists():
            return

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
