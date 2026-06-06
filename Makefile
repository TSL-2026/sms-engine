.PHONY: install dev test lint clean docker-build docker-run

install:
	pip install -r requirements.txt

dev:
	PYTHONPATH=$(PWD) uvicorn aviation.api.main:app --reload --host 0.0.0.0 --port 8000

dev-live:
	PYTHONPATH=$(PWD) uvicorn aviation.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

prod:
	PYTHONPATH=$(PWD) uvicorn aviation.api.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning

test:
	PYTHONPATH=$(PWD) python -m pytest tests/ -v

test-coverage:
	PYTHONPATH=$(PWD) python -m pytest tests/ -v --cov=aviation --cov-report=term-missing

lint:
	ruff check aviation/ tests/

docker-build:
	docker build -t sms-engine:latest .

docker-run:
	docker run -p 8000:8080 \
		-e OPENROUTER_API_KEY=${OPENROUTER_API_KEY} \
		-v $(PWD)/aviation_logs:/app/aviation_logs \
		sms-engine:latest

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
