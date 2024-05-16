from os import environ
from pathlib import Path
import subprocess
import tomllib

from blazeutils import containers
import copier
import pytest


proj_root = Path(__file__).parent


class LazyDict(containers.LazyDict):
    def __getattr__(self, attr):
        val = super().__getattr__(attr)
        if isinstance(val, dict) and not isinstance(val, LazyDict):
            return LazyDict(val)
        return val


def toml_load(fpath: Path):
    with fpath.open('rb') as f:
        return LazyDict(tomllib.load(f))


def sub_run(*args, **kwargs):
    kwargs.setdefault('check', True)
    kwargs.setdefault('capture_output', True)
    try:
        return subprocess.run(args, **kwargs)
    except subprocess.CalledProcessError as e:
        print('sub stdout', e.stdout.decode('utf-8'))
        print('sub stderr', e.stderr.decode('utf-8'))
        raise


class Package:
    def __init__(self, dpath: Path):
        self.dpath = dpath

    def generate(self, **kwargs):
        kwargs.setdefault('project_name', 'Enterprise')
        kwargs.setdefault('author_name', 'Picard')
        kwargs.setdefault('author_email', 'jpicard@starfleet.space')

        copier.run_copy(
            proj_root.as_posix(),
            self.dpath.as_posix(),
            kwargs,
            unsafe=True,
            defaults=True,
            vcs_ref='HEAD',
        )

    def sub_run(self, *args, **kwargs) -> subprocess.CompletedProcess:
        return sub_run(*args, cwd=self.dpath, **kwargs)

    def mise(self, *args, **kwargs) -> subprocess.CompletedProcess:
        venv_dpath = self.path('.venv')
        if not venv_dpath.exists():
            self.sub_run('uv', 'venv')

        env = environ.copy()
        env['WORKON_HOME'] = venv_dpath.as_posix()

        return self.sub_run('mise', *args, env=env, **kwargs)

    def toml_config(self, fname):
        with self.dpath.joinpath(fname).open('rb') as f:
            return LazyDict(tomllib.load(f))

    def path(self, path: str):
        return self.dpath.joinpath(path)

    def exists(self, path: str):
        return self.path(path).exists()


@pytest.fixture
def package(tmp_path):
    return Package(tmp_path)


class TestPyPackage:
    def test_pyproject(self, package: Package):
        package.generate()
        config = package.toml_config('pyproject.toml')

        assert config.project.name == 'Enterprise'
        assert 'scripts' not in config.project

        author = LazyDict(config.project.authors[0])
        assert author.name == 'Picard'
        assert author.email == 'jpicard@starfleet.space'

    def test_pyproject_with_script(self, package: Package):
        package.generate(script_name='ent', hatch_installer_uv=True)

        # Use uv to create the venv to speed up the test
        hatch = package.toml_config('hatch.toml')
        assert hatch.envs.default.installer == 'uv'

        proj = package.toml_config('pyproject.toml')
        assert proj.project.scripts['ent'] == 'enterprise.cli:main'

        # TODO: when reqs supports uv, make this use it so its faster
        package.sub_run('reqs', 'compile', '--force')
        result = package.sub_run('hatch', 'run', 'ent')
        assert 'Hello from enterprise.cli' in result.stdout.decode('utf-8')

    def test_mise(self, package: Package):
        package.generate()

        config = package.toml_config('mise/config.toml')
        venv = config.env._.python.venv
        assert venv.path == '{{env.WORKON_HOME}}/Enterprise'
        assert config.tools.python == '3.12'

        result = package.mise('tasks')
        stdout = result.stdout.decode('utf-8')
        assert stdout.startswith('bump  Bump version')

    def test_static_files(self, package: Package):
        package.generate()
        assert package.exists('ruff.toml')
        assert package.exists('.copier-answers-py.yaml')

    def test_version(self, package: Package):
        package.generate()

        result = package.sub_run('hatch', 'version')
        assert result.stdout.decode('utf-8').strip() == '0.1.0'

    def test_copier_update_script(self):
        pass
