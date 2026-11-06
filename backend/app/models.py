from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, Time, DateTime, 
    ForeignKey, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # ADMIN, FACULTY, STUDENT
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", foreign_keys="Booking.user_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    created_announcements = relationship("Announcement", back_populates="creator", foreign_keys="Announcement.created_by_id")
    audit_logs = relationship("AuditLog", back_populates="user")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # CSE, AIML, AIDS, ECE, ME, IT
    name = Column(String(255), nullable=False)
    total_capacity = Column(Integer, default=75)
    description = Column(String(255), nullable=True)

    students = relationship("Student", back_populates="branch")
    schedules = relationship("Schedule", back_populates="branch")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # e.g., "2023-2027"
    academic_year = Column(String(50), nullable=False)  # e.g., "2025-2026"
    is_active = Column(Boolean, default=True)

    students = relationship("Student", back_populates="batch")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    year = Column(Integer, nullable=False)  # 1, 2, 3, 4
    section = Column(String(5), nullable=False)  # A, B

    user = relationship("User", back_populates="student_profile")
    branch = relationship("Branch", back_populates="students")
    batch = relationship("Batch", back_populates="students")
    issue_reports = relationship("IssueReport", back_populates="student", cascade="all, delete-orphan")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    designation = Column(String(100), nullable=False)  # Professor, Associate Prof, Assistant Prof
    department = Column(String(100), nullable=False)
    cabin_room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    user = relationship("User", back_populates="faculty_profile")
    cabin = relationship("Room", foreign_keys=[cabin_room_id])
    schedules = relationship("Schedule", back_populates="faculty")


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # IET, DB
    description = Column(Text, nullable=True)
    total_floors = Column(Integer, default=3)
    distance_from_iet_meters = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    floors = relationship("Floor", back_populates="building", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_number = Column(Integer, nullable=False)  # 0=Ground, 1=First, 2=Second
    floor_name = Column(String(50), nullable=False)  # "Ground Floor", "First Floor", "Second Floor"

    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(50), nullable=False)  # e.g. "IET17", "IET18", "LH01", "LH13"
    room_name = Column(String(255), nullable=False)  # e.g. "Classroom IET17", "CSE Laboratory"
    room_type = Column(String(50), nullable=False)  # LECTURE_HALL, LAB, SEMINAR_HALL, OFFICE, LIBRARY
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    is_maintenance = Column(Boolean, default=False)
    
    # Official vs discrepancy verification (critical for Deeksha Bhawan LH13/LH14)
    verification_status = Column(String(50), default="OFFICIAL_VERIFIED")  # OFFICIAL_VERIFIED, PENDING_ADMIN_VERIFICATION, RESTRICTED
    verification_notes = Column(Text, nullable=True)
    
    permitted_uses = Column(Text, default="Lectures,Minor Exams,Seminars")
    svg_id = Column(String(100), nullable=True)  # Matches SVG element id in interactive map

    building = relationship("Building", back_populates="rooms")
    floor = relationship("Floor", back_populates="rooms")
    facilities = relationship("RoomFacility", back_populates="room", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="room")
    schedules = relationship("Schedule", back_populates="room")

    __table_args__ = (
        UniqueConstraint("building_id", "room_number", name="uq_building_room_number"),
    )


