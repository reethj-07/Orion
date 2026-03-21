.PHONY: dev down build migrate test lint frontend-install

dev:
	docker compose up --build

down:
	docker compose down -v

build:
	docker compose build

migrate:
	docker compose run --rm api alembic upgrade head

test:
	docker compose run --rm api pytest -q

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm api black --check .
	docker compose run --rm api mypy app

frontend-install:
	cd frontend && npm install
