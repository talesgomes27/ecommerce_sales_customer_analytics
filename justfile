default:
    @just --list

setup:
    uv sync

check:
    uv run ruff check .
    uv run ruff format --check .
    uv run pytest -q

format:
    uv run ruff format .
    uv run ruff check --fix .

test:
    uv run pytest -v tests/

serve:
    uv run streamlit run app.py
