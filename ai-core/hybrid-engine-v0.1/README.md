# Cockswain Hybrid Engine v0.1

Minimal *heartbeat* engine for the Helmsman ecosystem.
- FastAPI + Uvicorn
- Echo core (`/orchestrate`, `/v1/proxy/chat`)
- Memory hook to Cockswain Memory Keeper (`/append`)
- Health & Prometheus metrics

## Quickstart

```bash
cd /srv/cockswain-core/ai-core
unzip ~/下載/hybrid-engine-v0.1.zip -d hybrid-engine-v0.1
cd hybrid-engine-v0.1
python3 -m venv .venv && . .venv/bin/activate
pip install -U pip wheel setuptools
pip install -e .
cp .env.example .env
hybrid-engine
# visit http://127.0.0.1:7790/health
```

## Systemd

```bash
sudo ln -sfn /srv/cockswain-core/ai-core/hybrid-engine-v0.1 /srv/cockswain-core/ai-core/hybrid-engine
sudo cp deploy/systemd/cockswain-hybrid-engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cockswain-hybrid-engine
sudo systemctl status cockswain-hybrid-engine --no-pager
```

## API

- `GET /health` -> `{"status":"ok"}`
- `POST /orchestrate` -> `{ "content": "text", "role": "user|assistant|system", "tags": [] }`
- `POST /v1/proxy/chat` (alias of `/orchestrate`)
- `GET /metrics` -> Prometheus metrics