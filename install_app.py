import os
import yaml

root_dir = os.getcwd()


def get_values_template_for(namespace: str) -> dict:
    with open(f'envs/{namespace}/values.yaml') as values_file:
        return yaml.safe_load(values_file)


def get_declared_values_for_app(env_file: str, namespace: str, path: str) -> dict:
    os.chdir(path)

    with open(f'kube/{namespace}/{env_file}') as override_file:
        content = yaml.safe_load(override_file)
        os.chdir(root_dir)
        return content


def get_resources_for(app_name: str, namespace: str) -> dict:
    with open(f'resources/{app_name}/{namespace}.yaml') as resources_file:
        return yaml.safe_load(resources_file)


def execute_helm_commands(app_name: str, repository: str, namespace: str, values: dict) -> int:
    generated_file_name = 'values.yaml'
    with open(generated_file_name, 'w') as result:
        yaml.safe_dump(
            values,
            result,
            sort_keys=False,
            default_flow_style=None,
            allow_unicode=True,
        )

    os.system(
        f'helm template {app_name} ../envs/{namespace} -n {namespace} -f {generated_file_name} >'
        f' ../apps/{repository}/{app_name}-{namespace}.yaml'
    )
    app_installed = os.system(
        f'helm install {app_name} ../envs/{namespace} -n {namespace} -f {generated_file_name}'
    )
    if app_installed != 0:
        app_installed = os.system(
            f'helm upgrade {app_name} ../envs/{namespace} -n {namespace} -f {generated_file_name}'
        )

    return app_installed


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
    'port': 'service.port',
}


def handle_probes(values: dict, key: str | None = None, value=None):
    if key is None and value is None:
        has_liveness_http = values.get(
            'livenessProbe').get('httpGet') is not None
        has_readines_http = values.get(
            'readinessProbe').get('httpGet') is not None
        has_liveness_exec = values.get('livenessProbe').get('exec') is not None
        has_readiness_exec = values.get(
            'readinessProbe').get('exec') is not None
        has_startup_http = values.get(
            'startupProbe').get('httpGet') is not None
        has_startup_exec = values.get('startupProbe').get('exec') is not None

        if not has_liveness_http and not has_liveness_exec:
            update_value(values, 'livenessProbe', None)
        if not has_readines_http and not has_readiness_exec:
            update_value(values, 'readinessProbe', None)
        if not has_startup_http and not has_startup_exec:
            update_value(values, 'startupProbe', None)

        return

    real_key = 'livenessProbe' if 'liveness' in key else 'readinessProbe'
    probe = None
    if 'Cmd' in key:
        probe = {
            **values.get(real_key, {}),
            'exec': {
                'command': value
            }
        }
        update_value(values, real_key, probe)
    elif 'Path' in key:
        probe = {
            **values.get(real_key, {}),
            'httpGet': {
                'path': value,
                'port': 'http'
            }
        }
        update_value(values, real_key, probe)

    if probe is not None and real_key == 'livenessProbe':
        update_value(values, 'startupProbe', probe)


def install_app(application: str, repository: str,  environment_file: str, namespace: str, path: str) -> int:
    # os.system(f'k create namespace {namespace}')
    values = get_values_template_for(namespace)
    override_value = get_declared_values_for_app(
        environment_file, namespace, path)

    values_ref = {key: value for key, value in values.items()}
    update_value(values_ref, 'image.repository', f'{application}-{namespace}')
    for key, value in override_value.items():
        if 'Probe' in key:
            handle_probes(values_ref, key, value)
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

    handle_probes(values_ref)
    resources = get_resources_for(application, namespace)
    for key, value in resources.items():
        if key not in values_ref:
            values_ref[key] = value
        else:
            values_ref[key] = {**values_ref[key], **value}

    os.chdir(path)

    return execute_helm_commands(application, repository, namespace, values_ref)


def main(application: str, repository: str, environment_file: str, namespace: str, path: str) -> int:
    return install_app(application, repository, environment_file, namespace, path)


if __name__ == '__main__':
    args = os.sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required to install the app. Use -n flag to specify the namespace.")
        exit(1)

    if "-a" not in args:
        print("Application is required to install the app. Use -a flag to specify the application.")
        exit(1)

    if "-e" not in args:
        print("Environment is required to install the app. Use -e flag to specify the environment_file.")
        exit(1)

    if "-p" not in args:
        print("Path is required to install the app. Use -p flag to specify the path.")
        exit(1)

    application = args[args.index("-a") + 1]
    environment_file = args[args.index("-e") + 1]
    path = args[args.index("-p") + 1]
    namespace = args[args.index("-n") + 1]
    repository = args[args.index("-r") + 1]

    exit_code = main(
        application,
        repository,
        environment_file,
        namespace,
        path
    )

    os.chdir(root_dir)

    if exit_code != 0:
        raise Exception(
            f'Installation of {application} failed with code {exit_code}'
        )
