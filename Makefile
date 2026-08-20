.PHONY: format lint typecheck test test-integration docs openapi openapi-check run precommit hooks quality db-up db-ready db-psql db-stop migrate migration-current migration-check

format:
	uv run ruff format --check .

lint:
	uv run ruff check .

typecheck:
	uv run mypy

test:
	uv run pytest

test-integration:
	uv run pytest --run-integration

docs:
	uv run python scripts/check_docs_links.py

openapi:
	uv run python scripts/export_openapi.py

openapi-check:
	uv run python scripts/export_openapi.py --check

run:
	set -a; . ./.env; set +a; uv run uvicorn --factory contour.bootstrap:create_app_from_environment --host 127.0.0.1 --port 8000

precommit:
	uv run pre-commit run --all-files

hooks:
	uv run pre-commit install

db-up:
	docker compose up --detach database

db-ready:
	docker compose exec --no-TTY database sh -c 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-psql:
	docker compose exec database sh -c 'exec psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-stop:
	docker compose stop database

migrate:
	uv run alembic upgrade head

migration-current:
	uv run alembic current

migration-check:
	uv run alembic check

quality: format lint typecheck test openapi-check
