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
    db = next(get_db())
    db.query(Booking).filter(
        Booking.title.in_([
            "Automated Unit Test Lecture",
            "Overlapping Conflicting Lecture",
            "Session to be Cancelled",
            "Replacement Session in Freed Slot"
        ])
    ).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(Booking).filter(
        Booking.title.in_([
            "Automated Unit Test Lecture",
            "Overlapping Conflicting Lecture",
            "Session to be Cancelled",
            "Replacement Session in Freed Slot"
        ])
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
        "start_time": "14:00",
        "end_time": "15:00",
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

    # Step 1: Create initial booking from 14:00 to 15:00
    first_resp = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet24["id"],
            "title": "Automated Unit Test Lecture",
            "purpose": "EXTRA_LECTURE",
            "date": booking_date,
            "start_time": "14:00",
            "end_time": "15:00",
            "expected_students": 50,
            "is_test_data": True
        },
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert first_resp.status_code == 200

    # Step 2: An overlapping request from 14:30 to 15:30 MUST be rejected with 409 Conflict!
    overlap_payload = {
        "room_id": room_iet24["id"],
        "title": "Overlapping Conflicting Lecture",
        "purpose": "EXTRA_LECTURE",
        "date": booking_date,
        "start_time": "14:30",
        "end_time": "15:30",
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

    # Step 1: Book slot 10:00 - 11:00
    create_res = client.post(
        "/api/bookings",
        json={
            "room_id": room_iet28["id"],
            "title": "Session to be Cancelled",
            "purpose": "EXTRA_LECTURE",
            "date": booking_date,
            "start_time": "10:00",
            "end_time": "11:00",
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
            "start_time": "10:00",
            "end_time": "11:00",
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
