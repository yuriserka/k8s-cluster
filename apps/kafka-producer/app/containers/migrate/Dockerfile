FROM gradle:8-jdk17-alpine

WORKDIR /app

COPY . .

RUN chmod +x gradlew

CMD ["./gradlew", ":app:core:flywayMigrate", "-Dflyway.configFiles=flyway.conf"]
