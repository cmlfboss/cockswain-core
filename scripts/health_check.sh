#!/bin/bash
echo "[L7] checking node state..."
systemctl is-active cockswain-core.service --quiet && echo "core: active" || echo "core: inactive"
