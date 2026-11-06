import pytest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.seed import seed_database
from backend.app.models import Room, Booking, User, Branch

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_bookings():
    # The CI database is fresh, and TestClient does not run the app lifespan
    # unless used as a context manager. Seed the isolated test database here
    # so these integration tests have their required users, rooms, and settings.
    seed_database()
    db = next(get_db())
    db.query(Booking).filter(
        Booking.title.in_([
            "Automated Unit Test Lecture",
            "Overlapping Conflicting Lecture",
            "Session to be Cancelled",
            "Replacement Session in Freed Slot",
            "First Half-Open Slot",
            "Second Back-to-Back Slot",
            "Section CSE-3A Theory Session",
            "Colliding Section CSE-3A Lab Session",
            "Dr. Verma AI Guest Session",
            "Dr. Verma Simultaneous Session",
            "Minor Exam 1: Algorithms",
            "B.Tech Minor Exam Atomic Split (Sitting A)",
            "B.Tech Minor Exam Atomic Split (Sitting B)"
        ]) | Booking.title.like("Concurrent Race Request%")
    ).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(Booking).filter(
        Booking.title.in_([
            "Automated Unit Test Lecture",
            "Overlapping Conflicting Lecture",
            "Session to be Cancelled",
            "Replacement Session in Freed Slot",
            "First Half-Open Slot",
            "Second Back-to-Back Slot",
            "Section CSE-3A Theory Session",
            "Colliding Section CSE-3A Lab Session",
            "Dr. Verma AI Guest Session",
            "Dr. Verma Simultaneous Session",
            "Minor Exam 1: Algorithms",
            "B.Tech Minor Exam Atomic Split (Sitting A)",
            "B.Tech Minor Exam Atomic Split (Sitting B)"
        ]) | Booking.title.like("Concurrent Race Request%")
    ).delete(synchronize_session=False)
    db.commit()

# Helper to get auth token
def get_auth_token(email: str, password: str = "Admin@123") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]

