import uuid
import threading
from typing import List, Optional
from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, Query, status

_booking_lock = threading.Lock()
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
        "section_id": getattr(b, "section_id", None),
        "section": b.section,
        "faculty_id": getattr(b, "faculty_id", None),
        "additional_requirements": b.additional_requirements,
        "is_split_sitting": getattr(b, "is_split_sitting", False),
        "linked_booking_id": getattr(b, "linked_booking_id", None),
        "split_role": getattr(b, "split_role", None),
        "idempotency_key": getattr(b, "idempotency_key", None),
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
    with _booking_lock:
        # 0. Check Idempotency Key (Return existing booking if already processed)
        if booking_in.idempotency_key:
            existing_idemp = db.query(Booking).filter(Booking.idempotency_key == booking_in.idempotency_key).first()
            if existing_idemp:
                return format_booking(existing_idemp)

        # 1. Validate time bounds
        val_ok, val_err = ConflictEngine.validate_time_range(booking_in.start_time, booking_in.end_time)
        if not val_ok:
            raise HTTPException(status_code=400, detail=val_err)

        # 2. Check Room conflicts using ConflictEngine (half-open interval [start, end) + closures + exam spacing)
        is_avail, conflict_reason, conflict_info = ConflictEngine.check_room_availability(
            db=db,
            room_id=booking_in.room_id,
            booking_date=booking_in.date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            expected_students=booking_in.expected_students,
            purpose=booking_in.purpose
        )

        if not is_avail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflict_reason or "Room is unavailable due to conflicting reservation."
            )

        # 3. Check Section collision (Dimension 2: Academic Section cannot be double-booked)
        sec_avail, sec_err, sec_info = ConflictEngine.check_section_availability(
            db=db,
            branch_id=booking_in.branch_id,
            academic_year=booking_in.academic_year,
            section_name=booking_in.section,
            booking_date=booking_in.date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time
        )
        if not sec_avail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=sec_err or "Academic section collision detected."
            )

        # 4. Check Faculty collision (Dimension 3: Faculty cannot be double-booked)
        faculty_id_to_check = booking_in.faculty_id
        if not faculty_id_to_check and current_user.faculty_profile:
            faculty_id_to_check = current_user.faculty_profile.id

        fac_avail, fac_err, fac_info = ConflictEngine.check_faculty_availability(
            db=db,
            faculty_id=faculty_id_to_check,
            booking_date=booking_in.date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time
        )
        if not fac_avail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=fac_err or "Faculty schedule collision detected."
            )

        # 5. Check Campus travel buffer (100m cross-campus transition)
        buf_avail, buf_err = ConflictEngine.check_travel_buffer(
            db=db,
            target_room_id=booking_in.room_id,
            booking_date=booking_in.date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            branch_id=booking_in.branch_id,
            academic_year=booking_in.academic_year,
            section_name=booking_in.section,
            faculty_id=faculty_id_to_check
        )
        if not buf_avail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=buf_err
            )

        # 6. Generate reference
        ref_uuid = uuid.uuid4().hex[:6].upper()
        booking_ref = f"CS-{booking_in.date.strftime('%Y%m%d')}-{ref_uuid}"

        # Determine status: approval needed for library or large seminar halls
        room_obj = db.query(Room).filter(Room.id == booking_in.room_id).first()
        initial_status = "CONFIRMED"
        if current_user.role != "ADMIN":
            if room_obj and room_obj.room_number in ["LIB", "IET32"] and booking_in.expected_students > 100:
                initial_status = "PENDING_APPROVAL"

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
            section_id=booking_in.section_id,
            section=booking_in.section,
            faculty_id=faculty_id_to_check,
            additional_requirements=booking_in.additional_requirements,
            is_split_sitting=booking_in.is_split_sitting,
            linked_booking_id=booking_in.linked_booking_id,
            split_role=booking_in.split_role,
            idempotency_key=booking_in.idempotency_key,
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


