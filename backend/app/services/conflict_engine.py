from datetime import date, time, datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.app.models import (
    Room, Booking, Schedule, RoomClosure, TimetableSlot, Branch, Faculty, User, Section
)

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
        if duration_mins > 480:  # 8 hours
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
        expected_students: Optional[int] = None,
        purpose: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Comprehensive conflict check for a room on a given date and time range.
        Checks:
        1. Room existence, active status, and bookability
        2. Maintenance status
        3. Blueprint discrepancy / Verification status
        4. Room Closures (admin maintenance windows)
        5. Capacity match (nominal vs spaced examination capacity)
        6. Overlapping active bookings (half-open interval: start < existing_end AND end > existing_start)
        7. Overlapping academic timetable schedules / slots for that day of week
        """
        # 1. Fetch Room
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return False, f"Room with ID {room_id} does not exist.", None
            
        if not room.is_active:
            return False, f"Room {room.room_number} is currently marked inactive.", None

        if hasattr(room, "is_bookable") and not room.is_bookable:
            reason = getattr(room, "unconfirmed_reason", None) or "designated administrative or utility space"
            return False, f"Room {room.room_number} is non-bookable ({reason}).", None

        # 2. Maintenance Status
        if room.is_maintenance:
            return False, f"Room {room.room_number} is unavailable due to scheduled maintenance.", None

        # 3. Discrepancy & Verification Check
        if room.verification_status == "PENDING_ADMIN_VERIFICATION":
            return False, (
                f"Room {room.room_number} is pending administrative verification "
                f"(blueprint discrepancy ledger item) and cannot be booked directly without admin clearance."
            ), None
        elif room.verification_status == "RESTRICTED":
            return False, f"Room {room.room_number} has restricted access and requires administrative authorization.", None

        # 4. Check Room Closures
        target_start_dt = datetime.combine(booking_date, start_time)
        target_end_dt = datetime.combine(booking_date, end_time)
        active_closure = db.query(RoomClosure).filter(
            RoomClosure.room_id == room_id,
            RoomClosure.is_active == True,
            RoomClosure.start_time < target_end_dt,
            RoomClosure.end_time > target_start_dt
        ).first()

        if active_closure:
            conflict_info = {
                "type": "ROOM_CLOSURE",
                "title": active_closure.title,
                "reason": active_closure.reason,
                "start": active_closure.start_time.isoformat(),
                "end": active_closure.end_time.isoformat()
            }
            return False, (
                f"Room closure in effect: Room {room.room_number} is temporarily closed "
                f"for '{active_closure.title}' ({active_closure.reason})."
            ), conflict_info

        # 5. Capacity Check (Spaced exam capacity vs nominal capacity)
        is_exam_mode = purpose in ["MINOR_EXAM", "MAJOR_EXAM", "EXAM", "PRACTICAL_EXAM"]
        if is_exam_mode:
            exam_cap = getattr(room, "exam_capacity", int(room.capacity * 0.5))
            if expected_students is not None and expected_students > exam_cap:
                conflict_info = {
                    "type": "EXAM_SPACING_CAPACITY_EXCEEDED",
                    "room_capacity": room.capacity,
                    "exam_capacity": exam_cap,
                    "requested": expected_students,
                    "split_needed": True
                }
                return False, (
                    f"Spaced examination capacity exceeded: Room {room.room_number} seats up to {exam_cap} "
                    f"candidates with mandatory examination spacing (50% ratio), but {expected_students} were requested. "
                    f"A split sitting across two rooms is required."
                ), conflict_info
        else:
            if expected_students is not None and expected_students > room.capacity:
                return False, (
                    f"Room capacity exceeded: Room {room.room_number} accommodates up to {room.capacity} students, "
                    f"but {expected_students} were requested."
                ), None

        # 6. Overlapping Bookings Check using exact half-open interval formula:
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

        # 7. Overlapping Regular Academic Timetable Schedule Check
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

        # 8. Check TimetableSlot table if populated
        overlapping_slot = db.query(TimetableSlot).filter(
            TimetableSlot.room_id == room_id,
            TimetableSlot.day_of_week == day_of_week,
            TimetableSlot.is_active == True,
            TimetableSlot.start_time < end_time,
            TimetableSlot.end_time > start_time
        ).first()

        if overlapping_slot:
            conflict_info = {
                "type": "TIMETABLE_SLOT_CONFLICT",
                "subject_code": overlapping_slot.subject_code,
                "subject_name": overlapping_slot.subject_name,
                "start_time": overlapping_slot.start_time.strftime("%H:%M"),
                "end_time": overlapping_slot.end_time.strftime("%H:%M")
            }
            return False, (
                f"Timetable slot conflict: Room {room.room_number} is reserved for "
                f"{overlapping_slot.subject_code} ({overlapping_slot.subject_name}) from "
                f"{overlapping_slot.start_time.strftime('%I:%M %p')} to "
                f"{overlapping_slot.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        return True, None, None

    @staticmethod
    def check_section_availability(
        db: Session,
        branch_id: Optional[int],
        academic_year: Optional[int],
        section_name: Optional[str],
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Prevent Resource Collision Dimension 2: The same academic section double-booking.
        Students of a specific branch, year, and section cannot be in two classrooms at the same time.
        """
        if not branch_id or not academic_year or not section_name:
            return True, None, None

        active_statuses = ["CONFIRMED", "PENDING_APPROVAL", "APPROVED"]
        
        # Check existing section bookings
        query = db.query(Booking).filter(
            Booking.branch_id == branch_id,
            Booking.academic_year == academic_year,
            Booking.section == section_name,
            Booking.date == booking_date,
            Booking.status.in_(active_statuses),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        overlapping = query.first()
        if overlapping:
            conflict_room = overlapping.room.room_number if overlapping.room else f"Room #{overlapping.room_id}"
            branch = db.query(Branch).filter(Branch.id == branch_id).first()
            b_code = branch.code if branch else "Department"
            conflict_info = {
                "type": "SECTION_BOOKING_COLLISION",
                "section": f"{b_code}-{academic_year}{section_name}",
                "existing_title": overlapping.title,
                "room": conflict_room,
                "start": overlapping.start_time.strftime("%H:%M"),
                "end": overlapping.end_time.strftime("%H:%M")
            }
            return False, (
                f"Academic section collision: Students of {b_code} Year {academic_year} Section {section_name} "
                f"already have a scheduled event '{overlapping.title}' in {conflict_room} from "
                f"{overlapping.start_time.strftime('%I:%M %p')} to {overlapping.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        # Check regular academic timetable schedule
        day_of_week = booking_date.weekday()
        sched = db.query(Schedule).filter(
            Schedule.branch_id == branch_id,
            Schedule.academic_year == academic_year,
            Schedule.section == section_name,
            Schedule.day_of_week == day_of_week,
            Schedule.is_active == True,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time
        ).first()

        if sched:
            conflict_room = sched.room.room_number if sched.room else f"Room #{sched.room_id}"
            branch = db.query(Branch).filter(Branch.id == branch_id).first()
            b_code = branch.code if branch else "Department"
            conflict_info = {
                "type": "SECTION_TIMETABLE_COLLISION",
                "section": f"{b_code}-{academic_year}{section_name}",
                "subject": f"{sched.subject_code} - {sched.subject_name}",
                "room": conflict_room,
                "start": sched.start_time.strftime("%H:%M"),
                "end": sched.end_time.strftime("%H:%M")
            }
            return False, (
                f"Academic section timetable collision: {b_code} Year {academic_year} Section {section_name} "
                f"has scheduled lecture '{sched.subject_name}' in {conflict_room} from "
                f"{sched.start_time.strftime('%I:%M %p')} to {sched.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        return True, None, None

    @staticmethod
    def check_faculty_availability(
        db: Session,
        faculty_id: Optional[int],
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Prevent Resource Collision Dimension 3: The same faculty member double-booking.
        A professor cannot be in two classrooms or sessions at the same time.
        """
        if not faculty_id:
            return True, None, None

        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not faculty:
            return True, None, None

        prof_name = faculty.user.full_name if faculty.user else faculty.employee_code
        active_statuses = ["CONFIRMED", "PENDING_APPROVAL", "APPROVED"]

        # Check faculty bookings
        query = db.query(Booking).filter(
            or_(
                Booking.faculty_id == faculty_id,
                Booking.user_id == faculty.user_id
            ),
            Booking.date == booking_date,
            Booking.status.in_(active_statuses),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        overlapping = query.first()
        if overlapping:
            conflict_room = overlapping.room.room_number if overlapping.room else f"Room #{overlapping.room_id}"
            conflict_info = {
                "type": "FACULTY_BOOKING_COLLISION",
                "faculty_name": prof_name,
                "existing_title": overlapping.title,
                "room": conflict_room,
                "start": overlapping.start_time.strftime("%H:%M"),
                "end": overlapping.end_time.strftime("%H:%M")
            }
            return False, (
                f"Faculty collision: Professor {prof_name} already has a confirmed session "
                f"'{overlapping.title}' in {conflict_room} from "
                f"{overlapping.start_time.strftime('%I:%M %p')} to {overlapping.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        # Check regular academic schedule taught by this faculty
        day_of_week = booking_date.weekday()
        sched = db.query(Schedule).filter(
            Schedule.faculty_id == faculty_id,
            Schedule.day_of_week == day_of_week,
            Schedule.is_active == True,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time
        ).first()

        if sched:
            conflict_room = sched.room.room_number if sched.room else f"Room #{sched.room_id}"
            conflict_info = {
                "type": "FACULTY_TIMETABLE_COLLISION",
                "faculty_name": prof_name,
                "subject": f"{sched.subject_code} - {sched.subject_name}",
                "room": conflict_room,
                "start": sched.start_time.strftime("%H:%M"),
                "end": sched.end_time.strftime("%H:%M")
            }
            return False, (
                f"Faculty timetable collision: Professor {prof_name} is scheduled to teach "
                f"'{sched.subject_name}' in {conflict_room} from "
                f"{sched.start_time.strftime('%I:%M %p')} to {sched.end_time.strftime('%I:%M %p')}."
            ), conflict_info

        return True, None, None

    @staticmethod
    def check_travel_buffer(
        db: Session,
        target_room_id: int,
        booking_date: date,
        start_time: time,
        end_time: time,
        branch_id: Optional[int] = None,
        academic_year: Optional[int] = None,
        section_name: Optional[str] = None,
        faculty_id: Optional[int] = None,
        buffer_minutes: int = 10
    ) -> Tuple[bool, Optional[str]]:
        """
        Campus Intelligence: Verify 100m inter-building walking buffer between IET and Deeksha Bhawan.
        Classes scheduled within buffer_minutes of each other in different buildings are flagged.
        """
        target_room = db.query(Room).filter(Room.id == target_room_id).first()
        if not target_room or not target_room.building:
            return True, None

        target_building_code = target_room.building.code

        # Helper to test gap against prior or subsequent bookings
        target_start_dt = datetime.combine(booking_date, start_time)
        target_end_dt = datetime.combine(booking_date, end_time)

        # Check section's adjacent bookings on same date
        if branch_id and academic_year and section_name:
            adjacent_bookings = db.query(Booking).filter(
                Booking.branch_id == branch_id,
                Booking.academic_year == academic_year,
                Booking.section == section_name,
                Booking.date == booking_date,
                Booking.status.in_(["CONFIRMED", "APPROVED"])
            ).all()

            for adj in adjacent_bookings:
                adj_room = adj.room
                if not adj_room or not adj_room.building:
                    continue
                if adj_room.building.code != target_building_code:
                    adj_start_dt = datetime.combine(booking_date, adj.start_time)
                    adj_end_dt = datetime.combine(booking_date, adj.end_time)
                    
                    # Gap between adjacent end and target start
                    if timedelta(0) <= (target_start_dt - adj_end_dt) < timedelta(minutes=buffer_minutes):
                        return False, (
                            f"Campus walking buffer violation: Section has preceding class in {adj_room.building.code} ({adj_room.room_number}) "
                            f"ending at {adj.end_time.strftime('%I:%M %p')}. The 100m transit to {target_building_code} ({target_room.room_number}) "
                            f"requires at least {buffer_minutes} minutes buffer."
                        )
                    # Gap between target end and adjacent start
                    if timedelta(0) <= (adj_start_dt - target_end_dt) < timedelta(minutes=buffer_minutes):
                        return False, (
                            f"Campus walking buffer violation: Section has subsequent class in {adj_room.building.code} ({adj_room.room_number}) "
                            f"starting at {adj.start_time.strftime('%I:%M %p')}. Transit requires at least {buffer_minutes} minutes buffer."
                        )

        return True, None

    @staticmethod
    def recommend_split_sitting(
        db: Session,
        booking_date: date,
        start_time: time,
        end_time: time,
        total_students: int = 75
    ) -> List[Dict[str, Any]]:
        """
        Examination split sitting engine based on Table 18 & 19 of Corrected Design:
        A 75-strong student section requires 75 exam seats. With 0.5 spacing factor:
        - Only IET32 (100 exam seats) and LIB (90 exam seats) can seat the section single-handed.
        - Deeksha Bhawan pairs of long rooms (LH01 + LH02: 40 + 40 = 80 seats, LH08 + LH09: 40 + 40 = 80 seats)
          comfortably seat the section without room shortage.
        - Two standard 37-seat classrooms (37 + 37 = 74) fall 1 student short, requiring a 3rd room or long rooms.
        """
        candidates = []

        # Option A: Single room that clears full section with exam spacing (IET32 or LIB)
        large_rooms = db.query(Room).filter(
            Room.is_active == True,
            Room.is_bookable == True,
            Room.exam_capacity >= total_students
        ).all()

        for lr in large_rooms:
            avail, _, _ = ConflictEngine.check_room_availability(
                db=db, room_id=lr.id, booking_date=booking_date,
                start_time=start_time, end_time=end_time,
                expected_students=total_students, purpose="MINOR_EXAM"
            )
            if avail:
                candidates.append({
                    "strategy": "SINGLE_LARGE_ROOM",
                    "title": f"Single Room Seating: {lr.room_number}",
                    "description": f"{lr.room_name} seats up to {lr.exam_capacity} spaced candidates (exceeds {total_students} required).",
                    "requires_approval": lr.room_number in ["LIB", "IET32"],
                    "rooms": [
                        {"room_id": lr.id, "room_number": lr.room_number, "allocated_seats": total_students, "exam_capacity": lr.exam_capacity}
                    ],
                    "total_capacity": lr.exam_capacity
                })

        # Option B: Deeksha Bhawan Long Room Pairs (LH01+LH02 or LH08+LH09)
        db_pairs = [("LH01", "LH02"), ("LH08", "LH09")]
        for r1_code, r2_code in db_pairs:
            r1 = db.query(Room).filter(Room.room_number == r1_code).first()
            r2 = db.query(Room).filter(Room.room_number == r2_code).first()
            if r1 and r2 and r1.is_bookable and r2.is_bookable:
                avail1, _, _ = ConflictEngine.check_room_availability(
                    db=db, room_id=r1.id, booking_date=booking_date,
                    start_time=start_time, end_time=end_time,
                    expected_students=40, purpose="MINOR_EXAM"
                )
                avail2, _, _ = ConflictEngine.check_room_availability(
                    db=db, room_id=r2.id, booking_date=booking_date,
                    start_time=start_time, end_time=end_time,
                    expected_students=35, purpose="MINOR_EXAM"
                )
                if avail1 and avail2:
                    candidates.append({
                        "strategy": "SPLIT_LONG_ROOMS",
                        "title": f"Split Across Deeksha Bhawan Long Halls: {r1_code} + {r2_code}",
                        "description": f"Adjacent long lecture halls seat 40 + 40 = 80 spaced candidates, perfectly fitting section of {total_students}.",
                        "requires_approval": False,
                        "rooms": [
                            {"room_id": r1.id, "room_number": r1_code, "allocated_seats": 40, "exam_capacity": r1.exam_capacity},
                            {"room_id": r2.id, "room_number": r2_code, "allocated_seats": 35, "exam_capacity": r2.exam_capacity}
                        ],
                        "total_capacity": 80
                    })

        # Option C: Adjacent IET Classrooms (e.g. IET18 + IET19, each seats 37 -> total 74, with 1 auxiliary in IET20)
        iet_classrooms = db.query(Room).filter(
            Room.building.has(code="IET"),
            Room.room_type == "LECTURE_HALL",
            Room.is_active == True,
            Room.is_bookable == True,
            Room.exam_capacity == 37
        ).all()

        avail_iet = []
        for cr in iet_classrooms:
            ok, _, _ = ConflictEngine.check_room_availability(
                db=db, room_id=cr.id, booking_date=booking_date,
                start_time=start_time, end_time=end_time,
                expected_students=37, purpose="MINOR_EXAM"
            )
            if ok:
                avail_iet.append(cr)

        if len(avail_iet) >= 2:
            r1, r2 = avail_iet[0], avail_iet[1]
            candidates.append({
                "strategy": "SPLIT_IET_CLASSROOMS",
                "title": f"Split Across IET Floor Classrooms: {r1.room_number} + {r2.room_number}",
                "description": f"Classrooms seat {r1.exam_capacity} + {r2.exam_capacity} = 74 candidates on same floor.",
                "requires_approval": False,
                "rooms": [
                    {"room_id": r1.id, "room_number": r1.room_number, "allocated_seats": 37, "exam_capacity": r1.exam_capacity},
                    {"room_id": r2.id, "room_number": r2.room_number, "allocated_seats": 38, "exam_capacity": r2.exam_capacity}
                ],
                "total_capacity": 74
            })

        return candidates

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
        if getattr(room, "is_bookable", True) is False:
            return "RESTRICTED", {"reason": getattr(room, "unconfirmed_reason", "Administrative office space")}
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
            status_label = "PENDING_APPROVAL" if active_booking.status == "PENDING_APPROVAL" else "BOOKED"
            return status_label, {
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
