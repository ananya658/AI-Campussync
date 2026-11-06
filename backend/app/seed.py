from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.database import engine, SessionLocal, Base
from backend.app.models import (
    User, Student, Faculty, Branch, Batch, Building, Floor, Room, RoomFacility,
    Booking, Schedule, Announcement, AnnouncementVersion, Notification, IssueReport, AuditLog
)
from backend.app.auth import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Check if already seeded
    if db.query(Building).first():
        print("Database already contains data. Skipping re-seed.")
        db.close()
        return

    print("Seeding DDUGU CampusSync AI database with actual campus infrastructure...")

    # 1. Seed Branches
    branches_data = [
        {"code": "CSE", "name": "Computer Science & Engineering", "total_capacity": 150, "description": "Sections A and B"},
        {"code": "AIML", "name": "Artificial Intelligence & Machine Learning", "total_capacity": 150, "description": "Sections A and B"},
        {"code": "AIDS", "name": "Artificial Intelligence & Data Science", "total_capacity": 75, "description": "Section A"},
        {"code": "ECE", "name": "Electronics & Communication Engineering", "total_capacity": 75, "description": "Section A"},
        {"code": "ME", "name": "Mechanical Engineering", "total_capacity": 75, "description": "Section A"},
        {"code": "IT", "name": "Information Technology", "total_capacity": 75, "description": "Section A"},
    ]
    branch_objs = {}
    for b in branches_data:
        obj = Branch(**b)
        db.add(obj)
        db.flush()
        branch_objs[b["code"]] = obj

    # 2. Seed Batches
    batches_data = [
        {"name": "Batch 2022-2026", "academic_year": "2025-2026", "is_active": True}, # 4th year
        {"name": "Batch 2023-2027", "academic_year": "2025-2026", "is_active": True}, # 3rd year
        {"name": "Batch 2024-2028", "academic_year": "2025-2026", "is_active": True}, # 2nd year
        {"name": "Batch 2025-2029", "academic_year": "2025-2026", "is_active": True}, # 1st year
    ]
    batch_objs = []
    for bat in batches_data:
        obj = Batch(**bat)
        db.add(obj)
        db.flush()
        batch_objs.append(obj)

    # 3. Seed Buildings: IET and Deeksha Bhawan
    iet_building = Building(
        name="Institute of Engineering and Technology (IET)",
        code="IET",
        description="Core engineering building housing laboratories, classrooms, administrative offices, and library.",
        total_floors=3,
        distance_from_iet_meters=0,
        is_active=True
    )
    db.add(iet_building)
    db.flush()

    db_building = Building(
        name="Deeksha Bhawan",
        code="DB",
        description="Central lecture complex located approximately 100 metres from IET, housing lecture halls LH01 to LH14.",
        total_floors=2,
        distance_from_iet_meters=100,
        is_active=True
    )
    db.add(db_building)
    db.flush()

    # 4. Seed Floors for IET
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

    # 5. Seed Rooms for IET
    # Ground Floor: Library (150-180), Teachers' Office, Director's Office, Admin Office, Placement Cell
    iet_g_rooms = [
        {"num": "Library", "name": "Central Engineering Library", "type": "LIBRARY", "cap": 180, "svg": "iet-g-library", "uses": "Self-Study, Research, Reference"},
        {"num": "Teachers-Office", "name": "Faculty Central Lounge", "type": "OFFICE", "cap": 30, "svg": "iet-g-teachers", "uses": "Faculty Workspaces"},
        {"num": "Directors-Office", "name": "Directorate Office", "type": "OFFICE", "cap": 15, "svg": "iet-g-director", "uses": "Executive Meetings"},
        {"num": "Admin-Office", "name": "Central Academic Administration", "type": "OFFICE", "cap": 25, "svg": "iet-g-admin", "uses": "Student Affairs, Registration"},
        {"num": "Placement-Cell", "name": "Training & Placement Cell (T&P)", "type": "OFFICE", "cap": 40, "svg": "iet-g-placement", "uses": "Recruitment Drives, Interviews"}
    ]
    room_objects = {}
    for r in iet_g_rooms:
        rm = Room(
            building_id=iet_building.id,
            floor_id=iet_f0.id,
            room_number=r["num"],
            room_name=r["name"],
            room_type=r["type"],
            capacity=r["cap"],
            svg_id=r["svg"],
            permitted_uses=r["uses"],
            verification_status="OFFICIAL_VERIFIED"
        )
        db.add(rm)
        db.flush()
        room_objects[r["num"]] = rm

    # First Floor: CSE Lab, ME Lab, ECE Lab, IT Lab, IET20, IET18, IET19, IET17 (each classroom ~75 capacity)
    iet_1_rooms = [
        {"num": "CSE-Lab", "name": "Computer Science Laboratory", "type": "LAB", "cap": 40, "svg": "iet-1-cselab", "uses": "Coding Practicals, AI ML Labs"},
        {"num": "ME-Lab", "name": "Mechanical Engineering Lab", "type": "LAB", "cap": 40, "svg": "iet-1-melab", "uses": "Thermodynamics, CAD/CAM Practicals"},
        {"num": "ECE-Lab", "name": "Electronics & Circuits Lab", "type": "LAB", "cap": 40, "svg": "iet-1-ecelab", "uses": "Digital Electronics, Microprocessor Lab"},
        {"num": "IT-Lab", "name": "Information Technology Lab", "type": "LAB", "cap": 40, "svg": "iet-1-itlab", "uses": "Networking, Web Development Practicals"},
        {"num": "IET17", "name": "Classroom IET 17", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-1-iet17", "uses": "Lectures, Minor Exams, Seminars"},
        {"num": "IET18", "name": "Classroom IET 18", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-1-iet18", "uses": "Lectures, Minor Exams, Seminars"},
        {"num": "IET19", "name": "Classroom IET 19", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-1-iet19", "uses": "Lectures, Minor Exams, Seminars"},
        {"num": "IET20", "name": "Classroom IET 20", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-1-iet20", "uses": "Lectures, Minor Exams, Seminars"},
    ]
    for r in iet_1_rooms:
        rm = Room(
            building_id=iet_building.id,
            floor_id=iet_f1.id,
            room_number=r["num"],
            room_name=r["name"],
            room_type=r["type"],
            capacity=r["cap"],
            svg_id=r["svg"],
            permitted_uses=r["uses"],
            verification_status="OFFICIAL_VERIFIED"
        )
        db.add(rm)
        db.flush()
        room_objects[r["num"]] = rm

    # Second Floor: Seminar Hall IET32 (~200), IET24, IET25, IET29, IET30, IET28
    iet_2_rooms = [
        {"num": "IET32", "name": "Central Seminar Hall IET 32", "type": "SEMINAR_HALL", "cap": 200, "svg": "iet-2-iet32", "uses": "Conferences, Guest Lectures, Hackathons, Major Exams"},
        {"num": "IET24", "name": "Classroom IET 24", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-2-iet24", "uses": "Lectures, Minor Exams"},
        {"num": "IET25", "name": "Classroom IET 25", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-2-iet25", "uses": "Lectures, Minor Exams"},
        {"num": "IET28", "name": "Classroom IET 28", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-2-iet28", "uses": "Lectures, Minor Exams"},
        {"num": "IET29", "name": "Classroom IET 29", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-2-iet29", "uses": "Lectures, Minor Exams"},
        {"num": "IET30", "name": "Classroom IET 30", "type": "LECTURE_HALL", "cap": 75, "svg": "iet-2-iet30", "uses": "Lectures, Minor Exams"},
    ]
    for r in iet_2_rooms:
        rm = Room(
            building_id=iet_building.id,
            floor_id=iet_f2.id,
            room_number=r["num"],
            room_name=r["name"],
            room_type=r["type"],
            capacity=r["cap"],
            svg_id=r["svg"],
            permitted_uses=r["uses"],
            verification_status="OFFICIAL_VERIFIED"
        )
        db.add(rm)
        db.flush()
        room_objects[r["num"]] = rm

    # 6. Seed Rooms for Deeksha Bhawan: LH01 to LH14
    # Ground Floor: LH01 to LH07
    for i in range(1, 8):
        lh_code = f"LH{i:02d}"
        rm = Room(
            building_id=db_building.id,
            floor_id=db_f0.id,
            room_number=lh_code,
            room_name=f"Lecture Hall {lh_code}",
            room_type="LECTURE_HALL",
            capacity=90,
            svg_id=f"db-0-{lh_code.lower()}",
            permitted_uses="Major Lectures, Examinations, Combined Sections",
            verification_status="OFFICIAL_VERIFIED"
        )
        db.add(rm)
        db.flush()
        room_objects[lh_code] = rm

    # First Floor: LH08 to LH12 (official), LH13 and LH14 (Discrepancy: pending administrative verification!)
    for i in range(8, 15):
        lh_code = f"LH{i:02d}"
        is_discrepancy = i in [13, 14]
        v_status = "PENDING_ADMIN_VERIFICATION" if is_discrepancy else "OFFICIAL_VERIFIED"
        v_notes = "Blueprint discrepancy: visible in structural floor plan but unverified in academic allocation registry. Subject to administrative approval." if is_discrepancy else None

        rm = Room(
            building_id=db_building.id,
            floor_id=db_f1.id,
            room_number=lh_code,
            room_name=f"Lecture Hall {lh_code}" + (" (Unverified Space)" if is_discrepancy else ""),
            room_type="LECTURE_HALL",
            capacity=90,
            svg_id=f"db-1-{lh_code.lower()}",
            permitted_uses="Lectures, Examinations" if not is_discrepancy else "Pending Verification",
            verification_status=v_status,
            verification_notes=v_notes,
            is_maintenance=is_discrepancy  # Marked grey/restricted until verified
        )
        db.add(rm)
        db.flush()
        room_objects[lh_code] = rm

    # 7. Seed Facilities for Rooms
    facilities_data = [
        # Labs
        ("CSE-Lab", [("LAB_COMPUTERS", 40), ("PROJECTOR", 1), ("AC", 2), ("HIGH_SPEED_WIFI", 1)]),
        ("IT-Lab", [("LAB_COMPUTERS", 40), ("PROJECTOR", 1), ("AC", 2), ("HIGH_SPEED_WIFI", 1)]),
        ("ME-Lab", [("PROJECTOR", 1), ("LAB_COMPUTERS", 10), ("AC", 1)]),
        ("ECE-Lab", [("PROJECTOR", 1), ("LAB_COMPUTERS", 15), ("AC", 1)]),
        # Seminar Hall
        ("IET32", [("AUDIO_SYSTEM", 1), ("PROJECTOR", 2), ("AC", 4), ("SMART_BOARD", 1), ("HIGH_SPEED_WIFI", 1)]),
        # Standard Classrooms
        ("IET17", [("PROJECTOR", 1), ("SMART_BOARD", 1), ("AC", 2)]),
        ("IET18", [("PROJECTOR", 1), ("SMART_BOARD", 1), ("AC", 2)]),
        ("IET19", [("PROJECTOR", 1), ("AC", 2)]),
        ("IET20", [("PROJECTOR", 1), ("AC", 2)]),
        ("IET24", [("PROJECTOR", 1), ("AC", 2)]),
        ("IET25", [("PROJECTOR", 1), ("AC", 2)]),
        # Deeksha Bhawan Halls
        ("LH01", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH02", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH03", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH04", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH08", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
        ("LH09", [("PROJECTOR", 1), ("AUDIO_SYSTEM", 1), ("AC", 2)]),
    ]
    for r_num, facs in facilities_data:
        if r_num in room_objects:
            r_obj = room_objects[r_num]
            for f_name, qty in facs:
                db.add(RoomFacility(room_id=r_obj.id, facility_name=f_name, quantity=qty, condition="EXCELLENT"))

    # 8. Seed Users & Profiles (Admin, Faculty, Students)
    # Admin User
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
        cabin_room_id=room_objects["Teachers-Office"].id
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
        cabin_room_id=room_objects["Teachers-Office"].id
    )
    db.add(fac2_profile)

    # Student 1: Rahul Singh (CSE Year 3, Section A)
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
        batch_id=batch_objs[1].id, # 2023-2027
        year=3,
        section="A"
    )
    db.add(stu1_profile)

    # Student 2: Priya Maurya (AI ML Year 2, Section B)
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
        batch_id=batch_objs[2].id, # 2024-2028
        year=2,
        section="B"
    )
    db.add(stu2_profile)

    db.flush()

    # 9. Seed Academic Timetable Schedules
    # Rahul (CSE Year 3 Section A) schedules across weekdays
    schedules_data = [
        # Monday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 0, "s": time(9, 30), "e": time(10, 30), "code": "CS-301", "name": "Design & Analysis of Algorithms", "type": "LECTURE"},
        {"room": "IET18", "fac": fac2_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 0, "s": time(10, 30), "e": time(11, 30), "code": "CS-302", "name": "Database Management Systems", "type": "LECTURE"},
        {"room": "CSE-Lab", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 0, "s": time(14, 0), "e": time(16, 0), "code": "CS-305", "name": "DBMS Practical Laboratory", "type": "LAB"},
        # Tuesday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 1, "s": time(9, 30), "e": time(10, 30), "code": "CS-303", "name": "Computer Networks & Protocols", "type": "LECTURE"},
        {"room": "IET17", "fac": fac2_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 1, "s": time(11, 30), "e": time(12, 30), "code": "CS-304", "name": "Software Engineering & Agile", "type": "LECTURE"},
        # Wednesday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 2, "s": time(10, 30), "e": time(11, 30), "code": "CS-301", "name": "Design & Analysis of Algorithms", "type": "LECTURE"},
        {"room": "IET32", "fac": fac2_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 2, "s": time(15, 0), "e": time(16, 30), "code": "CS-306", "name": "Industry Guest Lecture Series", "type": "LECTURE"},
        # Thursday
        {"room": "IET18", "fac": fac2_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 3, "s": time(9, 30), "e": time(10, 30), "code": "CS-302", "name": "Database Management Systems", "type": "LECTURE"},
        {"room": "IT-Lab", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 3, "s": time(14, 0), "e": time(16, 0), "code": "CS-307", "name": "Network Socket Programming Lab", "type": "LAB"},
        # Friday
        {"room": "IET18", "fac": fac1_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 4, "s": time(10, 30), "e": time(11, 30), "code": "CS-303", "name": "Computer Networks & Protocols", "type": "LECTURE"},
        {"room": "IET17", "fac": fac2_profile, "branch": branch_objs["CSE"], "yr": 3, "sec": "A", "dow": 4, "s": time(11, 30), "e": time(12, 30), "code": "CS-304", "name": "Software Engineering & Agile", "type": "LECTURE"},
        # Priya (AI ML Year 2 Section B)
        {"room": "IET19", "fac": fac2_profile, "branch": branch_objs["AIML"], "yr": 2, "sec": "B", "dow": 0, "s": time(11, 0), "e": time(12, 0), "code": "AI-201", "name": "Discrete Mathematics & Graph Theory", "type": "LECTURE"},
        {"room": "IET19", "fac": fac2_profile, "branch": branch_objs["AIML"], "yr": 2, "sec": "B", "dow": 1, "s": time(10, 0), "e": time(11, 0), "code": "AI-202", "name": "Data Structures with Python", "type": "LECTURE"},
        {"room": "CSE-Lab", "fac": fac2_profile, "branch": branch_objs["AIML"], "yr": 2, "sec": "B", "dow": 2, "s": time(14, 0), "e": time(16, 0), "code": "AI-205", "name": "Python & Data Science Lab", "type": "LAB"},
    ]
    for s_item in schedules_data:
        db.add(Schedule(
            room_id=room_objects[s_item["room"]].id,
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

    # 10. Seed Realistic Sample Bookings (clearly labeled TEST DATA)
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
            "cap": 85,
            "branch": branch_objs["AIML"],
            "yr": 2,
            "sec": "B",
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
            "status": "CONFIRMED"
        }
    ]

    for sb in sample_bookings:
        db.add(Booking(
            booking_reference=sb["ref"],
            room_id=room_objects[sb["room"]].id,
            user_id=sb["user"].id,
            title=sb["title"],
            purpose=sb["purpose"],
            date=sb["date"],
            start_time=sb["s"],
            end_time=sb["e"],
            expected_students=sb["cap"],
            branch_id=sb["branch"].id if sb["branch"] else None,
            academic_year=sb["yr"],
            section=sb["sec"],
            status=sb["status"],
            is_test_data=True
        ))

    # 11. Seed Announcements with Version History
    ann1 = Announcement(
        title="B.Tech Odd Semester Minor Examination Schedule Announced",
        description="Minor Examinations for B.Tech CSE, AI ML, and IT 3rd Year are scheduled starting next Monday. Seating plans have been allocated across IET and Deeksha Bhawan.",
        announcement_type="MINOR_EXAM",
        date=today + timedelta(days=5),
        start_time=time(10, 0),
        end_time=time(12, 0),
        building_id=db_building.id,
        room_id=room_objects["LH01"].id,
        target_branch_id=branch_objs["CSE"].id,
        target_year=3,
        created_by_id=admin_user.id,
        status="PUBLISHED",
        version=2
    )
    db.add(ann1)
    db.flush()

    # Add versions for ann1 to show version history
    v1 = AnnouncementVersion(
        announcement_id=ann1.id,
        version=1,
        title="B.Tech Minor Examination Notice",
        description="Minor Exam 1 will be held in Room IET17.",
        room_id=room_objects["IET17"].id,
        date=today + timedelta(days=5),
        start_time=time(10, 0),
        end_time=time(12, 0),
        change_summary="Initial publication for Room IET17.",
        modified_by_id=admin_user.id
    )
    v2 = AnnouncementVersion(
        announcement_id=ann1.id,
        version=2,
        title="B.Tech Odd Semester Minor Examination Schedule Announced",
        description="Reassigned to Deeksha Bhawan LH01 due to increased student cohort capacity.",
        room_id=room_objects["LH01"].id,
        date=today + timedelta(days=5),
        start_time=time(10, 0),
        end_time=time(12, 0),
        change_summary="Venue upgraded to Deeksha Bhawan LH01 for combined seating.",
        modified_by_id=admin_user.id
    )
    db.add_all([v1, v2])

    ann2 = Announcement(
        title="AI ML Special Guest Lecture on Generative AI & Kubernetes",
        description="Distinguished speaker from Google Developer Group delivering masterclass on cloud microservices and scalable LLMs.",
        announcement_type="ACADEMIC_EVENT",
        date=tomorrow,
        start_time=time(14, 0),
        end_time=time(16, 0),
        building_id=iet_building.id,
        room_id=room_objects["IET32"].id,
        target_branch_id=None,
        target_year=None,
        created_by_id=fac2_user.id,
        status="PUBLISHED",
        version=1
    )
    db.add(ann2)
    db.flush()
    db.add(AnnouncementVersion(
        announcement_id=ann2.id,
        version=1,
        title=ann2.title,
        description=ann2.description,
        room_id=ann2.room_id,
        date=ann2.date,
        start_time=ann2.start_time,
        end_time=ann2.end_time,
        change_summary="Initial announcement",
        modified_by_id=fac2_user.id
    ))

    # 12. Seed Issue Reports
    rep1 = IssueReport(
        student_id=stu1_profile.id,
        reporter_user_id=stu1_user.id,
        category="WRONG_CLASSROOM",
        description="Timetable showed CS-301 in IET17, but the door notice indicated IET18. Please verify official lecture venue.",
        building_id=iet_building.id,
        room_id=room_objects["IET18"].id,
        scheduled_date=today,
        scheduled_time=time(9, 30),
        status="RESOLVED",
        admin_resolution_note="Classroom allocation verified. Room IET18 is the official venue for CS-301 Section A. Timetable synced.",
        resolved_by_id=admin_user.id,
        resolved_at=datetime.utcnow()
    )
    rep2 = IssueReport(
        student_id=stu2_profile.id,
        reporter_user_id=stu2_user.id,
        category="INCORRECT_TIMING",
        description="Minor exam for Mathematics appeared at 2 PM instead of 11 AM in student app sync.",
        building_id=db_building.id,
        room_id=room_objects["LH01"].id,
        scheduled_date=tomorrow,
        scheduled_time=time(11, 0),
        status="PENDING"
    )
    db.add_all([rep1, rep2])

    # 13. Seed Initial Notifications
    notifs = [
        Notification(
            user_id=stu1_user.id,
            title="Venue Update: Minor Exam in LH01",
            message="Your Odd Semester Minor Examination venue has been updated to Deeksha Bhawan LH01.",
            notification_type="EXAM_SCHEDULE_CHANGED",
            link_url="/student/announcements"
        ),
        Notification(
            user_id=stu1_user.id,
            title="Issue Report Resolved",
            message="Admin resolved your report regarding Classroom IET18. Venue confirmed.",
            notification_type="REPORT_RESOLVED",
            link_url="/student/reports"
        ),
        Notification(
            user_id=fac1_user.id,
            title="Booking Confirmed: IET20",
            message="Your reservation for Extra Lecture on Graph Algorithms is confirmed for today at 4:00 PM.",
            notification_type="BOOKING_CONFIRMED",
            link_url="/faculty/bookings"
        )
    ]
    db.add_all(notifs)

    # 14. Seed Initial Audit Logs
    audit_seeds = [
        AuditLog(
            user_id=admin_user.id,
            user_role="ADMIN",
            user_name=admin_user.full_name,
            action_type="CREATE",
            entity_type="ROOM",
            entity_id="ALL",
            new_value="Initialized 25 campus rooms across IET and Deeksha Bhawan",
            reason="Initial DDUGU Campus Infrastructure Setup"
        ),
        AuditLog(
            user_id=admin_user.id,
            user_role="ADMIN",
            user_name=admin_user.full_name,
            action_type="UPDATE",
            entity_type="ROOM",
            entity_id="LH13",
            new_value="Configured verification_status = PENDING_ADMIN_VERIFICATION",
            reason="Deeksha Bhawan blueprint discrepancy isolation"
        )
    ]
    db.add_all(audit_seeds)

    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
