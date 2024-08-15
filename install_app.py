import os
import yaml


def get_values_template_for(namespace: str):
    values_file = open(f'envs/{namespace}/values.yaml')
    values = yaml.safe_load(values_file)
    values_file.close()

    return values


def get_declared_values_for_apps(repository: str, namespace: str) -> dict:
    all_apps_with_extension = os.listdir(f'apps/{repository}/kube/{namespace}')
    values = {}

    for app_with_extension in all_apps_with_extension:
        app = app_with_extension.split('.')[0]
        with open(f'apps/{repository}/kube/{namespace}/{app_with_extension}') as override_file:
            values[app] = yaml.safe_load(override_file)

    return values


def get_resources_for(app_name: str, namespace: str) -> dict:
    resources_file = open(f'resources/{app_name}/{namespace}.yaml')
    resources = yaml.safe_load(resources_file)
    resources_file.close()

    return resources


def execute_helm_commands(app_name: str, namespace: str, values: dict):
    generated_file_name = f'tmp-{app_name}-values.yaml'
    generated_file_path = f'envs/{namespace}/{generated_file_name}'
    with open(generated_file_path, 'w') as result:
        yaml.safe_dump(
            values,
            result,
            sort_keys=False,
            default_flow_style=None,
            allow_unicode=True,
        )

    os.system(
        f'helm template {app_name} envs/{namespace} -n {namespace} -f {generated_file_path} >'
        f' apps/{repository}/{app_name}-{namespace}.yaml'
    )
    os.system(
        f'helm install {app_name} envs/{namespace} -n {namespace} -f {generated_file_path}'
    )
    os.system(f'rm {generated_file_path}')


def update_value(obj: dict, path: str, value):
    def update_deep_nested_dict(nested_dict, keys, new_value):
        if len(keys) == 1:
            nested_dict[keys[0]] = new_value
        else:
            update_deep_nested_dict(nested_dict[keys[0]], keys[1:], new_value)

    keys = path.split(".")
    return update_deep_nested_dict(obj, keys, value)


mapping_kube_to_helm_values = {
    'cmd': 'container.cmd',
    'args': 'container.args',
    'livenessProbePath': 'livenessProbe.httpGet.path',
    'readinessProbePath': 'readinessProbe.httpGet.path',
    'port': 'service.port',
}


def install_app(repository: str, namespace: str):
    # os.system(f'k create namespace {namespace}')
    values = get_values_template_for(namespace)
    override_values = get_declared_values_for_apps(repository, namespace)

    for app_name, override_value in override_values.items():
        values_ref = {key: value for key, value in values.items()}
        update_value(values_ref, 'image.repository', repository)
        for key, value in override_value.items():
            if key in mapping_kube_to_helm_values:
                update_value(
                    values_ref,
                    mapping_kube_to_helm_values.get(key),
                    value
                )
            elif key not in values_ref:
                values_ref[key] = value
            else:
                values_ref[key] = {**values_ref[key], **value}

        if values_ref['livenessProbe']['httpGet']['path'] == '':
            values_ref['livenessProbe'] = None
        if values_ref['readinessProbe']['httpGet']['path'] == '':
            values_ref['readinessProbe'] = None

        resources = get_resources_for(app_name, namespace)
        for key, value in resources.items():
            if key not in values_ref:
                values_ref[key] = value
            else:
                values_ref[key] = {**values_ref[key], **value}

        execute_helm_commands(app_name, namespace, values_ref)


def main(repository: str, namespace: str):
    install_app(repository, namespace)


if __name__ == '__main__':
    args = os.sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required to install the app. Use -n flag to specify the namespace.")
        exit(1)

    namespace = args[args.index("-n") + 1]
    repository = args[0]

    main(repository, namespace)
