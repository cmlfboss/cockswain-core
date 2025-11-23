# mind-proxy v0.1

A minimal, production-minded gateway that fronts Helmsman hybrid engines.
It exposes HTTP endpoints and forwards requests to configured upstreams.
Redis is optional; in-memory fallback is used if Redis is unavailable.

## Features (v0.1)
- FastAPI HTTP API: `/v1/proxy/chat`, `/health`, `/metrics`
- Pluggable upstreams (HTTP JSON by default)
- Request ID propagation and structured logs
- Basic rate-limit token bucket (in-memory; optional Redis)
- Simple circuit breaker (half-open after cooldown)
- Graceful shutdown hooks
- Systemd unit and Docker image
- Pytest smoke tests

## Quick start (local)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .
cp .env.example .env
mind-proxy
# visit http://127.0.0.1:7780/health
```

## Config
Env-first (dotenv supported). See `.env.example` for all knobs.

## Run with Docker
```bash
docker build -t mind-proxy:0.1 .
docker run --rm -p 7780:7780 --env-file .env mind-proxy:0.1
```

## Systemd (bare metal)
1. Copy `deploy/systemd/cockswain-mind-proxy.service` to `/etc/systemd/system/`
2. `sudo systemctl daemon-reload && sudo systemctl enable --now cockswain-mind-proxy`

## Endpoints
- `GET /health` — liveness/readiness
- `GET /metrics` — Prometheus
- `POST /v1/proxy/chat` — forwards to upstream (HTTP JSON). Body schema in `schemas.py`.

## Roadmap
- v0.2: gRPC adapter, JWT auth, multi-upstream routing, request cache
- v0.3: mTLS, priority queues, backpressure, tracing (OTel)
