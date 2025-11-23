#!/usr/bin/env bash
#
# create_task.sh
# 將 L5 決策結果轉成一筆待處理任務檔
#

set -euo pipefail

BASE_DIR="/srv/cockswain-core"
TASK_DIR="${BASE_DIR}/tasks/pending"
LOG_FILE="${BASE_DIR}/logs/create_task.log"

mkdir -p "${TASK_DIR}" "$(dirname "${LOG_FILE}")"

timestamp="$(date +'%Y%m%d-%H%M%S')"
host="$(hostname)"

TASK_TYPE="${1:-system-generic}"
PRIORITY="${2:-MEDIUM}"

task_file="${TASK_DIR}/${timestamp}-${TASK_TYPE}.json"

cat > "${task_file}" <<EOF
{
  "created_at": "${timestamp}",
  "host": "${host}",
  "task_type": "${TASK_TYPE}",
  "priority": "${PRIORITY}",
  "status": "PENDING",
  "source": "l5-decision",
  "notes": ""
}
EOF

echo "[${timestamp}] [OK] task created: ${task_file}" >> "${LOG_FILE}"

exit 0
