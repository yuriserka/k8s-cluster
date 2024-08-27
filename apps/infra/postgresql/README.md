# Postgresql

## installing:

```bash
helm install postgresql bitnami/postgresql -n dev -f infra/postgresql/values.yaml
```

## Connecting to postgres instance

```bash
minikube kubectl -- port-forward -n dev postgresql-0 5432:5432
```

## Adding permissions to created user

### Connect as admin user (postgres) with the following credentials

```
username: postgres
password: admin
```

then execute the following SQL queries to update custom user

```sql
SELECT usename AS role_name,
 CASE
  WHEN usesuper AND usecreatedb THEN
    CAST('superuser, create database' AS pg_catalog.text)
  WHEN usesuper THEN
    CAST('superuser' AS pg_catalog.text)
  WHEN usecreatedb THEN
    CAST('create database' AS pg_catalog.text)
  ELSE
    CAST('' AS pg_catalog.text)
 END role_attributes
FROM pg_catalog.pg_user
ORDER BY role_name desc;

alter role <OTHER_USER_DIFF_FROM_POSTGRES> with SUPERUSER;
```

## creating the database

### Connect as user with the following credentials

```
username: root
password: example
```

Create the database `kafka-worker` and execute the following query

```sql
CREATE TABLE IF NOT EXISTS example_events
(
    event_id uuid NOT NULL,
    event_type character varying(255) COLLATE pg_catalog."default" NOT NULL,
    user_id uuid NOT NULL,
    username character varying(255) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT example_events_pkey PRIMARY KEY (event_id)
)
```