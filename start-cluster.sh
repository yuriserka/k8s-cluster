#!/bin/bash

# check if minikube is installed
if ! [ -x "$(command -v minikube)" ]; then
    echo "minikube is not installed. Please install minikube and try again."
    exit 1
fi

# check if docker is installed
if ! [ -x "$(command -v docker)" ]; then
    echo "docker is not installed. Please install docker and try again."
    exit 1
fi

# check if minikube is running
if ! minikube status | grep -q "Running"; then
    echo "minikube is not running. Please start minikube and try again."
    exit 1
fi

# enable ingress
minikube addons enable ingress
minikube kubectl -- apply -f infra/ingress/backend-ingress.yaml

# apply the config for postgres and pgadmin
minikube kubectl -- apply -f infra/postgres/postgres.yaml
minikube kubectl -- apply -f infra/postgres/pgadmin.yaml

# wait for postgres to be ready
while ! minikube kubectl -- get pods -l app=postgres | grep -q "1/1"; do
    echo "waiting for postgres to be ready"
    sleep 5
done

# apply the config for kafka
minikube kubectl -- apply -f infra/kafka/zookeeper.yaml

# wait for zookeeper to be ready
while ! minikube kubectl -- get pods -l app=zookeeper | grep -q "1/1"; do
    echo "waiting for zookeeper to be ready"
    sleep 5
done

minikube kubectl -- apply -f infra/kafka/kafka.yaml

# wait for kafka to be ready
while ! minikube kubectl -- get pods -l app=kafka | grep -q "1/1"; do
    echo "waiting for kafka to be ready"
    sleep 5
done

minikube kubectl -- apply -f infra/kafka/admin.yaml

# apply the config for kafka-producer
cd apps/kafka-producer
docker build -t kafka-producer:latest -f ./Dockerfile .
minikube kubectl -- apply -f kafka-producer.yaml
cd -


# apply the config for kafka-worker
cd apps/kafka-worker
docker build -t kafka-worker:latest -f Dockerfile.example_events_worker .
minikube kubectl -- apply -f kafka-worker.yaml
cd -

# apply the config for kafka-worker-api
cd apps/kafka-worker
docker build -t kafka-worker-api:latest -f Dockerfile .
minikube kubectl -- apply -f kafka-worker-api.yaml
cd -
