from datetime import datetime
from typing import List, Optional, Union

from django.db.models import QuerySet

from core.domain.events.entities import Event
from core.domain.events.repositories import BaseEventRepository

from .models import EventModels


class DjangoEventRepository(BaseEventRepository):

    def _to_entity(
        self, event_models: Union[EventModels, List[EventModels]]
    ) -> Union[Event, List[Event]]:

        if isinstance(event_models, QuerySet):
            return [
                Event(
                    event_id=e.id,
                    title=e.title,
                    description=e.description,
                    capacity=e.capacity,
                    date=e.date,
                )
                for e in event_models
            ]
        else:
            return Event(
                event_id=event_models.id,
                title=event_models.title,
                description=event_models.description,
                capacity=event_models.capacity,
                date=event_models.date,
            )

    def get_by_id(self, id: int) -> Optional[Event]:
        event_model = EventModels.objects.filter(id=id).first()

        if not event_model:
            return None

        return self._to_entity(event_model)

    def get_all(self) -> Optional[List[Event]]:
        events_models = EventModels.objects.all()

        if not events_models:
            return None

        return self._to_entity(events_models)

    def create(
        self,
        title: str,
        description: str,
        capacity: int,
        date: datetime,
    ) -> Event:
        event_model = EventModels.objects.create(
            title=title, description=description, capacity=capacity, date=date
        )
        return self._to_entity(event_model)

    def save(self, event: Event) -> None:
        event_model = EventModels.objects.get(id=event.event_id)
        event_model.title = event.title
        event_model.description = event.description
        event_model.capacity = event.capacity
        event_model.date = event.date
        event_model.save()

    def delete(self, id: int) -> None:
        return EventModels.objects.get(id=id).delete()
