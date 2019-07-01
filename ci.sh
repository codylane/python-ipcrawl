#!/bin/bash -e

CMD="${BASH_SOURCE[0]}"
BIN_DIR="${CMD%/*}"
cd ${BIN_DIR}
BIN_DIR="${PWD}"

export PATH="${HOME}/miniconda/bin:${PATH}"
MINICONDA_INSTALL_DIR="${HOME}/miniconda"

install_miniconda() {
  local MINICONDA_INSTALLER="Miniconda3-latest-Linux-x86_64.sh"

  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ${MINICONDA_INSTALLER}
  chmod 755 ${MINICONDA_INSTALLER}

  ./${MINICONDA_INSTALLER} -b -p ${MINICONDA_INSTALL_DIR}

}

command -v 'conda' || install_miniconda
[ -f "${MINICONDA_INSTALL_DIR}/etc/profile.d/conda.sh" ] && . "${MINICONDA_INSTALL_DIR}/etc/profile.d/conda.sh"

# in order to keep travis from timeout problems we touch the db
touch ipcrawl.sqlite3

. ./init.sh

inv clean
tox
