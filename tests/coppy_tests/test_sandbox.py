from pathlib import Path

import pytest

from coppy.testing import Package


class TestContainer:
    @pytest.fixture(scope='class')
    def package(self, tmp_path_factory):
        temp_path: Path = tmp_path_factory.mktemp('test-py-pkg')
        package = Package(temp_path)
        package.generate()
        return package

    def test_sandbox(self, package: Package):
        """Ensure mise, uv, and python are all setup in the sandbox as expected"""

        with package.sandbox() as sb:
            py_ver = '3.13.'
            result = sb.mise_exec('python', '--version', capture=True)
            mise_py_ver = result.stdout.strip()
            assert py_ver in mise_py_ver
            assert 'mise creating venv with uv at: ~/project/.venv' in result.stderr.strip()

            result = sb.uv('pip', 'freeze', capture=True)
            assert len(result.stdout.strip().splitlines()) == 0

            result = sb.uv('run', 'python', '--version', capture=True)
            assert result.stdout.strip() == mise_py_ver

            # uv should be using the same virtualenv that mise created above.  If it's not,
            # something is probably wrong with the way the overlays are getting setup in the
            # sandbox.
            assert 'Creating virtual environment at: .venv' not in result.stderr.strip()

            # `uv run` should have triggered a `uv sync`
            result = sb.uv('pip', 'freeze', capture=True)
            assert len(result.stdout.strip().splitlines()) > 0

            nested_venv_dpath = '/home/ubuntu/project/.venv'
            assert sb.mise_env('VIRTUAL_ENV') == [nested_venv_dpath]
            result = sb.uv('run', 'printenv', 'VIRTUAL_ENV', capture=True)
            assert result.stdout.strip() == nested_venv_dpath

    def test_path_exists(self, package: Package):
        with package.sandbox() as sb:
            assert sb.path_exists('/home/ubuntu/project')
            assert sb.path_exists('/home/ubuntu/project/mise.toml')
            assert sb.path_exists('mise.toml')
            assert not sb.path_exists('.git')
