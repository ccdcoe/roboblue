#!/usr/bin/env bash
set -e

INSTALL_DIRECTORY=${INSTALL_DIRECTORY:-"/etc/dxlgrr"}

REPOSITORY=${REPOSITORY:-"github.com/ccdcoe/roboblue"}

# Try installing the robobluekit from possible sources
if [[ -d "../robobluekit" ]]; then
    pip install ../robobluekit
elif [[ -x "$(command -v git)" ]]; then
    pip install git+https://${REPOSITORY}.git@master#subdirectory=robobluekit
else
    echo "No robobluekit or git found. Either is required to install DXL GRR"
    exit 1
fi

pip install .

if [[ ! -d "${INSTALL_DIRECTORY}" ]]; then
    mkdir "${INSTALL_DIRECTORY}"
    mkdir "${INSTALL_DIRECTORY}/config"
fi

cp ./config/dxlgrr.config "${INSTALL_DIRECTORY}/config/dxlgrr.config"
cp ./config/monitoring.config "${INSTALL_DIRECTORY}/config/monitoring.config"

cp ./infra/dxlgrr.service /etc/systemd/system/

systemctl daemon-reload
