import os
import yaml


def get_values_template_for(namespace: str):
    values_file = open(f'envs/{namespace}/values.yaml')
    values = yaml.load(values_file, Loader=yaml.FullLoader)
    values_file.close()

    return values


def get_declared_values_for_apps(repository: str, namespace: str) -> dict:
    all_apps_with_extension = os.listdir(f'apps/{repository}/kube/{namespace}')
    values = {}

    for app_with_extension in all_apps_with_extension:
        app = app_with_extension.split('.')[0]
        with open(f'apps/{repository}/kube/{namespace}/{app_with_extension}') as override_file:
            values[app] = yaml.load(override_file, Loader=yaml.FullLoader)

    return values


def get_resources_for(app_name: str, namespace: str) -> dict:
    resources_file = open(f'resources/{app_name}/{namespace}.yaml')
    resources = yaml.load(resources_file, Loader=yaml.FullLoader)
    resources_file.close()

    return resources


def execute_helm_commands(app_name: str, namespace: str, values: dict):
    generated_file_name = f'tmp-{app_name}-values.yaml'
    generated_file_path = f'envs/{namespace}/{generated_file_name}'
    with open(generated_file_path, 'w') as result:
        yaml.dump(values, result)

    os.system(
        f'helm template {app_name} envs/{namespace} -n {namespace} -f {generated_file_path} >'
        f' apps/{repository}/{app_name}-{namespace}.yaml'
    )
    os.system(
        f'helm install {app_name} envs/{namespace} -n {namespace} -f {generated_file_path}'
    )
    os.system(f'rm {generated_file_path}')


def install_app(repository: str, namespace: str):
    # os.system(f'k create namespace {namespace}')
    values = get_values_template_for(namespace)
    override_values = get_declared_values_for_apps(repository, namespace)

    for app_name, override_value in override_values.items():
        values_ref = {key: value for key, value in values.items()}
        values_ref['image']['repository'] = app_name
        for key, value in override_value.items():
            if key == 'livenessProbePath':
                values_ref['livenessProbe']['httpGet']['path'] = value
            elif key == 'readinessProbePath':
                values_ref['readinessProbe']['httpGet']['path'] = value
            elif key == 'port':
                values_ref['service']['port'] = value
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
