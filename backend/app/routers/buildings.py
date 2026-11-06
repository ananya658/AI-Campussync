from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Building, Floor, Room, User
from backend.app.schemas import BuildingResponse, FloorResponse
from backend.app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/buildings", tags=["Buildings"])

@router.get("", response_model=List[BuildingResponse])
def get_buildings(db: Session = Depends(get_db)):
    buildings = db.query(Building).filter(Building.is_active == True).all()
    results = []
    for b in buildings:
        floors_list = []
        for f in b.floors:
            rooms_list = []
            for r in f.rooms:
                rooms_list.append({
                    "id": r.id,
                    "building_id": r.building_id,
                    "floor_id": r.floor_id,
                    "room_number": r.room_number,
                    "room_name": r.room_name,
                    "room_type": r.room_type,
                    "capacity": r.capacity,
                    "is_active": r.is_active,
                    "is_maintenance": r.is_maintenance,
                    "verification_status": r.verification_status,
                    "verification_notes": r.verification_notes,
                    "permitted_uses": r.permitted_uses,
                    "svg_id": r.svg_id,
                    "building_name": b.name,
                    "building_code": b.code,
                    "floor_name": f.floor_name,
                    "floor_number": f.floor_number,
                    "facilities": [
                        {"id": fac.id, "facility_name": fac.facility_name, "quantity": fac.quantity, "condition": fac.condition}
                        for fac in r.facilities
                    ],
                    "current_status": "AVAILABLE"
                })
            floors_list.append({
                "id": f.id,
                "building_id": f.building_id,
                "floor_number": f.floor_number,
                "floor_name": f.floor_name,
                "rooms": rooms_list
            })
        results.append({
            "id": b.id,
            "name": b.name,
            "code": b.code,
            "description": b.description,
            "total_floors": b.total_floors,
            "distance_from_iet_meters": b.distance_from_iet_meters,
            "is_active": b.is_active,
            "floors": floors_list
        })
    return results

@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(building_id: int, db: Session = Depends(get_db)):
    b = db.query(Building).filter(Building.id == building_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Building not found")
    
    floors_list = []
    for f in b.floors:
        rooms_list = []
        for r in f.rooms:
            rooms_list.append({
                "id": r.id,
                "building_id": r.building_id,
                "floor_id": r.floor_id,
                "room_number": r.room_number,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "is_active": r.is_active,
                "is_maintenance": r.is_maintenance,
                "verification_status": r.verification_status,
                "verification_notes": r.verification_notes,
                "permitted_uses": r.permitted_uses,
                "svg_id": r.svg_id,
                "building_name": b.name,
                "building_code": b.code,
                "floor_name": f.floor_name,
                "floor_number": f.floor_number,
                "facilities": [
                    {"id": fac.id, "facility_name": fac.facility_name, "quantity": fac.quantity, "condition": fac.condition}
                    for fac in r.facilities
                ],
                "current_status": "AVAILABLE"
            })
        floors_list.append({
            "id": f.id,
            "building_id": f.building_id,
            "floor_number": f.floor_number,
            "floor_name": f.floor_name,
            "rooms": rooms_list
        })
    return {
        "id": b.id,
        "name": b.name,
        "code": b.code,
        "description": b.description,
        "total_floors": b.total_floors,
        "distance_from_iet_meters": b.distance_from_iet_meters,
        "is_active": b.is_active,
        "floors": floors_list
    }

@router.get("/{building_id}/floors", response_model=List[FloorResponse])
def get_building_floors(building_id: int, db: Session = Depends(get_db)):
    floors = db.query(Floor).filter(Floor.building_id == building_id).order_by(Floor.floor_number).all()
    results = []
    for f in floors:
        rooms_list = []
        for r in f.rooms:
            rooms_list.append({
                "id": r.id,
                "building_id": r.building_id,
                "floor_id": r.floor_id,
                "room_number": r.room_number,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "is_active": r.is_active,
                "is_maintenance": r.is_maintenance,
                "verification_status": r.verification_status,
                "verification_notes": r.verification_notes,
                "permitted_uses": r.permitted_uses,
                "svg_id": r.svg_id,
                "building_name": f.building.name,
                "building_code": f.building.code,
                "floor_name": f.floor_name,
                "floor_number": f.floor_number,
                "facilities": [
                    {"id": fac.id, "facility_name": fac.facility_name, "quantity": fac.quantity, "condition": fac.condition}
                    for fac in r.facilities
                ],
                "current_status": "AVAILABLE"
            })
        results.append({
            "id": f.id,
            "building_id": f.building_id,
            "floor_number": f.floor_number,
            "floor_name": f.floor_name,
            "rooms": rooms_list
        })
    return results