# --- TEST 1: Successful login ---
def test_01_successful_login():
    response = client.post("/api/auth/login", json={
        "email": "admin@ddugu.ac.in",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@ddugu.ac.in"
    assert data["user"]["role"] == "ADMIN"

# --- TEST 2: Unauthorized access & invalid credentials ---
def test_02_unauthorized_access():
    # Bad credentials
    bad_login = client.post("/api/auth/login", json={
        "email": "admin@ddugu.ac.in",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # Protected endpoint without token
    protected_resp = client.get("/api/auth/me")
    assert protected_resp.status_code == 401

    # Protected endpoint with garbage token
    bad_token_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer fake.garbage.token"}
    )
    assert bad_token_resp.status_code == 401

# --- TEST 3: Room availability query ---
def test_03_room_availability():
    query_date = (date.today() + timedelta(days=10)).isoformat()
    response = client.get(
        "/api/rooms/availability",
        params={
            "booking_date": query_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "required_capacity": 50
        }
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    # There should be available rooms matching this criteria
    available_rooms = [r for r in results if r["is_available"]]
    assert len(available_rooms) > 0

# --- TEST 4: Successful classroom booking ---
def test_04_successful_booking():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    room_iet24 = next(r for r in rooms_resp.json() if r["room_number"] == "IET24")
    
    booking_date = (date.today() + timedelta(days=20)).isoformat()
    payload = {
        "room_id": room_iet24["id"],
        "title": "Automated Unit Test Lecture",
        "purpose": "EXTRA_LECTURE",
        "date": booking_date,
        "start_time": "17:00",
        "end_time": "18:00",
        "expected_students": 50,
        "is_test_data": True
    }

    res = client.post(
        "/api/bookings",
        json=payload,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res.status_code == 200
    booking_data = res.json()
    assert booking_data["room_id"] == room_iet24["id"]
    assert booking_data["status"] == "CONFIRMED"
    assert booking_data["booking_reference"].startswith("CS-")

# --- TEST 5: Overlapping booking rejection (existing_start < new_end AND existing_end > new_start) ---
def test_05_overlapping_booking_rejection():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    room_iet24 = next(r for r in rooms_resp.json() if r["room_number"] == "IET24")
    booking_date = (date.today() + timedelta(days=20)).isoformat()

    # Step 1: Create initial booking from 17:00 to 18:00
    first_resp = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet24["id"],
            "title": "Automated Unit Test Lecture",
            "purpose": "EXTRA_LECTURE",
            "date": booking_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 50,
            "is_test_data": True
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert first_resp.status_code == 200

    # Step 2: An overlapping request from 17:30 to 18:30 MUST be rejected with 409 Conflict!
    overlap_payload = {
        "room_id": room_iet24["id"],
        "title": "Overlapping Conflicting Lecture",
        "purpose": "EXTRA_LECTURE",
        "date": booking_date,
        "start_time": "17:30",
        "end_time": "18:30",
        "expected_students": 40,
        "is_test_data": True
    }

    res = client.post(
        "/api/bookings",
        json=overlap_payload,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res.status_code == 409
    assert "conflict" in res.json()["detail"].lower()

# --- TEST 6: Start time after or equal to end time ---
def test_06_invalid_time_range():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    room_iet25 = next(r for r in rooms_resp.json() if r["room_number"] == "IET25")
    booking_date = (date.today() + timedelta(days=21)).isoformat()

    bad_payload = {
        "room_id": room_iet25["id"],
        "title": "Backwards Time Lecture",
        "purpose": "EXTRA_LECTURE",
        "date": booking_date,
        "start_time": "15:00",
        "end_time": "14:00",
        "expected_students": 50
    }
    res = client.post(
        "/api/bookings",
        json=bad_payload,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res.status_code == 400

# --- TEST 7: Insufficient room capacity validation ---
def test_07_insufficient_room_capacity():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    # IET25 capacity is 75
    room_iet25 = next(r for r in rooms_resp.json() if r["room_number"] == "IET25")
    booking_date = (date.today() + timedelta(days=22)).isoformat()

    excessive_payload = {
        "room_id": room_iet25["id"],
        "title": "Overcrowded Session",
        "purpose": "SEMINAR",
        "date": booking_date,
        "start_time": "11:00",
        "end_time": "12:00",
        "expected_students": 150 # Exceeds 75 capacity
    }
    res = client.post(
        "/api/bookings",
        json=excessive_payload,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res.status_code == 409
    assert "capacity exceeded" in res.json()["detail"].lower()

# --- TEST 8: Cancelled booking frees up room availability ---
def test_08_cancelled_booking_frees_availability():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    room_iet28 = next(r for r in rooms_resp.json() if r["room_number"] == "IET28")
    booking_date = (date.today() + timedelta(days=25)).isoformat()

    # Step 1: Book slot 17:00 - 18:00
    create_res = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet28["id"],
            "title": "Session to be Cancelled",
            "purpose": "EXTRA_LECTURE",
            "date": booking_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 50
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert create_res.status_code == 200
    b_id = create_res.json()["id"]

    # Step 2: Cancel booking
    cancel_res = client.patch(
        f"/api/bookings/{b_id}/cancel",
        json={"reason": "Faculty attending urgent meeting"},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Step 3: Now booking the exact same slot should SUCCEED because it's cancelled!
    rebook_res = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet28["id"],
            "title": "Replacement Session in Freed Slot",
            "purpose": "EXTRA_LECTURE",
            "date": booking_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 50
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert rebook_res.status_code == 200
    assert rebook_res.json()["status"] == "CONFIRMED"

# --- TEST 9: Student permission restrictions (Must NOT be allowed to book classrooms or edit schedules) ---
def test_09_student_permission_restrictions():
    student_token = get_auth_token("rahul.cse23@ddugu.ac.in", "Student@123")
    rooms_resp = client.get("/api/rooms")
    room_id = rooms_resp.json()[0]["id"]

    # Student attempting to book classroom -> MUST BE 403 Forbidden!
    attempt_booking = client.post(
        "/api/bookings",
        json={
            "room_id": room_id,
            "title": "Unauthorized Student Booking",
            "purpose": "EXTRA_LECTURE",
            "date": str(date.today() + timedelta(days=30)),
            "start_time": "12:00",
            "end_time": "13:00",
            "expected_students": 20
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert attempt_booking.status_code == 403

    # Student attempting to create academic schedule -> MUST BE 403 Forbidden!
    attempt_sched = client.post(
        "/api/schedules",
        json={
            "room_id": room_id,
            "faculty_id": 1,
            "branch_id": 1,
            "academic_year": 3,
            "section": "A",
            "day_of_week": 1,
            "start_time": "09:00",
            "end_time": "10:00",
            "subject_code": "HACK-101",
            "subject_name": "Unauthorized Schedule Slot"
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert attempt_sched.status_code == 403

# --- TEST 10: Announcement publishing and version history ---
def test_10_announcement_publishing_and_versions():
    admin_token = get_auth_token("admin@ddugu.ac.in", "Admin@123")
    
    # 1. Create announcement (v1)
    create_ann = client.post(
        "/api/announcements",
        json={
            "title": "Semester Practical Exam Notice",
            "description": "Initial schedule for IT and CSE labs.",
            "announcement_type": "PRACTICAL_EXAM",
            "date": str(date.today() + timedelta(days=12)),
            "start_time": "09:00",
            "end_time": "12:00"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_ann.status_code == 200
    ann_data = create_ann.json()
    assert ann_data["version"] == 1
    ann_id = ann_data["id"]

    # 2. Update announcement to generate version 2
    update_ann = client.patch(
        f"/api/announcements/{ann_id}",
        json={
            "title": "Semester Practical Exam Notice - REVISED VENUE",
            "change_summary": "Shifted to CSE-Lab due to network requirement"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_ann.status_code == 200
    updated_data = update_ann.json()
    assert updated_data["version"] == 2
    assert len(updated_data["versions"]) >= 2

# --- TEST 11: Student report creation and admin resolution ---
def test_11_student_report_and_resolution():
    student_token = get_auth_token("rahul.cse23@ddugu.ac.in", "Student@123")
    admin_token = get_auth_token("admin@ddugu.ac.in", "Admin@123")

    # Student submits report
    report_res = client.post(
        "/api/reports",
        json={
            "category": "WRONG_CLASSROOM",
            "description": "The door of IET20 has a sign saying lecture moved to IET19.",
            "scheduled_date": str(date.today())
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["status"] == "PENDING"
    rep_id = report_data["id"]

    # Admin resolves report
    resolve_res = client.patch(
        f"/api/reports/{rep_id}/resolve",
        json={
            "status": "RESOLVED",
            "admin_resolution_note": "Signage corrected. Room IET20 remains official venue."
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()
    assert resolved_data["status"] == "RESOLVED"
    assert "Signage corrected" in resolved_data["admin_resolution_note"]

# --- TEST 12: AI recommendation validation against real database ---
def test_12_ai_recommendation_engine():
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    
    # Query: "Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM"
    ai_resp = client.post(
        "/api/ai/search",
        json={"query": "Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM"},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert ai_resp.status_code == 200
    data = ai_resp.json()
    assert "interpreted_query" in data
    assert data["interpreted_query"]["required_capacity"] == 70
    assert data["interpreted_query"]["building"] == "IET"
    
    # Must return verified available room(s)
    if data["primary_recommendation"]:
        rec = data["primary_recommendation"]
        assert rec["is_available"] == True
        assert rec["room"]["capacity"] >= 70
        assert "IET" in rec["room"]["building_code"]
        assert rec["match_score"] > 0
        assert len(rec["explanation"]) > 0

    # Query 2: Lab practical
    ai_lab_resp = client.post(
        "/api/ai/search",
        json={"query": "Find a laboratory for an IT practical session tomorrow at 2 pm"},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert ai_lab_resp.status_code == 200
    lab_data = ai_lab_resp.json()
    assert lab_data["interpreted_query"]["room_type"] == "LAB"


# --- TEST 13: Half-open interval semantics [start, end) ---
def test_13_half_open_interval_back_to_back():
    """
    Core correctness contract:
    A booking from 17:00–18:00 and another from 18:00–19:00 in the same room MUST be allowed.
    """
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms_resp = client.get("/api/rooms")
    room = next(r for r in rooms_resp.json() if r["room_number"] == "IET30")
    test_date = (date.today() + timedelta(days=28)).isoformat()

    # Slot 1: 17:00 to 18:00
    res1 = client.post(
        "/api/bookings",
        json={
            "room_id": room["id"],
            "title": "First Half-Open Slot",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 40
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res1.status_code == 200

    # Slot 2: 18:00 to 19:00 (Touches boundary at 18:00, MUST NOT collide!)
    res2 = client.post(
        "/api/bookings",
        json={
            "room_id": room["id"],
            "title": "Second Back-to-Back Slot",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "18:00",
            "end_time": "19:00",
            "expected_students": 40
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res2.status_code == 200, f"Half-open back-to-back booking failed: {res2.text}"


# --- TEST 14: Resource collision dimension 2: Academic Section collision ---
def test_14_academic_section_collision():
    """
    Section CSE Year 3 Section A cannot be scheduled in two rooms at the same time.
    """
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms = client.get("/api/rooms").json()
    r1 = next(r for r in rooms if r["room_number"] == "IET18")
    r2 = next(r for r in rooms if r["room_number"] == "IET19")
    test_date = (date.today() + timedelta(days=29)).isoformat()

    # Step 1: Book Section CSE-3A in Room 1
    b1_res = client.post(
        "/api/bookings",
        json={
            "room_id": r1["id"],
            "title": "Section CSE-3A Theory Session",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 70,
            "branch_id": 1,
            "academic_year": 3,
            "section": "A"
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert b1_res.status_code == 200

    # Step 2: Attempt to book same section CSE-3A in Room 2 during overlapping window
    b2_res = client.post(
        "/api/bookings",
        json={
            "room_id": r2["id"],
            "title": "Colliding Section CSE-3A Lab Session",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:30",
            "end_time": "18:30",
            "expected_students": 70,
            "branch_id": 1,
            "academic_year": 3,
            "section": "A"
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert b2_res.status_code == 409
    assert "section collision" in b2_res.json()["detail"].lower()


# --- TEST 15: Resource collision dimension 3: Faculty collision ---
def test_15_faculty_collision():
    """
    Professor Dr. Sunita Verma cannot be booked in two separate rooms at the same time.
    """
    faculty_token = get_auth_token("dr.verma@ddugu.ac.in", "Faculty@123")
    rooms = client.get("/api/rooms").json()
    r1 = next(r for r in rooms if r["room_number"] == "IET24")
    r2 = next(r for r in rooms if r["room_number"] == "IET25")
    test_date = (date.today() + timedelta(days=30)).isoformat()

    # Booking 1 with Dr. Verma in IET24
    res1 = client.post(
        "/api/bookings",
        json={
            "room_id": r1["id"],
            "title": "Dr. Verma AI Guest Session",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 40
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res1.status_code == 200

    # Booking 2 by same Dr. Verma in IET25 at same time MUST fail
    res2 = client.post(
        "/api/bookings",
        json={
            "room_id": r2["id"],
            "title": "Dr. Verma Simultaneous Session",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:15",
            "end_time": "18:15",
            "expected_students": 40
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res2.status_code == 409
    assert "faculty collision" in res2.json()["detail"].lower()


# --- TEST 16: Spaced Examination Capacity & Split Recommendation ---
def test_16_spaced_examination_capacity_and_split_recommendation():
    """
    In a room with nominal capacity 75 (IET18), spaced exam capacity is 37.
    Requesting 75 candidates for MINOR_EXAM must be refused and trigger split recommendations.
    """
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms = client.get("/api/rooms").json()
    room_iet18 = next(r for r in rooms if r["room_number"] == "IET18")
    test_date = (date.today() + timedelta(days=31)).isoformat()

    # Attempting 75 candidates in 37 exam seat room
    exam_res = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet18["id"],
            "title": "Minor Exam 1: Algorithms",
            "purpose": "MINOR_EXAM",
            "date": test_date,
            "start_time": "17:00",
            "end_time": "19:00",
            "expected_students": 75
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert exam_res.status_code == 409
    assert "spaced examination capacity exceeded" in exam_res.json()["detail"].lower()

    # Query split recommendation plan
    plan_res = client.get(
        f"/api/bookings/split-plan?booking_date={test_date}&start_time=17:00&end_time=19:00&total_students=75",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert "recommendations" in plan_data
    assert len(plan_data["recommendations"]) > 0


# --- TEST 17: Atomic Split Booking Creation ---
def test_17_atomic_split_booking_creation():
    """
    Atomically creates two linked bookings for an examination split sitting.
    """
    faculty_token = get_auth_token("prof.sharma@ddugu.ac.in", "Faculty@123")
    rooms = client.get("/api/rooms").json()
    r1 = next(r for r in rooms if r["room_number"] == "LH01")
    r2 = next(r for r in rooms if r["room_number"] == "LH02")
    test_date = (date.today() + timedelta(days=32)).isoformat()

    split_res = client.post(
        "/api/bookings/split-booking",
        json={
            "primary_room_id": r1["id"],
            "auxiliary_room_id": r2["id"],
            "date": test_date,
            "start_time": "17:00",
            "end_time": "19:00",
            "title": "B.Tech Minor Exam Atomic Split",
            "primary_students": 40,
            "auxiliary_students": 35,
            "branch_id": 1,
            "academic_year": 3,
            "section": "A"
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert split_res.status_code == 200
    data = split_res.json()
    assert data["status"] == "SUCCESS"
    assert data["primary_booking"]["is_split_sitting"] == True
    assert data["auxiliary_booking"]["is_split_sitting"] == True
    assert data["auxiliary_booking"]["linked_booking_id"] == data["primary_booking"]["id"]


# --- TEST 18: Concurrency Race Condition (20 Simultaneous Booking Requests) ---
def test_18_concurrency_race_condition_twenty_simultaneous_requests():
    """
    Critical concurrency stress test mandated by Master Prompt 2:
    20 simultaneous requests compete for the EXACT same room and slot at the exact same instant.
    Assert that exactly 1 succeeds and 19 fail with 409 Conflict.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    admin_token = get_auth_token("admin@ddugu.ac.in", "Admin@123")
    rooms = client.get("/api/rooms").json()
    room_iet29 = next(r for r in rooms if r["room_number"] == "IET29")
    test_date = (date.today() + timedelta(days=35)).isoformat()

    def make_booking_attempt(req_id: int):
        c = TestClient(app)
        payload = {
            "room_id": room_iet29["id"],
            "title": f"Concurrent Race Request #{req_id}",
            "purpose": "EXTRA_LECTURE",
            "date": test_date,
            "start_time": "17:00",
            "end_time": "18:00",
            "expected_students": 45,
            "is_test_data": True
        }
        resp = c.post(
            "/api/bookings",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        return resp.status_code

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_booking_attempt, i) for i in range(20)]
        for fut in as_completed(futures):
            results.append(fut.result())

    success_count = results.count(200)
    conflict_count = results.count(409)

    assert success_count == 1, f"Expected exactly 1 successful booking under concurrency race, got {success_count} (results: {results})"
    assert conflict_count == 19, f"Expected 19 conflict responses, got {conflict_count}"


# --- TEST 19: Reconciliation Ledger & System Settings ---
def test_19_reconciliation_ledger_and_system_settings():
    admin_token = get_auth_token("admin@ddugu.ac.in", "Admin@123")
    
    # 1. Reconciliation ledger
    ledger_res = client.get("/api/reconciliation/ledger", headers={"Authorization": f"Bearer {admin_token}"})
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert len(ledger_data["table_9_reconciliations"]) == 5
    assert ledger_data["summary"]["total_recorded_spaces"] == 34
    assert ledger_data["summary"]["total_bookable_rooms"] == 30

    # 2. System settings
    settings_res = client.get("/api/reconciliation/settings", headers={"Authorization": f"Bearer {admin_token}"})
    assert settings_res.status_code == 200
    settings = {s["key"]: s["value"] for s in settings_res.json()}
    assert "inter_building_walking_buffer_seconds" in settings
    assert settings["inter_building_walking_buffer_seconds"] == "600"
    assert settings["exam_seating_ratio"] == "0.5"

