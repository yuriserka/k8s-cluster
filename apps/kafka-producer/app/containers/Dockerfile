ARG CONTAINER=api

FROM eclipse-temurin:21-jdk-alpine AS jar
ARG CONTAINER
WORKDIR /build
COPY ./app/containers/${CONTAINER}/build/libs/*.jar application.jar
RUN java -Djarmode=tools -jar application.jar extract --layers --destination extracted

FROM eclipse-temurin:21-jre-alpine
ARG CONTAINER
WORKDIR /usr/src/java-app
COPY --from=jar /build/extracted/dependencies/ ./
COPY --from=jar /build/extracted/spring-boot-loader/ ./
COPY --from=jar /build/extracted/snapshot-dependencies/ ./
COPY --from=jar /build/extracted/application/ ./

ENV SPRING_PROFILE=local

CMD ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Dspring.backgroundpreinitializer.ignore=true", \
  "-Dspring.profiles.active=${SPRING_PROFILE}", \
  "-jar", "application.jar"]
