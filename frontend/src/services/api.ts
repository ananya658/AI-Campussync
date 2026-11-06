import { 
  User, Building, Floor, Room, Booking, Schedule, Announcement, 
  IssueReport, NotificationItem, AuditLogItem, AISearchResponse, AnalyticsSummary 
} from '../types';

const API_BASE = '/api';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('campussync_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
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

  getRooms: async (params?: {
    building_id?: number;
    floor_id?: number;
    room_type?: string;
    target_date?: string;
    target_time?: string;
  }): Promise<Room[]> => {
    const url = new URL(`${window.location.origin}${API_BASE}/rooms`);
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
  }): Promise<Array<{ room: Room; is_available: boolean; status: string; conflict_reason?: string }>> => {
    const url = new URL(`${window.location.origin}${API_BASE}/rooms/availability`);
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
    const url = new URL(`${window.location.origin}${API_BASE}/rooms/${roomId}/verify`);
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
  }): Promise<Booking[]> => {
    const url = new URL(`${window.location.origin}${API_BASE}/bookings`);
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
    const url = new URL(`${window.location.origin}${API_BASE}/audit-logs`);
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
};
