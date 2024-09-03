FROM eclipse-temurin:17-jdk-alpine

WORKDIR /usr/src/java-app

COPY ./scheduler/build/libs/*.jar ./scheduler.jar

ENV SPRING_PROFILE="local"

CMD ["java", "-jar", "-Dspring.profiles.active=${SPRING_PROFILE}", "scheduler.jar"]
