.PHONY: format lint typecheck test precommit hooks quality db-up db-ready db-psql db-stop

format:
	uv run ruff format --check .

lint:
	uv run ruff check .

typecheck:
	uv run mypy

test:
	uv run pytest

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

quality: format lint typecheck test
