.PHONY: dev docker-up docker-down test test-unit test-integration lint fmt install build clean type-check

install:
	pip install -e ".[dev]"

dev:
	python -m ustidnr_mcp

docker-up:
	docker compose -f docker/docker-compose.yml up -d --build

docker-down:
	docker compose -f docker/docker-compose.yml down

test:
	pytest --cov=ustidnr_mcp --cov-report=term-missing --cov-fail-under=95 -x -q

test-unit:
	pytest -m "not integration" --cov=ustidnr_mcp --cov-report=term-missing --cov-fail-under=95 -x -q

test-integration:
	pytest -m integration -x -q -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

fmt:
	ruff check --fix src/ tests/
	ruff format src/ tests/

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .coverage htmlcov/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

type-check:
	mypy src/ --strict
