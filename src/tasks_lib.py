from pathlib import Path

from coppy.utils import sub_run  # noqa


proj_root = Path(__file__).parent.parent


def demo_dest_default() -> Path:
    home_tmp = Path().home() / 'tmp'
    dest_dpath = home_tmp if home_tmp.exists() else Path('/tmp')
    return dest_dpath / 'copier-py-package-demo'
