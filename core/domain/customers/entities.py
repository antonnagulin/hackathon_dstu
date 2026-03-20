import random
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Literal, Optional

LevelType = Literal["Silver", "Gold", "Black"]
PositionType = Literal["KSO", "Manager", "ROP", "Director"]
SupportStatus = Literal["open", "closed"]
LeaderboardType = Literal["dealer", "region"]
TrainingType = Literal["video", "test"]


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    user_id: int
    phone_number: str
    name: Optional[str]
    role: UserRole = UserRole.USER
    is_verified: bool = False

    access_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    refresh_token: str = field(default_factory=lambda: secrets.token_urlsafe(64))
    access_expiration: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=25)
    )
    refresh_expiration: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )

    otp_code: int = field(default_factory=lambda: random.randint(100000, 999999))
    otp_expiration: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def generate_new_tokens(self) -> tuple[str, str]:
        self.access_token = secrets.token_urlsafe(32)
        self.refresh_token = secrets.token_urlsafe(64)
        self.access_expiration = datetime.now(timezone.utc) + timedelta(minutes=25)
        self.refresh_expiration = datetime.now(timezone.utc) + timedelta(days=30)
        return self.access_token, self.refresh_token

    def generate_new_otp(self):
        self.otp_code = random.randint(100000, 999999)
        self.otp_expiration = datetime.now(timezone.utc) + timedelta(minutes=5)
        return self.otp_code

    def verify_otp(self, code: int) -> bool:
        if datetime.now(timezone.utc) > self.otp_expiration:
            return False
        return self.otp_code == code

    def verify_access(self, token: str) -> bool:
        if datetime.now(timezone.utc) > self.access_expiration:
            return False
        return self.access_token == token

    def verify_refresh(self, token: str) -> bool:
        if datetime.now(timezone.utc) > self.refresh_expiration:
            return False
        return self.refresh_token == token


@dataclass
class Employee:
    id: str
    user_id: int
    full_name: str
    position: PositionType
    dealer_code: str
    level: LevelType
    score: int
    registration_date: datetime
    sber_id: str


@dataclass
class Level:
    id: int
    type: LevelType
    min_score: int
    max_score: int
    benefits: List["Benefit"] = field(default_factory=list)


@dataclass
class Benefit:
    id: str
    title: str
    description: str

    level_required: LevelType
    financial_value: float

    is_active: bool
