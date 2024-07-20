# This is the image used by .circleci/config.yml
# Its customized to avoid the mise install on every test run.

arg UBUNTU_VERSION=22.04
from cimg/base:current-${UBUNTU_VERSION} as this-base

workdir /home/circleci/project
# Virtual env should not be on /tmp so that the pre-install of reqs done in the nox target
# (below) will persist into the image.
env WORKON_HOME '/home/circleci/.cache'
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

# Remove the file or git checkout in CircleCI errors b/c directory isn't empty
run mise exec -- python -m pip install uv \
    && rm mise.toml


#### TARGET: nox  ####
from this-base as nox

# TARGET NOTE: lots of copying instead of bind mounting a volume to avoid docker writing files as
# root to the host file system.  Could have used a .dockerignore that matches the .gitignore and
# likely ended up with similar results.  But I (RLS) think explicit test failures from not copying
# something into the image are easier to troubleshoot than letting the .dockerignore get outdated
# and then have the image be larger.

# Prep for the reqs install just below
copy --chown=circleci:circleci mise.toml .
copy --chown=circleci:circleci requirements requirements

# This duplicates what is in the ci-tests task, but by doing it here we cache the results in the
# image which saves runtime whenever the reqs haven't changed, which is often.  uv still runs but
# everything is up to date, so the run only takes tens of ms.
run mise exec -- uv pip install -U uv
run mise exec -- uv pip install -r requirements/ci.txt

# Similar to the above, save pre-commit environments in image for faster runtimes
copy --chown=circleci:circleci .pre-commit-config.yaml .
copy --chown=circleci:circleci .git .git
run mise exec -- uv pip install -c requirements/dev.txt pre-commit
run mise exec -- pre-commit install-hooks

copy --chown=circleci:circleci \
    copier.yaml \
    copier_py_package.py \
    extensions.py \
    hatch.toml \
    mise.toml \
    noxfile.py \
    pyproject.toml \
    ruff.toml \
    tasks_lib.py \
    test_*.py \
    .
copy --chown=circleci:circleci ci/pytest.ini ci/pytest.ini
copy --chown=circleci:circleci mise/tasks mise/tasks
copy --chown=circleci:circleci template template

entrypoint ["/home/circleci/.local/bin/mise", "run", "ci-nox"]
cmd []
