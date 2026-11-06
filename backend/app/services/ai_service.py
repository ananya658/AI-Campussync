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
        q = query.lower()
        now = datetime.now()
        target_date = date.today()
        
        # 1. Date extraction
        if "tomorrow" in q:
            target_date = date.today() + timedelta(days=1)
        elif "day after tomorrow" in q:
            target_date = date.today() + timedelta(days=2)
        elif "today" in q:
            target_date = date.today()
        else:
            # Check for weekday names
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, d in enumerate(days):
                if d in q:
                    today_idx = date.today().weekday()
                    diff = (i - today_idx) % 7
                    if diff == 0:
                        diff = 7  # Next week's day
                    target_date = date.today() + timedelta(days=diff)
                    break

        # 2. Time extraction
        # e.g., "between 11 AM and 12 PM", "11:00 to 12:00", "2 pm to 4 pm", "at 10 am"
        start_t = time(10, 0)
        end_t = time(11, 0)
        
        # Match "between X AM and Y PM" or "from X to Y"
        time_range_match = re.search(
            r'(?:between|from)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:to|and|-)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
            q
        )
        if time_range_match:
            shour = int(time_range_match.group(1))
            smin = int(time_range_match.group(2) or 0)
            s_meridiem = time_range_match.group(3)
            ehour = int(time_range_match.group(4))
            emin = int(time_range_match.group(5) or 0)
            e_meridiem = time_range_match.group(6)
            
            # If start meridiem is missing, infer from end
            if not s_meridiem:
                s_meridiem = e_meridiem
                
            if s_meridiem == "pm" and shour < 12:
                shour += 12
            elif s_meridiem == "am" and shour == 12:
                shour = 0
                
            if e_meridiem == "pm" and ehour < 12:
                ehour += 12
            elif e_meridiem == "am" and ehour == 12:
                ehour = 0

            start_t = time(shour, smin)
            end_t = time(ehour, emin)
        else:
            # Look for single hour e.g. "at 11 am", "for 2 pm"
            single_time = re.search(r'(?:at|from|around)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)', q)
            if single_time:
                shour = int(single_time.group(1))
                smin = int(single_time.group(2) or 0)
                s_mer = single_time.group(3)
                if s_mer == "pm" and shour < 12:
                    shour += 12
                start_t = time(shour, smin)
                end_t = time(min(shour + 1, 23), smin)

        # 3. Capacity extraction
        # e.g., "for 70 students", "capacity of 150", "75 seats", "100 people"
        capacity = None
        cap_match = re.search(r'(?:for\s*)?(\d{2,3})\s*(?:students|people|seats|capacity)', q)
        if cap_match:
            capacity = int(cap_match.group(1))
        else:
            # Fallback search for bare 2-3 digit number (not part of time)
            nums = re.findall(r'\b(?!1[0-2]\b)(\d{2,3})\b', q)
            if nums:
                capacity = int(nums[0])

        # 4. Building preference
        building_code = None
        if "iet" in q or "engineering" in q:
            building_code = "IET"
        elif "deeksha" in q or "bhawan" in q or "lh" in q:
            building_code = "DB"

        # 5. Room Type
        room_type = None
        if "lab" in q or "laboratory" in q or "practical" in q:
            room_type = "LAB"
        elif "seminar" in q or "auditorium" in q or "hall" in q:
            room_type = "SEMINAR_HALL"
        elif "library" in q:
            room_type = "LIBRARY"
        elif "classroom" in q or "lecture" in q or "theory" in q:
            room_type = "LECTURE_HALL"

        # 6. Facilities
        facility_needed = None
        if "projector" in q:
            facility_needed = "PROJECTOR"
        elif "smart board" in q or "smartboard" in q:
            facility_needed = "SMART_BOARD"
        elif "computer" in q or "pc" in q:
            facility_needed = "LAB_COMPUTERS"
        elif "ac" in q or "air conditioning" in q:
            facility_needed = "AC"
        elif "audio" in q or "mic" in q or "sound" in q:
            facility_needed = "AUDIO_SYSTEM"

        # 7. Purpose
        purpose = "EXTRA_LECTURE"
        if "exam" in q or "minor" in q or "test" in q:
            purpose = "MINOR_EXAM"
        elif "practical" in q or "lab" in q:
            purpose = "PRACTICAL_SESSION"
        elif "seminar" in q or "workshop" in q or "event" in q:
            purpose = "SEMINAR"

        return {
            "target_date": target_date,
            "start_time": start_t,
            "end_time": end_t,
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
        target_date: date = parsed["target_date"]
        start_time: time = parsed["start_time"]
        end_time: time = parsed["end_time"]
        req_capacity: int = parsed["required_capacity"]
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
                expected_students=req_capacity
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
            cap_diff = r.capacity - req_capacity  # >= 0
            if r.capacity > 0:
                # Capacity efficiency: 100% when exact match, slightly decays with excess capacity
                cap_score = max(0.0, 100.0 - (cap_diff / r.capacity) * 40.0)
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
                f"Accommodates {r.capacity} students (perfect fit for your {req_capacity} expected count, with {r.capacity - req_capacity} buffer seats).",
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
                "capacity_difference": cap_diff
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
                        expected_students=req_capacity
                    )
                    if avail:
                        alt_time_slots.append({
                            "room_number": r.room_number,
                            "building_name": r.building.name,
                            "date": str(target_date),
                            "start_time": c_start.strftime("%H:%M"),
                            "end_time": c_end.strftime("%H:%M"),
                            "capacity": r.capacity,
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
