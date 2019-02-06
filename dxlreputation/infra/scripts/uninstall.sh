#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlreputation"}

rm -r "${INSTALL_DIRECTORY}"
rm -r /etc/systemd/system/dxlreputation.service

systemctl daemon-reload

pip uninstall dxlreputation
