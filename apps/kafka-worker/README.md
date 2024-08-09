# Kafka Worker

to run this app execute in this directory:

**Note**: remember to do [this](../README.md#terminals) before execute the build

```
docker build -t worker-test:latest -f Dockerfile.example_events_worker .
```

ensure that the image was created correctly:

```
minikube image ls --format table | grep "worker-test"
```

then in root directory

```
kubectl apply -f kafka-worker/kafka-worker.yaml
```

which expands to something like:

```
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
```

## Testing

follow the steps in [Testing Producer](../kafka-producer/README.md#testing) to setup the topic and be able to send messages to it.

follow the steps in [Testing PgAdmin](../postgres/README.md#testing) to setup the database which the events will be saved.

then do the following to check if everything is working properly:

```
kubectl get po | grep "kafka-worker"

kubectl logs -f kafka-worker-<HASH> 8085:8080
```

in other terminal send a request for the producer:

```
curl --location 'http://localhost:8085/produce/<YOUR_PARAM_VALUE>'
```

the response must be in this format

```json
{
    "id": "ea96fa55-9afa-4b4b-bab3-82ca4b0f625c",
    "type": "test",
    "timestamp": "2024-01-26T15:48:58.382264915",
    "data": {
        "userId": "f260a06e-a851-418d-b4cd-9f8ac56f9939",
        "name": "<YOUR_PARAM_VALUE>"
    }
}
```

open kafka-admin and check if there is a new message for the topic

with the terminal with the logs check if everything was executed without any errors

open pgadmin

and run the following query to check if the event was saved:

```sql
SELECT * FROM public.example_events ee
ORDER BY ee.created_at DESC; 
```

## TODO

understand how to create `initContainers` so I can apply migrations before the container start and avoid to manually setup everything by hand on postgres