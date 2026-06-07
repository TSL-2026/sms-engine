.PHONY: install dev test lint clean docker-build docker-run

install:
	pip install -r requirements.txt

dev:
	PYTHONPATH=$(PWD) uvicorn sms_engine.main:app --reload --host 0.0.0.0 --port 8000

dev-live:
	PYTHONPATH=$(PWD) uvicorn sms_engine.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

prod:
	PYTHONPATH=$(PWD) uvicorn sms_engine.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level warning

lint:
	ruff check sms_engine/

docker-build:
	docker build -t sms-engine:latest .

docker-run:
	docker run -p 8000:8080 \
		-v $(PWD)/sms_db:/app/sms_db \
		sms-engine:latest

clean:
	rm -rf __pycache__ .pytest_cache sms_db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
