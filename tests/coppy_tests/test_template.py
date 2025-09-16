import datetime as dt
from pathlib import Path

import pytest

from coppy.sandbox import Container
from coppy.testing import Package, data_fpath
from coppy.utils import LazyDict


@pytest.fixture()
def package(tmp_path_factory):
    temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
    return Package(temp_path)


def assert_pkg_file_eq(package: Package, p_fpath, d_fpath):
    assert package.read_text(p_fpath) == data_fpath(d_fpath).read_text()


class TestTemplateGen:
    @pytest.fixture(scope='class')
    def gen_pkg(self, tmp_path_factory):
        """A package with default config"""
        temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
        gen_pkg = Package(temp_path)
        gen_pkg.generate()
        return gen_pkg

    def test_pyproject(self, gen_pkg: Package):
        config = gen_pkg.toml_config('pyproject.toml')

        assert config.project.name == 'Enterprise'
        assert 'scripts' not in config.project

        author = LazyDict(config.project.authors[0])
        assert author.name == 'Picard'
        assert author.email == 'jpicard@starfleet.space'

    def test_hatch_uv(self, gen_pkg: Package):
        hatch = gen_pkg.toml_config('hatch.toml')
        assert hatch.envs.default.installer == 'uv'

    def test_hatch_version_sign_tag(self, gen_pkg: Package, package: Package):
        hatch = gen_pkg.toml_config('hatch.toml')
        assert hatch.version.get('tag_sign') is None
        toml_src = gen_pkg.path('hatch.toml').read_text()
        assert toml_src.endswith("version.py'\n")

        package.generate(hatch_version_tag_sign=False)
        hatch = package.toml_config('hatch.toml')
        assert hatch.version.tag_sign is False
        toml_src = package.path('hatch.toml').read_text()
        assert toml_src.endswith('false\n')

    def test_static_files(self, gen_pkg: Package):
        assert gen_pkg.exists('ruff.toml')
        assert gen_pkg.exists('.copier-answers-py.yaml')

    def test_ci_options(self, gen_pkg: Package, package: Package):
        # default
        assert_pkg_file_eq(gen_pkg, '.github/workflows/nox.yaml', 'gh-nox.yaml')
        assert not gen_pkg.exists('.circleci/config.yml')
        snippet = """
# Enterprise
[![nox](https://github.com/starfleet/enterprise/actions/workflows/nox.yaml/badge.svg)](https://github.com/starfleet/enterprise/actions/workflows/nox.yaml)

""".lstrip()
        assert snippet in gen_pkg.read_text('readme.md')

        # No nox: the default should switch for circleci when GH is not used
        package.generate(use_gh_nox=False)
        assert not package.exists('.github/workflows/nox.yaml')
        assert package.exists('.circleci/config.yml')
        snippet = """
# Enterprise

""".lstrip()
        assert snippet in package.read_text('readme.md')

        # No CI
        package.generate(use_gh_nox=False, use_circleci=False)
        assert not package.exists('.github/workflows/nox.yaml')
        assert not package.exists('.circleci/config.yml')

    def test_scripts(self, gen_pkg: Package, package: Package):
        # No script by default
        proj = gen_pkg.toml_config('pyproject.toml')
        assert proj.project.get('scripts') is None
        snippet = """
readme = 'readme.md'


[dependency-groups]
"""
        assert snippet in gen_pkg.read_text('pyproject.toml')

        # Script
        package.generate(script_name='ent')
        snippet = """
readme = 'readme.md'


[project.scripts]
'ent' = 'enterprise.cli:main'


[dependency-groups]
"""
        assert snippet in package.read_text('pyproject.toml')


class TestTemplateWithSandbox:
    """
    Sandbox tests take longer.  Separate them out for easier targeting of quicker tests.

    There is some overlap with the test_sandbox tests.  These integration tests are focused on
    ensuring template is setup as expected by actually running commands not just expecting
    config files.
    """

    @pytest.fixture(scope='class')
    def gen_pkg(self, tmp_path_factory):
        temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
        package = Package(temp_path)
        package.generate()
        return package

    @pytest.fixture(scope='class')
    def sb(self, gen_pkg: Package):
        with gen_pkg.sandbox() as sb:
            yield sb

    def test_version(self, sb: Container):
        result = sb.uv('run', 'hatch', 'version', capture=True)
        assert result.stdout.strip() == '0.1.0'

    def test_python_and_venv(self, sb: Container):
        # Delete the .venv so it's re-created otherwise this test will be flaky
        sb.path_rm('.venv')

        # Default python version
        result = sb.mise_exec('python', '--version', capture=True)
        assert result.stdout.strip().startswith('Python 3.13.')

        # Mise should be configured to create the venv if it doesn't exist
        assert 'mise creating venv with uv at: ~/project/.venv' in result.stderr.strip()

        # Ensure slug is set and mise is activating the virtualenv
        assert sb.mise_env('PROJECT_SLUG', 'VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT') == [
            'project',
            '/home/ubuntu/project/.venv',
        ]

    def test_venv_not_nested(self, sb: Container):
        """Ensure using a non-nested venv defined by UV_PROJECT_ENVIRONMENT works"""

        with sb.place(data_fpath('mise-config.toml'), '~/.config/mise/config.toml'):
            result = sb.mise_exec('python', '--version', capture=True)
            py_ver = result.stdout.strip()
            assert (
                'mise creating venv with uv at: ~/.cache/uv-venvs/project' in result.stderr.strip()
            )

            assert sb.mise_env('VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT') == [
                '/home/ubuntu/.cache/uv-venvs/project',
                '/home/ubuntu/.cache/uv-venvs/project',
            ]

            result = sb.mise_exec('uv', 'pip', 'freeze', capture=True)
            assert (
                result.stderr.strip()
                == f'Using {py_ver} environment at: /home/ubuntu/.cache/uv-venvs/project'
            )

    def test_tasks(self, package: Package):
        package.generate(hatch_version_tag_sign=False)

        with package.sandbox() as sb:
            # Task listing
            task_meta = sb.mise('tasks', '--json', json=True)

            assert len(task_meta) == 4
            task_meta = sorted(task_meta, key=lambda rec: rec['name'])

            bootstrap = LazyDict(task_meta[0])
            assert bootstrap.name == 'bootstrap'
            assert bootstrap.description == 'Bootstrap project'

            bump = LazyDict(task_meta[1])
            assert bump.name == 'bump'
            assert bump.description == 'Bump version'

            # Run bootstrap
            assert not sb.path_exists('.git')
            assert not sb.path_exists('.git/hooks/pre-commit')
            assert not sb.path_exists('uv.lock')

            sb.mise('run', 'bootstrap')

            assert sb.path_exists('.git')
            assert sb.path_exists('.git/hooks/pre-commit')
            assert sb.path_exists('uv.lock')

            # Run bump
            sb.mise('run', 'bump', '--no-push')
            result = sb.uv('run', 'hatch', 'version', capture=True)
            date_str = dt.datetime.utcnow().date().strftime(r'%Y%m%d')
            assert result.stdout.strip() == f'0.{date_str}.1'

    def test_script_run(self, package: Package):
        package.generate(script_name='ent')

        with package.sandbox() as sb:
            result = sb.uv('run', 'ent', capture=True)
            assert 'Hello from enterprise.cli' in result.stdout
