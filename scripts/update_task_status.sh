#!/usr/bin/env bash
# update_task_status.sh <task_json> <STATUS>

task_file="$1"
new_status="$2"

if [[ -z "$task_file" || -z "$new_status" ]]; then
  echo "usage: $0 <task_json> <STATUS>"
  exit 1
fi

tmpfile="$(mktemp)"
jq --arg st "$new_status" '.status = $st' "$task_file" > "$tmpfile" && mv "$tmpfile" "$task_file"
echo "updated $task_file to $new_status"
