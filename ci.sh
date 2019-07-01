#!/bin/bash -e

CMD="${BASH_SOURCE[0]}"
BIN_DIR="${CMD%/*}"
cd ${BIN_DIR}
BIN_DIR="${PWD}"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"

# in order to keep travis from timeout problems we touch the db
touch ipcrawl.sqlite3

. ./init.sh

inv clean
tox -e bandit,coverage,docs-html,flake8,py37
