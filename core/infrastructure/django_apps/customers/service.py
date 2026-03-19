from core.domain.customers.service import BaseCodeSenderService


class ConsoleCodeSenderService(BaseCodeSenderService):

    def send_code(self, code: int, phone_number: str):
        print(code, phone_number)
