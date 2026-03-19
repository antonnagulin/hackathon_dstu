from typing import List

from ninja import Router

from core.application.events.use_cases import (
    CreateEventUseCase,
    DeleteEventUseCase,
    GetAllEventUseCase,
    UpdateEventUseCase,
)
from core.infrastructure.django_apps.events.repository import DjangoEventRepository

from ..customers.handlers import admin_auth, user_auth
from .shemas import EventInSchema, EventOutSchema

router = Router(tags=["Events"])


@router.get("/", auth=user_auth, response=List[EventOutSchema])
def get_all_events(request):

    use_case = GetAllEventUseCase(DjangoEventRepository())
    return use_case.execute()


@router.post("/", auth=admin_auth, response=EventOutSchema)
def create_event(request, data: EventInSchema):

    use_case = CreateEventUseCase(DjangoEventRepository())
    return use_case.execute(data)


@router.put("/{id}", auth=admin_auth, response=EventOutSchema)
def update_event(request, id: int, data: EventInSchema):

    use_case = UpdateEventUseCase(DjangoEventRepository())
    return use_case.execute(id, data)


@router.delete(
    "/{id}",
    auth=admin_auth,
)
def delete_event(request, id: int):

    use_case = DeleteEventUseCase(DjangoEventRepository())
    return use_case.execute(id)
