#!/usr/bin/env bash
# 自動把下載資料夾的規格/白皮書 zip 搬到母機 docs 裡並解壓

SRC_DIR="/home/cocksmain/下載"
DEST_DIR="/srv/cockswain-core/docs/specs"

mkdir -p "$DEST_DIR"

# 只處理 .zip
for f in "$SRC_DIR"/*.zip; do
  [ -e "$f" ] || continue

  echo "[move_specs] found: $f"
  sudo mv "$f" "$DEST_DIR"/
  fn=$(basename "$f")

  (
    cd "$DEST_DIR" || exit 1
    sudo unzip -o "$fn" >/dev/null 2>&1
    echo "[move_specs] unpacked: $fn"
  )
done
