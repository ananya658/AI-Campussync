import uuid
from typing import List, Optional
from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import Booking, Room, User, Branch
from backend.app.schemas import (
    BookingCreate, BookingResponse, BookingCancelRequest, BookingStatusUpdateRequest, RoomResponse
)
from backend.app.services.conflict_engine import ConflictEngine
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService
from backend.app.dependencies import get_current_user, require_role
from backend.app.routers.rooms import format_room

router = APIRouter(prefix="/bookings", tags=["Bookings"])

def format_booking(b: Booking) -> dict:
    return {
        "id": b.id,
        "booking_reference": b.booking_reference,
        "room_id": b.room_id,
        "user_id": b.user_id,
        "title": b.title,
        "purpose": b.purpose,
        "date": b.date,
        "start_time": b.start_time,
        "end_time": b.end_time,
        "expected_students": b.expected_students,
        "branch_id": b.branch_id,
        "academic_year": b.academic_year,
        "batch_id": b.batch_id,
        "section": b.section,
        "additional_requirements": b.additional_requirements,
        "status": b.status,
        "is_test_data": b.is_test_data,
        "cancellation_reason": b.cancellation_reason,
        "cancelled_at": b.cancelled_at,
        "created_at": b.created_at,
        "room": format_room(b.room) if b.room else None,
        "booked_by_name": b.user.full_name if b.user else None,
        "booked_by_email": b.user.email if b.user else None
    }

@router.post("", response_model=BookingResponse)
def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    # 1. Validate time bounds
    val_ok, val_err = ConflictEngine.validate_time_range(booking_in.start_time, booking_in.end_time)
    if not val_ok:
        raise HTTPException(status_code=400, detail=val_err)

    # 2. Check for conflicts using ConflictEngine (enforces existing_start < new_end AND existing_end > new_start)
    is_avail, conflict_reason, conflict_info = ConflictEngine.check_room_availability(
        db=db,
        room_id=booking_in.room_id,
        booking_date=booking_in.date,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        expected_students=booking_in.expected_students
    )

    if not is_avail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_reason or "Room is unavailable due to conflicting reservation."
        )

    # 3. Generate reference
    ref_uuid = uuid.uuid4().hex[:6].upper()
    booking_ref = f"CS-{booking_in.date.strftime('%Y%m%d')}-{ref_uuid}"

    # Determine status: Admin bookings or standard faculty lecture bookings are auto-CONFIRMED,
    # large seminars (>150) or restricted types can be PENDING_APPROVAL if desired
    initial_status = "CONFIRMED"

    new_booking = Booking(
        booking_reference=booking_ref,
        room_id=booking_in.room_id,
        user_id=current_user.id,
        title=booking_in.title,
        purpose=booking_in.purpose,
        date=booking_in.date,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        expected_students=booking_in.expected_students,
        branch_id=booking_in.branch_id,
        academic_year=booking_in.academic_year,
        batch_id=booking_in.batch_id,
        section=booking_in.section,
        additional_requirements=booking_in.additional_requirements,
        status=initial_status,
        is_test_data=booking_in.is_test_data
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # 4. Audit Log
    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="BOOKING",
        entity_id=new_booking.id,
        user=current_user,
        new_value={
            "ref": booking_ref,
            "room_id": new_booking.room_id,
            "date": str(new_booking.date),
            "start": str(new_booking.start_time),
            "end": str(new_booking.end_time),
            "title": new_booking.title,
            "is_test_data": new_booking.is_test_data
        },
        reason="Classroom reservation confirmed"
    )

    # 5. Send In-App Notifications
    NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        title="Classroom Booking Confirmed",
        message=f"Your booking {booking_ref} for {new_booking.room.room_number} on {new_booking.date} ({new_booking.start_time.strftime('%I:%M %p')}) is confirmed.",
        notification_type="BOOKING_CONFIRMED",
        link_url=f"/bookings/{new_booking.id}"
    )

    # Notify students if target branch/year is specified
    if new_booking.branch_id and new_booking.academic_year:
        NotificationService.notify_target_students(
            db=db,
            title=f"Schedule Update: {new_booking.title}",
            message=f"{new_booking.purpose.replace('_', ' ').title()} scheduled in Room {new_booking.room.room_number} on {new_booking.date.strftime('%b %d')} at {new_booking.start_time.strftime('%I:%M %p')}.",
            notification_type="BOOKING_CONFIRMED",
            branch_id=new_booking.branch_id,
            year=new_booking.academic_year,
            section=new_booking.section
        )

    return format_booking(new_booking)

