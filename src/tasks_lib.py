from pathlib import Path

from coppy.utils import sub_run  # noqa


proj_root = Path(__file__).parent.parent

home_proj = Path().home() / 'projects'
home_tmp = Path().home() / 'tmp'
sys_tmp = Path('/tmp')
demo_dname = 'coppy-demo-pkg'


def demo_dest_default() -> Path:
    for path in (home_proj, home_tmp, sys_tmp):
        if path.exists():
            return path / demo_dname

    raise RuntimeError('No file system location found to place demo')
