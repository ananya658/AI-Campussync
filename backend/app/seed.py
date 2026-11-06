import os
import json
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.database import engine, SessionLocal, Base
from backend.app.models import (
    User, Student, Faculty, Branch, Batch, Building, Floor, Room, RoomFacility,
    Booking, Schedule, TimetableSlot, Section, RoomClosure, SystemSetting,
    Announcement, AnnouncementVersion, Notification, IssueReport, AuditLog
)
from backend.app.auth import hash_password

def seed_database(force_reseed: bool = False):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Check if already seeded
    if not force_reseed and db.query(Building).first() and db.query(Section).first():
        print("Database already contains initialized campus data. Skipping re-seed.")
        db.close()
        return

    if force_reseed:
        print("Force reseed requested: clearing existing data...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    print("Seeding DDUGU CampusSync AI database with complete campus infrastructure...")

    # 1. Seed Branches
    branches_data = [
        {"code": "CSE", "name": "Computer Science & Engineering", "total_capacity": 150, "description": "Sections A and B (75 students each)"},
        {"code": "AIML", "name": "Artificial Intelligence & Machine Learning", "total_capacity": 150, "description": "Sections A and B (75 students each)"},
        {"code": "AIDS", "name": "Artificial Intelligence & Data Science", "total_capacity": 75, "description": "Section A (75 students)"},
        {"code": "ECE", "name": "Electronics & Communication Engineering", "total_capacity": 75, "description": "Section A (75 students)"},
        {"code": "ME", "name": "Mechanical Engineering", "total_capacity": 75, "description": "Section A (75 students)"},
        {"code": "IT", "name": "Information Technology", "total_capacity": 75, "description": "Section A (75 students)"},
    ]
    branch_objs = {}
    for b in branches_data:
        obj = Branch(**b)
        db.add(obj)
        db.flush()
        branch_objs[b["code"]] = obj

    # 2. Seed Batches
    batches_data = [
        {"name": "Batch 2022-2026", "academic_year": "2025-2026", "is_active": True},  # 4th year
        {"name": "Batch 2023-2027", "academic_year": "2025-2026", "is_active": True},  # 3rd year
        {"name": "Batch 2024-2028", "academic_year": "2025-2026", "is_active": True},  # 2nd year
        {"name": "Batch 2025-2029", "academic_year": "2025-2026", "is_active": True},  # 1st year
    ]
    batch_objs = []
    for bat in batches_data:
        obj = Batch(**bat)
        db.add(obj)
        db.flush()
        batch_objs.append(obj)

    # 3. Seed 32 Academic Sections (all 75 strong per Corrected Design Table 6)
    section_configs = []
    for yr in [1, 2, 3, 4]:
        for br_code in ["CSE", "AIML"]:
            section_configs.append((br_code, yr, "A", 75))
            section_configs.append((br_code, yr, "B", 75))
        for br_code in ["AIDS", "ECE", "ME", "IT"]:
            section_configs.append((br_code, yr, "A", 75))

    section_objs = {}
    for br_code, yr, sec_name, strength in section_configs:
        sec_code = f"{br_code}-{yr}{sec_name}"
        sec = Section(
            code=sec_code,
            branch_id=branch_objs[br_code].id,
            academic_year=yr,
            section_name=sec_name,
            student_count=strength
        )
        db.add(sec)
        db.flush()
        section_objs[sec_code] = sec

    # 4. Seed Buildings: IET and Deeksha Bhawan
    iet_building = Building(
        name="Institute of Engineering and Technology (IET)",
        code="IET",
        description="Core engineering building housing laboratories, lecture halls, directorate, and central library.",
        total_floors=3,
        distance_from_iet_meters=0,
        is_active=True
    )
    db.add(iet_building)
    db.flush()

    db_building = Building(
        name="Deeksha Bhawan",
        code="DB",
        description="Central lecture hall complex located approximately 100 metres across campus from IET.",
        total_floors=2,
        distance_from_iet_meters=100,
        is_active=True
    )
    db.add(db_building)
    db.flush()

    # Floors for IET
    iet_f0 = Floor(building_id=iet_building.id, floor_number=0, floor_name="Ground Floor")
    iet_f1 = Floor(building_id=iet_building.id, floor_number=1, floor_name="First Floor")
    iet_f2 = Floor(building_id=iet_building.id, floor_number=2, floor_name="Second Floor")
    db.add_all([iet_f0, iet_f1, iet_f2])
    db.flush()

    # Floors for Deeksha Bhawan
    db_f0 = Floor(building_id=db_building.id, floor_number=0, floor_name="Ground Floor")
    db_f1 = Floor(building_id=db_building.id, floor_number=1, floor_name="First Floor")
    db.add_all([db_f0, db_f1])
    db.flush()

    # 5. Seed Rooms from authoritative campus_room_registry.json (34 rooms, 30 bookable)
    registry_path = os.path.join(os.path.dirname(__file__), "campus_room_registry.json")
    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            registry_data = json.load(f)
    else:
        registry_data = []

    floor_map = {
        ("IET", 0): iet_f0.id,
        ("IET", 1): iet_f1.id,
        ("IET", 2): iet_f2.id,
        ("DB", 0): db_f0.id,
        ("DB", 1): db_f1.id,
    }
    bldg_map = {
        "IET": iet_building.id,
        "DB": db_building.id
    }

    room_objects = {}
    for r in registry_data:
        fl_id = floor_map.get((r["building_code"], r["floor_number"]))
        b_id = bldg_map.get(r["building_code"])
        rm = Room(
            building_id=b_id,
            floor_id=fl_id,
            room_number=r["room_number"],
            room_name=r["room_name"],
            room_type=r["room_type"],
            capacity=r["capacity"],
            exam_capacity=r.get("exam_capacity", int(r["capacity"] * 0.5)),
            is_bookable=r.get("is_bookable", True),
            is_unconfirmed=r.get("is_unconfirmed", False),
            unconfirmed_reason=r.get("unconfirmed_reason"),
            verification_status=r.get("verification_status", "OFFICIAL_VERIFIED"),
            verification_notes=r.get("verification_notes"),
            permitted_uses=r.get("permitted_uses", "Lectures,Examinations"),
            svg_id=r.get("svg_id"),
            is_active=True,
            is_maintenance=(r.get("verification_status") == "PENDING_ADMIN_VERIFICATION")
        )
        db.add(rm)
        db.flush()
        room_objects[r["room_number"]] = rm

    # Compatibility aliases
    room_objects["Library"] = room_objects.get("LIB")
    room_objects["CSE-Lab"] = room_objects.get("IET22")
    room_objects["ME-Lab"] = room_objects.get("IET16")
    room_objects["ECE-Lab"] = room_objects.get("IET14")
    room_objects["IT-Lab"] = room_objects.get("IET15")
    room_objects["Teachers-Office"] = room_objects.get("TO")
    room_objects["Directors-Office"] = room_objects.get("DO")
    room_objects["Placement-Cell"] = room_objects.get("PC")

    # 6. Seed Facilities for Key Rooms
    facilities_data = [
        ("IET22", [("LAB_COMPUTERS", 40), ("PROJECTOR", 1), ("AC", 2), ("HIGH_SPEED_WIFI", 1)]),
        ("IET15", [("LAB_COMPUTERS", 40), ("PROJECTOR", 1), ("AC", 2), ("HIGH_SPEED_WIFI", 1)]),
        ("IET16", [("PROJECTOR", 1), ("LAB_COMPUTERS", 15), ("AC", 1)]),
        ("IET14", [("PROJECTOR", 1), ("LAB_COMPUTERS", 20), ("AC", 1)]),
        ("IET32", [("AUDIO_SYSTEM", 1), ("PROJECTOR", 2), ("AC", 4), ("SMART_BOARD", 1), ("HIGH_SPEED_WIFI", 1)]),
        ("LIB",   [("HIGH_SPEED_WIFI", 1), ("AC", 4), ("SMART_BOARD", 1)]),
        ("IET17", [("PROJECTOR", 1), ("SMART_BOARD", 1), ("AC", 2)]),
        ("IET18", [("PROJECTOR", 1), ("SMART_BOARD", 1), ("AC", 2)]),
        ("IET19", [("PROJECTOR", 1), ("AC", 2)]),
        ("IET20", [("PROJECTOR", 1), ("AC", 2)]),
        ("LH01",  [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH02",  [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH08",  [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH09",  [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
    ]
    for r_num, facs in facilities_data:
        if r_num in room_objects and room_objects[r_num]:
            r_obj = room_objects[r_num]
            for f_name, qty in facs:
                db.add(RoomFacility(room_id=r_obj.id, facility_name=f_name, quantity=qty, condition="EXCELLENT"))

    # 7. Seed Admin, Faculty & Student Profiles
    admin_user = User(
        email="admin@ddugu.ac.in",
        hashed_password=hash_password("Admin@123"),
        full_name="Prof. Arvind Kumar",
        role="ADMIN",
        department="Dean Office & Academic Planning",
        phone="+91 94150 11223",
        is_active=True
    )
    db.add(admin_user)
    db.flush()

    # Faculty 1 (CSE HOD)
    fac1_user = User(
        email="prof.sharma@ddugu.ac.in",
        hashed_password=hash_password("Faculty@123"),
        full_name="Dr. Ramesh Sharma",
        role="FACULTY",
        department="Computer Science & Engineering",
        phone="+91 94150 22334",
        is_active=True
    )
    db.add(fac1_user)
    db.flush()
    fac1_profile = Faculty(
        user_id=fac1_user.id,
        employee_code="FAC-CSE-01",
        designation="Professor & HOD",
        department="Computer Science & Engineering",
        cabin_room_id=room_objects.get("TO", room_objects.get("LIB")).id
    )
    db.add(fac1_profile)

    # Faculty 2 (AI ML)
    fac2_user = User(
        email="dr.verma@ddugu.ac.in",
        hashed_password=hash_password("Faculty@123"),
        full_name="Dr. Sunita Verma",
        role="FACULTY",
        department="Artificial Intelligence & Machine Learning",
        phone="+91 94150 33445",
        is_active=True
    )
    db.add(fac2_user)
    db.flush()
    fac2_profile = Faculty(
        user_id=fac2_user.id,
        employee_code="FAC-AIML-02",
        designation="Associate Professor",
        department="Artificial Intelligence & Machine Learning",
        cabin_room_id=room_objects.get("TO", room_objects.get("LIB")).id
    )
    db.add(fac2_profile)

    # Student 1: Rahul Singh (CSE Year 3 Section A)
    stu1_user = User(
        email="rahul.cse23@ddugu.ac.in",
        hashed_password=hash_password("Student@123"),
        full_name="Rahul Singh",
        role="STUDENT",
        department="Computer Science & Engineering",
        phone="+91 98380 44556",
        is_active=True
    )
    db.add(stu1_user)
    db.flush()
    stu1_profile = Student(
        user_id=stu1_user.id,
        roll_number="23001CSE045",
        branch_id=branch_objs["CSE"].id,
        batch_id=batch_objs[1].id,
        section_id=section_objs["CSE-3A"].id,
        year=3,
        section="A"
    )
    db.add(stu1_profile)

    # Student 2: Priya Maurya (AI ML Year 2 Section B)
    stu2_user = User(
        email="priya.aiml24@ddugu.ac.in",
        hashed_password=hash_password("Student@123"),
        full_name="Priya Maurya",
        role="STUDENT",
        department="Artificial Intelligence & Machine Learning",
        phone="+91 98380 55667",
        is_active=True
    )
    db.add(stu2_user)
    db.flush()
    stu2_profile = Student(
        user_id=stu2_user.id,
        roll_number="24001AIML012",
        branch_id=branch_objs["AIML"].id,
        batch_id=batch_objs[2].id,
        section_id=section_objs["AIML-2B"].id,
        year=2,
        section="B"
    )
    db.add(stu2_profile)
    db.flush()

    # 8. Seed System Settings
    settings_data = [
        {"key": "inter_building_walking_buffer_seconds", "value": "600", "category": "CAMPUS", "description": "100m inter-building walking transition buffer between IET and Deeksha Bhawan (10 minutes)"},
        {"key": "floor_transition_buffer_seconds", "value": "300", "category": "CAMPUS", "description": "Staircase/floor transition buffer between different floors in the same building (5 minutes)"},
        {"key": "exam_seating_ratio", "value": "0.5", "category": "SPACING", "description": "Mandatory candidate spacing ratio during examinations (spaced capacity = nominal * 0.5)"},
        {"key": "default_section_size", "value": "75", "category": "SCHEDULING", "description": "Standard headcount size for campus academic cohorts"},
        {"key": "max_booking_hours", "value": "8", "category": "SCHEDULING", "description": "Maximum contiguous duration allowed for a single room reservation slot"},
        {"key": "library_requires_approval", "value": "true", "category": "POLICY", "description": "Flag requiring administrator review for Central Library reservations"},
        {"key": "seminar_hall_requires_approval", "value": "true", "category": "POLICY", "description": "Flag requiring administrator review for IET32 Seminar Hall reservations exceeding 100 students"}
    ]
    for s_dict in settings_data:
        db.add(SystemSetting(
            key=s_dict["key"],
            value=s_dict["value"],
            category=s_dict["category"],
            description=s_dict["description"],
            updated_at=datetime.utcnow(),
            updated_by_id=admin_user.id
        ))
    db.flush()

    # 9. Seed Room Closure (Maintenance Window Demo)
    if "LH10" in room_objects:
        closure_sample = RoomClosure(
            room_id=room_objects["LH10"].id,
            title="Air Conditioning System Overhaul",
            reason="Scheduled preventive maintenance of HVAC compressor and air duct filters",
            start_time=datetime.utcnow() + timedelta(days=5),
            end_time=datetime.utcnow() + timedelta(days=5, hours=6),
            created_by_id=admin_user.id,
            is_active=True
        )
        db.add(closure_sample)

    # 10. Seed Academic Timetable Schedules & Timetable Slots
    schedules_data = [
        # Monday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 0, "s": time(9, 30), "e": time(10, 30), "period": 1, "code": "CS-301", "name": "Design & Analysis of Algorithms", "type": "LECTURE"},
        {"room": "IET18", "fac": fac2_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 0, "s": time(10, 30), "e": time(11, 30), "period": 2, "code": "CS-302", "name": "Database Management Systems", "type": "LECTURE"},
        {"room": "IET22", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 0, "s": time(14, 0), "e": time(16, 0), "period": 5, "code": "CS-305", "name": "DBMS Practical Laboratory", "type": "LAB"},
        # Tuesday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 1, "s": time(9, 30), "e": time(10, 30), "period": 1, "code": "CS-303", "name": "Computer Networks & Protocols", "type": "LECTURE"},
        {"room": "IET17", "fac": fac2_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 1, "s": time(11, 30), "e": time(12, 30), "period": 3, "code": "CS-304", "name": "Software Engineering & Agile", "type": "LECTURE"},
        # Wednesday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 2, "s": time(10, 30), "e": time(11, 30), "period": 2, "code": "CS-301", "name": "Design & Analysis of Algorithms", "type": "LECTURE"},
        {"room": "IET32", "fac": fac2_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 2, "s": time(15, 0), "e": time(16, 30), "period": 6, "code": "CS-306", "name": "Industry Guest Lecture Series", "type": "LECTURE"},
        # Thursday
        {"room": "IET18", "fac": fac2_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 3, "s": time(9, 30), "e": time(10, 30), "period": 1, "code": "CS-302", "name": "Database Management Systems", "type": "LECTURE"},
        {"room": "IET15", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 3, "s": time(14, 0), "e": time(16, 0), "period": 5, "code": "CS-307", "name": "Network Socket Programming Lab", "type": "LAB"},
        # Friday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 4, "s": time(10, 30), "e": time(11, 30), "period": 2, "code": "CS-303", "name": "Computer Networks & Protocols", "type": "LECTURE"},
        {"room": "IET17", "fac": fac2_profile, "branch": branch_objs["CSE"], "sec_code": "CSE-3A", "yr": 3, "sec": "A", "dow": 4, "s": time(11, 30), "e": time(12, 30), "period": 3, "code": "CS-304", "name": "Software Engineering & Agile", "type": "LECTURE"},
        # Priya (AI ML Year 2 Section B)
        {"room": "IET19", "fac": fac2_profile, "branch": branch_objs["AIML"], "sec_code": "AIML-2B", "yr": 2, "sec": "B", "dow": 0, "s": time(11, 0), "e": time(12, 0), "period": 3, "code": "AI-201", "name": "Discrete Mathematics & Graph Theory", "type": "LECTURE"},
        {"room": "IET19", "fac": fac2_profile, "branch": branch_objs["AIML"], "sec_code": "AIML-2B", "yr": 2, "sec": "B", "dow": 1, "s": time(10, 0), "e": time(11, 0), "period": 2, "code": "AI-202", "name": "Data Structures with Python", "type": "LECTURE"},
        {"room": "IET22", "fac": fac2_profile, "branch": branch_objs["AIML"], "sec_code": "AIML-2B", "yr": 2, "sec": "B", "dow": 2, "s": time(14, 0), "e": time(16, 0), "period": 5, "code": "AI-205", "name": "Python & Data Science Lab", "type": "LAB"},
    ]

    for s_item in schedules_data:
        r_obj = room_objects.get(s_item["room"])
        if not r_obj:
            continue
        db.add(Schedule(
            room_id=r_obj.id,
            faculty_id=s_item["fac"].id,
            branch_id=s_item["branch"].id,
            academic_year=s_item["yr"],
            section=s_item["sec"],
            day_of_week=s_item["dow"],
            start_time=s_item["s"],
            end_time=s_item["e"],
            subject_code=s_item["code"],
            subject_name=s_item["name"],
            schedule_type=s_item["type"],
            is_active=True
        ))
        db.add(TimetableSlot(
            room_id=r_obj.id,
            faculty_id=s_item["fac"].id,
            branch_id=s_item["branch"].id,
            section_id=section_objs.get(s_item["sec_code"]).id if s_item.get("sec_code") in section_objs else None,
            academic_year=s_item["yr"],
            section_name=s_item["sec"],
            day_of_week=s_item["dow"],
            period=s_item["period"],
            start_time=s_item["s"],
            end_time=s_item["e"],
            subject_code=s_item["code"],
            subject_name=s_item["name"],
            slot_type=s_item["type"],
            is_active=True
        ))

    # 11. Seed Sample Bookings
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    sample_bookings = [
        {
            "ref": "CS-TEST-001",
            "room": "IET20",
            "user": fac1_user,
            "title": "[TEST DATA] Extra Lecture: Graph Algorithms Revision",
            "purpose": "EXTRA_LECTURE",
            "date": today,
            "s": time(16, 0),
            "e": time(17, 30),
            "cap": 70,
            "branch": branch_objs["CSE"],
            "yr": 3,
            "sec": "A",
            "sec_code": "CSE-3A",
            "status": "CONFIRMED"
        },
        {
            "ref": "CS-TEST-002",
            "room": "LH01",
            "user": fac2_user,
            "title": "[TEST DATA] Minor Exam I: Mathematics for AI",
            "purpose": "MINOR_EXAM",
            "date": tomorrow,
            "s": time(11, 0),
            "e": time(13, 0),
            "cap": 40,
            "branch": branch_objs["AIML"],
            "yr": 2,
            "sec": "B",
            "sec_code": "AIML-2B",
            "status": "CONFIRMED"
        },
        {
            "ref": "CS-TEST-003",
            "room": "IET32",
            "user": admin_user,
            "title": "[TEST DATA] GDG Hackathon Orientation: DevOps 2026",
            "purpose": "ACADEMIC_EVENT",
            "date": day_after,
            "s": time(10, 0),
            "e": time(13, 0),
            "cap": 180,
            "branch": None,
            "yr": None,
            "sec": None,
            "sec_code": None,
            "status": "CONFIRMED"
        }
    ]

    for sb in sample_bookings:
        r_obj = room_objects.get(sb["room"])
        if not r_obj:
            continue
        db.add(Booking(
            booking_reference=sb["ref"],
            room_id=r_obj.id,
            user_id=sb["user"].id,
            title=sb["title"],
            purpose=sb["purpose"],
            date=sb["date"],
            start_time=sb["s"],
            end_time=sb["e"],
            expected_students=sb["cap"],
            branch_id=sb["branch"].id if sb["branch"] else None,
            academic_year=sb["yr"],
            section_id=section_objs.get(sb["sec_code"]).id if sb.get("sec_code") in section_objs else None,
            section=sb["sec"],
            status=sb["status"],
            is_test_data=True
        ))

    # 12. Seed Announcements & Versioning
    ann1 = Announcement(
        title="B.Tech Odd Semester Minor Examination Schedule 2026",
        description="Official dates and seat allotments for B.Tech CSE, AIML, AIDS, ECE, ME, and IT batches. Candidates must occupy their designated halls 15 minutes before commencement.",
        announcement_type="MINOR_EXAM",
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(13, 0),
        building_id=db_building.id,
        room_id=room_objects["LH01"].id,
        target_branch_id=branch_objs["CSE"].id,
        target_year=3,
        created_by_id=admin_user.id,
        status="PUBLISHED",
        version=1
    )
    db.add(ann1)
    db.flush()
    db.add(AnnouncementVersion(
        announcement_id=ann1.id,
        version=1,
        title=ann1.title,
        description=ann1.description,
        room_id=ann1.room_id,
        date=ann1.date,
        start_time=ann1.start_time,
        end_time=ann1.end_time,
        change_summary="Initial publication of Minor Exam timetable",
        modified_by_id=admin_user.id
    ))

    # 13. Seed Issue Reports
    rep1 = IssueReport(
        student_id=stu1_profile.id,
        reporter_user_id=stu1_user.id,
        category="WRONG_CLASSROOM",
        description="Timetable indicated CS-301 in IET17, but the door notice indicated IET18. Please verify official lecture venue.",
        building_id=iet_building.id,
        room_id=room_objects["IET18"].id,
        scheduled_date=today,
        scheduled_time=time(9, 30),
        status="RESOLVED",
        admin_resolution_note="Classroom allocation verified. Room IET18 is the official venue for CS-301 Section A. Timetable synced.",
        resolved_by_id=admin_user.id,
        resolved_at=datetime.utcnow()
    )
    db.add(rep1)

    # 14. Seed Notifications
    db.add(Notification(
        user_id=stu1_user.id,
        title="Venue Update: Minor Exam in LH01",
        message="Your Odd Semester Minor Examination venue has been confirmed for Deeksha Bhawan LH01.",
        notification_type="EXAM_SCHEDULE_CHANGED",
        link_url="/student/announcements"
    ))

    # 15. Seed Audit Logs
    db.add(AuditLog(
        user_id=admin_user.id,
        user_role="ADMIN",
        user_name=admin_user.full_name,
        action_type="CREATE",
        entity_type="ROOM",
        entity_id="ALL",
        new_value="Seeded 34 campus rooms from campus_room_registry.json (30 bookable)",
        reason="DDUGU Campus Infrastructure Initialization"
    ))

    db.commit()
    db.close()
    print("Database seeding completed successfully with 34 rooms, 32 sections, settings, and closures!")

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    seed_database(force_reseed=force)
