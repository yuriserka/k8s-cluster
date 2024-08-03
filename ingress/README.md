# Ingress

## Rules

the URLs defined in this ingress follows the rules below:

- `rewrite.bar.com/something` rewrites to `rewrite.bar.com/`
- `rewrite.bar.com/something/` rewrites to `rewrite.bar.com/`
- `rewrite.bar.com/something/new` rewrites to `rewrite.bar.com/new`

this way to access an endpoint in some service you just need to call it like you normally would but with the service prefix.

## Connecting

first of all you need to open a terminal and run.

```bash
minikube tunnel
```

then, in another terminal send your request to the desired service

```bash
curl "localhost/<service-path>/<endpoint>

```