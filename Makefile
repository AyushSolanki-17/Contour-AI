.PHONY: format lint typecheck test precommit hooks quality

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

quality: format lint typecheck test
