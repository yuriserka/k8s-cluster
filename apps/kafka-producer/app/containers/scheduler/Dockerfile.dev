FROM gradle:8.9-jdk17-alpine AS cache
RUN mkdir -p /home/gradle/cache_home
ENV GRADLE_USER_HOME /home/gradle/cache_home
COPY *.gradle /home/gradle/java-code/
WORKDIR /home/gradle/java-code
RUN gradle :scheduler:clean :scheduler:build -x bootJar

FROM gradle:8.9-jdk17-alpine AS builder
COPY --from=cache /home/gradle/cache_home /home/gradle/.gradle
COPY . /usr/src/java-code/
WORKDIR /usr/src/java-code
RUN gradle :scheduler:bootJar

FROM eclipse-temurin:17-jdk-alpine
USER root
WORKDIR /usr/src/java-app
COPY --from=builder /usr/src/java-code/build/libs/*.jar ./scheduler.jar

EXPOSE 8080

ENV SPRING_PROFILE="local"

CMD ["java", "-jar", "-Dspring.profiles.active=${SPRING_PROFILE}", "scheduler.jar"]
