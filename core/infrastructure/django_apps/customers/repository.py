from typing import Optional

from core.domain.customers.entities import User
from core.domain.customers.repositories import BaseCustomersRepository

from .models import UserModels


class DjangoCustomersRepository(BaseCustomersRepository):

    def get_by_phone(self, phone: str) -> Optional[User]:
        user_model = UserModels.objects.filter(phone_number=phone).first()
        if not user_model:
            return None

        return self._to_entity(user_model)

    def create(self, phone: str) -> User:
        user = User(
            user_id=0,
            phone_number=phone,
            name=None,
        )

        user_model = UserModels.objects.create(
            phone_number=user.phone_number,
            name=user.name,
            otp_code=user.otp_code,
            otp_expiration=user.otp_expiration,
            access_token=user.access_token,
            refresh_token=user.refresh_token,
            access_expiration=user.access_expiration,
            refresh_expiration=user.refresh_expiration,
            is_verified=user.is_verified,
            role=user.role,
        )

        user.user_id = user_model.id

        return user

    def save(self, user: User) -> None:
        user_model = UserModels.objects.get(id=user.user_id)
        user_model.name = user.name
        user_model.role = user.role
        user_model.is_verified = user.is_verified
        user_model.access_token = user.access_token
        user_model.refresh_token = user.refresh_token
        user_model.access_expiration = user.access_expiration
        user_model.refresh_expiration = user.refresh_expiration
        user_model.otp_code = user.otp_code
        user_model.otp_expiration = user.otp_expiration
        user_model.save()

    def get_by_access_token(self, access_token: str) -> Optional[User]:
        user_model: Optional[UserModels] = UserModels.objects.filter(
            access_token=access_token
        ).first()
        if not user_model:
            return None

        return self._to_entity(user_model)

    def get_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        user_model: Optional[UserModels] = UserModels.objects.filter(
            refresh_token=refresh_token
        ).first()
        if not user_model:
            return None

        return self._to_entity(user_model)

    def _to_entity(self, user_model: UserModels) -> User:
        return User(
            user_id=user_model.id,
            phone_number=user_model.phone_number,
            name=user_model.name,
            role=user_model.role,
            is_verified=user_model.is_verified,
            access_token=user_model.access_token,
            refresh_token=user_model.refresh_token,
            access_expiration=user_model.access_expiration,
            refresh_expiration=user_model.refresh_expiration,
            otp_code=user_model.otp_code,
            otp_expiration=user_model.otp_expiration,
        )
