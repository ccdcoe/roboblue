#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlhistorian"}

rm -r "${INSTALL_DIRECTORY}"
rm -r /etc/systemd/system/dxlhistorian.service

systemctl daemon-reload

pip uninstall dxlhistorian
