# ── Open436 Auth Service ── 多阶段构建
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

FROM eclipse-temurin:21-jre-alpine
# 关键：alpine 21-jre 默认不含 wget/curl，用于 healthcheck 与诊断
RUN apk add --no-cache curl tini
COPY --from=builder /app/target/Open436-Auth-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8081
ENTRYPOINT ["/sbin/tini", "--", "java", "-jar", "app.jar"]
