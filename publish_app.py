import os

root_dir = os.getcwd()


def main(
    repository: str,
    dockerfile_path: str,
    namespace: str,
    intra_cluster: bool,
    tag: str = None
) -> int:
    tag = tag or 'latest'
    image = f'{repository}-{namespace}:{tag}'
    provider = 'minikube image' if intra_cluster else 'docker'
    return os.system(
        f'{provider} build -t {image} -f {dockerfile_path} .'
    )


if __name__ == '__main__':
    args = os.sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required to publish the app. Use -n flag to specify the namespace.")
        exit(1)

    if "-d" not in args:
        print("Dockerfile path is required to publish the app. Use -d flag to specify the dockerfile path.")
        exit(1)

    if "-r" not in args:
        print("Repository is required to publish the app. Use -r flag to specify the repository.")
        exit(1)

    if "-p" not in args:
        print("Path is required to publish the app. Use -p flag to specify the path.")
        exit(1)

    namespace = args[args.index("-n") + 1]
    dockerfile_path = args[args.index("-d") + 1]
    repository = args[args.index("-r") + 1]
    path = args[args.index("-p") + 1]
    tag = args[args.index("-t") + 1] if "-t" in args else None
    intra_cluster = "-k" in args

    os.chdir(path)

    exit_code = main(repository, dockerfile_path, namespace, intra_cluster, tag)

    os.chdir(root_dir)

    if exit_code != 0:
        raise Exception(f'Failed to publish app with repository: {repository}')
