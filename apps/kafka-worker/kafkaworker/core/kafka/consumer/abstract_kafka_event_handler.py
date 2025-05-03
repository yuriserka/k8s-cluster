from typing import Optional, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar("T")
K = TypeVar("K")


class AbstractKafkaEventHandler(ABC, Generic[K, T]):
    @abstractmethod
    async def handle(self, key: Optional[K], event: T) -> None:
        raise NotImplementedError()
