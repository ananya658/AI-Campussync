from datetime import date, time, datetime
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.app.models import Room, Booking, Schedule

class ConflictEngine:
    @staticmethod
    def validate_time_range(start_time: time, end_time: time) -> Tuple[bool, Optional[str]]:
        """Validate start time is before end time and duration is reasonable."""
        if start_time >= end_time:
            return False, "Start time must be strictly before end time."
        
        # Calculate duration in minutes
        start_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        duration_mins = (end_dt - start_dt).total_seconds() / 60
        
        if duration_mins < 15:
            return False, "Booking duration must be at least 15 minutes."
        if duration_mins > 480: # 8 hours
            return False, "Booking duration cannot exceed 8 hours in a single slot."
            
        return True, None

    @staticmethod
    def check_room_availability(
        db: Session,
        room_id: int,
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: Optional[int] = None,
        expected_students: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Comprehensive conflict check for a room on a given date and time range.
        Checks:
        1. Room existence and active status
        2. Maintenance status
        3. Verification status (e.g. Deeksha Bhawan LH13/LH14)
        4. Capacity match
        5. Overlapping active bookings (existing_start < new_end AND existing_end > new_start)
        6. Overlapping academic timetable schedules for that day of week
        """
        # 1. Fetch Room
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return False, f"Room with ID {room_id} does not exist.", None
            
        if not room.is_active:
            return False, f"Room {room.room_number} is currently marked inactive.", None

        # 2. Maintenance Status
        if room.is_maintenance:
            return False, f"Room {room.room_number} is unavailable due to scheduled maintenance.", None

        # 3. Discrepancy & Verification Check
        if room.verification_status == "PENDING_ADMIN_VERIFICATION":
            return False, f"Room {room.room_number} is pending administrative verification (blueprint discrepancy flag) and cannot be booked directly.", None
        elif room.verification_status == "RESTRICTED":
            return False, f"Room {room.room_number} has restricted access and requires administrative authorization.", None

        # 4. Capacity Check
        if expected_students is not None and expected_students > room.capacity:
            return False, (
                f"Room capacity exceeded: Room {room.room_number} accommodates up to {room.capacity} students, "
                f"but {expected_students} were requested."
            ), None

        # 5. Overlapping Bookings Check using exact formula:
        # existing_start < new_end AND existing_end > new_start
        active_statuses = ["CONFIRMED", "PENDING_APPROVAL", "APPROVED"]
        query = db.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.date == booking_date,
            Booking.status.in_(active_statuses),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        overlapping_booking = query.first()
        if overlapping_booking:
            conflict_info = {
                "type": "BOOKING_CONFLICT",
                "booking_reference": overlapping_booking.booking_reference,
                "title": overlapping_booking.title,
                "purpose": overlapping_booking.purpose,
                "start_time": overlapping_booking.start_time.strftime("%H:%M"),
                "end_time": overlapping_booking.end_time.strftime("%H:%M"),
                "status": overlapping_booking.status
            }
            return False, (
                f"Time slot conflict: Room {room.room_number} is already booked from "
                f"{overlapping_booking.start_time.strftime('%I:%M %p')} to "
                f"{overlapping_booking.end_time.strftime('%I:%M %p')} ({overlapping_booking.title})."
            ), conflict_info

        # 6. Overlapping Regular Academic Timetable Schedule Check
        day_of_week = booking_date.weekday()  # 0=Monday, ..., 6=Sunday
        overlapping_schedule = db.query(Schedule).filter(
            Schedule.room_id == room_id,
            Schedule.day_of_week == day_of_week,
            Schedule.is_active == True,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time
        ).first()

        if overlapping_schedule:
            conflict_info = {
                "type": "ACADEMIC_SCHEDULE_CONFLICT",
                "subject_code": overlapping_schedule.subject_code,
                "subject_name": overlapping_schedule.subject_name,
                "start_time": overlapping_schedule.start_time.strftime("%H:%M"),
                "end_time": overlapping_schedule.end_time.strftime("%H:%M")
            }
            return False, (
                f"Academic timetable conflict: Room {room.room_number} has regular scheduled lecture/lab: "
                f"{overlapping_schedule.subject_code} - {overlapping_schedule.subject_name} from "
                f"{overlapping_schedule.start_time.strftime('%I:%M %p')} to "
                f"{overlapping_schedule.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        return True, None, None

    @staticmethod
    def get_room_current_status(
        db: Session,
        room: Room,
        target_date: Optional[date] = None,
        target_time: Optional[time] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Determine a room's status at a specific date and time."""
        if not room.is_active:
            return "MAINTENANCE", {"reason": "Inactive room"}
        if room.is_maintenance:
            return "MAINTENANCE", {"reason": "Under active maintenance"}
        if room.verification_status == "PENDING_ADMIN_VERIFICATION":
            return "MAINTENANCE", {"reason": "Pending admin blueprint verification"}

        if target_date is None:
            target_date = date.today()
        if target_time is None:
            target_time = datetime.now().time()

        # Check booking at that exact time
        active_booking = db.query(Booking).filter(
            Booking.room_id == room.id,
            Booking.date == target_date,
            Booking.status.in_(["CONFIRMED", "PENDING_APPROVAL", "APPROVED"]),
            Booking.start_time <= target_time,
            Booking.end_time > target_time
        ).first()

        if active_booking:
            if active_booking.status == "PENDING_APPROVAL":
                return "PENDING_APPROVAL", {
                    "booking_ref": active_booking.booking_reference,
                    "title": active_booking.title,
                    "purpose": active_booking.purpose,
                    "start": active_booking.start_time.strftime("%H:%M"),
                    "end": active_booking.end_time.strftime("%H:%M")
                }
            return "BOOKED", {
                "booking_ref": active_booking.booking_reference,
                "title": active_booking.title,
                "purpose": active_booking.purpose,
                "start": active_booking.start_time.strftime("%H:%M"),
                "end": active_booking.end_time.strftime("%H:%M")
            }

        # Check regular schedule
        dow = target_date.weekday()
        sched = db.query(Schedule).filter(
            Schedule.room_id == room.id,
            Schedule.day_of_week == dow,
            Schedule.is_active == True,
            Schedule.start_time <= target_time,
            Schedule.end_time > target_time
        ).first()

        if sched:
            return "BOOKED", {
                "title": f"{sched.subject_code} - {sched.subject_name}",
                "purpose": sched.schedule_type,
                "start": sched.start_time.strftime("%H:%M"),
                "end": sched.end_time.strftime("%H:%M")
            }

        return "AVAILABLE", None
