from pathlib import Path

from coppy.sandbox import Container


class TestCopierPy:
    def test_create_then_update(self, tmp_path: Path):
        with Container(tmp_path, copy_cppy=True) as sb:
            sb.git_commit(sb.c_cppy_dpath, tag='v100.0')

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
                'author_name=Picard',
                '--data',
                'author_email=jpicard@starfleet.space',
                '/home/ubuntu/cppy-pkg',
                sb.c_proj_dpath,
            )
            assert sb.host_proj_dpath.joinpath('mise.toml').exists()
            assert not sb.host_proj_dpath.joinpath('full-phasers.txt').exists()

            sb.uv('sync', '--no-dev', '--group', 'tasks')
            sb.git_commit(sb.c_proj_dpath, init=True)

            sb.exec('touch', sb.c_cppy_dpath / 'template/full-phasers.txt')
            sb.git_commit(sb.c_cppy_dpath)

            sb.exec('mise', 'trust')

            sb.exec('mise', 'copier-update')
            assert not sb.host_proj_dpath.joinpath('full-phasers.txt').exists()

            sb.exec('mise', 'copier-update', '--head')
            assert sb.host_proj_dpath.joinpath('full-phasers.txt').exists()
