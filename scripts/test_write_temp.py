#!/usr/bin/env python3
# /srv/cockswain-core/scripts/test_write_temp.py

import sys
sys.path.append("/srv/cockswain-core/ai-core")
import tempstore  # noqa

cid = tempstore.create_conversation({
    "role": "user",
    "event": "manual_test",
    "text": "hello from manual test"
})
print("created conversation:", cid)
