from typing import NamedTuple


class SendMessageToUserEventPayloadDTO(NamedTuple):
    user_id: str
    username: str
