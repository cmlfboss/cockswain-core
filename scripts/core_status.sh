#!/bin/bash
echo "[L7] core status..."
systemctl is-active cockswain-core.service --no-pager 2>/dev/null || echo "core: unknown"
