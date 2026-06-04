from kafkaworker.tests.postgres_testcontainer import get_database_config, start_postgres_container

start_postgres_container()

from kafkaworker.config.settings import *  # noqa: F401,F403,E402

DATABASES = {
    'default': get_database_config(),
}
