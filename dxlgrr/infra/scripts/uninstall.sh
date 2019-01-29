#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlgrr"}

rm -r "${INSTALL_DIRECTORY}"
rm -r /etc/systemd/system/dxlgrr.service

systemctl daemon-reload

pip uninstall dxlgrr
