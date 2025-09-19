from pathlib import Path

import pytest

from .libs.sandbox import UserBox
from .libs.testing import UserPackage


class TestUserBox:
    @pytest.fixture(scope='class')
    def package(self):
        package = UserPackage('test-sandbox')
        package.generate()
        return package

    def test_sudo_integration(self):
        sb = UserBox()
        assert sb.exec_stdout('id', '-un') == 'coppy-tests'
        assert sb.exec_stdout('printenv', 'PATH').startswith('/home/coppy-tests/.local/bin:')
        assert sb.uv_python('import os; print(os.getcwd())') == '/home/coppy-tests'
        assert (
            sb.uv_python('import os; print(os.getcwd())', cwd='/home/coppy-tests/tmp')
            == '/home/coppy-tests/tmp'
        )

    def test_sandbox(self, package: UserPackage):
        """Ensure mise, uv, and python are all setup in the sandbox as expected"""

        with package.sandbox() as sb:
            nested_venv_dpath = package.dpath / '.venv'

            # The sandbox runs `mise exec` which should result in the creation of the venv.
            assert nested_venv_dpath.exists()

            # Mise should be using the virtualenv
            assert sb.mise_env('VIRTUAL_ENV') == [nested_venv_dpath.as_posix()]

            # And just sanity check that uv is using the same venv
            virtual_env = sb.uv_run('printenv', 'VIRTUAL_ENV')
            assert virtual_env == nested_venv_dpath.as_posix()

            # Ensure the python version being used is what the project's pyproject.toml called
            # for.
            py_ver = '3.13.'
            mise_py_ver = sb.mise_exec('python', '--version')
            assert py_ver in mise_py_ver

            # Ensure mise and uv are both using the python executable from the venv
            mise_py_fpath = Path(
                sb.mise_exec(
                    'python',
                    '-c',
                    'import sys;print(sys.executable)',
                ),
            ).resolve()

            assert mise_py_fpath == nested_venv_dpath.joinpath('bin/python').resolve()

            executable_path = sb.uv_python('import sys;print(sys.executable)')
            assert Path(executable_path).resolve() == mise_py_fpath

            # `uv run` should have triggered a `uv sync`
            result = sb.uv('pip', 'freeze', capture=True)
            assert len(result.stdout.strip().splitlines()) > 0
