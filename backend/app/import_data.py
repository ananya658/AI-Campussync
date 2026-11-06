import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Branch, Batch, Student, User, Building, Floor, Room, RoomFacility
from backend.app.auth import hash_password

def import_students_from_csv(db: Session, csv_path: str) -> int:
    """
    Imports student records from CSV.
    Expected CSV columns:
    roll_number, full_name, email, branch_code, year, section, batch_name, phone
    """
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return 0

    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip().lower()
            roll = row.get("roll_number", "").strip().upper()
            branch_code = row.get("branch_code", "").strip().upper()
            batch_name = row.get("batch_name", "").strip()

            if not email or not roll:
                continue

            # Verify branch and batch
            branch = db.query(Branch).filter(Branch.code == branch_code).first()
            if not branch:
                print(f"Warning: Branch {branch_code} not found for student {roll}. Skipping.")
                continue

            batch = db.query(Batch).filter(Batch.name == batch_name).first()
            if not batch:
                batch = db.query(Batch).first()

            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                continue

            new_user = User(
                email=email,
                hashed_password=hash_password(row.get("password", "Student@123")),
                full_name=row.get("full_name", "Student").strip(),
                role="STUDENT",
                department=branch.name,
                phone=row.get("phone", "").strip(),
                is_active=True
            )
            db.add(new_user)
            db.flush()

            new_student = Student(
                user_id=new_user.id,
                roll_number=roll,
                branch_id=branch.id,
                batch_id=batch.id if batch else 1,
                year=int(row.get("year", 1)),
                section=row.get("section", "A").strip().upper()
            )
            db.add(new_student)
            count += 1

    db.commit()
    return count

def import_rooms_from_json(db: Session, json_path: str) -> int:
    """
    Imports building and room configurations from JSON structure.
    """
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return 0

    with open(json_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    buildings_data = data.get("buildings", [])
    for b_data in buildings_data:
        building = db.query(Building).filter(Building.code == b_data["code"]).first()
        if not building:
            building = Building(
                name=b_data["name"],
                code=b_data["code"],
                description=b_data.get("description", ""),
                total_floors=b_data.get("total_floors", 3),
                distance_from_iet_meters=b_data.get("distance_from_iet_meters", 0)
            )
            db.add(building)
            db.flush()

        for f_data in b_data.get("floors", []):
            floor = db.query(Floor).filter(
                Floor.building_id == building.id,
                Floor.floor_number == f_data["floor_number"]
            ).first()
            if not floor:
                floor = Floor(
                    building_id=building.id,
                    floor_number=f_data["floor_number"],
                    floor_name=f_data["floor_name"]
                )
                db.add(floor)
                db.flush()

            for r_data in f_data.get("rooms", []):
                existing_room = db.query(Room).filter(
                    Room.building_id == building.id,
                    Room.room_number == r_data["room_number"]
                ).first()
                if not existing_room:
                    new_room = Room(
                        building_id=building.id,
                        floor_id=floor.id,
                        room_number=r_data["room_number"],
                        room_name=r_data["room_name"],
                        room_type=r_data.get("room_type", "LECTURE_HALL"),
                        capacity=r_data.get("capacity", 75),
                        permitted_uses=r_data.get("permitted_uses", "Lectures,Minor Exams"),
                        verification_status=r_data.get("verification_status", "OFFICIAL_VERIFIED"),
                        verification_notes=r_data.get("verification_notes", None),
                        svg_id=r_data.get("svg_id", None)
                    )
                    db.add(new_room)
                    count += 1

    db.commit()
    return count

if __name__ == "__main__":
    db = SessionLocal()
    print("DDUGU Campus Data Import Utility Ready.")
    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        path = sys.argv[2]
        if cmd == "students":
            c = import_students_from_csv(db, path)
            print(f"Successfully imported {c} student records.")
        elif cmd == "rooms":
            c = import_rooms_from_json(db, path)
            print(f"Successfully imported {c} room records.")
    else:
        print("Usage:")
        print("  python -m backend.app.import_data students <path_to_csv>")
        print("  python -m backend.app.import_data rooms <path_to_json>")
    db.close()
