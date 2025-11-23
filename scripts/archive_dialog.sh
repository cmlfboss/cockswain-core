#!/usr/bin/env bash
#
# archive_dialog.sh
# 將對話暫存檔歸檔＋壓縮＋寫入索引
# 用於 L5 規則中的 QUEUE_ARCHIVE 行為
#

set -euo pipefail

BASE_DIR="/srv/cockswain-core"
TMP_DIR="${BASE_DIR}/tmp/dialog"
ARCHIVE_DIR="${BASE_DIR}/archive/dialog"
LOG_FILE="${BASE_DIR}/logs/archive_dialog.log"

mkdir -p "${TMP_DIR}" "${ARCHIVE_DIR}" "$(dirname "${LOG_FILE}")"

timestamp="$(date +'%Y%m%d-%H%M%S')"
host="$(hostname)"

# 接收來源檔（可用參數傳，也可從 stdin 接）
SRC_FILE="${1:-}"

if [[ -z "${SRC_FILE}" ]]; then
  # 沒傳檔名就從 stdin 暫存一份
  SRC_FILE="${TMP_DIR}/dialog-${timestamp}.txt"
  cat /dev/stdin > "${SRC_FILE}"
fi

if [[ ! -f "${SRC_FILE}" ]]; then
  echo "[${timestamp}] [ERROR] source file not found: ${SRC_FILE}" | tee -a "${LOG_FILE}"
  exit 1
fi

filename="$(basename "${SRC_FILE}")"
archive_name="${filename%.txt}-${timestamp}.tar.gz"
archive_path="${ARCHIVE_DIR}/${archive_name}"

tar -czf "${archive_path}" -C "$(dirname "${SRC_FILE}")" "${filename}"

# 建立簡單索引，給之後一次性入庫用
INDEX_FILE="${ARCHIVE_DIR}/index.csv"
if [[ ! -f "${INDEX_FILE}" ]]; then
  echo "timestamp,host,archive_file,src_file" > "${INDEX_FILE}"
fi
echo "${timestamp},${host},${archive_name},${SRC_FILE}" >> "${INDEX_FILE}"

echo "[${timestamp}] [OK] archived ${SRC_FILE} -> ${archive_path}" >> "${LOG_FILE}"

# 可以視情況清掉暫存
# rm -f "${SRC_FILE}"

exit 0
