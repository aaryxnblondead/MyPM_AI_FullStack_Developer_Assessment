dev-backend:
	cd backend && ./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && ./.venv/Scripts/python -m pytest -q
	cd frontend && npm run lint
