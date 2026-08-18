from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr


class UserRead(UserCreate):
    id: UUID


class GoogleCredential(BaseModel):
    credential: str = Field(min_length=1)


class TeaRead(BaseModel):
    id: UUID
    name: str
    active: bool = True


class AvailabilityRead(BaseModel):
    date: date
    slots: list[str]


class ReservationCreate(BaseModel):
    reservation_date: date
    start_time: time
    guest_count: int = Field(ge=1, le=6)
    tea_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class ReservationUpdate(BaseModel):
    reservation_date: date | None = None
    start_time: time | None = None
    guest_count: int | None = Field(default=None, ge=1, le=6)
    tea_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class ReservationRead(ReservationCreate):
    id: UUID
    user_id: UUID


class SlackLinkCreate(BaseModel):
    slack_user_id: str
    slack_team_id: str
    email: EmailStr


class SlackLinkRead(BaseModel):
    user_id: UUID | None = None
    email: EmailStr
    linked: bool
    registration_url: str | None = None
