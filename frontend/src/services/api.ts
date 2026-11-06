import { 
  User, Building, Branch, AcademicSection, Floor, Room, Booking, Schedule, Announcement,
  IssueReport, NotificationItem, AuditLogItem, AISearchResponse, AnalyticsSummary 
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface BookingAlternative {
  room_id: number;
  room_number: string;
  building_id: number;
  building_name: string;
  capacity: number;
  reason: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  alternatives: BookingAlternative[];

  constructor(message: string, status: number, code?: string, alternatives: BookingAlternative[] = []) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.alternatives = alternatives;
  }
}

function buildUrl(path: string): URL {
  if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
    const cleanBase = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
    const cleanPath = path.startsWith('/') ? path : '/' + path;
    return new URL(`${cleanBase}${cleanPath}`);
  }
  return new URL(`${window.location.origin}${API_BASE}${path.startsWith('/') ? path : '/' + path}`);
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('campussync_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errJson: any;
    try {
      errJson = await res.json();
    } catch {
      throw new ApiError('An unexpected error occurred', res.status);
    }

    const detail = errJson.detail;
    if (detail && typeof detail === 'object') {
      throw new ApiError(
        detail.message || errJson.message || 'An unexpected error occurred',
        res.status,
        detail.code,
        Array.isArray(detail.alternatives) ? detail.alternatives : [],
      );
    }
    throw new ApiError(
      typeof detail === 'string' ? detail : errJson.message || JSON.stringify(errJson),
      res.status,
    );
  }
  return res.json();
}

