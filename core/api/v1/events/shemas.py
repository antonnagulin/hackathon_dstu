from datetime import datetime

from ninja import Schema


class EventInSchema(Schema):
    title: str
    description: str
    capacity: int
    date: datetime


class EventOutSchema(Schema):
    event_id: int
    title: str
    description: str
    capacity: int
    date: datetime
