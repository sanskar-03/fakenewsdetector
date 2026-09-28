install:
	python -m pip install -r requirements.txt
run:
	uvicorn backend.app:app --reload
test:
	pytest -q
docker-up:
	docker compose up --build
