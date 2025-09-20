from pathlib import Path
import shutil

import coppy.paths


class dirs(coppy.paths.dirs):
    systemd = coppy.paths.dirs.pkg / 'systemd'
    tests = coppy.paths.dirs.pkg / 'tests'
    coppy_tests = tests / 'coppy_tests'
    test_data = coppy_tests / 'data'

    tmp = coppy.paths.dirs.pkg / 'tmp'
    dist = tmp / 'dist'


def tmp_dir(base_dir: Path, prefix: str):
    """Consecutive temporary directory paths modeled after pytest's tmp_path fixture."""
    prefix = f'{prefix}-'

    base_dir.mkdir(exist_ok=True)

    # Remove symlink for previous run to avoid getting it in the existing_dirs lookup
    current_link = base_dir / f'{prefix}current'
    if current_link.exists():
        current_link.unlink()

    # Find all existing directories sorted by creation time
    existing_dirs = sorted(
        base_dir.glob(f'{prefix}*'),
        key=lambda x: int(x.name.rsplit('-', 1)[-1]),
    )

    # Keep only the last three runs, delete others
    if len(existing_dirs) > 2:
        for dir_to_remove in existing_dirs[:-2]:
            shutil.rmtree(dir_to_remove)

    # Create new temp directory for the current run
    if existing_dirs:
        last_dir = existing_dirs[-1]
        count = int(last_dir.name.replace(prefix, '', 1))
    else:
        count = 0

    run_dir = base_dir / f'{prefix}{count + 1}'
    run_dir.mkdir()

    current_link.symlink_to(run_dir)

    return run_dir