export const api = {
  // --- Auth ---
  login: async (email: string, password: string): Promise<{ access_token: string; user: User }> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(res);
  },

  getMe: async (): Promise<User> => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Buildings & Rooms ---
  getBuildings: async (): Promise<Building[]> => {
    const res = await fetch(`${API_BASE}/buildings`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  getBranches: async (): Promise<Branch[]> => {
    const res = await fetch(`${API_BASE}/branches`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  getSections: async (branchId: number, academicYear: number): Promise<AcademicSection[]> => {
    const url = buildUrl('/branches/sections');
    url.searchParams.set('branch_id', String(branchId));
    url.searchParams.set('academic_year', String(academicYear));
    const res = await fetch(url.toString(), { headers: { ...getAuthHeader() } });
    return handleResponse(res);
  },

  getRooms: async (params?: {
    building_id?: number;
    floor_id?: number;
    room_type?: string;
    target_date?: string;
    target_time?: string;
  }): Promise<Room[]> => {
    const url = buildUrl('/rooms');
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  queryRoomAvailability: async (params: {
    booking_date: string;
    start_time: string;
    end_time: string;
    building_id?: number;
    floor_id?: number;
    required_capacity?: number;
    room_type?: string;
    facility_needed?: string;
    purpose?: string;
  }): Promise<Array<{ room: Room; is_available: boolean; status: string; conflict_reason?: string }>> => {
    const url = buildUrl('/rooms/availability');
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.append(k, String(v));
      }
    });
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  updateRoom: async (roomId: number, data: Partial<Room>): Promise<Room> => {
    const res = await fetch(`${API_BASE}/rooms/${roomId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  verifyRoomDiscrepancy: async (roomId: number, verified_status: string, admin_notes?: string): Promise<Room> => {
    const url = buildUrl(`/rooms/${roomId}/verify`);
    url.searchParams.append('verified_status', verified_status);
    if (admin_notes) url.searchParams.append('admin_notes', admin_notes);

    const res = await fetch(url.toString(), {
      method: 'POST',
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Bookings ---
  getBookings: async (params?: {
    status?: string;
    date?: string;
    building_id?: number;
    is_test_data?: boolean;
    my_bookings_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<Booking[]> => {
    const url = buildUrl('/bookings');
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  createBooking: async (data: {
    room_id: number;
    title: string;
    purpose: string;
    date: string;
    start_time: string;
    end_time: string;
    expected_students: number;
    branch_id?: number;
    academic_year?: number;
    batch_id?: number;
    section?: string;
    additional_requirements?: string;
    is_test_data?: boolean;
  }): Promise<Booking> => {
    const res = await fetch(`${API_BASE}/bookings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  cancelBooking: async (bookingId: number, reason: string): Promise<Booking> => {
    const res = await fetch(`${API_BASE}/bookings/${bookingId}/cancel`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({ reason }),
    });
    return handleResponse(res);
  },

  updateBookingStatus: async (bookingId: number, status: string, reason?: string): Promise<Booking> => {
    const res = await fetch(`${API_BASE}/bookings/${bookingId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({ status, reason }),
    });
    return handleResponse(res);
  },

  // --- Schedules ---
  getMySchedule: async (): Promise<Schedule[]> => {
    const res = await fetch(`${API_BASE}/schedules/me`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  getAllSchedules: async (params?: {
    branch_id?: number;
    academic_year?: number;
    section?: string;
    day_of_week?: number;
  }): Promise<Schedule[]> => {
    const url = new URL(`${window.location.origin}${API_BASE}/schedules`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  updateSchedule: async (scheduleId: number, data: Partial<Schedule>): Promise<Schedule> => {
    const res = await fetch(`${API_BASE}/schedules/${scheduleId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  cancelSchedule: async (scheduleId: number, reason: string): Promise<{ message: string; schedule_id: number }> => {
    const url = buildUrl(`/schedules/${scheduleId}`);
    url.searchParams.set('reason', reason);
    const res = await fetch(url.toString(), {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Announcements ---
  getAnnouncements: async (typeFilter?: string): Promise<Announcement[]> => {
    const url = new URL(`${window.location.origin}${API_BASE}/announcements`);
    if (typeFilter) url.searchParams.append('type', typeFilter);
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  createAnnouncement: async (data: any): Promise<Announcement> => {
    const res = await fetch(`${API_BASE}/announcements`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  updateAnnouncement: async (id: number, data: any): Promise<Announcement> => {
    const res = await fetch(`${API_BASE}/announcements/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  // --- Reports ---
  getReports: async (statusFilter?: string): Promise<IssueReport[]> => {
    const url = new URL(`${window.location.origin}${API_BASE}/reports`);
    if (statusFilter) url.searchParams.append('status', statusFilter);
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  createReport: async (data: {
    category: string;
    description: string;
    building_id?: number;
    room_id?: number;
    scheduled_date?: string;
    scheduled_time?: string;
  }): Promise<IssueReport> => {
    const res = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  resolveReport: async (id: number, status: string, admin_resolution_note: string): Promise<IssueReport> => {
    const res = await fetch(`${API_BASE}/reports/${id}/resolve`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({ status, admin_resolution_note }),
    });
    return handleResponse(res);
  },

  // --- Notifications ---
  getNotifications: async (): Promise<NotificationItem[]> => {
    const res = await fetch(`${API_BASE}/notifications`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  markNotificationRead: async (id: number): Promise<NotificationItem> => {
    const res = await fetch(`${API_BASE}/notifications/${id}/read`, {
      method: 'PATCH',
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  markAllNotificationsRead: async (): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/notifications/read-all`, {
      method: 'PATCH',
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- AI Smart Assistant ---
  aiSearch: async (query: string): Promise<AISearchResponse> => {
    const res = await fetch(`${API_BASE}/ai/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({ query }),
    });
    return handleResponse(res);
  },

  // --- Audit Logs ---
  getAuditLogs: async (params?: { entity_type?: string; action_type?: string; limit?: number }): Promise<AuditLogItem[]> => {
    const url = buildUrl('/audit-logs');
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Analytics ---
  getAnalytics: async (): Promise<AnalyticsSummary> => {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Split Sitting (Hackathon Advanced Scheduling) ---
  getSplitPlan: async (params: {
    building_id: number;
    total_candidates: number;
    date: string;
    start_time: string;
    end_time: string;
  }): Promise<{
    strategy: string;
    total_candidates: number;
    room_1: { id: number; room_number: string; exam_capacity: number; building_id: number };
    room_2: { id: number; room_number: string; exam_capacity: number; building_id: number };
    total_exam_seats: number;
    notes: string;
  }> => {
    const url = buildUrl('/bookings/split-plan');
    Object.entries(params).forEach(([k, v]) => {
      url.searchParams.append(k, String(v));
    });
    const res = await fetch(url.toString(), {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  createSplitBooking: async (data: {
    booking_1: any;
    booking_2: any;
  }): Promise<{
    message: string;
    booking_1: Booking;
    booking_2: Booking;
  }> => {
    const res = await fetch(`${API_BASE}/bookings/split-booking`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  // --- Generic HTTP Methods for Dynamic & Reconciliation Endpoints ---
  get: async <T = any>(endpoint: string, _config?: any): Promise<{ data: T }> => {
    const cleanPath = endpoint.startsWith('http') ? endpoint : (endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`);
    const res = await fetch(cleanPath, {
      headers: { ...getAuthHeader() },
    });
    const data = await handleResponse<T>(res);
    return { data };
  },

  post: async <T = any>(endpoint: string, body?: any, _config?: any): Promise<{ data: T }> => {
    const cleanPath = endpoint.startsWith('http') ? endpoint : (endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`);
    const headers: Record<string, string> = { ...getAuthHeader() };
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(cleanPath, {
      method: 'POST',
      headers,
      body: isFormData ? body : JSON.stringify(body),
    });
    const data = await handleResponse<T>(res);
    return { data };
  },

  put: async <T = any>(endpoint: string, body?: any, _config?: any): Promise<{ data: T }> => {
    const cleanPath = endpoint.startsWith('http') ? endpoint : (endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`);
    const res = await fetch(cleanPath, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(body),
    });
    const data = await handleResponse<T>(res);
    return { data };
  },

  delete: async <T = any>(endpoint: string, _config?: any): Promise<{ data: T }> => {
    const cleanPath = endpoint.startsWith('http') ? endpoint : (endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`);
    const res = await fetch(cleanPath, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    const data = await handleResponse<T>(res);
    return { data };
  },
};

export default api;

