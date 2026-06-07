import os


def read_env_file(env_file: str) -> dict:
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f"Environment file {env_file} does not exist.")

    secrets = {}
    with open(env_file) as secrets_file:
        for line in secrets_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.split("#", 1)[0]
            key, value = line.split("=", maxsplit=1)
            secrets[key.upper()] = value.strip()
    return secrets
