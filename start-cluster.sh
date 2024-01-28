#!/bin/bash

# check if minikube is installed
if ! [ -x "$(command -v minikube)" ]; then
    echo "minikube is not installed. Please install minikube and try again."
    exit 1
fi

# check if kubectl is installed
if ! [ -x "$(command -v kubectl)" ]; then
    echo "kubectl is not installed. Please install kubectl and try again."
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

# apply the config for postgres and pgadmin
kubectl apply -f postgres/postgres.yaml
kubectl apply -f postgres/pgadmin.yaml

# apply the config for kafka
kubectl apply -f kafka/zookeeper.yaml

# wait for zookeeper to be ready
while ! kubectl get pods -l app=zookeeper | grep -q "1/1"; do
    echo "waiting for zookeeper to be ready"
    sleep 5
done

kubectl apply -f kafka/kafka.yaml

# wait for kafka to be ready
while ! kubectl get pods -l app=kafka | grep -q "1/1"; do
    echo "waiting for kafka to be ready"
    sleep 5
done

kubectl apply -f kafka/admin.yaml

# apply the config for kafka-producer
cd kafka-producer
docker build -t worker-test:latest .
kubectl apply -f kafka-producer.yaml
cd ..


# apply the config for kafka-worker
cd kafka-worker
docker build -t worker-test:latest -f Dockerfile.example_events_worker .
kubectl apply -f kafka-worker.yaml
cd ..

