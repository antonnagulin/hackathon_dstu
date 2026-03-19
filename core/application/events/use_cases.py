from typing import List, Optional

from core.application.events.dto import EventDTO
from core.domain.events.entities import Event
from core.domain.events.repositories import BaseEventRepository


class GetAllEventUseCase:
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    def execute(self) -> List[Event]:
        events = self.repo.get_all()
        return events


class CreateEventUseCase:
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    def execute(self, event_data: EventDTO) -> Event:

        event = self.repo.create(
            event_data.title,
            event_data.description,
            event_data.capacity,
            event_data.date,
        )
        self.repo.save(event)
        return event


class UpdateEventUseCase:
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    def execute(self, id: int, event_data: EventDTO) -> Optional[Event]:

        event = self.repo.get_by_id(id)

        if not event:
            raise ValueError("indalid id event")

        event.update(
            event_data.title,
            event_data.description,
            event_data.capacity,
            event_data.date,
        )

        self.repo.save(event)
        return event


class DeleteEventUseCase:
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    def execute(self, id: int) -> None:
        event = self.repo.get_by_id(id)

        if not event:
            raise ValueError("indalid id event")

        self.repo.delete(id)
