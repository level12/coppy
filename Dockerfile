from ghcr.io/level12/ubuntu-mive:24-3.13

arg UBUNTU_UID=1000

# The id of the user that is active whn running the docker container sandbox needs to match the
# id of the host user that is running the tests and generating the package files that get mounted
# into the docker container when it's running.
user root
run userdel ubuntu && \
    useradd -s /bin/bash -u ${UBUNTU_UID} ubuntu &&\
    chown -R ubuntu:ubuntu /home/ubuntu
user ubuntu

env USER=ubuntu
workdir /home/ubuntu

run mkdir project \
    && mkdir -p ~/.config/mise \
    && mkdir -p ~/.cache/uv-venvs \
    && git config --global user.name 'Jean-Luc Picard' \
    && git config --global user.email 'j.l.Picard@starfleet.uni' \
    && uv tool install --with copier-templates-extensions copier

entrypoint ["/bin/sleep"]
cmd ["5"]
