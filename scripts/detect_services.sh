#!/usr/bin/env bash
# 掃描系統裡跟 cockswain 相關的 systemd 服務，輸出成 JSON
OUT="/srv/cockswain-core/tmp/services.json"
mkdir -p /srv/cockswain-core/tmp

services=$(systemctl list-units --type=service | grep cockswain | awk '{print $1, $3, $4}')

{
  echo '{'
  echo '  "generated_at": "'$(date +%Y-%m-%dT%H:%M:%S)'",'
  echo '  "services": ['
  first=1
  while read -r name load active; do
    [[ -z "$name" ]] && continue
    [[ "$name" == "●" ]] && continue
    if [[ $first -eq 0 ]]; then
      echo '    ,'
    fi
    echo -n "    {\"name\": \"$name\", \"load\": \"$load\", \"active\": \"$active\"}"
    first=0
  done <<< "$services"
  echo
  echo '  ]'
  echo '}'
} > "$OUT"

echo "written to $OUT"
