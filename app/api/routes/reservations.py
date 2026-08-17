from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_current_user
from app.schemas.domain import ReservationCreate, ReservationRead, ReservationUpdate, UserRead
from app.services.store import store

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    current_user: Annotated[UserRead, Depends(require_current_user)],
) -> list[ReservationRead]:
    return store.list_reservations(current_user.id)


@router.post("", response_model=ReservationRead, status_code=201)
def create_reservation(
    payload: ReservationCreate,
    current_user: Annotated[UserRead, Depends(require_current_user)],
) -> ReservationRead:
    try:
        return store.create_reservation(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: UUID,
    payload: ReservationUpdate,
    current_user: Annotated[UserRead, Depends(require_current_user)],
) -> ReservationRead:
    existing = store.reservations.get(reservation_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reservation not found")
    try:
        return store.update_reservation(reservation_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Reservation not found") from exc


@router.delete("/{reservation_id}", status_code=204)
def cancel_reservation(
    reservation_id: UUID,
    current_user: Annotated[UserRead, Depends(require_current_user)],
) -> None:
    existing = store.reservations.get(reservation_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reservation not found")
    store.reservations.pop(reservation_id)
