# Postgres

to run do in the following order:

```
kubectl apply -f postgres.yaml
kubectl apply -f pgadmin.yaml
```

which expands to something like:

```
kubectl apply -f db/secret.yaml
kubectl apply -f db/persistent-volume.yaml
kubectl apply -f db/deployment.yaml
kubectl apply -f db/service.yaml


kubectl apply -f admin/secret.yaml
kubectl apply -f admin/deployment.yaml
kubectl apply -f admin/service.yaml
```


## PgAdmin4

### Connecting

once the deployment and the service is up and running, to connect to pgAdmin, do the following:

`minikube service pgadmin-service`

### Credentials

- Email: admin@admin.com
- Password: admin

### Testing

### Testing

create a new database with the following query:

```sql
CREATE TABLE IF NOT EXISTS public.example_events
(
    event_id uuid NOT NULL,
    event_type character varying(255) COLLATE pg_catalog."default" NOT NULL,
    user_id uuid NOT NULL,
    username character varying(255) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT example_events_pkey PRIMARY KEY (event_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.example_events
    OWNER to root;
```

## Database

### Connecting

Use the pgAdmin to create a new database and set the host to `postgres-service`

### Credentials

- Username: root
- Password: example