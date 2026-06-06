# Postgresql

## Installing

From the repository root:

```bash
helm install postgresql bitnami/postgresql -n dev -f apps/infra/postgresql/values.yaml
```

## Connecting to postgres instance

Port-forward (optional — for host-side `psql` or GUI only):

```bash
minikube kubectl -- port-forward -n dev postgresql-0 5432:5432
```

[`create_database.py`](../../../scripts/create_database.py) and pipeline migrations use **`kubectl exec` into `postgresql-0`** — no port-forward required.

## Local Compose vs cluster

| | Local Compose | Cluster (`dev`) |
|--|--|--|
| Container | `k8s-cluster-postgres` on network `k8s-cluster-local` | Helm `postgresql-0` pod |
| Default user | `ysdcr` / `ysdcr` | Admin: vault `_admin`; app: vault per repo |
| Databases | `kafka-producer`, `kafka-worker` (worker via [`initdb`](../../kafka-worker/initdb/) on first volume init) | Created by `create_database.py` per app |
| Migrations | Producer: `make migrate` (Gradle Flyway); worker: `make migrate` (Django) | Pipeline `dev-migrate` step |

See [kafka-producer README](../../kafka-producer/README.md) and [kafka-worker README](../../kafka-worker/README.md) for compose quick starts.

## Creating a database and granting permissions (PostgreSQL 15+)

On PostgreSQL 15+, the `public` schema no longer grants `CREATE` to all users. Django (and other apps) need the **application user** to own the database and `public` schema.

Use the repo script from `scripts/` (creates the DB if missing, then always applies owner/grants — safe to re-run on an existing database):

```bash
cd scripts
python create_database.py --namespace dev --repository <app_name>
```

Example for `kafka-worker`: creates database `kafka-worker` owned by `root` (from `resources/vault/kafka-worker/database/dev/.env`).

### Manual fix for an existing database

If the database was created without owner/grants, connect as admin (`postgres` / `admin` from `resources/vault/_admin/database/dev/.env`) and run:

```sql
ALTER DATABASE "kafka-worker" OWNER TO root;
GRANT CONNECT ON DATABASE "kafka-worker" TO root;
```

Then connect to the app database (`\c kafka-worker` or `psql -d kafka-worker`):

```sql
GRANT ALL ON SCHEMA public TO root;
ALTER SCHEMA public OWNER TO root;
```

Or re-run `python create_database.py --namespace dev --repository kafka-worker` to apply the same grants automatically.

Avoid `ALTER ROLE ... WITH SUPERUSER` unless you explicitly want full cluster admin for that user in dev.

## Application credentials

App services use credentials from `resources/vault/<app>/database/<namespace>/.env`, for example:

```
username: root
password: example
database: kafka-worker
```

Migrations run as this user after `create_database.py` has been executed.
