#!/usr/bin/env python
import os
import psycopg2

from kafkaworker.config import config


db_config = config.get('DB')

SUCCESS = 0
ERROR = 1


def log(message):
    os.system(f'echo "[HealthCheck] {message}" > /proc/1/fd/1')


def check_db_connection():
    connection = None
    health_check = ERROR
    try:
        connection = psycopg2.connect(
            host=db_config.get('HOST'),
            port="5432",
            user=db_config.get('USER'),
            password=db_config.get('PASSWORD'),
            database=db_config.get('NAME')
        )
        with connection.cursor() as cursor:
            cursor.execute('SELECT version();')
            record = cursor.fetchone()
            log(f'Database version: {record}')
            health_check = SUCCESS
    except Exception as error:
        log(f'Error: {error}')
    finally:
        if connection is not None and connection.closed == 0:
            connection.close()
    return health_check


def health_check():
    db_connection_health_check = check_db_connection()
    connection_checks = [db_connection_health_check]
    return SUCCESS if all([connection == SUCCESS for connection in connection_checks]) else ERROR


if __name__ == '__main__':
    exit(health_check())