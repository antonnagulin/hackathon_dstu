from dataclasses import dataclass
from datetime import datetime


@dataclass
class EventDTO:
    title: str
    description: str
    capacity: int
    date: datetime
