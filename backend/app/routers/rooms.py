from typing import List, Optional
from datetime import date, time, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload
from backend.app.database import get_db
from backend.app.models import Room, Building, Floor, RoomFacility, User
from backend.app.schemas import RoomResponse, RoomUpdate, RoomAvailabilityResult
from backend.app.services.conflict_engine import ConflictEngine
from backend.app.services.audit_service import AuditService
from backend.app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/rooms", tags=["Rooms"])

def format_room(r: Room, current_status: str = "AVAILABLE", active_booking: Optional[dict] = None) -> dict:
    return {
        "id": r.id,
        "building_id": r.building_id,
        "floor_id": r.floor_id,
        "room_number": r.room_number,
        "room_name": r.room_name,
        "room_type": r.room_type,
        "capacity": r.capacity,
        "exam_capacity": getattr(r, "exam_capacity", int(r.capacity * 0.5)),
        "is_bookable": getattr(r, "is_bookable", True),
        "is_unconfirmed": getattr(r, "is_unconfirmed", False),
        "unconfirmed_reason": getattr(r, "unconfirmed_reason", None),
        "is_active": r.is_active,
        "is_maintenance": r.is_maintenance,
        "verification_status": r.verification_status,
        "verification_notes": r.verification_notes,
        "permitted_uses": r.permitted_uses,
        "svg_id": r.svg_id,
        "building_name": r.building.name if r.building else None,
        "building_code": r.building.code if r.building else None,
        "floor_name": r.floor.floor_name if r.floor else None,
        "floor_number": r.floor.floor_number if r.floor else None,
        "facilities": [
            {"id": f.id, "facility_name": f.facility_name, "quantity": f.quantity, "condition": f.condition}
            for f in r.facilities
        ],
        "current_status": current_status,
        "active_booking": active_booking
    }

@router.get("", response_model=List[RoomResponse])
def get_rooms(
    building_id: Optional[int] = Query(None),
    floor_id: Optional[int] = Query(None),
    room_type: Optional[str] = Query(None),
    target_date: Optional[date] = Query(None),
    target_time_str: Optional[str] = Query(None, alias="target_time"),
    db: Session = Depends(get_db)
):
    query = db.query(Room).options(
        joinedload(Room.building),
        joinedload(Room.floor),
        selectinload(Room.facilities),
    )
    if building_id:
        query = query.filter(Room.building_id == building_id)
    if floor_id:
        query = query.filter(Room.floor_id == floor_id)
    if room_type:
        query = query.filter(Room.room_type == room_type)

    rooms = query.all()
    
    # Parse target time if provided
    t_time = None
    if target_time_str:
        try:
            parts = [int(p) for p in target_time_str.split(":")]
            t_time = time(parts[0], parts[1])
        except Exception:
            t_time = None

    statuses = ConflictEngine.get_room_current_statuses(
        db=db,
        rooms=rooms,
        target_date=target_date,
        target_time=t_time,
    )
    results = []
    for r in rooms:
        status_val, active_info = statuses[r.id]
        results.append(format_room(r, current_status=status_val, active_booking=active_info))

    return results

