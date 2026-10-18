install:
	uv sync

run:
	uv run database

build:
	uv build

lint:
	uv run ruff check .

package-install:
	uv tool install --force dist/*.whl
