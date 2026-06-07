.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

DOCKERFILE_DEV := kafkaworker/containers/Dockerfile.dev

.PHONY: help venv create-env install install-requirements code-checks test format check \
	docker-build-api docker-build-scheduler docker-build-consumer migrate pipeline

help:
	@echo "kafka-worker targets:"
	@echo "  make venv                 Create .venv (alias: create-env)"
	@echo "  make install              pip install requirements.txt + requirements_dev.txt"
	@echo "  make code-checks          black --check + flake8 (pipeline lint step)"
	@echo "  make test                 run_tests.py with coverage (pipeline test step)"
	@echo "  make format               Apply black to kafkaworker/"
	@echo "  make check                code-checks then test"
	@echo "  make docker-build-api     Build api dev image locally"
	@echo "  make docker-build-scheduler Build scheduler dev image locally"
	@echo "  make docker-build-consumer  Build example-topic-consumer dev image locally"
	@echo "  make migrate              Django migrate against compose Postgres (docker compose run api)"
	@echo "  make pipeline             Run full cluster pipeline via python -m k8s_cluster pipeline run"

venv create-env:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Virtual environment created."

install install-requirements: | $(VENV)/bin/python
	@echo "Installing requirements..."
	$(PIP) install -r requirements.txt -r requirements_dev.txt
	@echo "Requirements installed."

code-checks: install
	$(PYTHON) code_checks.py

test: install
	$(PYTHON) run_tests.py

format: install
	$(PYTHON) -m black kafkaworker

check: code-checks test

docker-build-api:
	docker build -t kafka-worker-api-local:latest -f $(DOCKERFILE_DEV) --build-arg CONTAINER=api .

docker-build-scheduler:
	docker build -t kafka-worker-scheduler-local:latest -f $(DOCKERFILE_DEV) --build-arg CONTAINER=scheduler .

docker-build-consumer:
	docker build -t kafka-worker-example-topic-consumer-local:latest -f $(DOCKERFILE_DEV) --build-arg CONTAINER=example-topic-consumer .

migrate:
	docker compose run --rm api python manage.py migrate

pipeline:
	cd ../../scripts && PYTHONPATH=. python3 -m k8s_cluster pipeline run kafka-worker
