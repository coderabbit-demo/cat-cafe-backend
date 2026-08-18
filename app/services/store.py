from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from secrets import token_urlsafe
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.domain import (
    ReservationCreate,
    ReservationRead,
    ReservationUpdate,
    TeaRead,
    UserRead,
)


@dataclass(frozen=True)
class SessionRecord:
    user_id: UUID
    expires_at: datetime


class MemoryStore:
    MAX_SESSIONS = 10_000

    def __init__(self) -> None:
        self.users: dict[str, UUID] = {}
        self.user_emails: dict[UUID, str] = {}
        self.google_identities: dict[str, UUID] = {}
        self.sessions: dict[str, SessionRecord] = {}
        self._session_lock = Lock()
        self.links: dict[tuple[str, str], str] = {}
        self.reservations: dict[UUID, ReservationRead] = {}
        self.teas = [
            TeaRead(id=UUID("11111111-1111-1111-1111-111111111111"), name="Chamomile"),
            TeaRead(id=UUID("22222222-2222-2222-2222-222222222222"), name="Peppermint"),
            TeaRead(id=UUID("33333333-3333-3333-3333-333333333333"), name="Rooibos"),
        ]

    def create_user(self, email: str) -> UUID:
        normalized_email = email.lower()
        user_id = self.users.setdefault(normalized_email, uuid4())
        self.user_emails[user_id] = normalized_email
        return user_id

    def sign_in_with_google(self, subject: str, email: str) -> UserRead:
        user_id = self.google_identities.get(subject)
        if user_id is None:
            user_id = self.create_user(email)
            self.google_identities[subject] = user_id
        return UserRead(id=user_id, email=self.user_emails[user_id])

    def get_user(self, user_id: UUID) -> UserRead | None:
        email = self.user_emails.get(user_id)
        return UserRead(id=user_id, email=email) if email is not None else None

    def create_session(self, user_id: UUID, ttl_seconds: int) -> str:
        token = token_urlsafe(32)
        now = datetime.now(UTC)
        with self._session_lock:
            self._evict_expired_sessions(now)
            while len(self.sessions) >= self.MAX_SESSIONS:
                self.sessions.pop(next(iter(self.sessions)))
            self.sessions[token] = SessionRecord(
                user_id=user_id,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
        return token

    def get_session_user(self, token: str) -> UserRead | None:
        now = datetime.now(UTC)
        with self._session_lock:
            self._evict_expired_sessions(now)
            session = self.sessions.get(token)
        if session is None:
            return None
        return self.get_user(session.user_id)

    def delete_session(self, token: str) -> None:
        with self._session_lock:
            self.sessions.pop(token, None)

    def _evict_expired_sessions(self, now: datetime) -> None:
        expired_tokens = [
            token for token, session in self.sessions.items() if session.expires_at <= now
        ]
        for token in expired_tokens:
            self.sessions.pop(token, None)

    def slots(self, on_date: date) -> list[str]:
        if on_date.weekday() == 0:
            return []
        return [f"{hour:02d}:00" for hour in range(10, 17)]

    def list_reservations(self, user_id: UUID) -> list[ReservationRead]:
        return [item for item in self.reservations.values() if item.user_id == user_id]

    def create_reservation(self, user_id: UUID, data: ReservationCreate) -> ReservationRead:
        if data.start_time.strftime("%H:%M") not in self.slots(data.reservation_date):
            raise ValueError("Selected time is unavailable")
        reservation = ReservationRead(id=uuid4(), user_id=user_id, **data.model_dump())
        self.reservations[reservation.id] = reservation
        return reservation

    def update_reservation(self, reservation_id: UUID, data: ReservationUpdate) -> ReservationRead:
        current = self.reservations[reservation_id]
        updated = current.model_copy(update=data.model_dump(exclude_none=True))
        self.reservations[reservation_id] = updated
        return updated


store = MemoryStore()
