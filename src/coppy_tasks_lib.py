from os import environ
from pathlib import Path

from coppy.utils import sub_run  # noqa


proj_root = Path(__file__).parent.parent

demo_dpath = environ.get('DEMO_PKG_DPATH')
home_tmp = Path().home() / 'tmp'
sys_tmp = Path('/tmp')
demo_dname = 'coppy-demo-pkg'


def demo_dest_default() -> Path:
    if demo_dpath:
        return Path(demo_dpath).expanduser().resolve()

    for path in (home_tmp, sys_tmp):
        if path.exists():
            return path / demo_dname

    raise RuntimeError('No file system location found to place demo')
