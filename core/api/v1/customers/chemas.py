from ninja import Schema


class RequestAuthInShema(Schema):
    phone: str


class RequestAuthOutShema(Schema):
    status: str
    phone: str


class ConfirmAuthInShema(Schema):
    code: int
    phone: str


class ConfirmAuthOutShema(Schema):
    acsess_token: str
    refresh_token: str


class RefreshInShema(Schema):
    refresh_token: str
