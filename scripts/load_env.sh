#!/usr/bin/env bash
#
# load_env.sh
# 從 /srv/cockswain-core/.env 載入環境變數
#

ENV_FILE="/srv/cockswain-core/.env"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "${ENV_FILE}" | xargs -d '\n')
else
  echo "[WARN] .env not found at ${ENV_FILE}, skip loading env"
fi
