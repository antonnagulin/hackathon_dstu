from datetime import date

from ninja import Schema


class BookingOutSchema(Schema):
    booking_id: int
    user_id: int
    event_id: int
    status: str
    created_at: date
