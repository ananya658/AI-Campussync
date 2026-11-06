from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, true
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Booking, Schedule, Student, Faculty, Room, Branch, User
from backend.app.schemas import ScheduleCreate, ScheduleResponse
from backend.app.dependencies import get_current_user, require_role
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/schedules", tags=["Schedules"])


def _validate_schedule_slot(db: Session, schedule_in: ScheduleCreate, exclude_id: Optional[int] = None) -> None:
    schedule_in.section = schedule_in.section.strip().upper()
    if schedule_in.day_of_week not in range(6):
        raise HTTPException(status_code=422, detail="day_of_week must be between 0 (Monday) and 5 (Saturday).")
    if schedule_in.start_time >= schedule_in.end_time:
        raise HTTPException(status_code=422, detail="Schedule start time must be before its end time.")
    if schedule_in.academic_year not in {1, 2, 3, 4}:
        raise HTTPException(status_code=422, detail="academic_year must be between 1 and 4.")
    if not schedule_in.section.strip():
        raise HTTPException(status_code=422, detail="section cannot be empty.")

    room = db.query(Room).filter(Room.id == schedule_in.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    if (
        not room.is_active
        or not room.is_bookable
        or room.is_maintenance
        or room.verification_status in {"PENDING_ADMIN_VERIFICATION", "RESTRICTED"}
    ):
        raise HTTPException(status_code=409, detail=f"Room {room.room_number} is not available for a timetable allocation.")
    if not db.query(Faculty).filter(Faculty.id == schedule_in.faculty_id).first():
        raise HTTPException(status_code=404, detail="Faculty profile not found.")
    if not db.query(Branch).filter(Branch.id == schedule_in.branch_id).first():
        raise HTTPException(status_code=404, detail="Branch not found.")

    query = db.query(Schedule).filter(
        Schedule.day_of_week == schedule_in.day_of_week,
        Schedule.is_active.is_(True),
        Schedule.start_time < schedule_in.end_time,
        Schedule.end_time > schedule_in.start_time,
    )
    if exclude_id is not None:
        query = query.filter(Schedule.id != exclude_id)
    overlaps = query.all()

    for existing in overlaps:
        conflict = None
        if existing.room_id == schedule_in.room_id:
            conflict = ("ROOM_SCHEDULE_CONFLICT", "Room")
        elif existing.faculty_id == schedule_in.faculty_id:
            conflict = ("FACULTY_SCHEDULE_CONFLICT", "Faculty")
        elif (
            existing.branch_id == schedule_in.branch_id
            and existing.academic_year == schedule_in.academic_year
            and (
                schedule_in.section.upper() == "ALL"
                or existing.section.upper() == "ALL"
                or existing.section == schedule_in.section
            )
        ):
            conflict = ("SECTION_SCHEDULE_CONFLICT", "Student section")
        if conflict:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": conflict[0],
                    "message": f"{conflict[1]} already has an overlapping timetable slot: {existing.subject_code} ({existing.start_time:%H:%M}-{existing.end_time:%H:%M}).",
                },
            )

    section_filter = (
        true()
        if schedule_in.section.upper() == "ALL"
        else or_(Schedule.section == schedule_in.section, Schedule.section == "ALL")
    )
    related_schedules = db.query(Schedule).filter(
        Schedule.day_of_week == schedule_in.day_of_week,
        Schedule.is_active.is_(True),
        or_(
            Schedule.faculty_id == schedule_in.faculty_id,
            (
                (Schedule.branch_id == schedule_in.branch_id)
                & (Schedule.academic_year == schedule_in.academic_year)
                & section_filter
            ),
        ),
    )
    if exclude_id is not None:
        related_schedules = related_schedules.filter(Schedule.id != exclude_id)
    for existing in related_schedules.all():
        existing_room = db.query(Room).filter(Room.id == existing.room_id).first()
        if not existing_room or existing_room.building_id == room.building_id:
            continue
        before_gap = (
            datetime.combine(date.today(), schedule_in.start_time)
            - datetime.combine(date.today(), existing.end_time)
        ).total_seconds() / 60
        after_gap = (
            datetime.combine(date.today(), existing.start_time)
            - datetime.combine(date.today(), schedule_in.end_time)
        ).total_seconds() / 60
        if 0 <= before_gap < 10 or 0 <= after_gap < 10:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "TRAVEL_BUFFER_CONFLICT",
                    "message": "The section or faculty member needs at least 10 minutes to move between campus buildings.",
                },
            )

    future_bookings = db.query(Booking).filter(
        Booking.date >= date.today(),
        Booking.status.in_(["CONFIRMED", "PENDING_APPROVAL", "APPROVED"]),
        Booking.start_time < schedule_in.end_time,
        Booking.end_time > schedule_in.start_time,
        or_(
            Booking.room_id == schedule_in.room_id,
            Booking.faculty_id == schedule_in.faculty_id,
            (
                (Booking.branch_id == schedule_in.branch_id)
                & (Booking.academic_year == schedule_in.academic_year)
                & (
                    true()
                    if schedule_in.section == "ALL"
                    else or_(Booking.section == schedule_in.section, Booking.section == "ALL")
                )
            ),
        ),
    ).all()
    for booking in future_bookings:
        if booking.date.weekday() != schedule_in.day_of_week:
            continue
        if booking.room_id == schedule_in.room_id:
            resource = "Room"
        elif booking.faculty_id == schedule_in.faculty_id:
            resource = "Faculty"
        else:
            resource = "Student section"
        raise HTTPException(
            status_code=409,
            detail={
                "code": "BOOKING_SCHEDULE_CONFLICT",
                "message": f"The timetable slot overlaps an existing booking ({booking.booking_reference}) for this {resource.lower()}.",
            },
        )

