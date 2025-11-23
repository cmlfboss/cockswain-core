#!/usr/bin/env bash
set -euo pipefail

BASE="/srv/cockswain-core"

echo "[Phase1] 初始化 cockswain-core 目錄結構..."

mkdir -p \
  "$BASE/ai-core" \
  "$BASE/docs/specs" \
  "$BASE/docs/whitepapers" \
  "$BASE/logs/core" \
  "$BASE/logs/services" \
  "$BASE/logs/security" \
  "$BASE/scripts/core" \
  "$BASE/scripts/maintenance" \
  "$BASE/scripts/security" \
  "$BASE/configs/docker" \
  "$BASE/configs/systemd" \
  "$BASE/configs/app" \
  "$BASE/backups/db" \
  "$BASE/backups/docs" \
  "$BASE/backups/configs"

# 權限與擁有者設定（符合你「本機自主管理」的思路）
chown -R cocksmain:cocksmain "$BASE"
chmod 750 "$BASE"
chmod -R 750 "$BASE/logs" "$BASE/backups" "$BASE/scripts" "$BASE/configs" "$BASE/ai-core"

# 簡單 README，讓未來看到也知道這裡是啥
cat <<'RMD' > "$BASE/README-core.txt"
Cockswain Mother-Machine Core
--------------------------------
Node: cocksmain-node-00
Phase: Core Phase 1 (Base Layout)
Owner: cocksmain
This tree is the canonical home for:
- ai-core      : hybrid engine, L1-L7, mind-proxy, etc.
- docs         : specs, whitepapers, governance docs.
- logs         : core/service/security logs.
- configs      : docker, systemd, app-level configs.
- scripts      : core automation and maintenance.
- backups      : db/docs/configs backups.

Do NOT put secrets directly here. Secrets live in local .env files only.
RMD

echo "[Phase1] 目錄初始化完成。"
