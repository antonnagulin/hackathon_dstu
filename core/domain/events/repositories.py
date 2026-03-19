from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from core.domain.events.entities import Event


class BaseEventRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Event]:
        pass

    @abstractmethod
    def get_all(self) -> Optional[List[Event]]:
        pass

    @abstractmethod
    def create(
        self,
        title: str,
        description: str,
        capacity: int,
        date: datetime,
    ) -> Event:
        pass

    @abstractmethod
    def save(self, event: Event) -> None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass
