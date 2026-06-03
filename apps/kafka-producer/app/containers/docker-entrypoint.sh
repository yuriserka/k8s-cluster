#!/bin/sh
set -e

profile="${SPRING_PROFILE:-local}"
jar="${APP_JAR:?APP_JAR must be set}"

agent=""
case "${OTEL_JAVAAGENT_ENABLED}" in
  true|1|yes|TRUE|YES|on|ON)
    agent="-javaagent:/app/opentelemetry-javaagent.jar"
    ;;
esac

exec java ${agent} -jar "-Dspring.profiles.active=${profile}" "${jar}"
