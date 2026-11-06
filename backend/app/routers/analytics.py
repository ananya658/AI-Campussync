from datetime import date, datetime, time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import Room, Booking, Announcement, IssueReport, Building
from backend.app.schemas import AnalyticsSummary
from backend.app.dependencies import require_role
from backend.app.models import User
from backend.app.services.conflict_engine import ConflictEngine

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsSummary)
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    today = date.today()
    now_time = datetime.now().time()

    # Total counts by room type
    total_classrooms = db.query(Room).filter(Room.room_type == "LECTURE_HALL", Room.is_active == True).count()
    total_laboratories = db.query(Room).filter(Room.room_type == "LAB", Room.is_active == True).count()
    total_seminar_halls = db.query(Room).filter(Room.room_type == "SEMINAR_HALL", Room.is_active == True).count()
    all_active_rooms = db.query(Room).filter(Room.is_active == True).all()

    # Real-time room status calculation
    occupied_count = 0
    available_count = 0
    for r in all_active_rooms:
        status, _ = ConflictEngine.get_room_current_status(db, r, target_date=today, target_time=now_time)
        if status == "BOOKED":
            occupied_count += 1
        elif status == "AVAILABLE":
            available_count += 1

    # Bookings stats
    total_active_bookings = db.query(Booking).filter(
        Booking.status == "CONFIRMED",
        Booking.date >= today
    ).count()

    pending_booking_requests = db.query(Booking).filter(
        Booking.status == "PENDING_APPROVAL"
    ).count()

    upcoming_examinations = db.query(Announcement).filter(
        Announcement.announcement_type.in_(["MINOR_EXAM", "MAJOR_EXAM", "PRACTICAL_EXAM"]),
        Announcement.status == "PUBLISHED"
    ).count()

    pending_student_reports = db.query(IssueReport).filter(
        IssueReport.status == "PENDING"
    ).count()

    # Overall room utilization % (occupied vs total active rooms)
    total_rooms_count = len(all_active_rooms)
    utilization_pct = round((occupied_count / total_rooms_count * 100), 1) if total_rooms_count > 0 else 0.0

    # Peak booking hours breakdown based on confirmed bookings
    # Create hour buckets 8 AM to 6 PM (08:00 to 18:00)
    hour_buckets = {h: 0 for h in range(8, 19)}
    recent_bookings = db.query(Booking).filter(
        Booking.status == "CONFIRMED"
    ).all()

    for b in recent_bookings:
        start_h = b.start_time.hour
        end_h = b.end_time.hour
        for h in range(max(8, start_h), min(19, end_h + 1)):
            hour_buckets[h] += 1

    peak_hours_list = [
        {"hour": f"{h:02d}:00", "bookings": count, "label": f"{h if h <= 12 else h-12} {'AM' if h < 12 else 'PM'}"}
        for h, count in sorted(hour_buckets.items())
    ]

    # Building-wise utilization
    buildings = db.query(Building).filter(Building.is_active == True).all()
    building_util = []
    for b in buildings:
        b_rooms = [r for r in all_active_rooms if r.building_id == b.id]
        b_total = len(b_rooms)
        b_occupied = 0
        for r in b_rooms:
            st, _ = ConflictEngine.get_room_current_status(db, r, target_date=today, target_time=now_time)
            if st == "BOOKED":
                b_occupied += 1
        b_rate = round((b_occupied / b_total * 100), 1) if b_total > 0 else 0.0
        building_util.append({
            "building_id": b.id,
            "building_name": b.name,
            "building_code": b.code,
            "total_rooms": b_total,
            "occupied_rooms": b_occupied,
            "utilization_pct": b_rate
        })

    return {
        "total_classrooms": total_classrooms,
        "total_laboratories": total_laboratories,
        "total_seminar_halls": total_seminar_halls,
        "total_available_now": available_count,
        "total_occupied_now": occupied_count,
        "total_active_bookings": total_active_bookings,
        "upcoming_examinations": upcoming_examinations,
        "pending_booking_requests": pending_booking_requests,
        "pending_student_reports": pending_student_reports,
        "overall_room_utilization_pct": utilization_pct,
        "peak_booking_hours": peak_hours_list,
        "building_wise_utilization": building_util
    }