class RoomFacility(Base):
    __tablename__ = "room_facilities"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    facility_name = Column(String(100), nullable=False)  # PROJECTOR, SMART_BOARD, AC, LAB_COMPUTERS, AUDIO_SYSTEM, HIGH_SPEED_WIFI
    quantity = Column(Integer, default=1)
    condition = Column(String(50), default="EXCELLENT")

    room = relationship("Room", back_populates="facilities")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)  # CS-2026-XXXX
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)  # EXTRA_LECTURE, MINOR_EXAM, PRACTICAL_SESSION, SEMINAR, ACADEMIC_EVENT, WORKSHOP, OTHER
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    expected_students = Column(Integer, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    academic_year = Column(Integer, nullable=True)  # 1, 2, 3, 4
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    section = Column(String(10), nullable=True)
    additional_requirements = Column(Text, nullable=True)
    
    status = Column(String(50), default="CONFIRMED", index=True)  # CONFIRMED, PENDING_APPROVAL, CANCELLED, REJECTED, COMPLETED
    is_test_data = Column(Boolean, default=True)  # Flag demo data vs official records
    
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    room = relationship("Room", back_populates="bookings")
    user = relationship("User", back_populates="bookings", foreign_keys=[user_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    branch = relationship("Branch")
    batch = relationship("Batch")

    __table_args__ = (
        Index("idx_booking_room_date_status", "room_id", "date", "status"),
    )


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    academic_year = Column(Integer, nullable=False)  # 1, 2, 3, 4
    section = Column(String(5), nullable=False)  # A, B
    
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    subject_code = Column(String(50), nullable=False)
    subject_name = Column(String(255), nullable=False)
    schedule_type = Column(String(50), default="LECTURE")  # LECTURE, LAB, TUTORIAL
    is_active = Column(Boolean, default=True)

    room = relationship("Room", back_populates="schedules")
    faculty = relationship("Faculty", back_populates="schedules")
    branch = relationship("Branch", back_populates="schedules")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    announcement_type = Column(String(50), nullable=False)  # MINOR_EXAM, MAJOR_EXAM, EXTRA_LECTURE, PRACTICAL_EXAM, SCHEDULE_CHANGE, CLASS_CANCELLATION, ACADEMIC_EVENT, IMPORTANT_NOTICE
    
    date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    
    target_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    target_year = Column(Integer, nullable=True)
    target_batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    target_section = Column(String(10), nullable=True)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="PUBLISHED")  # PUBLISHED, ARCHIVED, DRAFT
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_announcements", foreign_keys=[created_by_id])
    building = relationship("Building")
    room = relationship("Room")
    target_branch = relationship("Branch")
    versions = relationship("AnnouncementVersion", back_populates="announcement", cascade="all, delete-orphan", order_by="desc(AnnouncementVersion.version)")


class AnnouncementVersion(Base):
    __tablename__ = "announcement_versions"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    change_summary = Column(Text, nullable=False)
    modified_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    announcement = relationship("Announcement", back_populates="versions")
    modified_by = relationship("User")
    room = relationship("Room")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # BOOKING_CONFIRMED, BOOKING_CANCELLED, ROOM_CHANGED, EXAM_SCHEDULE_CHANGED, ANNOUNCEMENT, REPORT_RESOLVED
    link_url = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    reporter_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # WRONG_CLASSROOM, INCORRECT_TIMING, CANCELLED_CLASS, INCORRECT_EXAMINATION_INFO, MISSING_ANNOUNCEMENT, OUTDATED_SCHEDULE
    description = Column(Text, nullable=False)
    
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    scheduled_date = Column(Date, nullable=True)
    scheduled_time = Column(Time, nullable=True)
    
    status = Column(String(50), default="PENDING")  # PENDING, UNDER_REVIEW, RESOLVED, REJECTED
    admin_resolution_note = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="issue_reports")
    reporter = relationship("User", foreign_keys=[reporter_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    building = relationship("Building")
    room = relationship("Room")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_role = Column(String(50), nullable=False)
    user_name = Column(String(255), nullable=True)
    action_type = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, CANCEL, APPROVE, REJECT, RESOLVE
    entity_type = Column(String(50), nullable=False)  # BOOKING, SCHEDULE, ANNOUNCEMENT, ROOM, REPORT, USER
    entity_id = Column(String(50), nullable=False)
    previous_value = Column(Text, nullable=True)  # JSON or text snapshot
    new_value = Column(Text, nullable=True)       # JSON or text snapshot
    reason = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

