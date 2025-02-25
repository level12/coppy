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
            py_meta: dict = sb.mise('ls', '--json', '--current', 'python', json=True)
            assert len(py_meta) == 1
            py_meta = py_meta[0]
            py_ver = py_meta['version']
            assert py_meta['requested_version'] == '3.13'
            assert (
                py_meta['install_path']
                == f'/home/ubuntu/.local/share/mise/installs/python/{py_ver}'
            )
            assert py_meta['source'] == {
                'type': 'idiomatic-version-file',
                'path': '/home/ubuntu/project/.python-version',
            }
            result = sb.mise_exec('python', '--version', capture=True)
            assert result.stdout.strip() == f'Python {py_ver}', sb.mise_env('PATH')
            assert 'mise creating venv with uv at: ~/project/.venv' in result.stderr.strip()

            result = sb.uv('pip', 'freeze', capture=True)
            assert len(result.stdout.strip().splitlines()) == 0

            result = sb.uv('run', 'python', '--version', capture=True)
            assert result.stdout.strip() == f'Python {py_ver}'
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
