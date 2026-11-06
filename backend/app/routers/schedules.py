from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Schedule, Student, Faculty, Room, Branch, User
from backend.app.schemas import ScheduleCreate, ScheduleResponse
from backend.app.dependencies import get_current_user, require_role
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/schedules", tags=["Schedules"])

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
            Schedule.section == student.section,
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
    db: Session = Depends(get_db)
):
    query = db.query(Schedule).filter(Schedule.is_active == True)
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
    # Check for room conflict at same day & time
    conflict = db.query(Schedule).filter(
        Schedule.room_id == sched_in.room_id,
        Schedule.day_of_week == sched_in.day_of_week,
        Schedule.is_active == True,
        Schedule.start_time < sched_in.end_time,
        Schedule.end_time > sched_in.start_time
    ).first()

    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Room conflict: Already allocated to {conflict.subject_code} from {conflict.start_time.strftime('%H:%M')} to {conflict.end_time.strftime('%H:%M')}"
        )

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

    old_data = {
        "room_id": sched.room_id,
        "start_time": str(sched.start_time),
        "end_time": str(sched.end_time),
        "day_of_week": sched.day_of_week
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

    # Notify affected students
    NotificationService.notify_target_students(
        db=db,
        title=f"Timetable Updated: {sched.subject_name}",
        message=f"Timetable for {sched.subject_code} updated to Room {sched.room.room_number} ({sched.start_time.strftime('%I:%M %p')}).",
        notification_type="EXAM_SCHEDULE_CHANGED",
        branch_id=sched.branch_id,
        year=sched.academic_year,
        section=sched.section
    )

    return format_schedule(sched)
