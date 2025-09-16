from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import shutil
import tomllib

import copier

from coppy import utils
from coppy.sandbox import Container


tests_dpath = utils.pkg_dpath / 'tests' / 'coppy_tests'
data_dpath = tests_dpath / 'data'


def data_fpath(rel_path):
    return data_dpath.joinpath(rel_path)


def toml_load(fpath: Path):
    with fpath.open('rb') as f:
        return utils.LazyDict(tomllib.load(f))


class Package:
    def __init__(self, dpath: Path):
        self.dpath = dpath

    def generate(self, rm_first=True, **kwargs):
        kwargs.setdefault('project_name', 'Enterprise')
        kwargs.setdefault('author_name', 'Picard')
        kwargs.setdefault('author_email', 'jpicard@starfleet.space')
        kwargs.setdefault('script_name', '')
        kwargs.setdefault('gh_org', 'starfleet')

        if rm_first and self.dpath.exists():
            shutil.rmtree(self.dpath)

        copier.run_copy(
            utils.pkg_dpath.as_posix(),
            self.dpath.as_posix(),
            kwargs,
            unsafe=True,
            defaults=True,
            vcs_ref='HEAD',
        )

    def toml_config(self, fname):
        with self.dpath.joinpath(fname).open('rb') as f:
            return utils.LazyDict(tomllib.load(f))

    def path(self, path: str):
        return self.dpath.joinpath(path)

    def exists(self, path: str):
        return self.path(path).exists()

    def read_text(self, path: str):
        return self.path(path).read_text()

    @contextmanager
    def sandbox(self, *args, **kwargs) -> Iterator[Container]:
        with Container(self.dpath, *args, **kwargs) as sb:
            yield sb
