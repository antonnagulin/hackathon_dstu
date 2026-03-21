from core.domain.customers.repositories import BaseCustomersRepository
from core.domain.customers.service import BaseCodeSenderService


class RequestAuthCodeUseCase:

    def __init__(
        self,
        code_sender: BaseCodeSenderService,
        customers_repo: BaseCustomersRepository,
    ):
        self.code_sender = code_sender
        self.customers_repo = customers_repo

    def execute(self, phone: str) -> dict:
        user = self.customers_repo.get_by_phone(phone)
        if not user:
            # raise ValueError("User not found")
            user = self.customers_repo.create(phone)

        code = user.generate_new_otp()

        self.code_sender.send_code(code, phone)

        self.customers_repo.save(user)

        return {"status": "code_sent", "phone": phone}


class ConfirmAuthCodeUseCase:

    def __init__(
        self,
        customers_repo: BaseCustomersRepository,
    ):
        self.customers_repo = customers_repo

    def execute(self, code: int, phone: str) -> dict:
        user = self.customers_repo.get_by_phone(phone)
        if not user:
            raise ValueError("User not found")

        if user.verify_otp(code):
            user.is_verified = True

            access, refresh = user.generate_new_tokens()
            self.customers_repo.save(user)

            return {"acsess_token": access, "refresh_token": refresh}

        raise ValueError("code insorrected")


class RefreshTokenUseCase:

    def __init__(self, customers_repo: BaseCustomersRepository):
        self.customers_repo = customers_repo

    def execute(self, refresh_token: str):

        user = self.customers_repo.get_by_refresh_token(refresh_token)
        if not user:
            raise ValueError("Invalid refresh token")

        if not user.verify_refresh(refresh_token):
            raise ValueError("Refresh token expired")

        access, refresh = user.generate_new_tokens()

        self.customers_repo.save(user)

        return {"acsess_token": access, "refresh_token": refresh}


class RefreshTokenVerifyUseCase:

    def __init__(self, customers_repo: BaseCustomersRepository):
        self.customers_repo = customers_repo

    def execute(self, refresh_token: str):

        user = self.customers_repo.get_by_refresh_token(refresh_token)
        if not user:
            raise ValueError("Invalid refresh token")
        return True