@router.get("/split-plan")
def get_split_plan(
    booking_date: Optional[str] = Query(None, description="Target exam date (YYYY-MM-DD)"),
    date: Optional[str] = Query(None, description="Target exam date alias (YYYY-MM-DD)"),
    start_time: str = Query("09:00", description="Exam start time (HH:MM)"),
    end_time: str = Query("11:00", description="Exam end time (HH:MM)"),
    total_students: Optional[int] = Query(None, description="Total candidates in section"),
    total_candidates: Optional[int] = Query(None, description="Total candidates alias"),
    building_id: Optional[int] = Query(None, description="Building ID preference"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """
    Returns calculated split-sitting arrangements according to the Corrected Design PDF:
    - Large single halls (IET32, LIB)
    - Deeksha Bhawan long room pairs (LH01 + LH02, LH08 + LH09)
    - Adjacent IET classrooms with auxiliary seats
    """
    target_date_str = booking_date or date or str(date.today())
    target_count = total_students or total_candidates or 75

    try:
        b_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except Exception:
        b_date = date.today()

    try:
        s_time = datetime.strptime(start_time, "%H:%M").time()
    except Exception:
        try:
            s_time = datetime.strptime(start_time, "%H:%M:%S").time()
        except Exception:
            s_time = time(9, 0)

    try:
        e_time = datetime.strptime(end_time, "%H:%M").time()
    except Exception:
        try:
            e_time = datetime.strptime(end_time, "%H:%M:%S").time()
        except Exception:
            e_time = time(11, 0)

    candidates = ConflictEngine.recommend_split_sitting(
        db=db,
        booking_date=b_date,
        start_time=s_time,
        end_time=e_time,
        total_students=target_count
    )
    return {
        "date": b_date,
        "start_time": s_time.strftime("%H:%M"),
        "end_time": e_time.strftime("%H:%M"),
        "total_students": target_count,
        "recommendations": candidates
    }


@router.post("/split-booking")
def create_split_booking(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """
    Creates an atomic split-sitting arrangement across two rooms for an examination.
    Generates linked bookings: Primary and Auxiliary.
    """
    with _booking_lock:
        primary_room_id = payload.get("primary_room_id")
        auxiliary_room_id = payload.get("auxiliary_room_id")
        date_str = payload.get("date")
        start_str = payload.get("start_time")
        end_str = payload.get("end_time")
        title = payload.get("title", "Section Examination Sitting")
        primary_students = payload.get("primary_students", 38)
        auxiliary_students = payload.get("auxiliary_students", 37)
        branch_id = payload.get("branch_id")
        academic_year = payload.get("academic_year")
        section = payload.get("section")

        if not primary_room_id or not auxiliary_room_id or not date_str or not start_str or not end_str:
            raise HTTPException(status_code=400, detail="Missing required fields for split booking.")

        b_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        s_time = datetime.strptime(start_str, "%H:%M").time()
        e_time = datetime.strptime(end_str, "%H:%M").time()

        # Validate availability of both rooms
        p_ok, p_err, _ = ConflictEngine.check_room_availability(
            db=db, room_id=primary_room_id, booking_date=b_date,
            start_time=s_time, end_time=e_time, expected_students=primary_students,
            purpose="MINOR_EXAM"
        )
        if not p_ok:
            raise HTTPException(status_code=409, detail=f"Primary room conflict: {p_err}")

        a_ok, a_err, _ = ConflictEngine.check_room_availability(
            db=db, room_id=auxiliary_room_id, booking_date=b_date,
            start_time=s_time, end_time=e_time, expected_students=auxiliary_students,
            purpose="MINOR_EXAM"
        )
        if not a_ok:
            raise HTTPException(status_code=409, detail=f"Auxiliary room conflict: {a_err}")

        ref_uuid1 = uuid.uuid4().hex[:6].upper()
        ref_uuid2 = uuid.uuid4().hex[:6].upper()

        b1 = Booking(
            booking_reference=f"CS-{b_date.strftime('%Y%m%d')}-SPLIT-{ref_uuid1}",
            room_id=primary_room_id,
            user_id=current_user.id,
            title=f"{title} (Sitting A)",
            purpose="MINOR_EXAM",
            date=b_date,
            start_time=s_time,
            end_time=e_time,
            expected_students=primary_students,
            branch_id=branch_id,
            academic_year=academic_year,
            section=section,
            is_split_sitting=True,
            split_role="PRIMARY",
            status="CONFIRMED"
        )
        db.add(b1)
        db.flush()

        b2 = Booking(
            booking_reference=f"CS-{b_date.strftime('%Y%m%d')}-SPLIT-{ref_uuid2}",
            room_id=auxiliary_room_id,
            user_id=current_user.id,
            title=f"{title} (Sitting B)",
            purpose="MINOR_EXAM",
            date=b_date,
            start_time=s_time,
            end_time=e_time,
            expected_students=auxiliary_students,
            branch_id=branch_id,
            academic_year=academic_year,
            section=section,
            is_split_sitting=True,
            split_role="AUXILIARY",
            linked_booking_id=b1.id,
            status="CONFIRMED"
        )
        db.add(b2)
        db.flush()

        b1.linked_booking_id = b2.id
        db.commit()
        db.refresh(b1)
        db.refresh(b2)

        NotificationService.notify_target_students(
            db=db,
            title=f"Exam Split Sitting Announced: {title}",
            message=f"Your section examination is split across Room {b1.room.room_number} (candidates 1-{primary_students}) and Room {b2.room.room_number} (candidates {primary_students+1}-{primary_students+auxiliary_students}).",
            notification_type="EXAM_SCHEDULE_CHANGED",
            branch_id=branch_id,
            year=academic_year,
            section=section
        )

        return {
            "status": "SUCCESS",
            "message": "Atomic split sitting successfully reserved.",
            "primary_booking": format_booking(b1),
            "auxiliary_booking": format_booking(b2)
        }


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


@router.get("/split-plan")
def get_split_plan(
    booking_date: Optional[str] = Query(None, description="Target exam date (YYYY-MM-DD)"),
    date: Optional[str] = Query(None, description="Target exam date alias (YYYY-MM-DD)"),
    start_time: str = Query("09:00", description="Exam start time (HH:MM)"),
    end_time: str = Query("11:00", description="Exam end time (HH:MM)"),
    total_students: Optional[int] = Query(None, description="Total candidates in section"),
    total_candidates: Optional[int] = Query(None, description="Total candidates alias"),
    building_id: Optional[int] = Query(None, description="Building ID preference"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """
    Returns calculated split-sitting arrangements according to the Corrected Design PDF:
    - Large single halls (IET32, LIB)
    - Deeksha Bhawan long room pairs (LH01 + LH02, LH08 + LH09)
    - Adjacent IET classrooms with auxiliary seats
    """
    target_date_str = booking_date or date or str(date.today())
    target_count = total_students or total_candidates or 75

    try:
        b_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except Exception:
        b_date = date.today()

    try:
        s_time = datetime.strptime(start_time, "%H:%M").time()
    except Exception:
        try:
            s_time = datetime.strptime(start_time, "%H:%M:%S").time()
        except Exception:
            s_time = time(9, 0)

    try:
        e_time = datetime.strptime(end_time, "%H:%M").time()
    except Exception:
        try:
            e_time = datetime.strptime(end_time, "%H:%M:%S").time()
        except Exception:
            e_time = time(11, 0)

    candidates = ConflictEngine.recommend_split_sitting(
        db=db,
        booking_date=b_date,
        start_time=s_time,
        end_time=e_time,
        total_students=target_count
    )
    return {
        "date": b_date,
        "start_time": s_time.strftime("%H:%M"),
        "end_time": e_time.strftime("%H:%M"),
        "total_students": target_count,
        "recommendations": candidates
    }


@router.post("/split-booking")
def create_split_booking(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """
    Creates an atomic split-sitting arrangement across two rooms for an examination.
    Generates linked bookings: Primary and Auxiliary.
    """
    with _booking_lock:
        primary_room_id = payload.get("primary_room_id")
        auxiliary_room_id = payload.get("auxiliary_room_id")
        date_str = payload.get("date")
        start_str = payload.get("start_time")
        end_str = payload.get("end_time")
        title = payload.get("title", "Section Examination Sitting")
        primary_students = payload.get("primary_students", 38)
        auxiliary_students = payload.get("auxiliary_students", 37)
        branch_id = payload.get("branch_id")
        academic_year = payload.get("academic_year")
        section = payload.get("section")

        if not primary_room_id or not auxiliary_room_id or not date_str or not start_str or not end_str:
            raise HTTPException(status_code=400, detail="Missing required fields for split booking.")

        b_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        s_time = datetime.strptime(start_str, "%H:%M").time()
        e_time = datetime.strptime(end_str, "%H:%M").time()

        # Validate availability of both rooms
        p_ok, p_err, _ = ConflictEngine.check_room_availability(
            db=db, room_id=primary_room_id, booking_date=b_date,
            start_time=s_time, end_time=e_time, expected_students=primary_students,
            purpose="MINOR_EXAM"
        )
        if not p_ok:
            raise HTTPException(status_code=409, detail=f"Primary room conflict: {p_err}")

        a_ok, a_err, _ = ConflictEngine.check_room_availability(
            db=db, room_id=auxiliary_room_id, booking_date=b_date,
            start_time=s_time, end_time=e_time, expected_students=auxiliary_students,
            purpose="MINOR_EXAM"
        )
        if not a_ok:
            raise HTTPException(status_code=409, detail=f"Auxiliary room conflict: {a_err}")

        ref_uuid1 = uuid.uuid4().hex[:6].upper()
        ref_uuid2 = uuid.uuid4().hex[:6].upper()

        b1 = Booking(
            booking_reference=f"CS-{b_date.strftime('%Y%m%d')}-SPLIT-{ref_uuid1}",
            room_id=primary_room_id,
            user_id=current_user.id,
            title=f"{title} (Sitting A)",
            purpose="MINOR_EXAM",
            date=b_date,
            start_time=s_time,
            end_time=e_time,
            expected_students=primary_students,
            branch_id=branch_id,
            academic_year=academic_year,
            section=section,
            is_split_sitting=True,
            split_role="PRIMARY",
            status="CONFIRMED"
        )
        db.add(b1)
        db.flush()

        b2 = Booking(
            booking_reference=f"CS-{b_date.strftime('%Y%m%d')}-SPLIT-{ref_uuid2}",
            room_id=auxiliary_room_id,
            user_id=current_user.id,
            title=f"{title} (Sitting B)",
            purpose="MINOR_EXAM",
            date=b_date,
            start_time=s_time,
            end_time=e_time,
            expected_students=auxiliary_students,
            branch_id=branch_id,
            academic_year=academic_year,
            section=section,
            is_split_sitting=True,
            split_role="AUXILIARY",
            linked_booking_id=b1.id,
            status="CONFIRMED"
        )
        db.add(b2)
        db.flush()

        b1.linked_booking_id = b2.id
        db.commit()
        db.refresh(b1)
        db.refresh(b2)

        NotificationService.notify_target_students(
            db=db,
            title=f"Exam Split Sitting Announced: {title}",
            message=f"Your section examination is split across Room {b1.room.room_number} (candidates 1-{primary_students}) and Room {b2.room.room_number} (candidates {primary_students+1}-{primary_students+auxiliary_students}).",
            notification_type="EXAM_SCHEDULE_CHANGED",
            branch_id=branch_id,
            year=academic_year,
            section=section
        )

        return {
            "status": "SUCCESS",
            "message": "Atomic split sitting successfully reserved.",
            "primary_booking": format_booking(b1),
            "auxiliary_booking": format_booking(b2)
        }

