import csv
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import (
    Room, Building, Floor, User, Student, Branch, Batch, Section,
    RoomClosure, SystemSetting, AuditLog
)
from backend.app.schemas import (
    RoomResponse, SectionResponse, RoomClosureCreate, RoomClosureResponse,
    SystemSettingResponse, SystemSettingUpdate
)
from backend.app.dependencies import get_current_user, require_role
from backend.app.services.audit_service import AuditService
from backend.app.routers.rooms import format_room

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation & System Management"])


# ==========================================
# 1. Blueprint Reconciliation Ledger (Table 9)
# ==========================================
@router.get("/ledger")
def get_reconciliation_ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Returns the authoritative 5 Reconciliation Ledger entries (Table 9 of Corrected Design)
    plus all campus rooms with unconfirmed or discrepancy flags.
    """
    # Authoritative Table 9 ledger items from specification
    table_9_items = [
        {
            "id": 1,
            "title": "IET 1st Floor North Rooms: Labs vs Classrooms",
            "disagreement": "Problem statement designates four 1st floor rooms as labs (CSE, ME, ECE, IT). Architectural plan shows 4 unlabelled rooms.",
            "decision": "Seeded as specialized laboratories (IET22, IET16, IET14, IET15) with branch mappings; flagged as unconfirmed.",
            "rationale": "One configuration row changes them to classrooms if administration clarifies; flags remain visible in interface.",
            "affected_rooms": ["IET22", "IET16", "IET14", "IET15"],
            "status": "CONFIGURED_UNCONFIRMED"
        },
        {
            "id": 2,
            "title": "IET 2nd Floor Classroom IET23",
            "disagreement": "Problem statement text lists 5 second-floor classrooms; architectural floor plan shows 6, including room IET23.",
            "decision": "Kept as an active bookable classroom (75 capacity); flagged as unconfirmed.",
            "rationale": "Floor plan is physically specific where statement is a summary. Dropping a usable room costs more than keeping one that exists.",
            "affected_rooms": ["IET23"],
            "status": "RETAINED_ACTIVE"
        },
        {
            "id": 3,
            "title": "Deeksha Bhawan Total Room Count: LH13 & LH14",
            "disagreement": "Statement estimates 'around 10-12 rooms in Deeksha Bhawan'; structural floor plan contains 14 halls (LH01 to LH14).",
            "decision": "Seeded all 14 lecture halls; LH13 and LH14 placed under PENDING_ADMIN_VERIFICATION.",
            "rationale": "The word 'around' licenses the plan. Physical verification gate prevents unconfirmed scheduling while preserving honesty.",
            "affected_rooms": ["LH13", "LH14"],
            "status": "PENDING_ADMIN_VERIFICATION"
        },
        {
            "id": 4,
            "title": "Deeksha Bhawan Headcount Capacity Inferences",
            "disagreement": "No room capacities were stated in problem statement for Deeksha Bhawan halls.",
            "decision": "Inferred from relative floor plan dimensions: Long rooms (LH01, LH02, LH08, LH09) at 80; Medium rooms (LH06, LH07, LH13, LH14) at 55; Compact rooms at 45.",
            "rationale": "Stored as editable parameters in database, allowing immediate administrative calibration without schema migration.",
            "affected_rooms": ["LH01", "LH02", "LH08", "LH09", "LH06", "LH07", "LH13", "LH14", "LH03", "LH04", "LH05", "LH10", "LH11", "LH12"],
            "status": "CALIBRATED_EDITABLE"
        },
        {
            "id": 5,
            "title": "Central Engineering Library Dual Examination Mode",
            "disagreement": "Library is used for examinations during peak semester periods; regular student study during semester.",
            "decision": "Configured as bookable for examinations (>100 headcount) subject to administrator approval gate and library exclusion windows.",
            "rationale": "Modeled as adaptive policy rather than hard denial, recovering up to 90 spaced examination seats.",
            "affected_rooms": ["LIB"],
            "status": "APPROVAL_GATED"
        }
    ]

    # Query all rooms that have flags or non-verified status
    flagged_rooms = db.query(Room).filter(
        (Room.is_unconfirmed == True) | 
        (Room.verification_status != "OFFICIAL_VERIFIED") |
        (Room.is_bookable == False)
    ).all()

    return {
        "table_9_reconciliations": table_9_items,
        "flagged_rooms": [format_room(r) for r in flagged_rooms],
        "summary": {
            "total_recorded_spaces": db.query(Room).count(),
            "total_bookable_rooms": db.query(Room).filter(Room.is_bookable == True).count(),
            "total_non_bookable": db.query(Room).filter(Room.is_bookable == False).count(),
            "unconfirmed_count": db.query(Room).filter(Room.is_unconfirmed == True).count(),
            "pending_verification_count": db.query(Room).filter(Room.verification_status == "PENDING_ADMIN_VERIFICATION").count()
        }
    }


@router.post("/rooms/{room_id}/verify")
def verify_reconciliation_room(
    room_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Administrative reconciliation action:
    - Approve/clear discrepancy (OFFICIAL_VERIFIED, RESTRICTED)
    - Confirm unconfirmed flag
    - Adjust capacity / exam capacity
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    old_status = room.verification_status
    old_capacity = room.capacity
    old_unconfirmed = room.is_unconfirmed

    if "verification_status" in payload:
        room.verification_status = payload["verification_status"]
    if "is_unconfirmed" in payload:
        room.is_unconfirmed = payload["is_unconfirmed"]
    if "is_bookable" in payload:
        room.is_bookable = payload["is_bookable"]
    if "capacity" in payload:
        room.capacity = int(payload["capacity"])
    if "exam_capacity" in payload:
        room.exam_capacity = int(payload["exam_capacity"])
    if "verification_notes" in payload:
        room.verification_notes = payload["verification_notes"]

    db.commit()
    db.refresh(room)

    AuditService.log(
        db=db,
        action_type="UPDATE",
        entity_type="ROOM",
        entity_id=room.id,
        user=current_user,
        previous_value={"status": old_status, "capacity": old_capacity, "is_unconfirmed": old_unconfirmed},
        new_value={
            "status": room.verification_status,
            "capacity": room.capacity,
            "exam_capacity": room.exam_capacity,
            "is_unconfirmed": room.is_unconfirmed
        },
        reason=payload.get("admin_notes") or "Administrative reconciliation decision verified."
    )

    return {
        "status": "SUCCESS",
        "message": f"Room {room.room_number} reconciliation updated.",
        "room": format_room(room)
    }


# ==========================================
# 2. System Settings Management
# ==========================================
@router.get("/settings", response_model=List[SystemSettingResponse])
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "FACULTY"]))
):
    settings = db.query(SystemSetting).all()
    return settings


@router.put("/settings/{setting_key}", response_model=SystemSettingResponse)
def update_system_setting(
    setting_key: str,
    update_in: SystemSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    setting = db.query(SystemSetting).filter(SystemSetting.key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"System setting '{setting_key}' not found.")

    old_val = setting.value
    setting.value = update_in.value
    setting.updated_at = datetime.utcnow()
    setting.updated_by_id = current_user.id

    db.commit()
    db.refresh(setting)

    AuditService.log(
        db=db,
        action_type="UPDATE",
        entity_type="SETTING",
        entity_id=setting.id,
        user=current_user,
        previous_value={"key": setting_key, "value": old_val},
        new_value={"key": setting_key, "value": setting.value},
        reason=f"Configured {setting_key} to {setting.value}"
    )

    return setting


# ==========================================
# 3. Room Closures (Maintenance Windows)
# ==========================================
@router.get("/closures", response_model=List[RoomClosureResponse])
def get_room_closures(
    room_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(RoomClosure)
    if room_id:
        query = query.filter(RoomClosure.room_id == room_id)
    if is_active is not None:
        query = query.filter(RoomClosure.is_active == is_active)

    closures = query.order_by(desc(RoomClosure.start_time)).all()
    results = []
    for c in closures:
        results.append({
            "id": c.id,
            "room_id": c.room_id,
            "room_number": c.room.room_number if c.room else None,
            "title": c.title,
            "reason": c.reason,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "is_active": c.is_active,
            "created_at": c.created_at,
            "created_by_name": c.created_by.full_name if c.created_by else None
        })
    return results


@router.post("/closures", response_model=RoomClosureResponse)
def create_room_closure(
    closure_in: RoomClosureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    room = db.query(Room).filter(Room.id == closure_in.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    if closure_in.start_time >= closure_in.end_time:
        raise HTTPException(status_code=400, detail="Start time must be strictly before end time.")

    closure = RoomClosure(
        room_id=closure_in.room_id,
        title=closure_in.title,
        reason=closure_in.reason,
        start_time=closure_in.start_time,
        end_time=closure_in.end_time,
        created_by_id=current_user.id,
        is_active=True
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)

    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="ROOM_CLOSURE",
        entity_id=closure.id,
        user=current_user,
        new_value={"room": room.room_number, "title": closure.title, "reason": closure.reason},
        reason=f"Scheduled room closure for {room.room_number}: {closure.title}"
    )

    return {
        "id": closure.id,
        "room_id": closure.room_id,
        "room_number": room.room_number,
        "title": closure.title,
        "reason": closure.reason,
        "start_time": closure.start_time,
        "end_time": closure.end_time,
        "is_active": closure.is_active,
        "created_at": closure.created_at,
        "created_by_name": current_user.full_name
    }


@router.delete("/closures/{closure_id}")
def delete_room_closure(
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    closure = db.query(RoomClosure).filter(RoomClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="Closure not found.")

    db.delete(closure)
    db.commit()
    return {"status": "SUCCESS", "message": "Room closure removed."}


# ==========================================
# 4. Academic Sections (32 Sections)
# ==========================================
@router.get("/sections", response_model=List[SectionResponse])
def get_sections(
    academic_year: Optional[int] = Query(None),
    branch_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Section)
    if academic_year:
        query = query.filter(Section.academic_year == academic_year)
    if branch_id:
        query = query.filter(Section.branch_id == branch_id)

    sections = query.all()
    results = []
    for s in sections:
        results.append({
            "id": s.id,
            "code": s.code,
            "branch_id": s.branch_id,
            "academic_year": s.academic_year,
            "section_name": s.section_name,
            "student_count": s.student_count,
            "branch_code": s.branch.code if s.branch else None,
            "branch_name": s.branch.name if s.branch else None
        })
    return results


# ==========================================
# 5. Student CSV Import Endpoint (Direct UI File Upload)
# ==========================================
@router.post("/students/import-csv")
async def import_students_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Parses and validates student records from uploaded CSV.
    Detects duplicate emails/roll numbers, associates branch & batch, and creates accounts.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_fields = ["email", "full_name", "roll_number", "branch_code", "year", "section"]
    for rf in required_fields:
        if rf not in (reader.fieldnames or []):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required CSV column '{rf}'. Required headers: {', '.join(required_fields)}"
            )

    from backend.app.auth import hash_password

    # Cache lookup dictionaries
    branches = {b.code.upper(): b.id for b in db.query(Branch).all()}
    active_batch = db.query(Batch).filter(Batch.is_active == True).first()
    if not active_batch:
        raise HTTPException(status_code=500, detail="No active academic batch configured in database.")

    existing_emails = set(e[0] for e in db.query(User.email).all())
    existing_rolls = set(r[0] for r in db.query(Student.roll_number).all())

    imported = 0
    skipped_duplicates = 0
    errors = []

    for row_idx, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip().lower()
        full_name = (row.get("full_name") or "").strip()
        roll_number = (row.get("roll_number") or "").strip().upper()
        branch_code = (row.get("branch_code") or "").strip().upper()
        year_str = (row.get("year") or "").strip()
        section_str = (row.get("section") or "A").strip().upper()
        password = (row.get("password") or "Student@2026").strip()

        if not email or not roll_number or not full_name:
            errors.append(f"Row {row_idx}: Missing email, roll number, or name.")
            continue

        if email in existing_emails or roll_number in existing_rolls:
            skipped_duplicates += 1
            continue

        if branch_code not in branches:
            errors.append(f"Row {row_idx}: Unknown branch code '{branch_code}'. Valid: {list(branches.keys())}")
            continue

        try:
            year = int(year_str)
        except ValueError:
            errors.append(f"Row {row_idx}: Invalid academic year '{year_str}'.")
            continue

        # Find or link Section
        sec_code = f"{branch_code}-{year}{section_str}"
        sec_obj = db.query(Section).filter(Section.code == sec_code).first()

        # Create user & student
        new_user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="STUDENT",
            department=branch_code,
            is_active=True
        )
        db.add(new_user)
        db.flush()

        new_student = Student(
            user_id=new_user.id,
            roll_number=roll_number,
            branch_id=branches[branch_code],
            batch_id=active_batch.id,
            section_id=sec_obj.id if sec_obj else None,
            year=year,
            section=section_str
        )
        db.add(new_student)

        existing_emails.add(email)
        existing_rolls.add(roll_number)
        imported += 1

    db.commit()

    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="USER",
        entity_id=f"BATCH-IMPORT-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
        user=current_user,
        new_value={"imported_count": imported, "skipped_duplicates": skipped_duplicates},
        reason=f"Imported {imported} students from CSV ({file.filename})"
    )

    return {
        "status": "SUCCESS",
        "imported_records": imported,
        "skipped_duplicates": skipped_duplicates,
        "validation_errors": errors
    }

