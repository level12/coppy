# This is the image used by .circleci/config.yml
# Its customized to avoid the mise install on every test run.

arg UBUNTU_VERSION=22.04
from cimg/base:current-${UBUNTU_VERSION}

env WORKON_HOME '/tmp'
workdir /home/circleci/project
copy mise.toml .

# The bootstrap script commits, so git needs to be configured or it will error out
run git config --global user.email "foo@bar.com" \
    && git config --global user.name "foo" \
    && git config --global init.defaultBranch main \
    && curl https://mise.run | sh \
    # Experimental necessary for task support
    && mise settings set experimental true \
    && mise settings set python_venv_auto_create true \
    && mise trust \
    && mise install

# Remove the file or git checkout errors b/c directory isn't empty
run rm mise.toml
