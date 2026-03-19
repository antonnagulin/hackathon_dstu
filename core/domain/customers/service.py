from abc import ABC, abstractmethod


class BaseCodeSenderService(ABC):

    @abstractmethod
    def send_code(self, code: int, phone_number: str) -> int:
        pass
