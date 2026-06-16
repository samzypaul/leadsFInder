.PHONY: help up down logs backend frontend seed test fmt

help:
	@echo "make up        - build & start full stack (docker compose)"
	@echo "make down      - stop stack"
	@echo "make logs      - tail logs"
	@echo "make backend   - run backend locally (uvicorn --reload)"
	@echo "make frontend  - run frontend locally (next dev)"
	@echo "make seed      - load demo fixtures into the DB"
	@echo "make test      - run backend tests"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

seed:
	cd backend && python -m app.seed

test:
	cd backend && pytest -q
