export type UserRole = 'ADMIN' | 'FACULTY' | 'STUDENT';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  phone?: string;
  is_active: boolean;
  student_profile?: {
    id: number;
    roll_number: string;
    branch_id: number;
    branch_code: string;
    branch_name: string;
    batch_id: number;
    year: number;
    section: string;
  } | null;
  faculty_profile?: {
    id: number;
    employee_code: string;
    designation: string;
    department: string;
    cabin_room_id?: number;
  } | null;
}

export interface RoomFacility {
  id: number;
  facility_name: string;
  quantity: number;
  condition: string;
}

export type RoomStatus = 'AVAILABLE' | 'BOOKED' | 'MAINTENANCE' | 'PENDING_APPROVAL' | 'SELECTED';

export interface Room {
  id: number;
  building_id: number;
  floor_id: number;
  room_number: string;
  room_name: string;
  room_type: 'LECTURE_HALL' | 'LAB' | 'SEMINAR_HALL' | 'OFFICE' | 'LIBRARY';
  capacity: number;
  is_active: boolean;
  is_maintenance: boolean;
  verification_status: 'OFFICIAL_VERIFIED' | 'PENDING_ADMIN_VERIFICATION' | 'RESTRICTED';
  verification_notes?: string;
  permitted_uses: string;
  svg_id?: string;
  building_name?: string;
  building_code?: string;
  floor_name?: string;
  floor_number?: number;
  facilities: RoomFacility[];
  current_status?: RoomStatus;
  active_booking?: {
    booking_ref?: string;
    title: string;
    purpose: string;
    start: string;
    end: string;
  } | null;
}

export interface Floor {
  id: number;
  building_id: number;
  floor_number: number;
  floor_name: string;
  rooms: Room[];
}

export interface Building {
  id: number;
  name: string;
  code: string;
  description?: string;
  total_floors: number;
  distance_from_iet_meters: number;
  is_active: boolean;
  floors: Floor[];
}

export interface Booking {
  id: number;
  booking_reference: string;
  room_id: number;
  user_id: number;
  title: string;
  purpose: 'EXTRA_LECTURE' | 'MINOR_EXAM' | 'PRACTICAL_SESSION' | 'SEMINAR' | 'ACADEMIC_EVENT' | 'WORKSHOP' | 'OTHER';
  date: string;
  start_time: string;
  end_time: string;
  expected_students: number;
  branch_id?: number;
  academic_year?: number;
  batch_id?: number;
  section?: string;
  additional_requirements?: string;
  status: 'CONFIRMED' | 'PENDING_APPROVAL' | 'CANCELLED' | 'REJECTED' | 'COMPLETED';
  is_test_data: boolean;
  cancellation_reason?: string;
  cancelled_at?: string;
  created_at: string;
  room?: Room;
  booked_by_name?: string;
  booked_by_email?: string;
}

export interface Schedule {
  id: number;
  room_id: number;
  faculty_id: number;
  branch_id: number;
  academic_year: number;
  section: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  subject_code: string;
  subject_name: string;
  schedule_type: string;
  is_active: boolean;
  room_number?: string;
  building_name?: string;
  faculty_name?: string;
  branch_code?: string;
}

export interface AnnouncementVersion {
  id: number;
  version: number;
  title: string;
  description: string;
  room_id?: number;
  date?: string;
  start_time?: string;
  end_time?: string;
  change_summary: string;
  modified_by_id: number;
  created_at: string;
}

export interface Announcement {
  id: number;
  title: string;
  description: string;
  announcement_type: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  building_id?: number;
  room_id?: number;
  building_name?: string;
  room_number?: string;
  target_branch_id?: number;
  target_year?: number;
  target_batch_id?: number;
  target_section?: string;
  created_by_id: number;
  creator_name?: string;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
  versions: AnnouncementVersion[];
}

export interface IssueReport {
  id: number;
  student_id: number;
  reporter_user_id: number;
  reporter_name?: string;
  reporter_roll?: string;
  category: string;
  description: string;
  building_id?: number;
  room_id?: number;
  building_name?: string;
  room_number?: string;
  scheduled_date?: string;
  scheduled_time?: string;
  status: 'PENDING' | 'UNDER_REVIEW' | 'RESOLVED' | 'REJECTED';
  admin_resolution_note?: string;
  resolved_by_id?: number;
  resolved_by_name?: string;
  resolved_at?: string;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: string;
  link_url?: string;
  is_read: boolean;
  created_at: string;
}

export interface AuditLogItem {
  id: number;
  user_id?: number;
  user_role: string;
  user_name?: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  previous_value?: string;
  new_value?: string;
  reason?: string;
  ip_address?: string;
  created_at: string;
}

export interface AIRecommendationItem {
  room: Room;
  match_score: number;
  is_available: boolean;
  explanation: string;
  facilities_matched: string[];
  capacity_difference: number;
}

export interface AISearchResponse {
  interpreted_query: {
    date: string;
    start_time: string;
    end_time: string;
    required_capacity: number;
    building: string;
    room_type: string;
    facility_needed: string;
    purpose: string;
  };
  primary_recommendation?: AIRecommendationItem;
  alternative_rooms: AIRecommendationItem[];
  alternative_time_slots: Array<{
    room_number: string;
    building_name: string;
    date: string;
    start_time: string;
    end_time: string;
    capacity: number;
    label: string;
  }>;
  total_matches: number;
  raw_ai_explanation: string;
}

export interface AnalyticsSummary {
  total_classrooms: number;
  total_laboratories: number;
  total_seminar_halls: number;
  total_available_now: number;
  total_occupied_now: number;
  total_active_bookings: number;
  upcoming_examinations: number;
  pending_booking_requests: number;
  pending_student_reports: number;
  overall_room_utilization_pct: number;
  peak_booking_hours: Array<{ hour: string; bookings: number; label: string }>;
  building_wise_utilization: Array<{
    building_id: number;
    building_name: string;
    building_code: string;
    total_rooms: number;
    occupied_rooms: number;
    utilization_pct: number;
  }>;
}

