from typing import Optional

from core.domain.booking.entities import Booking
from core.domain.booking.repositories import BaseBookingRepository
from core.domain.events.repositories import BaseEventRepository


class CreateBookingUseCse:
    def __init__(
        self,
        repo: BaseBookingRepository,
        event_repo: BaseEventRepository,
    ):
        self.repo = repo
        self.event_repo = event_repo

    def execute(self, event_id: int, user_id: int) -> Optional[Booking]:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            raise ValueError("Event not found")

        event.reserve_seat()

        return self.repo.create(user_id=user_id, event_id=event.event_id)


class GetBookingForUserUseCse:
    def __init__(
        self,
        repo: BaseBookingRepository,
    ):
        self.repo = repo

    def execute(self, user_id: int) -> Optional[Booking]:
        return self.repo.get_by_user_id(id=user_id)


class CancelBookingUserUseCse:
    def __init__(
        self,
        repo: BaseBookingRepository,
    ):
        self.repo = repo

    def execute(self, booking_id: int, user_id: int) -> Optional[Booking]:
        booking = self.repo.get_by_booking_id(id=booking_id)
        if not booking:
            raise ValueError("booking not found")
        if booking.user_id != user_id:
            raise ValueError(f"current user do not have booking {booking_id}")

        booking.cancel()

        self.repo.save(booking)
        return booking
