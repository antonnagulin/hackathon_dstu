from typing import List, Union

from django.db.models import QuerySet

from core.domain.booking.entities import Booking
from core.domain.booking.repositories import BaseBookingRepository

from .models import BookingModels


class DjangoBookingRepository(BaseBookingRepository):
    def _to_entity(
        self, booking_models: Union[BookingModels, List[BookingModels]]
    ) -> Booking | List[Booking]:

        if isinstance(booking_models, QuerySet):
            return [
                Booking(
                    booking_id=e.id,
                    user_id=e.user_id,
                    event_id=e.event_id,
                    status=e.status,
                    created_at=e.created_at,
                )
                for e in booking_models
            ]
        else:
            return Booking(
                booking_id=booking_models.id,
                user_id=booking_models.user_id,
                event_id=booking_models.event_id,
                status=booking_models.status,
                created_at=booking_models.created_at,
            )

    def create(self, user_id: int, event_id: int) -> Booking:
        booking_model = BookingModels.objects.create(
            user_id=user_id,
            event_id=event_id,
        )

        return self._to_entity(booking_model)

    def get_by_user_id(self, id: int) -> list[Booking] | Booking | None:
        booking_model = BookingModels.objects.filter(
            user_id=id,
        )
        if not booking_model:
            raise ValueError("booking not found")
        return self._to_entity(booking_model)

    def get_by_booking_id(self, id: int) -> Booking | None:
        booking_model = BookingModels.objects.filter(
            id=id,
        ).first()
        if not booking_model:
            raise ValueError("booking not found")
        return self._to_entity(booking_model)

    def save(self, booking: Booking) -> None:
        booking_model = BookingModels.objects.get(id=booking.booking_id)
        booking_model.status = booking.status
        return booking_model.save()
