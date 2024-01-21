# My k8s cluster

for educational purposes only.

probably everything here could be more optimized but I still dont know a lot

## Secrets

use the following snipper to inspect the value of some secret

```bash
kubectl get secret

kubectl get secret <SECRET_NAME> -o go-template='{{range $k,$v := .data}}{{printf "%s: " $k}}{{if not $v}}{{$v}}{{else}}{{$v | base64decode}}{{end}}{{"\n"}}{{end}}'
``` 