.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

REPO_ROOT := $(abspath ..)
APPS_DIR := $(REPO_ROOT)/apps
REPOSITORIES := $(sort $(filter-out infra,$(notdir $(wildcard $(APPS_DIR)/*))))

# make deploy-app kafka-worker — extra words are goals, not args; stub them so Make does not fail.
ifneq ($(filter deploy-app,$(MAKECMDGOALS)),)
  DEPLOY_ARGS := $(filter-out deploy-app,$(MAKECMDGOALS))
  ifneq ($(DEPLOY_ARGS),)
    $(foreach arg,$(DEPLOY_ARGS),$(eval $(arg):;@:))
  endif
endif

ifndef REPOSITORY
  REPOSITORY := $(firstword $(filter $(REPOSITORIES),$(filter-out deploy-app,$(MAKECMDGOALS))))
endif

.PHONY: help venv install install-quiet lint format check deploy-app setup-infra print-repositories

help:
	@echo "scripts targets:"
	@echo "  make venv                 Create .venv"
	@echo "  make install              pip install requirements.txt + requirements_dev.txt"
	@echo "  make lint                 black --check + flake8"
	@echo "  make format               Apply black to scripts/"
	@echo "  make check                lint (no tests in scripts today)"
	@echo "  make deploy-app <repo>    Run full pipeline (e.g. make deploy-app kafka-worker)"
	@echo "  make setup-infra          Install infra (cluster default; MODE=compose for Compose)"
	@echo "    Optional: MODE=compose WITH_KAFKA_UI=1"
	@echo "  Available repositories: $(REPOSITORIES)"

venv:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Virtual environment created."

install: | $(VENV)/bin/python
	@echo "Installing requirements..."
	$(PIP) install -r requirements.txt -r requirements_dev.txt
	@echo "Requirements installed."

install-quiet: | $(VENV)/bin/python
	@$(PIP) install -q --disable-pip-version-check -r requirements.txt -r requirements_dev.txt

$(VENV)/bin/python:
	@python3 -m venv $(VENV)

lint: install
	$(PYTHON) code_checks.py

format: install
	$(PYTHON) -m black .

check: lint

print-repositories:
	@printf '%s\n' $(REPOSITORIES)

deploy-app: install-quiet
ifeq ($(REPOSITORY),)
	@echo "Available repositories:"
	@printf '  %s\n' $(REPOSITORIES)
	$(error Usage: make deploy-app <repository>, e.g. make deploy-app kafka-worker)
endif
ifneq ($(filter $(REPOSITORY),$(REPOSITORIES)),$(REPOSITORY))
	@echo "Available repositories:"
	@printf '  %s\n' $(REPOSITORIES)
	$(error Unknown repository "$(REPOSITORY)")
endif
	$(PYTHON) pipeline_parser.py $(REPOSITORY)

setup-infra: install-quiet
	$(PYTHON) install_infra.py \
		$(if $(MODE),--mode $(MODE),) \
		$(if $(WITH_KAFKA_UI),--with-kafka-ui,)
