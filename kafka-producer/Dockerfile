FROM gradle:8.5-jdk17 AS build
RUN mkdir /project
COPY . /project
WORKDIR /project
RUN gradle assemble

FROM openjdk:17-jdk-slim
RUN mkdir /app
COPY --from=build ./project/build/libs/kafka-producer-0.0.1-SNAPSHOT.jar /app/java-application.jar
WORKDIR /app
CMD ["java", "-jar", "java-application.jar"]
