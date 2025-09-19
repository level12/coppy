#!/usr/bin/env bash
# [MISE] description="systemctl wrapper for test user"
# Only needed when testing the systemd units installed by test-user-prep.  Creating the task as
# a reminder of what the syntax is as `sudo -iu coppy-tests systemctl --user ...` doesn't work as
# expected.
sudo systemctl --user --machine coppy-tests@ "$@" || true