@router.get("", response_model=List[BookingResponse])
def get_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    building_id: Optional[int] = Query(None),
    is_test_data: Optional[bool] = Query(None),
    my_bookings_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Booking)

    # Faculty viewing only their own bookings or if flag set
    if my_bookings_only or current_user.role == "FACULTY" and my_bookings_only:
        query = query.filter(Booking.user_id == current_user.id)
    elif current_user.role == "STUDENT":
        # Students see confirmed/active academic bookings
        query = query.filter(Booking.status.in_(["CONFIRMED", "COMPLETED"]))

    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if date_filter:
        query = query.filter(Booking.date == date_filter)
    if building_id:
        query = query.join(Room).filter(Room.building_id == building_id)
    if is_test_data is not None:
        query = query.filter(Booking.is_test_data == is_test_data)

    bookings = query.order_by(desc(Booking.date), desc(Booking.start_time)).all()
    return [format_booking(b) for b in bookings]

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return format_booking(b)

@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    cancel_in: BookingCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Faculty can only cancel their own bookings; Admin can cancel any
    if current_user.role == "FACULTY" and b.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings.")

    if b.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Booking is already cancelled.")

    old_status = b.status
    b.status = "CANCELLED"
    b.cancellation_reason = cancel_in.reason
    b.cancelled_at = datetime.utcnow()
    b.cancelled_by_id = current_user.id

    db.commit()
    db.refresh(b)

    # Audit log
    AuditService.log(
        db=db,
        action_type="CANCEL",
        entity_type="BOOKING",
        entity_id=b.id,
        user=current_user,
        previous_value={"status": old_status},
        new_value={"status": "CANCELLED", "reason": cancel_in.reason},
        reason=f"Booking cancelled: {cancel_in.reason}"
    )

    # Notify booking owner if admin cancelled it
    if b.user_id != current_user.id:
        NotificationService.create_notification(
            db=db,
            user_id=b.user_id,
            title="Classroom Booking Cancelled by Admin",
            message=f"Booking {b.booking_reference} for {b.room.room_number} on {b.date} was cancelled by administrator. Reason: {cancel_in.reason}",
            notification_type="BOOKING_CANCELLED"
        )
    else:
        NotificationService.create_notification(
            db=db,
            user_id=current_user.id,
            title="Booking Cancelled",
            message=f"Your booking {b.booking_reference} has been successfully cancelled.",
            notification_type="BOOKING_CANCELLED"
        )

    # Notify target students of cancellation
    if b.branch_id and b.academic_year:
        NotificationService.notify_target_students(
            db=db,
            title=f"Class Cancelled: {b.title}",
            message=f"The scheduled session in Room {b.room.room_number} on {b.date.strftime('%b %d')} has been cancelled. Reason: {cancel_in.reason}",
            notification_type="BOOKING_CANCELLED",
            branch_id=b.branch_id,
            year=b.academic_year,
            section=b.section
        )

    return format_booking(b)

@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    status_in: BookingStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    old_status = b.status
    b.status = status_in.status
    db.commit()
    db.refresh(b)

    AuditService.log(
        db=db,
        action_type="APPROVE" if status_in.status == "CONFIRMED" else "UPDATE",
        entity_type="BOOKING",
        entity_id=b.id,
        user=current_user,
        previous_value={"status": old_status},
        new_value={"status": b.status, "reason": status_in.reason},
        reason=status_in.reason or f"Status changed to {b.status}"
    )

    NotificationService.create_notification(
        db=db,
        user_id=b.user_id,
        title=f"Booking Status: {b.status}",
        message=f"Your reservation {b.booking_reference} for {b.room.room_number} has been updated to {b.status}.",
        notification_type="BOOKING_CONFIRMED" if b.status == "CONFIRMED" else "BOOKING_CANCELLED"
    )

    return format_booking(b)

