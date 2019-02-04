#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlwazuh"}

rm -r "${INSTALL_DIRECTORY}"
rm -r /etc/systemd/system/dxlwazuh.service

systemctl daemon-reload

pip uninstall dxlwazuh
