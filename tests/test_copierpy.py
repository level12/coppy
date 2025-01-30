from os import environ
from pathlib import Path
import subprocess
import tomllib

from blazeutils import containers
import copier
import pytest


proj_root = Path(__file__).parent.parent


class LazyDict(containers.LazyDict):
    def __getattr__(self, attr):
        val = super().__getattr__(attr)
        if isinstance(val, dict) and not isinstance(val, LazyDict):
            return LazyDict(val)
        return val


def toml_load(fpath: Path):
    with fpath.open('rb') as f:
        return LazyDict(tomllib.load(f))


def sub_run(*args, capture=True, **kwargs):
    kwargs.setdefault('check', True)
    kwargs.setdefault('capture_output', capture)
    try:
        return subprocess.run(args, **kwargs)
    except subprocess.CalledProcessError as e:
        if kwargs['capture_output']:
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
        kwargs.setdefault('script_name', '')

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
        env['VIRTUALENVS_DIR'] = venv_dpath.as_posix()

        return self.sub_run('mise', *args, env=env, **kwargs)

    def toml_config(self, fname):
        with self.dpath.joinpath(fname).open('rb') as f:
            return LazyDict(tomllib.load(f))

    def path(self, path: str):
        return self.dpath.joinpath(path)

    def exists(self, path: str):
        return self.path(path).exists()


class TestPyPackage:
    @pytest.fixture(scope='class')
    def package(self, tmp_path_factory):
        temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
        package = Package(temp_path)
        package.generate()
        return package

    def test_pyproject(self, package: Package):
        config = package.toml_config('pyproject.toml')

        assert config.project.name == 'Enterprise'
        assert 'scripts' not in config.project

        author = LazyDict(config.project.authors[0])
        assert author.name == 'Picard'
        assert author.email == 'jpicard@starfleet.space'

    def test_pyproject_with_script(self, tmp_path: Path):
        package = Package(tmp_path)
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
        config = package.toml_config('mise.toml')
        venv = config.env._.python.venv
        assert venv.path == (
            "{% if env.VIRTUALENVS_DIR %}{{ env.VIRTUALENVS_DIR }}/{{ virtualenv_name }}"
            "{% else %}.venv{% endif %}"
        )
        assert config.tools.python == '3.12'

        result = package.mise('tasks')
        stdout = result.stdout.decode('utf-8')
        assert stdout.startswith('bootstrap  Bootstrap project')

    def test_static_files(self, package: Package):
        package.generate()
        assert package.exists('ruff.toml')
        assert package.exists('.copier-answers-py.yaml')

    def test_version(self, package: Package):
        result = package.sub_run('hatch', 'version')
        assert result.stdout.decode('utf-8').strip() == '0.1.0'

    def test_demo_bootstrap(self, tmp_path: Path):
        sub_run('mise', 'run', 'demo', tmp_path, cwd=proj_root, capture=False)
        package = Package(tmp_path)
        assert package.exists('.git')
        assert package.exists('.git/hooks/pre-commit')
        assert package.exists('requirements/dev.txt')

        venvs_dpath = Path(environ.get('VIRTUALENVS_DIR', '/tmp')).expanduser().absolute()
        demo_venv = venvs_dpath / 'copierpypackagedemo'
        venv_bin = demo_venv / 'bin'
        print('demo venv_bin', venv_bin)

        result = sub_run(f'{venv_bin}/uv', 'pip', 'freeze', env={'VIRTUAL_ENV': demo_venv})
        reqs = result.stdout.decode('utf-8')
        assert 'ruff==' in reqs

        # git should return non-zero if everything hasn't been committed
        sub_run('git', 'diff-index', '--quiet', 'HEAD', cwd=tmp_path)
