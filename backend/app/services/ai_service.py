import re
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models import Room, Building, Floor, RoomFacility
from backend.app.services.conflict_engine import ConflictEngine
from backend.app.config import settings

class AIService:
    @staticmethod
    def parse_natural_language_query(query: str) -> Dict[str, Any]:
        """
        Parses user intent, extracting:
        - target_date (today, tomorrow, or specific day/date)
        - start_time & end_time
        - required_capacity
        - building_code (IET or DB)
        - room_type (LECTURE_HALL, LAB, SEMINAR_HALL, etc.)
        - facility_needed (PROJECTOR, AC, LAB_COMPUTERS, etc.)
        - purpose (EXTRA_LECTURE, PRACTICAL_SESSION, SEMINAR, MINOR_EXAM)
        """
        q = query.lower().strip()
        today = date.today()
        target_date = today
        date_error = None
        
        # 1. Date extraction
        if "day after tomorrow" in q:
            target_date = today + timedelta(days=2)
        elif "tomorrow" in q:
            target_date = today + timedelta(days=1)
        elif "today" in q:
            target_date = today
        else:
            explicit_date = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", q)
            if explicit_date:
                try:
                    target_date = date.fromisoformat(explicit_date.group(1))
                except ValueError:
                    date_error = "Enter a valid date in YYYY-MM-DD format."
            # Check for weekday names
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, d in enumerate(days):
                if d in q and not explicit_date:
                    diff = (i - today.weekday()) % 7
                    if diff == 0 or re.search(rf"\bnext\s+{d}\b", q):
                        diff += 7
                    target_date = today + timedelta(days=diff)
                    break

        # 2. Time extraction
        # e.g., "between 11 AM and 12 PM", "11:00 to 12:00", "2 pm to 4 pm", "at 10 am"
        duration_match = re.search(
            r"\b(?:for|lasting)\s+(\d+(?:\.\d+)?)\s*(hours?|hrs?|minutes?|mins?)\b",
            q,
        )
        duration_minutes = 60
        if duration_match:
            amount = float(duration_match.group(1))
            unit = duration_match.group(2)
            duration_minutes = round(amount * (60 if unit.startswith(("h", "hr")) else 1))

        time_error = None
        start_minutes = 10 * 60
        end_minutes = start_minutes + duration_minutes

        def to_minutes(hour_text: str, minute_text: Optional[str], meridiem: Optional[str]) -> Optional[int]:
            hour = int(hour_text)
            minute = int(minute_text or 0)
            if minute > 59:
                return None
            if meridiem:
                if not 1 <= hour <= 12:
                    return None
                hour = hour % 12 + (12 if meridiem == "pm" else 0)
            elif hour > 23:
                return None
            return hour * 60 + minute

        time_range_match = re.search(
            r"\b(?:between|from)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:to|until|and|-)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
            q,
        )
        if time_range_match:
            shour, smin, s_meridiem, ehour, emin, e_meridiem = time_range_match.groups()
            if s_meridiem is None:
                s_meridiem = e_meridiem
            if e_meridiem is None:
                e_meridiem = s_meridiem
            start_minutes = to_minutes(shour, smin, s_meridiem)
            end_minutes = to_minutes(ehour, emin, e_meridiem)

            # Resolve common omitted-meridiem phrases such as "11 AM to 1" and "9 to 5 PM".
            if (
                start_minutes is not None
                and end_minutes is not None
                and end_minutes <= start_minutes
            ):
                if time_range_match.group(6) is None and time_range_match.group(3) is not None:
                    end_meridiem = "pm" if time_range_match.group(3) == "am" else "am"
                    end_minutes = to_minutes(ehour, emin, end_meridiem)
                elif time_range_match.group(3) is None and time_range_match.group(6) is not None:
                    start_meridiem = "am" if time_range_match.group(6) == "pm" else "pm"
                    start_minutes = to_minutes(shour, smin, start_meridiem)
            if (
                start_minutes is None
                or end_minutes is None
                or end_minutes <= start_minutes
                or end_minutes - start_minutes > 8 * 60
                or end_minutes - start_minutes < 15
            ):
                time_error = "Enter a valid time range between 15 minutes and 8 hours."
        else:
            single_time = re.search(
                r"\b(?:at|around|from)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
                q,
            )
            if single_time:
                start_minutes = to_minutes(*single_time.groups())
                if start_minutes is None:
                    time_error = "Enter a valid start time."
                else:
                    end_minutes = start_minutes + duration_minutes

        if start_minutes is None or end_minutes is None:
            time_error = "Enter a valid start and end time."
        if duration_minutes < 15 or duration_minutes > 8 * 60:
            time_error = "Requested duration must be between 15 minutes and 8 hours."
        if end_minutes is not None and end_minutes > 23 * 60 + 59:
            time_error = "The requested time slot must end before midnight."

        if time_error:
            start_minutes = 10 * 60
            end_minutes = start_minutes + 60

        start_t = time(start_minutes // 60, start_minutes % 60)
        end_t = time(end_minutes // 60, end_minutes % 60)
        duration_minutes = end_minutes - start_minutes

        # 3. Capacity extraction
        # e.g., "for 70 students", "capacity of 150", "75 seats", "100 people"
        capacity_text = re.sub(
            r"\b(?:for|lasting)\s+\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b",
            " ",
            q,
        )
        capacity_text = re.sub(
            r"\b(?:between|from)?\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:to|until|and|-)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b",
            " ",
            capacity_text,
        )
        capacity_text = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", " ", capacity_text)
        capacity = None
        cap_match = re.search(
            r"\b(?:for\s+|capacity\s+(?:of\s+)?)?(\d{1,4})\s*(?:students?|people|seats|candidates?)\b|\b(?:for|capacity\s+(?:of)?)\s+(\d{1,4})\b",
            capacity_text,
        )
        if cap_match:
            capacity = int(cap_match.group(1) or cap_match.group(2))
            if capacity < 1:
                raise ValueError("Requested capacity must be at least one person.")

        # 4. Building preference
        building_code = None
        if re.search(r"\biet(?:\s*\d+)?\b|\bengineering\b", q):
            building_code = "IET"
        elif re.search(r"\bdeeksha\b|\bbhawan\b|\blh\d+\b", q):
            building_code = "DB"

        # 5. Room Type
        room_type = None
        if re.search(r"\blabs?\b|\blaborator(?:y|ies)\b|\bpracticals?\b", q):
            room_type = "LAB"
        elif re.search(r"\bseminars?\b|\bauditoriums?\b", q):
            room_type = "SEMINAR_HALL"
        elif re.search(r"\blibrary\b|\blibraries\b", q):
            room_type = "LIBRARY"
        elif re.search(r"\bclassrooms?\b|\blectures?\b|\btheory\b", q):
            room_type = "LECTURE_HALL"
        elif re.search(r"\bhalls?\b", q):
            room_type = "SEMINAR_HALL"

        # 6. Facilities
        facility_needed = None
        if "projector" in q:
            facility_needed = "PROJECTOR"
        elif "smart board" in q or "smartboard" in q:
            facility_needed = "SMART_BOARD"
        elif "computer" in q or re.search(r"\bpcs?\b", q):
            facility_needed = "LAB_COMPUTERS"
        elif re.search(r"\bac\b|air conditioning", q):
            facility_needed = "AC"
        elif re.search(r"\baudio\b|\bmics?\b|\bmicrophones?\b|\bsound\b", q):
            facility_needed = "AUDIO_SYSTEM"

        # 7. Purpose
        purpose = "EXTRA_LECTURE"
        if re.search(r"\bmajor\s+(?:exam|examination|test)\b", q):
            purpose = "MAJOR_EXAM"
        elif re.search(r"\bpractical\s+(?:exam|examination|test)\b", q):
            purpose = "PRACTICAL_EXAM"
        elif re.search(r"\b(?:exam|examination|minor|test)\b", q):
            purpose = "MINOR_EXAM"
        elif re.search(r"\bpracticals?\b|\blabs?\b", q):
            purpose = "PRACTICAL_SESSION"
        elif re.search(r"\bworkshops?\b", q):
            purpose = "WORKSHOP"
        elif re.search(r"\bseminars?\b", q):
            purpose = "SEMINAR"
        elif re.search(r"\bevents?\b|\bconferences?\b|\bhackathons?\b", q):
            purpose = "ACADEMIC_EVENT"

        return {
            "target_date": target_date,
            "date_error": date_error,
            "start_time": start_t,
            "end_time": end_t,
            "duration_minutes": duration_minutes,
            "time_error": time_error,
            "required_capacity": capacity or 60,
            "building_code": building_code,
            "room_type": room_type,
            "facility_needed": facility_needed,
            "purpose": purpose,
            "raw_query": query
        }

    @staticmethod
    def search_and_recommend(
        db: Session,
        query: str,
        user_role: str = "FACULTY"
    ) -> Dict[str, Any]:
        """
        Executes verified AI search:
        - Extracts intent
        - Queries real DB rooms
        - Verifies exact availability via ConflictEngine
        - Scores and ranks valid rooms
        - Formulates transparent explanations and alternatives
        """
        parsed = AIService.parse_natural_language_query(query)
        if parsed["date_error"]:
            raise ValueError(parsed["date_error"])
        if parsed["time_error"]:
            raise ValueError(parsed["time_error"])
        if parsed["target_date"] < date.today():
            raise ValueError("Choose today or a future date for a room search.")
        target_date: date = parsed["target_date"]
        start_time: time = parsed["start_time"]
        end_time: time = parsed["end_time"]
        req_capacity: int = parsed["required_capacity"]
        purpose: str = parsed["purpose"]
        is_exam = purpose in {"MINOR_EXAM", "MAJOR_EXAM", "PRACTICAL_EXAM"}
        building_code: Optional[str] = parsed["building_code"]
        room_type: Optional[str] = parsed["room_type"]
        facility_needed: Optional[str] = parsed["facility_needed"]

        # Base DB query
        rooms_query = db.query(Room).filter(Room.is_active == True)
        if building_code:
            rooms_query = rooms_query.join(Building).filter(Building.code == building_code)
        if room_type:
            rooms_query = rooms_query.filter(Room.room_type == room_type)

        all_candidate_rooms = rooms_query.all()
        scored_recommendations = []

        for r in all_candidate_rooms:
            # 1. Mandatory constraint check via ConflictEngine
            is_avail, conflict_reason, _ = ConflictEngine.check_room_availability(
                db=db,
                room_id=r.id,
                booking_date=target_date,
                start_time=start_time,
                end_time=end_time,
                expected_students=req_capacity,
                purpose=purpose,
            )

            # Facility check
            room_facilities = [f.facility_name for f in r.facilities]
            facility_match = True
            if facility_needed and facility_needed not in room_facilities:
                facility_match = False

            # If room fails mandatory constraints
            if not is_avail or not facility_match:
                continue

            # 2. Ranking Algorithm
            # Capacity fitness: Best score if room capacity is just right (avoid wasting a 200-seat hall for 25 students)
            usable_capacity = r.exam_capacity if is_exam else r.capacity
            cap_diff = usable_capacity - req_capacity  # >= 0
            if usable_capacity > 0:
                # Capacity efficiency: 100% when exact match, slightly decays with excess capacity
                cap_score = max(0.0, 100.0 - (cap_diff / usable_capacity) * 40.0)
            else:
                cap_score = 50.0

            # Building suitability
            b_score = 100.0 if (building_code and r.building.code == building_code) else 80.0
            
            # Floor accessibility (Ground & 1st floor have higher convenience for regular classes)
            floor_score = 95.0 if r.floor.floor_number <= 1 else 85.0
            
            # Facility bonus
            facility_score = 100.0 if facility_needed and facility_needed in room_facilities else 90.0

            # Composite weighted match score (0 to 100)
            total_score = round(
                (cap_score * 0.45) +
                (b_score * 0.25) +
                (floor_score * 0.15) +
                (facility_score * 0.15),
                1
            )

            # Explanation generation
            explanation_parts = [
                f"Verified available on {target_date.strftime('%a, %b %d')} between {start_time.strftime('%I:%M %p')} and {end_time.strftime('%I:%M %p')}.",
                f"Accommodates {usable_capacity} {('spaced exam candidates' if is_exam else 'students')} "
                f"(your request is {req_capacity}, with {cap_diff} seats to spare).",
                f"Located in {r.building.name} on the {r.floor.floor_name}."
            ]
            if room_facilities:
                explanation_parts.append(f"Equipped with: {', '.join(room_facilities)}.")
            
            explanation = " ".join(explanation_parts)

            room_dict = {
                "id": r.id,
                "building_id": r.building_id,
                "floor_id": r.floor_id,
                "room_number": r.room_number,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "exam_capacity": r.exam_capacity,
                "is_active": r.is_active,
                "is_maintenance": r.is_maintenance,
                "verification_status": r.verification_status,
                "verification_notes": r.verification_notes,
                "permitted_uses": r.permitted_uses,
                "svg_id": r.svg_id,
                "building_name": r.building.name,
                "building_code": r.building.code,
                "floor_name": r.floor.floor_name,
                "floor_number": r.floor.floor_number,
                "facilities": [
                    {"id": f.id, "facility_name": f.facility_name, "quantity": f.quantity, "condition": f.condition}
                    for f in r.facilities
                ],
                "current_status": "AVAILABLE"
            }

            scored_recommendations.append({
                "room": room_dict,
                "match_score": total_score,
                "is_available": True,
                "explanation": explanation,
                "facilities_matched": room_facilities,
                "capacity_difference": cap_diff,
                "effective_capacity": usable_capacity,
            })

        # Sort recommendations descending by score
        scored_recommendations.sort(key=lambda x: x["match_score"], reverse=True)

        primary_rec = scored_recommendations[0] if scored_recommendations else None
        alt_rooms = scored_recommendations[1:5] if len(scored_recommendations) > 1 else []

        # If no room is available at this time, find alternative time slots
        alt_time_slots = []
        if not primary_rec:
            # Probe alternative time slots on the same date: +1 hour, +2 hours, -1 hour
            offsets = [60, 120, -60]
            base_start_dt = datetime.combine(target_date, start_time)
            base_end_dt = datetime.combine(target_date, end_time)
            
            for offset in offsets:
                cand_start_dt = base_start_dt + timedelta(minutes=offset)
                cand_end_dt = base_end_dt + timedelta(minutes=offset)
                
                # Check within operating hours (08:00 to 18:00)
                if cand_start_dt.hour < 8 or cand_end_dt.hour > 19:
                    continue

                c_start = cand_start_dt.time()
                c_end = cand_end_dt.time()

                for r in all_candidate_rooms:
                    avail, _, _ = ConflictEngine.check_room_availability(
                        db=db,
                        room_id=r.id,
                        booking_date=target_date,
                        start_time=c_start,
                        end_time=c_end,
                        expected_students=req_capacity,
                        purpose=purpose,
                    )
                    has_facility = (
                        not facility_needed
                        or any(f.facility_name == facility_needed for f in r.facilities)
                    )
                    if avail and has_facility:
                        alt_time_slots.append({
                            "room_id": r.id,
                            "building_id": r.building_id,
                            "room_number": r.room_number,
                            "building_name": r.building.name,
                            "date": str(target_date),
                            "start_time": c_start.strftime("%H:%M"),
                            "end_time": c_end.strftime("%H:%M"),
                            "capacity": r.exam_capacity if is_exam else r.capacity,
                            "label": f"{c_start.strftime('%I:%M %p')} - {c_end.strftime('%I:%M %p')}"
                        })
                        if len(alt_time_slots) >= 3:
                            break
                if len(alt_time_slots) >= 3:
                    break

        # Generate summary natural language commentary
        if primary_rec:
            raw_summary = (
                f"I found {len(scored_recommendations)} verified available room(s) matching your criteria. "
                f"Top pick is **{primary_rec['room']['room_number']}** ({primary_rec['room']['building_name']}) "
                f"with a match score of **{primary_rec['match_score']}%**."
            )
        else:
            raw_summary = (
                f"No rooms in the requested category are available on {target_date.strftime('%b %d')} "
                f"between {start_time.strftime('%I:%M %p')} and {end_time.strftime('%I:%M %p')} for {req_capacity} students. "
                "I have calculated alternative time slots that are currently vacant."
            )

        return {
            "interpreted_query": {
                "date": str(target_date),
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "duration_minutes": parsed["duration_minutes"],
                "required_capacity": req_capacity,
                "building": building_code or "Any Building",
                "room_type": room_type or "Any Room Type",
                "facility_needed": facility_needed or "None specified",
                "purpose": parsed["purpose"]
            },
            "primary_recommendation": primary_rec,
            "alternative_rooms": alt_rooms,
            "alternative_time_slots": alt_time_slots,
            "total_matches": len(scored_recommendations),
            "raw_ai_explanation": raw_summary
        }

