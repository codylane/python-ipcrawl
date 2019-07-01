#!/bin/bash -e

CMD="${BASH_SOURCE[0]}"
BIN_DIR="${CMD%/*}"
cd ${BIN_DIR}
BIN_DIR="${PWD}"

[ -f /usr/local/miniconda3/etc/profile.d/conda.sh ] && . /usr/local/miniconda3/etc/profile.d/conda.sh
[ -f /etc/profile.d/miniconda.sh ] && . /etc/profile.d/miniconda.sh

export USER_UID=$(id -u $USER)
export USER_GID=$(id -g $USER)

PROJNAME="ipcrawl"

CONDA_ENV_PYTHON36="3.6"
CONDA_ENV_NAME36="${BIN_DIR##*/}-${CONDA_ENV_PYTHON36}"

CONDA_ENV_PYTHON="3.7"
CONDA_ENV_NAME="${BIN_DIR##*/}-${CONDA_ENV_PYTHON}"

OS_TYPE="${OS_TYPE:-}"

export PATH="$PWD/bin:$PWD/:$PATH"

BLACK="\033[0;30m"
BLACKBOLD="\033[1;30m"
RED="\033[0;31m"
REDBOLD="\033[1;31m"
GREEN="\033[0;32m"
GREENBOLD="\033[1;32m"
YELLOW="\033[0;33m"
YELLOWBOLD="\033[1;33m"
BLUE="\033[0;34m"
BLUEBOLD="\033[1;34m"
PURPLE="\033[0;35m"
PURPLEBOLD="\033[1;35m"
CYAN="\033[0;36m"
CYANBOLD="\033[1;36m"
WHITE="\033[0;37m"
WHITEBOLD="\033[1;37m"

get_os_type() {

  case "$(uname -s)" in

    Darwin)
      OS_TYPE="osx"
      return 0
    ;;

    Linux)
      OS_TYPE="linux"
      return 0
    ;;

    *)
      return 1
    ;;

  esac

}

has_conda_env() {
  conda list -n "${1}" 2>&1 >>/dev/null 2>&1
}

err() {
  echo "ERR: $* exiting" >&2
  exit 1
}


info() {
	local MSG_COLOR="${1:-$WHITE}"
	shift

	echo -en "${MSG_COLOR}${@}\033[0m"
  echo
}

activate-ci() {

  info "$GREEN" "Activating CI..."
  echo

  run-pip-if-recent-requirements-change "${BIN_DIR}/test-requirements.txt"

  CSV_FILES=$(find ${BIN_DIR}/data/geolite2 -name '*.csv')
  if [ -z "${CSV_FILES}" ]; then

    info "$GREEN" "Geolite database files do not exist yet, so I'll download them for you."
    inv download-geolite-dbs
  fi

  local sqlite3_filename="${BIN_DIR}/ipcrawl.sqlite3"

  if [ ! -f "${sqlite3_filename}" ]; then

    info "$GREEN" "The sqlite database ${sqlite3_filename} does not exist yet so i'll populate this for you."
    inv populate-sqlite3

  fi

}

activate-prod() {

  info "$GREEN" "Activating PROD..."
  echo

}

activate-env() {
  local ACTIVATE_ENV="${1}"

  case "$ACTIVATE_ENV" in

    prod|production)
      activate-prod
      ;;

    *)
      activate-ci
      ;;

  esac
}


filetime-last-change-in-seconds() {

  stat -c %Z "${1}"

}

get-file-contents() {

  cat "${1}" 2>>/dev/null || echo ""

}

get-cache-filename() {

  local _default_cache="${1}"
  is-conda-env-active && _default_cache="${1}-${CONDA_DEFAULT_ENV}" || _default_cache="${1}"

  local CACHE_FILENAME="${BIN_DIR}/.${_default_cache##*/}.lcts"

  echo "${CACHE_FILENAME}"

}

update-cache-file() {

  local DEFAULT_CACHE_FILENAME=$(get-cache-filename "${1}")
  local CHECK_FILENAME="${1}"
  local CACHE_FILENAME="${2:-${DEFAULT_CACHE_FILENAME}}"
  local LAST_CHANGE_TIME_SECS=$(filetime-last-change-in-seconds "${CHECK_FILENAME}")

  info "$GREEN" "update-cache-file: DEFAULT_CACHE_FILENAME=${DEFAULT_CACHE_FILENAME} CACHE_FILENAME=$CACHE_FILENAME"

  echo "${LAST_CHANGE_TIME_SECS}" > "${CACHE_FILENAME}"

  echo $LAST_CHANGE_TIME_SECS

}


