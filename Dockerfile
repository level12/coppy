from ghcr.io/level12/ubuntu-mive:24-3.13

arg UBUNTU_UID=1000

# The id of the user that is active whn running the docker container sandbox needs to match the
# id of the host user that is running the tests and generating the package files that get mounted
# into the docker container when it's running.
user root
run userdel -r ubuntu && \
    useradd -m -s /bin/bash -u ${UBUNTU_UID} ubuntu
user ubuntu

env USER=ubuntu
workdir /home/ubuntu

run mkdir project \
    && mkdir -p ~/.config/mise \
    && mkdir -p ~/.cache/uv-venvs

entrypoint ["/bin/sleep"]
cmd ["5"]
