#!/usr/bin/env bash
# 把下載好的白皮書/規格 zip 搬到母機的 docs 目錄並解壓

SRC_DIR="$HOME/Downloads"
DEST_DIR="/srv/cockswain-core/docs/specs"

mkdir -p "$DEST_DIR"

# 你也可以改成 *.zip，看你之後要丟的檔名規則
for f in "$SRC_DIR"/*.zip; do
  [ -e "$f" ] || continue

  echo "[move_docs] found: $f"
  # 先搬
  sudo mv "$f" "$DEST_DIR"/
  fn=$(basename "$f")

  # 再解
  (
    cd "$DEST_DIR" || exit 1
    sudo unzip -o "$fn" >/dev/null 2>&1
    echo "[move_docs] unpacked: $fn"
  )
done
