from abc import ABC, abstractmethod
from typing import Optional

from core.domain.customers.entities import User


class BaseCustomersRepository(ABC):

    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, phone: str) -> User:
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def get_by_access_token(self, access_token: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_refresh_token(self, refrash_token: str) -> Optional[User]:
        pass
