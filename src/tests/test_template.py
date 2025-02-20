import datetime as dt
from pathlib import Path

import pytest

from coppy.sandbox import Sandbox
from coppy.testing import Package, data_fpath
from coppy.utils import LazyDict


class TestTemplate:
    @pytest.fixture(scope='class')
    def package(self, tmp_path_factory):
        temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
        package = Package(temp_path)
        package.generate()
        return package

    @pytest.fixture(scope='class')
    def sb(self, package: Package):
        with package.sandbox() as sb:
            yield sb

    def test_pyproject(self, package: Package):
        config = package.toml_config('pyproject.toml')

        assert config.project.name == 'Enterprise'
        assert 'scripts' not in config.project

        author = LazyDict(config.project.authors[0])
        assert author.name == 'Picard'
        assert author.email == 'jpicard@starfleet.space'

    def test_pyproject_with_script(self, tmp_path: Path):
        # Don't use the fixture, we need to re-generate to test a non-default script_name
        package = Package(tmp_path)
        package.generate(script_name='ent')

        # Ensure hatch is using uv
        hatch = package.toml_config('hatch.toml')
        assert hatch.envs.default.installer == 'uv'

        proj = package.toml_config('pyproject.toml')
        assert proj.project.scripts['ent'] == 'enterprise.cli:main'

        with package.sandbox() as sb:
            result = sb.uv('run', 'ent', capture=True)
            assert 'Hello from enterprise.cli' in result.stdout

    def test_hatch_version_sign_tag(self, tmp_path: Path, package: Package):
        hatch = package.toml_config('hatch.toml')
        assert hatch.version.get('tag_sign') is None
        toml_src = package.path('hatch.toml').read_text()
        assert toml_src.endswith("version.py'\n")

        package = Package(tmp_path)
        package.generate(hatch_version_tag_sign=False)
        hatch = package.toml_config('hatch.toml')
        assert hatch.version.tag_sign is False
        toml_src = package.path('hatch.toml').read_text()
        assert toml_src.endswith('false\n')

    def test_python_and_venv(self, sb: Sandbox):
        # There is some overlap with the sandbox tests above  These are focused on ensuring the
        # template is setup as expected for mise, not that the sandbox got configured correctly.

        # Default python version
        result = sb.mise_exec('python', '--version', capture=True)
        assert result.stdout.strip().startswith('Python 3.13.')

        # Mise should be configured to create the venv if it doesn't exist
        assert 'mise creating venv with uv at: ~/project/.venv' in result.stderr.strip()

        # Ensure slug is set and mise is activating the virtualenv
        assert sb.mise_env('PROJECT_SLUG', 'VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT') == [
            'project',
            '/home/picard/project/.venv',
        ]

    def test_venv_not_nested(self, package: Package):
        """Ensure using a non-nested venv defined by UV_PROJECT_ENVIRONMENT works"""

        # NOTE: we are NOT using the `sb` fixture b/c sb.mise_config() affects the entire session
        # and we only want to place this file for this particular test.
        with package.sandbox() as sb:
            sb.mise_config(data_fpath('mise-config.toml'))

            result = sb.mise_exec('python', '--version', capture=True)
            py_ver = result.stdout.strip()
            assert (
                'mise creating venv with uv at: ~/.cache/uv-venvs/project' in result.stderr.strip()
            )

            assert sb.mise_env('VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT') == [
                '/home/picard/.cache/uv-venvs/project',
                '/home/picard/.cache/uv-venvs/project',
            ]

            result = sb.mise_exec('uv', 'pip', 'freeze', capture=True)
            assert (
                result.stderr.strip()
                == f'Using {py_ver} environment at: /home/picard/.cache/uv-venvs/project'
            )

    def test_static_files(self, package: Package):
        assert package.exists('ruff.toml')
        assert package.exists('.copier-answers-py.yaml')

    def test_version(self, sb: Sandbox):
        result = sb.uv('run', 'hatch', 'version', capture=True)
        assert result.stdout.strip() == '0.1.0'

    def test_tasks(self, tmp_path: Path):
        package = Package(tmp_path)
        package.generate(hatch_version_tag_sign=False)

        with package.sandbox() as sb:
            # Task listing
            task_meta = sb.mise('tasks', '--json', json=True)
            assert len(task_meta) == 2
            bootstrap = LazyDict(task_meta[0])
            assert bootstrap.name == 'bootstrap'
            assert bootstrap.description == 'Bootstrap project'

            bump = LazyDict(task_meta[1])
            assert bump.name == 'bump'
            assert bump.description == 'Bump version'

            # Run bootstrap
            assert not sb.proj_rw_path('.git').exists()
            assert not sb.proj_rw_path('.git/hooks/pre-commit').exists()
            assert not sb.proj_rw_path('uv.lock').exists()

            sb.run('git', 'config', '--global', 'user.name', 'Jean-Luc Picard')
            sb.run('git', 'config', '--global', 'user.email', 'j.l.picard@starfleet.uni')
            sb.mise('run', 'bootstrap')
            assert sb.proj_rw_path('.git').exists()
            assert sb.proj_rw_path('.git/hooks/pre-commit').exists()
            assert sb.proj_rw_path('uv.lock').exists()

            # Run bump
            sb.mise('run', 'bump', '--no-push')
            result = sb.uv('run', 'hatch', 'version', capture=True)
            date_str = dt.datetime.utcnow().date().strftime(r'%Y%m%d')
            assert result.stdout.strip() == f'0.{date_str}.1'
