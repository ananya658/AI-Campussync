from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime as dt_datetime, date as dt_date, time as dt_time

# --- Authentication & User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # ADMIN, FACULTY, STUDENT
    department: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: dt_datetime
    student_profile: Optional[Dict[str, Any]] = None
    faculty_profile: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Campus Infrastructure Schemas ---
class RoomFacilitySchema(BaseModel):
    id: int
    facility_name: str
    quantity: int
    condition: str

    model_config = ConfigDict(from_attributes=True)

class RoomBase(BaseModel):
    room_number: str
    room_name: str
    room_type: str
    capacity: int
    is_active: bool = True
    is_maintenance: bool = False
    verification_status: str = "OFFICIAL_VERIFIED"
    verification_notes: Optional[str] = None
    permitted_uses: str = "Lectures,Minor Exams,Seminars"
    svg_id: Optional[str] = None

class RoomCreate(RoomBase):
    building_id: int
    floor_id: int

class RoomUpdate(BaseModel):
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_maintenance: Optional[bool] = None
    verification_status: Optional[str] = None
    verification_notes: Optional[str] = None
    permitted_uses: Optional[str] = None

class RoomResponse(RoomBase):
    id: int
    building_id: int
    floor_id: int
    building_name: Optional[str] = None
    building_code: Optional[str] = None
    floor_name: Optional[str] = None
    floor_number: Optional[int] = None
    facilities: List[RoomFacilitySchema] = []
    current_status: Optional[str] = "AVAILABLE"  # AVAILABLE, BOOKED, MAINTENANCE, PENDING_APPROVAL
    active_booking: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class FloorResponse(BaseModel):
    id: int
    building_id: int
    floor_number: int
    floor_name: str
    rooms: List[RoomResponse] = []

    model_config = ConfigDict(from_attributes=True)

class BuildingResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    total_floors: int
    distance_from_iet_meters: int
    is_active: bool
    floors: List[FloorResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Room Availability & Search Schemas ---
class RoomAvailabilityQuery(BaseModel):
    date: dt_date
    start_time: dt_time
    end_time: dt_time
    building_id: Optional[int] = None
    floor_id: Optional[int] = None
    required_capacity: Optional[int] = None
    room_type: Optional[str] = None
    facility_needed: Optional[str] = None

class RoomAvailabilityResult(BaseModel):
    room: RoomResponse
    is_available: bool
    status: str  # AVAILABLE, BOOKED, MAINTENANCE, PENDING_APPROVAL
    conflict_reason: Optional[str] = None
    current_or_next_booking: Optional[Dict[str, Any]] = None

# --- Booking Schemas ---
class BookingCreate(BaseModel):
    room_id: int
    title: str
    purpose: str  # EXTRA_LECTURE, MINOR_EXAM, PRACTICAL_SESSION, SEMINAR, ACADEMIC_EVENT, WORKSHOP, OTHER
    date: dt_date
    start_time: dt_time
    end_time: dt_time
    expected_students: int
    branch_id: Optional[int] = None
    academic_year: Optional[int] = None
    batch_id: Optional[int] = None
    section: Optional[str] = None
    additional_requirements: Optional[str] = None
    is_test_data: bool = True

class BookingCancelRequest(BaseModel):
    reason: str

class BookingStatusUpdateRequest(BaseModel):
    status: str  # CONFIRMED, REJECTED, PENDING_APPROVAL
    reason: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    room_id: int
    user_id: int
    title: str
    purpose: str
    date: dt_date
    start_time: dt_time
    end_time: dt_time
    expected_students: int
    branch_id: Optional[int] = None
    academic_year: Optional[int] = None
    batch_id: Optional[int] = None
    section: Optional[str] = None
    additional_requirements: Optional[str] = None
    status: str
    is_test_data: bool
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[dt_datetime] = None
    created_at: dt_datetime
    room: Optional[RoomResponse] = None
    booked_by_name: Optional[str] = None
    booked_by_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Schedule Schemas ---
class ScheduleCreate(BaseModel):
    room_id: int
    faculty_id: int
    branch_id: int
    academic_year: int
    section: str
    day_of_week: int  # 0=Monday ... 5=Saturday
    start_time: dt_time
    end_time: dt_time
    subject_code: str
    subject_name: str
    schedule_type: str = "LECTURE"

class ScheduleResponse(BaseModel):
    id: int
    room_id: int
    faculty_id: int
    branch_id: int
    academic_year: int
    section: str
    day_of_week: int
    start_time: dt_time
    end_time: dt_time
    subject_code: str
    subject_name: str
    schedule_type: str
    is_active: bool
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    faculty_name: Optional[str] = None
    branch_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Announcement Schemas ---
class AnnouncementCreate(BaseModel):
    title: str
    description: str
    announcement_type: str
    date: Optional[dt_date] = None
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    building_id: Optional[int] = None
    room_id: Optional[int] = None
    target_branch_id: Optional[int] = None
    target_year: Optional[int] = None
    target_batch_id: Optional[int] = None
    target_section: Optional[str] = None
    status: str = "PUBLISHED"

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[dt_date] = None
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    building_id: Optional[int] = None
    room_id: Optional[int] = None
    status: Optional[str] = None
    change_summary: str = "Details updated"

class AnnouncementVersionResponse(BaseModel):
    id: int
    version: int
    title: str
    description: str
    room_id: Optional[int] = None
    date: Optional[dt_date] = None
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    change_summary: str
    modified_by_id: int
    created_at: dt_datetime

    model_config = ConfigDict(from_attributes=True)

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    description: str
    announcement_type: str
    date: Optional[dt_date] = None
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    building_id: Optional[int] = None
    room_id: Optional[int] = None
    building_name: Optional[str] = None
    room_number: Optional[str] = None
    target_branch_id: Optional[int] = None
    target_year: Optional[int] = None
    target_batch_id: Optional[int] = None
    target_section: Optional[str] = None
    created_by_id: int
    creator_name: Optional[str] = None
    status: str
    version: int
    created_at: dt_datetime
    updated_at: dt_datetime
    versions: List[AnnouncementVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Issue Report Schemas ---
class IssueReportCreate(BaseModel):
    category: str  # WRONG_CLASSROOM, INCORRECT_TIMING, CANCELLED_CLASS, INCORRECT_EXAMINATION_INFO, MISSING_ANNOUNCEMENT, OUTDATED_SCHEDULE
    description: str
    building_id: Optional[int] = None
    room_id: Optional[int] = None
    scheduled_date: Optional[dt_date] = None
    scheduled_time: Optional[dt_time] = None

class IssueReportResolve(BaseModel):
    status: str  # RESOLVED, REJECTED
    admin_resolution_note: str

class IssueReportResponse(BaseModel):
    id: int
    student_id: int
    reporter_user_id: int
    reporter_name: Optional[str] = None
    reporter_roll: Optional[str] = None
    category: str
    description: str
    building_id: Optional[int] = None
    room_id: Optional[int] = None
    building_name: Optional[str] = None
    room_number: Optional[str] = None
    scheduled_date: Optional[dt_date] = None
    scheduled_time: Optional[dt_time] = None
    status: str
    admin_resolution_note: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[dt_datetime] = None
    created_at: dt_datetime

    model_config = ConfigDict(from_attributes=True)

# --- Notification Schemas ---
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    link_url: Optional[str] = None
    is_read: bool
    created_at: dt_datetime

    model_config = ConfigDict(from_attributes=True)

# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_role: str
    user_name: Optional[str] = None
    action_type: str
    entity_type: str
    entity_id: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: dt_datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI Schemas ---
class AISearchRequest(BaseModel):
    query: str
    user_role: Optional[str] = "FACULTY"

class AIRecommendationItem(BaseModel):
    room: RoomResponse
    match_score: float  # 0 to 100
    is_available: bool
    explanation: str
    facilities_matched: List[str]
    capacity_difference: int

class AISearchResponse(BaseModel):
    interpreted_query: Dict[str, Any]
    primary_recommendation: Optional[AIRecommendationItem] = None
    alternative_rooms: List[AIRecommendationItem] = []
    alternative_time_slots: List[Dict[str, Any]] = []
    total_matches: int
    raw_ai_explanation: str

# --- Analytics Schemas ---
class AnalyticsSummary(BaseModel):
    total_classrooms: int
    total_laboratories: int
    total_seminar_halls: int
    total_available_now: int
    total_occupied_now: int
    total_active_bookings: int
    upcoming_examinations: int
    pending_booking_requests: int
    pending_student_reports: int
    overall_room_utilization_pct: float
    peak_booking_hours: List[Dict[str, Any]]
    building_wise_utilization: List[Dict[str, Any]]