def format_schedule(s: Schedule) -> dict:
    return {
        "id": s.id,
        "room_id": s.room_id,
        "faculty_id": s.faculty_id,
        "branch_id": s.branch_id,
        "academic_year": s.academic_year,
        "section": s.section,
        "day_of_week": s.day_of_week,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "subject_code": s.subject_code,
        "subject_name": s.subject_name,
        "schedule_type": s.schedule_type,
        "is_active": s.is_active,
        "room_number": s.room.room_number if s.room else None,
        "building_name": s.room.building.name if s.room and s.room.building else None,
        "faculty_name": s.faculty.user.full_name if s.faculty and s.faculty.user else None,
        "branch_code": s.branch.code if s.branch else None
    }

@router.get("/me", response_model=List[ScheduleResponse])
def get_my_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns personalized academic schedule:
    - For students: mapped to their branch, academic year, and section.
    - For faculty: classes they are scheduled to teach.
    """
    if current_user.role == "STUDENT":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        schedules = db.query(Schedule).filter(
            Schedule.branch_id == student.branch_id,
            Schedule.academic_year == student.year,
            or_(Schedule.section == student.section, Schedule.section == "ALL"),
            Schedule.is_active == True
        ).order_by(Schedule.day_of_week, Schedule.start_time).all()
        return [format_schedule(s) for s in schedules]

    elif current_user.role == "FACULTY":
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty:
            return []
        schedules = db.query(Schedule).filter(
            Schedule.faculty_id == faculty.id,
            Schedule.is_active == True
        ).order_by(Schedule.day_of_week, Schedule.start_time).all()
        return [format_schedule(s) for s in schedules]

    else:
        # Admin gets full schedule by default
        schedules = db.query(Schedule).filter(Schedule.is_active == True).order_by(Schedule.day_of_week, Schedule.start_time).all()
        return [format_schedule(s) for s in schedules]

@router.get("", response_model=List[ScheduleResponse])
def get_schedules(
    branch_id: Optional[int] = Query(None),
    academic_year: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    room_id: Optional[int] = Query(None),
    day_of_week: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Schedule).filter(Schedule.is_active == True)
    if current_user.role == "STUDENT":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        query = query.filter(
            Schedule.branch_id == student.branch_id,
            Schedule.academic_year == student.year,
            or_(Schedule.section == student.section, Schedule.section == "ALL"),
        )
    elif current_user.role == "FACULTY":
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty:
            return []
        query = query.filter(Schedule.faculty_id == faculty.id)
    else:
        if branch_id:
            query = query.filter(Schedule.branch_id == branch_id)
        if academic_year:
            query = query.filter(Schedule.academic_year == academic_year)
        if section:
            query = query.filter(Schedule.section == section)
        if room_id:
            query = query.filter(Schedule.room_id == room_id)
    if day_of_week is not None:
        query = query.filter(Schedule.day_of_week == day_of_week)

    schedules = query.order_by(Schedule.day_of_week, Schedule.start_time).all()
    return [format_schedule(s) for s in schedules]

@router.post("", response_model=ScheduleResponse)
def create_schedule(
    sched_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    _validate_schedule_slot(db, sched_in)

    new_sched = Schedule(
        room_id=sched_in.room_id,
        faculty_id=sched_in.faculty_id,
        branch_id=sched_in.branch_id,
        academic_year=sched_in.academic_year,
        section=sched_in.section,
        day_of_week=sched_in.day_of_week,
        start_time=sched_in.start_time,
        end_time=sched_in.end_time,
        subject_code=sched_in.subject_code,
        subject_name=sched_in.subject_name,
        schedule_type=sched_in.schedule_type,
        is_active=True
    )
    db.add(new_sched)
    db.commit()
    db.refresh(new_sched)

    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="SCHEDULE",
        entity_id=new_sched.id,
        user=current_user,
        new_value=sched_in.model_dump(mode="json"),
        reason="Academic timetable slot configured"
    )

    NotificationService.notify_target_students(
        db=db,
        title=f"New timetable entry: {new_sched.subject_name}",
        message=f"{new_sched.subject_code} is scheduled in Room {new_sched.room.room_number} on day {new_sched.day_of_week} from {new_sched.start_time:%H:%M} to {new_sched.end_time:%H:%M}.",
        notification_type="EXAM_SCHEDULE_CHANGED",
        branch_id=new_sched.branch_id,
        year=new_sched.academic_year,
        section=new_sched.section,
    )

    return format_schedule(new_sched)

@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    sched_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    sched = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule slot not found")

    _validate_schedule_slot(db, sched_in, exclude_id=sched.id)

    old_data = {
        "room_id": sched.room_id,
        "start_time": str(sched.start_time),
        "end_time": str(sched.end_time),
        "day_of_week": sched.day_of_week,
        "faculty_id": sched.faculty_id,
        "branch_id": sched.branch_id,
        "academic_year": sched.academic_year,
        "section": sched.section,
        "subject_code": sched.subject_code,
        "subject_name": sched.subject_name,
    }

    sched.room_id = sched_in.room_id
    sched.faculty_id = sched_in.faculty_id
    sched.branch_id = sched_in.branch_id
    sched.academic_year = sched_in.academic_year
    sched.section = sched_in.section
    sched.day_of_week = sched_in.day_of_week
    sched.start_time = sched_in.start_time
    sched.end_time = sched_in.end_time
    sched.subject_code = sched_in.subject_code
    sched.subject_name = sched_in.subject_name
    sched.schedule_type = sched_in.schedule_type

    db.commit()
    db.refresh(sched)

    AuditService.log(
        db=db,
        action_type="UPDATE",
        entity_type="SCHEDULE",
        entity_id=sched.id,
        user=current_user,
        previous_value=old_data,
        new_value=sched_in.model_dump(mode="json"),
        reason="Schedule modified by administrator"
    )

    if (
        old_data["branch_id"] != sched.branch_id
        or old_data["academic_year"] != sched.academic_year
        or old_data["section"] != sched.section
    ):
        NotificationService.notify_target_students(
            db=db,
            title=f"Timetable change: {old_data['subject_name']}",
            message="A timetable entry has moved to a different student group. Check your updated timetable.",
            notification_type="EXAM_SCHEDULE_CHANGED",
            branch_id=old_data["branch_id"],
            year=old_data["academic_year"],
            section=old_data["section"],
        )

    # Notify affected students
    NotificationService.notify_target_students(
        db=db,
        title=f"Timetable Updated: {sched.subject_name}",
        message=f"{sched.subject_code} now meets in Room {sched.room.room_number} on day {sched.day_of_week} from {sched.start_time:%H:%M} to {sched.end_time:%H:%M}.",
        notification_type="EXAM_SCHEDULE_CHANGED",
        branch_id=sched.branch_id,
        year=sched.academic_year,
        section=sched.section
    )

    return format_schedule(sched)


@router.delete("/{schedule_id}")
def cancel_schedule(
    schedule_id: int,
    reason: str = Query(..., min_length=3, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    sched = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule slot not found")
    if not sched.is_active:
        raise HTTPException(status_code=409, detail="Schedule slot is already cancelled")

    previous = {
        "room_id": sched.room_id,
        "day_of_week": sched.day_of_week,
        "start_time": str(sched.start_time),
        "end_time": str(sched.end_time),
        "subject_code": sched.subject_code,
        "subject_name": sched.subject_name,
    }
    sched.is_active = False
    db.commit()
    db.refresh(sched)
    AuditService.log(
        db=db,
        action_type="CANCEL",
        entity_type="SCHEDULE",
        entity_id=sched.id,
        user=current_user,
        previous_value=previous,
        new_value={"is_active": False},
        reason=reason,
    )
    NotificationService.notify_target_students(
        db=db,
        title=f"Class cancelled: {sched.subject_name}",
        message=f"{sched.subject_code} on day {sched.day_of_week} from {sched.start_time:%H:%M} to {sched.end_time:%H:%M} has been cancelled. Reason: {reason}",
        notification_type="BOOKING_CANCELLED",
        branch_id=sched.branch_id,
        year=sched.academic_year,
        section=sched.section,
    )
    return {"message": "Schedule cancelled", "schedule_id": sched.id}

