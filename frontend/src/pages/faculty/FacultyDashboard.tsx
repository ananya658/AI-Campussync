import React, { useState, useEffect } from 'react';
import { Schedule, Booking, Announcement } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  Calendar, Clock, Search, Sparkles, MapPin, 
  ArrowRight, BookOpen, Megaphone, CheckCircle2 
} from 'lucide-react';

interface FacultyDashboardProps {
  onNavigate: (view: string) => void;
  onBookRoomPrefill?: (roomId: number) => void;
}

export const FacultyDashboard: React.FC<FacultyDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [todayClasses, setTodayClasses] = useState<Schedule[]>([]);
  const [myBookings, setMyBookings] = useState<Booking[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [sched, bookings, notifs] = await Promise.all([
          api.getMySchedule(),
          api.getBookings({ my_bookings_only: true }),
          api.getAnnouncements(),
        ]);
        // Filter classes for today's day of week
        const todayDow = (new Date().getDay() + 6) % 7; // Convert Sun=0..Sat=6 to Mon=0..Sat=5
        const todays = sched.filter((s) => s.day_of_week === todayDow);
        setTodayClasses(todays.length > 0 ? todays : sched.slice(0, 3));
        setMyBookings(bookings.slice(0, 4));
        setAnnouncements(notifs.slice(0, 3));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Faculty Academic Portal • DDUGU
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome, {user?.full_name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
            {user?.faculty_profile?.designation} • {user?.department}. Manage classrooms, check timetable schedules, and allocate lecture halls with automated conflict detection.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => onNavigate('room-finder')}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/25 flex items-center gap-1.5 transition-all"
          >
            <Search className="w-4 h-4" /> Smart Room Finder
          </button>

          <button
            onClick={() => onNavigate('ai-assistant')}
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs border border-white/20 backdrop-blur-sm flex items-center gap-1.5 transition-all"
          >
            <Sparkles className="w-4 h-4 text-indigo-400" /> AI Assistant
          </button>
        </div>
      </div>

      {/* Two Column Grid: Today's Classes & My Bookings */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Today's Teaching Schedule */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" /> Today's Teaching Schedule
            </h3>
            <button
              onClick={() => onNavigate('faculty-schedule')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
            >
              Full Timetable →
            </button>
          </div>

          <div className="space-y-3">
            {todayClasses.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No scheduled lectures for today.
              </div>
            ) : (
              todayClasses.map((c) => (
                <div
                  key={c.id}
                  className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="font-bold text-xs text-slate-900">
                      {c.subject_code} - {c.subject_name}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                      <span className="font-semibold text-blue-700">Room {c.room_number}</span>
                      <span>•</span>
                      <span>Yr {c.academic_year} Sec {c.section}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-800 font-bold text-xs font-mono">
                      {c.start_time.slice(0, 5)} - {c.end_time.slice(0, 5)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* My Reservations */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-600" /> My Classroom Bookings
            </h3>
            <button
              onClick={() => onNavigate('create-booking')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
            >
              + New Booking
            </button>
          </div>

          <div className="space-y-3">
            {myBookings.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                You haven't reserved any classrooms yet.
              </div>
            ) : (
              myBookings.map((b) => (
                <div
                  key={b.id}
                  className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="font-bold text-xs text-slate-900">{b.title}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                      <span className="font-semibold text-indigo-700">Room {b.room?.room_number}</span>
                      <span>•</span>
                      <span>{b.date} ({b.start_time.slice(0, 5)} - {b.end_time.slice(0, 5)})</span>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      b.status === 'CONFIRMED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : b.status === 'CANCELLED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {b.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
