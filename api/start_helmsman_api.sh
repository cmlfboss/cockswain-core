#!/bin/bash
cd /srv/cockswain-core/api
# 建議先確定 fastapi/uvicorn 都裝了
# pip install fastapi uvicorn
python3 -m uvicorn helmsman_api:app --host 127.0.0.1 --port 7701
