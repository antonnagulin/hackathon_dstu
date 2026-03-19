from abc import ABC, abstractmethod

from .entities import Booking


class BaseBookingRepository(ABC):

    @abstractmethod
    def create(
        self,
        user_id: int,
        event_id: int,
    ) -> Booking:
        pass

    @abstractmethod
    def get_by_user_id(self, id: int) -> list[Booking] | Booking | None:
        pass

    def get_by_booking_id(self, id: int) -> Booking | None:
        pass

    @abstractmethod
    def save(booking: Booking) -> None:
        pass
