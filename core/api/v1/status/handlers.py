from django.http import HttpRequest
from ninja import Router

from core.api.v1.customers.handlers import user_auth

router = Router(tags=["Status"])


@router.get("/", auth=user_auth)
def get_prof(request: HttpRequest):
    return "Hello world"
