from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


@dataclass
class Event:
    event_id: int
    title: str
    description: str
    capacity: int
    date: datetime
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def reserve_seat(self) -> None:
        with self._lock:
            if self.date < datetime.now(timezone.utc):
                raise ValueError("Мероприятие уже прошло")

            if self.capacity <= 0:
                raise ValueError("Нет свободных мест")

            self.capacity -= 1

    def update(self, title: str, description: str, capacity: int, date: datetime):
        # Пример проверки
        if capacity < 0:
            raise ValueError("Capacity must be a positive number")

        self.title = title
        self.description = description
        self.capacity = capacity
        self.date = date
