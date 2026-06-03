FROM eclipse-temurin:21-jre-alpine

WORKDIR /usr/src/java-app

COPY ./app/containers/scheduler/build/libs/*.jar ./scheduler.jar

ENV SPRING_PROFILE="local"

CMD ["java", "-jar", "-Dspring.profiles.active=${SPRING_PROFILE}", "scheduler.jar"]
