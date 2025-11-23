
.PHONY: run test fmt

run:
	python -m mind_proxy

test:
	pytest -q

fmt:
	python -m pip install ruff black || true
	ruff check --fix . || true
	black . || true
