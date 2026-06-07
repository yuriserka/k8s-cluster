from typing import NamedTuple


class CreateDatabaseRequest(NamedTuple):
    repository: str
    namespace: str
