import datetime
from pathlib import Path

import pytest

from coppy import utils
from coppy.utils import LazyDict

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
        assert config.project['requires-python'] == '~=3.13.0'
        assert gen_pkg.read_text('.python-version').strip() == '3.13'
        assert 'scripts' not in config.project

        author = LazyDict(config.project.authors[0])
        assert author.name == 'Picard'
        assert author.email == 'jpicard@starfleet.space'

    def test_pyproject_python_version_min(self, package: Package):
        package.generate(python_version='3.13', python_version_min='3.12')

        config = package.toml_config('pyproject.toml')

        assert config.project['requires-python'] == '>=3.12'
        assert package.read_text('.python-version').strip() == '3.13'

    def test_ruff_tracks_python_version_min(self, gen_pkg: Package, package: Package):
        assert gen_pkg.toml_config('ruff.toml')['target-version'] == 'py313'

        package.generate(python_version='3.13', python_version_min='3.12')

        assert package.toml_config('ruff.toml')['target-version'] == 'py312'

    def test_hatchling_backend(self, gen_pkg: Package):
        config = gen_pkg.toml_config('pyproject.toml')
        hatch = gen_pkg.toml_config('hatch.toml')

        assert config['build-system']['requires'] == ['hatchling']
        assert config['build-system']['build-backend'] == 'hatchling.build'
        assert config.project.dynamic == ['version']
        assert hatch.build['dev-mode-dirs'] == ['src']
        assert hatch.version.source == 'regex'
        assert hatch.version.path == 'src/enterprise/version.py'

    def test_version_source(self, gen_pkg: Package):
        assert gen_pkg.read_text('src/enterprise/__init__.py') == ''
        assert gen_pkg.read_text('src/enterprise/version.py') == "VERSION = '0.1.0'\n"

    def test_static_files(self, gen_pkg: Package):
        assert gen_pkg.exists('.python-version')
        assert gen_pkg.exists('mise.lock')
        assert gen_pkg.exists('ruff.toml')
        assert gen_pkg.exists('.copier-answers-py.yaml')

    def test_supply_chain_configs(self):
        template_expected = {
            '.npmrc': 'min-release-age=3',
            'pnpm-workspace.yaml': 'minimumReleaseAge: 4320',
            'bunfig.toml': 'minimumReleaseAge = 259200',
            '.yarnrc.yml': 'npmMinimalAgeGate: "3d"',
            'uv.toml': 'exclude-newer = "3 days"',
        }

        assert 'exclude-newer = "3 days"' in (utils.pkg_dpath / 'uv.toml').read_text()

        for rel_fpath, expected_text in template_expected.items():
            assert expected_text in (utils.pkg_dpath / 'template' / rel_fpath).read_text()

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
        sb.mise_exec('uv', 'sync')
        result = sb.mise('run', 'version', 'show', capture=True)
        assert result.stdout.strip() == '0.1.0'

    def test_python_and_venv(self, sb: UserBox):
        # Default python version
        py_ver = sb.mise_exec('python', '--version')
        assert py_ver.startswith('Python 3.13.')

        # Ensure slug is set and mise is activating the virtualenv
        venv, uv_proj_env, uv_python = sb.mise_env(
            'VIRTUAL_ENV',
            'UV_PROJECT_ENVIRONMENT',
            'UV_PYTHON',
        )
        assert venv.endswith('template-with-sandbox/.venv')
        assert venv == uv_proj_env
        assert uv_python == f'{venv}/bin/python'

    def test_uv_project_environment(self):
        """Ensure using a non-nested venv defined by UV_PROJECT_ENVIRONMENT works"""

        # Need a separate package b/c mise caches values in mise.toml and they don't refresh even
        # though we change to centralized_venvs below. Use a unique path to avoid reusing an old
        # centralized venv from a previous test run.
        ident = 'template-central-venvs-' + datetime.datetime.now(datetime.UTC).strftime('%H%M%S%f')
        pkg = UserPackage(ident)
        pkg.generate()

        with pkg.sandbox(centralized_venvs=True) as sb:
            py_ver = sb.mise_exec('python', '--version')
            venv, uv_proj_env = sb.mise_env('VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT')
            hash_part = Path(venv).name.removeprefix(f'{ident}-')

            assert venv == uv_proj_env
            assert Path(venv).parent == Path('/home/coppy-tests/.cache/uv-venvs')
            assert Path(venv).name.startswith(f'{ident}-')
            assert hash_part
            assert len(hash_part) == 4
            assert hash_part.isalnum()
            assert hash_part == hash_part.lower()

            result = sb.mise_exec('uv', 'pip', 'freeze', stderr=True)
            assert result == f'Using {py_ver} environment at: {venv}'

    def test_uv_project_environment_hash_disabled(self):
        ident = 'template-central-venvs-zero-' + datetime.datetime.now(datetime.UTC).strftime(
            '%H%M%S%f',
        )
        pkg = UserPackage(ident)
        pkg.generate()

        mise_toml_fpath = pkg.path('mise.toml')
        mise_toml_fpath.write_text(
            mise_toml_fpath.read_text().replace('[env]\n', "[env]\nCOPPY_VENV_HASH_LEN = '0'\n", 1),
        )

        with pkg.sandbox(centralized_venvs=True) as sb:
            py_ver = sb.mise_exec('python', '--version')
            venv, uv_proj_env = sb.mise_env('VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT')

            assert venv == uv_proj_env
            assert Path(venv).parent == Path('/home/coppy-tests/.cache/uv-venvs')
            assert Path(venv).name == ident

            result = sb.mise_exec('uv', 'pip', 'freeze', stderr=True)
            assert result == f'Using {py_ver} environment at: {venv}'

    def test_tasks(self, pkg: UserPackage):
        # TODO: we should revisit the pkg vs sandbox isolation for a test like this that modifies
        # the package.  When the sandbox used docker, modifications in the sandbox didn't affect
        # subsequent runs because we created a new container for each sandbox and copied the
        # package into it.  We might want to have the sandbox generate packages as needed instead
        # of having a package use a sandbox.
        with pkg.sandbox() as sb:
            # Task listing
            task_meta = sb.mise('tasks', '--json', json=True)

            assert len(task_meta) == 4
            task_meta = {rec['name']: LazyDict(rec) for rec in task_meta}

            bootstrap = task_meta['bootstrap']
            assert bootstrap.name == 'bootstrap'
            assert bootstrap.description == 'Bootstrap project'

            version_task = task_meta['version']
            assert version_task.name == 'version'
            assert version_task.description == 'Manage version'

            # Prepare a minimal git repo so bump can create a commit and tag.
            assert not pkg.path_exists('.git')
            sb.exec('git', 'init')
            sb.exec('git', 'config', 'user.name', 'Coppy Tests')
            sb.exec('git', 'config', 'user.email', 'coppy-tests@example.com')
            sb.exec('git', 'add', '.')
            sb.exec('git', 'commit', '-m', 'initial commit')

            assert pkg.path_exists('.git')

            # Mirror real usage: initialize the project's managed environment before running tasks.
            sb.mise_exec('uv', 'sync')
            assert sb.mise_exec('python', '-c', 'import click, enterprise_tasks_lib') == ''

            # Run bump
            # Tests have no release signing key; exercise the environment-variable override while
            # keeping the generated bump command's signing default unchanged.
            sb.exec(
                'env',
                'COPPY_VERSION_SIGN=false',
                sb.local_bin_dpath / 'mise',
                'run',
                'version',
                'bump',
                '--no-push',
            )
            result = sb.mise('run', 'version', 'show', capture=True)
            version = result.stdout.strip()
            date_str = datetime.datetime.today().strftime(r'%Y%m%d')
            assert version == f'0.{date_str}.1'
            assert sb.exec_stdout('git', 'tag', '--list') == f'v{version}'
            assert f'Release v{version}' in sb.exec_stdout('git', 'cat-file', '-p', f'v{version}')

    def test_script_run(self, pkg: UserPackage):
        pkg.generate(script_name='ent')

        with pkg.sandbox() as sb:
            ent_hello = sb.uv_run('ent')
            assert 'Hello from enterprise.cli' in ent_hello
