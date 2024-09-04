FROM eclipse-temurin:17-jdk-alpine

WORKDIR /usr/src/java-app

COPY ./app/containers/api/build/libs/*.jar ./api.jar

ENV SPRING_PROFILE="local"

CMD ["java", "-jar", "-Dspring.profiles.active=${SPRING_PROFILE}", "api.jar"]
