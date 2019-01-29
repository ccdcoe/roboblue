#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlgrr"}

pip install ../robobluekit
pip install .

if [[ ! -d "${INSTALL_DIRECTORY}" ]]; then
    mkdir "${INSTALL_DIRECTORY}"
    mkdir "${INSTALL_DIRECTORY}/config"
fi

cp ./config/dxlgrr.config "${INSTALL_DIRECTORY}/config/dxlgrr.config"
cp ./config/monitoring.config "${INSTALL_DIRECTORY}/config/monitoring.config"

cp ./infra/dxlgrr.service /etc/systemd/system/

systemctl daemon-reload
