#!/bin/bash

# 安全更新 / 新增 .env 變數的小工具
upsert_env() {
  local env_file="$1"
  local var="$2"
  local val="$3"

  touch "$env_file"
  if grep -qE "^${var}=" "$env_file"; then
    sed -i "s/^${var}=.*/${var}=${val}/" "$env_file"
  else
    printf '%s=%s\n' "$var" "$val" >> "$env_file"
  fi
}
