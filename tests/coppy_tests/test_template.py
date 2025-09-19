from pathlib import Path

import pytest

from coppy.utils import LazyDict, utc_now

from .libs.sandbox import UserBox
from .libs.testing import Package, UserPackage, data_fpath


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
    def pkg(self):
        package = UserPackage('template-with-sandbox')
        package.generate()
        return package

    @pytest.fixture(scope='class')
    def sb(self, pkg: Package):
        with pkg.sandbox() as sb:
            yield sb

    def test_version(self, sb: UserBox):
        result = sb.uv_run('hatch', 'version')
        assert result == '0.1.0'

    def test_python_and_venv(self, sb: UserBox):
        # Default python version
        py_ver = sb.mise_exec('python', '--version')
        assert py_ver.startswith('Python 3.13.')

        # Ensure slug is set and mise is activating the virtualenv
        venv, uv_proj_env = sb.mise_env(
            'VIRTUAL_ENV',
            'UV_PROJECT_ENVIRONMENT',
        )
        assert venv.endswith('template-with-sandbox/.venv')
        assert venv == uv_proj_env

    def test_uv_project_environment(self):
        """Ensure using a non-nested venv defined by UV_PROJECT_ENVIRONMENT works"""

        # Need a separate package b/c mise cache's the values in mise.toml and they don't refresh
        # even though we change to centralized_venvs below.
        pkg = UserPackage('template-central-venvs')
        pkg.generate()

        with pkg.sandbox(centralized_venvs=True) as sb:
            sb.mise_exec('uv', 'venv')

            py_ver = sb.mise_exec('python', '--version')

            assert sb.mise_env('VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT') == [
                '/home/coppy-tests/.cache/uv-venvs/template-central-venvs',
                '/home/coppy-tests/.cache/uv-venvs/template-central-venvs',
            ]

            result = sb.mise_exec('uv', 'pip', 'freeze', stderr=True)
            assert (
                result
                == f'Using {py_ver} environment at: /home/coppy-tests/.cache/uv-venvs/template-central-venvs'  # noqa: E501
            )

    def test_tasks(self, pkg: UserPackage):
        pkg.generate(hatch_version_tag_sign=False)

        # TODO: we should revisit the pkg vs sandbox isolation for a test like this that modifies
        # the package.  When the sandbox used docker, modifications in the sandbox didn't affect
        # subsequent runs because we created a new container for each sandbox and copied the
        # package into it.  We might want to have the sandbox generate packages as needed instead
        # of having a package use a sandbox.
        with pkg.sandbox() as sb:
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
            assert not pkg.path_exists('.git')
            assert not pkg.path_exists('.git/hooks/pre-commit')
            assert not pkg.path_exists('uv.lock')

            sb.mise('run', 'bootstrap')

            assert pkg.path_exists('.git')
            assert pkg.path_exists('.git/hooks/pre-commit')
            assert pkg.path_exists('uv.lock')

            # Run bump
            sb.mise('run', 'bump', '--no-push')
            hatch_ver = sb.uv_run('hatch', 'version')
            date_str = utc_now().date().strftime(r'%Y%m%d')
            assert hatch_ver == f'0.{date_str}.1'

    def test_script_run(self, pkg: UserPackage):
        pkg.generate(script_name='ent')

        with pkg.sandbox() as sb:
            ent_hello = sb.uv_run('ent')
            assert 'Hello from enterprise.cli' in ent_hello
