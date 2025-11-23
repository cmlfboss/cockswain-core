#!/usr/bin/env bash
set -e

cd /srv/cockswain-core/ai-core
python3 knowledge_center/process_inbox.py "$@"