@router.get("/availability", response_model=List[RoomAvailabilityResult])
def query_rooms_availability(
    booking_date: date = Query(...),
    start_time_str: str = Query(..., alias="start_time"),
    end_time_str: str = Query(..., alias="end_time"),
    building_id: Optional[int] = Query(None),
    floor_id: Optional[int] = Query(None),
    required_capacity: Optional[int] = Query(None, ge=1),
    room_type: Optional[str] = Query(None),
    facility_needed: Optional[str] = Query(None),
    purpose: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"])),
):
    if booking_date < date.today():
        raise HTTPException(status_code=422, detail="Availability can only be searched for today or a future date.")

    try:
        sh, sm = [int(x) for x in start_time_str.split(":")[:2]]
        eh, em = [int(x) for x in end_time_str.split(":")[:2]]
        s_time = time(sh, sm)
        e_time = time(eh, em)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    # Time sanity check
    val_ok, val_err = ConflictEngine.validate_time_range(s_time, e_time)
    if not val_ok:
        raise HTTPException(status_code=400, detail=val_err)

    query = db.query(Room).filter(Room.is_active == True)
    if building_id:
        query = query.filter(Room.building_id == building_id)
    if floor_id:
        query = query.filter(Room.floor_id == floor_id)
    if room_type:
        query = query.filter(Room.room_type == room_type)

    rooms = query.all()
    results = []

    for r in rooms:
        is_avail, conflict_reason, conflict_info = ConflictEngine.check_room_availability(
            db=db,
            room_id=r.id,
            booking_date=booking_date,
            start_time=s_time,
            end_time=e_time,
            expected_students=required_capacity,
            purpose=purpose,
        )

        # Check facility filter if specified
        if facility_needed:
            has_facility = any(f.facility_name == facility_needed for f in r.facilities)
            if not has_facility:
                is_avail = False
                conflict_reason = f"Lacks required facility: {facility_needed}"

        status_val = "AVAILABLE" if is_avail else ("MAINTENANCE" if r.is_maintenance or r.verification_status == "PENDING_ADMIN_VERIFICATION" else "BOOKED")
        
        results.append({
            "room": format_room(r, current_status=status_val),
            "is_available": is_avail,
            "status": status_val,
            "conflict_reason": conflict_reason,
            "current_or_next_booking": conflict_info
        })

    return results

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    r = db.query(Room).filter(Room.id == room_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")
    status_val, active_info = ConflictEngine.get_room_current_status(db=db, room=r)
    return format_room(r, current_status=status_val, active_booking=active_info)

@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    r = db.query(Room).filter(Room.id == room_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")

    old_state = {
        "room_name": r.room_name,
        "capacity": r.capacity,
        "is_maintenance": r.is_maintenance,
        "verification_status": r.verification_status,
        "permitted_uses": r.permitted_uses
    }

    if room_data.room_name is not None:
        r.room_name = room_data.room_name
    if room_data.capacity is not None:
        r.capacity = room_data.capacity
    if room_data.room_type is not None:
        r.room_type = room_data.room_type
    if room_data.is_active is not None:
        r.is_active = room_data.is_active
    if room_data.is_maintenance is not None:
        r.is_maintenance = room_data.is_maintenance
    if room_data.verification_status is not None:
        r.verification_status = room_data.verification_status
    if room_data.verification_notes is not None:
        r.verification_notes = room_data.verification_notes
    if room_data.permitted_uses is not None:
        r.permitted_uses = room_data.permitted_uses

    db.commit()
    db.refresh(r)

    # Audit log
    AuditService.log(
        db=db,
        action_type="UPDATE",
        entity_type="ROOM",
        entity_id=r.id,
        user=current_user,
        previous_value=old_state,
        new_value=room_data.model_dump(exclude_unset=True),
        reason="Administrative room update"
    )

    return format_room(r)

@router.post("/{room_id}/verify", response_model=RoomResponse)
def verify_blueprint_discrepancy_room(
    room_id: int,
    verified_status: str = Query("OFFICIAL_VERIFIED", pattern="^(OFFICIAL_VERIFIED|RESTRICTED)$"),
    admin_notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Specifically for Deeksha Bhawan LH13 / LH14 blueprint discrepancy verification.
    """
    r = db.query(Room).filter(Room.id == room_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")

    old_verif = r.verification_status
    r.verification_status = verified_status
    r.verification_notes = admin_notes or f"Administratively verified and authorized by {current_user.full_name}."
    db.commit()
    db.refresh(r)

    AuditService.log(
        db=db,
        action_type="APPROVE" if verified_status == "OFFICIAL_VERIFIED" else "UPDATE",
        entity_type="ROOM",
        entity_id=r.id,
        user=current_user,
        previous_value={"verification_status": old_verif},
        new_value={"verification_status": verified_status, "notes": r.verification_notes},
        reason=f"Blueprint discrepancy resolution for {r.room_number}"
    )

    return format_room(r)

