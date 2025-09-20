#!/usr/bin/env bash
# [MISE] description="journalctl wrapper for test user"
sudo journalctl _SYSTEMD_USER_UNIT=mise-uv-update.service _SYSTEMD_USER_UNIT=mise-uv-update.timer _SYSTEMD_OWNER_UID=$(id -u coppy-tests)
