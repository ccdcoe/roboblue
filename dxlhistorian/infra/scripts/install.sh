#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlhistorian"}

pip install .

if [[ ! -d "${INSTALL_DIRECTORY}" ]]; then
    mkdir "${INSTALL_DIRECTORY}"
    mkdir "${INSTALL_DIRECTORY}/config"
fi

cp ./config/dxlhistorian.config "${INSTALL_DIRECTORY}/config/dxlhistorian.config"

cp ./infra/dxlhistorian.service /etc/systemd/system/

systemctl daemon-reload
