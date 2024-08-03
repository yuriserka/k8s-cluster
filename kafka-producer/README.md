# Kafka Producer

to run this app execute in this directory:

**Note**: remember to do [this](../README.md#terminals) before execute the build

```
docker build -t producer-test:latest .
```

ensure that the image was created correctly:

```
minikube image ls --format table | grep "producer-test"
```

then in root directory

```
kubectl apply -f kafka-producer/kafka-producer.yaml
```

which expands to something like:

```
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
```

## Testing

Create a new topic called `example-topic` following the instructions in [kafka-admin](../kafka/README.md#admin)

then do the following to port-forward to container:

```
kubectl get po | grep "kafka-producer"

kubectl port-forward kafka-producer-<HASH> 8085:8080
```

and send a request with:

```
curl --location 'http://localhost:8085/message/produce/<YOUR_PARAM_VALUE>'
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