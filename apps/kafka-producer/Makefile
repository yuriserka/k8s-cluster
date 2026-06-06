.DEFAULT_GOAL := help

GRADLE := ./gradlew
DOCKERFILE_DEV := app/containers/Dockerfile.dev

COMPOSE_DB_USER := ysdcr
COMPOSE_DB_PASSWORD := ysdcr
COMPOSE_DB_HOST := localhost
COMPOSE_DB_PORT := 5432
COMPOSE_DB_NAME := kafka-producer

.PHONY: help install code-checks test build check \
	docker-build-api docker-build-scheduler docker-build-migrate migrate pipeline

help:
	@echo "kafka-producer targets:"
	@echo "  make install              ./gradlew clean assemble -x bootJar (pipeline install)"
	@echo "  make code-checks          ./gradlew codeChecks (pipeline lint)"
	@echo "  make test                 ./gradlew test -x bootJar (pipeline test)"
	@echo "  make build                ./gradlew bootJar"
	@echo "  make check                code-checks then test"
	@echo "  make docker-build-api     Build api dev image locally"
	@echo "  make docker-build-scheduler Build scheduler dev image locally"
	@echo "  make docker-build-migrate Build migrate image locally"
	@echo "  make migrate              Flyway against compose Postgres on localhost (start postgres first)"
	@echo "  make pipeline             Run full cluster pipeline via scripts/pipeline_parser.py"

install:
	$(GRADLE) clean assemble -x bootJar

code-checks:
	$(GRADLE) codeChecks

test:
	$(GRADLE) test -x bootJar

build:
	$(GRADLE) bootJar

check: code-checks test

docker-build-api:
	docker build -t kafka-producer-api-local:latest -f $(DOCKERFILE_DEV) --build-arg CONTAINER=api .

docker-build-scheduler:
	docker build -t kafka-producer-scheduler-local:latest -f $(DOCKERFILE_DEV) --build-arg CONTAINER=scheduler .

docker-build-migrate:
	docker build -t kafka-producer-migrate:local -f app/containers/migrate/Dockerfile .

migrate:
	DATABASE_USER=$(COMPOSE_DB_USER) DATABASE_PASSWORD=$(COMPOSE_DB_PASSWORD) \
	DATABASE_HOST=$(COMPOSE_DB_HOST) DATABASE_PORT=$(COMPOSE_DB_PORT) \
	DATABASE_NAME=$(COMPOSE_DB_NAME) \
	$(GRADLE) :app:core:flywayMigrate -Dflyway.configFiles=flyway.conf

pipeline:
	cd ../../scripts && python3 pipeline_parser.py kafka-producer
