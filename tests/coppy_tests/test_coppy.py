from pathlib import Path

from coppy.sandbox import Container


class TestCoppy:
    def test_build_installed_coppy(self, tmp_path: Path):
        with Container(tmp_path, mount_coppy=True) as sb:
            result = sb.exec('coppy', 'version', capture=True)
            assert result.stdout.strip().startswith('coppy version: ')

    def test_create_then_update(self, tmp_path: Path):
        with Container(tmp_path, copy_coppy=True) as sb:
            sb.git_commit(sb.c_coppy_dpath, tag='v100.0', init=True)

            sb.exec(
                'copier',
                'copy',
                '--trust',
                '--quiet',
                '--vcs-ref',
                'HEAD',
                '--defaults',
                '--data',
                'project_name=foo',
                '--data',
                'gh_org=starfleet',
                '--data',
                'author_name=Picard',
                '--data',
                'author_email=jpicard@starfleet.space',
                '--data',
                'coppy_dep_url=/home/ubuntu/coppy-pkg',
                '/home/ubuntu/coppy-pkg',
                sb.c_proj_dpath,
            )

            assert sb.host_proj_dpath.joinpath('mise.toml').exists()
            assert not sb.host_proj_dpath.joinpath('full-phasers.txt').exists()

            # Copier won't update if the target directory isn't clean
            sb.git_commit(sb.c_proj_dpath, init=True)

            # New file committed to the coppy template
            sb.exec('touch', sb.c_coppy_dpath / 'template/full-phasers.txt')
            sb.git_commit(sb.c_coppy_dpath)

            # Shouldn't make an update because, by default, HEAD is not used and we didn't tag
            # after adding full-phasers.txt.
            sb.exec('coppy', 'update')
            assert not sb.host_proj_dpath.joinpath('full-phasers.txt').exists()

            # But we can tell it to pull from the head instead
            sb.exec('coppy', 'update', '--head')
            assert sb.host_proj_dpath.joinpath('full-phasers.txt').exists()
