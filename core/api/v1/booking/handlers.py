from typing import List

from ninja import Router

from core.application.booking.use_cases import (
    CancelBookingUserUseCse,
    CreateBookingUseCse,
    GetBookingForUserUseCse,
)
from core.domain.booking.entities import Booking
from core.infrastructure.django_apps.booking.repository import DjangoBookingRepository
from core.infrastructure.django_apps.events.repository import DjangoEventRepository

from ..customers.handlers import user_auth
from .shemas import BookingOutSchema

router = Router(tags=["Booking"])


@router.post("/events/{event_id}/book", auth=user_auth, response=BookingOutSchema)
def create_booking(request, event_id: int):

    use_case = CreateBookingUseCse(
        DjangoBookingRepository(),
        DjangoEventRepository(),
    )
    user_id = request.auth.user_id

    return use_case.execute(event_id=event_id, user_id=user_id)


@router.get("users/bookings", auth=user_auth, response=List[Booking])
def get_user_bookings(request):
    use_case = GetBookingForUserUseCse(DjangoBookingRepository())
    user_id = request.auth.user_id

    return use_case.execute(user_id=user_id)


@router.put("bookings/{booking_id}/cancel", auth=user_auth, response=BookingOutSchema)
def cancel_bookings(request, booking_id: int):
    use_case = CancelBookingUserUseCse(DjangoBookingRepository())
    user_id = request.auth.user_id

    return use_case.execute(booking_id=booking_id, user_id=user_id)
