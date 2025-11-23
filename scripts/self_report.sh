#!/usr/bin/env bash
TS=$(date --iso-8601=seconds)
curl -s -X POST http://127.0.0.1:7800/api/store \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"mother-cron\",
    \"timestamp\": \"${TS}\",
    \"user\": \"system\",
    \"topic\": \"mother-health-report\",
    \"payload\": {
      \"message\": \"Mother node heartbeat from cron at ${TS}\"
    }
  }" > /dev/null
