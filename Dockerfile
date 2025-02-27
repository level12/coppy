from ghcr.io/level12/ubuntu-mive:24-3.13

arg UBUNTU_UID=1000

# The id of the user that is active whn running the docker container sandbox needs to match the
# id of the host user that is running the tests and generating the package files that get mounted
# into the docker container when it's running.
user root
run userdel -r ubuntu && \
    useradd -s /bin/bash -u ${UBUNTU_UID} ubuntu
user ubuntu

env USER=ubuntu
workdir /home/ubuntu
run mkdir project && \
    mkdir -p ~/.config/mise && \
    mkdir -p ~/.cache/uv-venvs && \
    git config --global user.name 'Jean-Luc Picard' && \
    git config --global user.email 'j.l.Picard@starfleet.uni' && \
    # Reinstall Python b/c we deleted the install mive did when we delete the ubuntu user's home dir
    mise install python@3.13 && \
    # `mise sync python --uv` errors when when this directory isn't present.
    # Refs: https://github.com/jdx/mise/discussions/4474
    mkdir -p /home/ubuntu/.local/share/uv/python/ && \
    mise sync python --uv && \
    # User level copier install
    uv tool install copier --with copier-templates-extensions

workdir /home/ubuntu/coppy-pkg

# User level coppy install.  This is just enough to get the dependencies cached in the image to make
# the tests faster.  Anywhere we need coppy src files for a test, they are mounted into the
# container or copied fresh.  We don't wan tto copy all source files b/c that makes the docker
# build take longer and that slows down every test run due to the docker_build() fixture.
copy --chown=ubuntu:ubuntu src/coppy/__init__.py src/coppy/__init__.py
copy --chown=ubuntu:ubuntu src/coppy/version.py src/coppy/version.py
copy --chown=ubuntu:ubuntu pyproject.toml hatch.toml .
run uv tool install --editable .

entrypoint ["/bin/sleep"]
cmd ["5"]
