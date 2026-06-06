FROM flyway/flyway:11.3.1-alpine

COPY app/core/src/main/resources/db/migration/ /flyway/sql
COPY app/containers/migrate/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["migrate"]
