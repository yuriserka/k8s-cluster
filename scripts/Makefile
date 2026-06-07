.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

REPO_ROOT := $(abspath ..)
APPS_DIR := $(REPO_ROOT)/apps
REPOSITORIES := $(sort $(filter-out infra,$(notdir $(wildcard $(APPS_DIR)/*))))

NAMESPACE ?= dev

# make deploy-app kafka-worker / make drop-app kafka-worker — stub extra words as goals.
APP_GOAL := $(firstword $(filter deploy-app drop-app,$(MAKECMDGOALS)))
ifneq ($(APP_GOAL),)
  APP_ARGS := $(filter-out deploy-app drop-app,$(MAKECMDGOALS))
  ifneq ($(APP_ARGS),)
    $(foreach arg,$(APP_ARGS),$(eval $(arg):;@:))
  endif
endif

ifndef REPOSITORY
  REPOSITORY := $(firstword $(filter $(REPOSITORIES),$(filter-out deploy-app drop-app,$(MAKECMDGOALS))))
endif

.PHONY: help venv install install-quiet lint format check deploy-app drop-app setup-infra drop-infra print-repositories

help:
	@echo "scripts targets:"
	@echo "  make venv                 Create .venv"
	@echo "  make install              pip install requirements.txt + requirements_dev.txt"
	@echo "  make lint                 black --check + flake8"
	@echo "  make format               Apply black to scripts/"
	@echo "  make check                lint (no tests in scripts today)"
	@echo "  make deploy-app <repo>    Run full pipeline (e.g. make deploy-app kafka-worker)"
	@echo "  make drop-app <repo>      Uninstall app Helm releases (e.g. make drop-app kafka-worker)"
	@echo "  make setup-infra          Install infra (cluster default; MODE=compose for Compose)"
	@echo "    Optional: MODE=compose WITH_KAFKA_UI=1"
	@echo "  make drop-infra           Uninstall infra (cluster default; MODE=compose for Compose)"
	@echo "    Optional: MODE=compose VOLUMES=1 NAMESPACE=dev"
	@echo "    Optional: SERVICES=\"postgresql kafka\" (default: all)"
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

drop-app: install-quiet
ifeq ($(REPOSITORY),)
	@echo "Available repositories:"
	@printf '  %s\n' $(REPOSITORIES)
	$(error Usage: make drop-app <repository>, e.g. make drop-app kafka-worker)
endif
ifneq ($(filter $(REPOSITORY),$(REPOSITORIES)),$(REPOSITORY))
	@echo "Available repositories:"
	@printf '  %s\n' $(REPOSITORIES)
	$(error Unknown repository "$(REPOSITORY)")
endif
	$(PYTHON) drop_app.py --repository $(REPOSITORY) --namespace $(NAMESPACE)

setup-infra: install-quiet
	$(PYTHON) install_infra.py \
		$(if $(MODE),--mode $(MODE),) \
		$(if $(WITH_KAFKA_UI),--with-kafka-ui,)

drop-infra: install-quiet
	$(PYTHON) drop_infra.py \
		--namespace $(NAMESPACE) \
		$(if $(MODE),--mode $(MODE),) \
		$(if $(VOLUMES),--volumes,) \
		$(foreach svc,$(SERVICES),--service $(svc))
