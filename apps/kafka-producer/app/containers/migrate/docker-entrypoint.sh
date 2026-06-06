#!/bin/sh
set -eu

: "${DATABASE_HOST:?DATABASE_HOST is required}"
: "${DATABASE_PORT:?DATABASE_PORT is required}"
: "${DATABASE_NAME:?DATABASE_NAME is required}"
: "${DATABASE_USER:?DATABASE_USER is required}"
: "${DATABASE_PASSWORD:?DATABASE_PASSWORD is required}"

export FLYWAY_URL="jdbc:postgresql://${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}"
export FLYWAY_USER="${DATABASE_USER}"
export FLYWAY_PASSWORD="${DATABASE_PASSWORD}"
export FLYWAY_BASELINE_ON_MIGRATE=true
export FLYWAY_VALIDATE_ON_MIGRATE=true
export FLYWAY_LOCATIONS="filesystem:/flyway/sql"

exec flyway "$@"
