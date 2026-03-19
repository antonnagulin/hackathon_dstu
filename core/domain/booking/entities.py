from dataclasses import dataclass
from datetime import date
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class Booking:
    booking_id: int
    user_id: int
    event_id: int
    created_at: date
    status: BookingStatus = BookingStatus.PENDING

    def cancel(self):
        if self.status == BookingStatus.CONFIRMED:
            raise ValueError("booking status is confirmed")
        self.status = BookingStatus.CANCELLED
