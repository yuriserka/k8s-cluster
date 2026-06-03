ARG CONTAINER=api

FROM eclipse-temurin:21-jre-alpine
ARG CONTAINER
WORKDIR /usr/src/java-app
COPY ./app/containers/${CONTAINER}/build/libs/*.jar ./app.jar

ENV SPRING_PROFILE=local

CMD ["java", "-jar", "-Dspring.profiles.active=${SPRING_PROFILE}", "app.jar"]
