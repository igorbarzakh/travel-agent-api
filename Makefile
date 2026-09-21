dev:
	uvicorn app.main:app --reload

test:
	python -m pytest -vv

lint:
	ruff check .

format:
	ruff format .

freeze:
	python -m pip freeze > requirements.txt