cache-file-last-change-in-seconds() {

  [ -z "${1}" ] && err "Please pass a filename path as the first argument"

  local CHECK_FILENAME="${1}"
  local CACHE_FILENAME=$(get-cache-filename "${1}")

  # get last change time
  local LAST_CHANGE_TIME_SECS=$(filetime-last-change-in-seconds "${CHECK_FILENAME}")

  # if cache file does not exist, display seconds since list last change and return
  if [ ! -f "${CACHE_FILENAME}" ]; then
    echo $LAST_CHANGE_TIME_SECS
    return
  fi

  # cache file exists, get cache file last change time stamp (LCTS)
  local CACHE_FILE_LCTS=$(get-file-contents "${CACHE_FILENAME}")

  local DELTA_LCTS=$((LAST_CHANGE_TIME_SECS - CACHE_FILE_LCTS))
  [ $DELTA_LCTS -lt 0 ] && DELTA_LCTS=$((DELTA_LCTS * -1))

  echo $DELTA_LCTS

}

debug_console() {

	echo "#############|  Entering DEBUG mode  |####################";
	CMD=
  set -x
	while [ "${CMD}" != "exit" ]; do
			read -p "> " CMD
			case "${CMD}" in

					vars)
						(set -o posix ; set)
						;;

					exit|quit)
						;;

					*)
						eval "${CMD}"
						;;
			esac
	done
  set +x
	echo "#############|  End of DEBUG mode |####################";

}

is-conda-env-active() {

  # If not NULL, environment is active, rc=0, otherwise rc=1
  [ -n ${CONDA_DEFAULT_ENV} ]

}

run-pip-if-recent-requirements-change() {
  local REQUIREMENTS_FILE="${1}"
  local CACHE_FILE=

  info "${GREEN}" "The active conda environment is: '${CONDA_DEFAULT_ENV}'"
  CACHE_FILE=$(get-cache-filename "${REQUIREMENTS_FILE}")

  info "${GREEN}" "cache state file: ${CACHE_FILE}"

  [ -f "${REQUIREMENTS_FILE}" ] || err "The requirements file: ${REQUIREMENTS_FILE} does not exist"
  info "${GREEN}" "REQUIREMENTS_FILE=$REQUIREMENTS_FILE"

  local CACHE_FILE_LCTS=$(cache-file-last-change-in-seconds "${REQUIREMENTS_FILE}")
  info "${GREEN}" "CACHE_FILE_LCTS=$CACHE_FILE_LCTS"

  if [ ${CACHE_FILE_LCTS} -ne 0 ]; then
    info "${GREEN}" "Refreshing requirements deps"
    update-cache-file "${REQUIREMENTS_FILE}" "${CACHE_FILE}" >>/dev/null

    pip install -r "${REQUIREMENTS_FILE}"
    [ -f setup.py ] && pip install -e . || true
  fi

}

init-osx() {

  info "$YELLOWBOLD" "WARNING: there is no handler for osx yet"

}

init-linux() {

  info "$YELLOWBOLD" "WARNING: there is no handler for linux yet"

}

coverage_report() {

  coverage run -m pytest || true
  coverage report --show-missing

}

bandit_report() {

  bandit --ini tox.ini -r "$@"

}

create-conda-env() {

    local NAME="${1}"
    local PYTHON="${2}"

    [ -z "${1}" ] && err "Please pass NAME as first argument to create-conda-env"
    [ -z "${2}" ] && err "Please pass PYTHON as second argument to create-conda-env"

    conda create -y -n "${NAME}" python="${PYTHON}"

    # activate conda environment
    conda activate ${NAME}

    # remove last change time stamps
    rm -f .*.lcts

    run-pip-if-recent-requirements-change "${BIN_DIR}/requirements.txt"

    conda deactivate

}

## main ##

[ "$(command -v conda)" != "conda" ] && err "Please install conda or source the miniconda conda.sh file first"
[ -z "${CONDA_ENV_NAME36}" ] && err "Please set CONDA_ENV_NAME36"
[ -z "${CONDA_ENV_NAME}" ] && err "Please set CONDA_ENV_NAME"
[ -z "${PROJNAME}" ] && err "please set PROJNAME"

info "$GREEN" "BIN_DIR=${BIN_DIR}"

info "$GREEN" "CONDA_ENV_NAME36=$CONDA_ENV_NAME36"
info "$GREEN" "CONDA_ENV_NAME=$CONDA_ENV_NAME"
info "$GREEN" "CONDA_ENV_PYTHON36=$CONDA_ENV_PYTHON36"
info "$GREEN" "CONDA_ENV_PYTHON=$CONDA_ENV_PYTHON"

get_os_type || err "The OS type $OS_TYPE is not supported for local development"

eval "init-${OS_TYPE}"

has_conda_env "${CONDA_ENV_NAME36}" || create-conda-env "${CONDA_ENV_NAME36}" "${CONDA_ENV_PYTHON36}"
has_conda_env "${CONDA_ENV_NAME}" || create-conda-env "${CONDA_ENV_NAME}" "${CONDA_ENV_PYTHON}"

conda activate ${CONDA_ENV_NAME36}
run-pip-if-recent-requirements-change "${BIN_DIR}/requirements.txt"

conda activate ${CONDA_ENV_NAME}
run-pip-if-recent-requirements-change "${BIN_DIR}/requirements.txt"

export PATH="${PATH}:/usr/local/miniconda3/envs/${CONDA_ENV_NAME36}/bin"

activate-env "${1:-ci}"
