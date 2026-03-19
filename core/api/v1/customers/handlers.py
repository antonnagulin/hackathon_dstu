
from django.http import HttpRequest
from ninja import Router
from ninja.security import HttpBearer

from core.application.customers.use_cases import (
    ConfirmAuthCodeUseCase,
    RefreshTokenUseCase,
    RequestAuthCodeUseCase,
)
from core.infrastructure.django_apps.customers.repository import (
    DjangoCustomersRepository,
)
from core.infrastructure.django_apps.customers.service import ConsoleCodeSenderService

from .chemas import (
    ConfirmAuthInShema,
    ConfirmAuthOutShema,
    RefreshInShema,
    RequestAuthInShema,
    RequestAuthOutShema,
)


class UserAuthBearer(HttpBearer):

    def authenticate(self, request: HttpRequest, token: str):
        repo = DjangoCustomersRepository()
        user = repo.get_by_access_token(token)

        if not user:
            return None

        if not user.verify_access(token):
            return None

        return user


class SuperUserAuthBearer(HttpBearer):

    def authenticate(self, request: HttpRequest, token: str):
        repo = DjangoCustomersRepository()
        user = repo.get_by_access_token(token)

        if not user:
            return None

        if not user.verify_access(token):
            return None

        if not user.is_admin:
            return None

        return user


router = Router(tags=["Customers"])
user_auth = UserAuthBearer()
admin_auth = SuperUserAuthBearer()


@router.post("/auth", response=RequestAuthOutShema)
def auth_request(request: HttpRequest, shema: RequestAuthInShema):

    customers_repo = DjangoCustomersRepository()
    code_sender = ConsoleCodeSenderService()

    use_case = RequestAuthCodeUseCase(
        code_sender=code_sender, customers_repo=customers_repo
    )
    return use_case.execute(shema.phone)


@router.post("/auth-confirm", response=ConfirmAuthOutShema)
def auth_confirm(request: HttpRequest, shema: ConfirmAuthInShema):

    customers_repo = DjangoCustomersRepository()
    use_case = ConfirmAuthCodeUseCase(customers_repo=customers_repo)
    return use_case.execute(phone=shema.phone, code=shema.code)


@router.post("/refresh", response=ConfirmAuthOutShema)
def refresh_token(request, shema: RefreshInShema):

    use_case = RefreshTokenUseCase(DjangoCustomersRepository())
    return use_case.execute(shema.refresh_token)


@router.get("/profile", auth=user_auth)
def get_prof(request):
    return "Hello world"
