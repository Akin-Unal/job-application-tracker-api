.PHONY: install run test lint format typecheck migration migrate docker-up docker-down seed create-admin

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy app

migration:
	alembic revision --autogenerate -m "$(message)"

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down

seed:
	python scripts/seed.py

create-admin:
	python scripts/create_admin.py --email admin@example.com --password StrongPassword123 --name "Admin User"
