import React, { useState, useEffect } from 'react';
import { Schedule, Announcement, IssueReport } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  GraduationCap, Clock, Calendar, AlertCircle, Megaphone, 
  MapPin, CheckCircle2, ArrowRight, ShieldAlert 
} from 'lucide-react';

interface StudentDashboardProps {
  onNavigate: (view: string) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [myReports, setMyReports] = useState<IssueReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [sched, ann, reports] = await Promise.all([
          api.getMySchedule(),
          api.getAnnouncements(),
          api.getReports(),
        ]);
        setSchedules(sched);
        setAnnouncements(ann.slice(0, 4));
        setMyReports(reports.slice(0, 3));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const todayDow = (new Date().getDay() + 6) % 7;
  const todayClasses = schedules.filter((s) => s.day_of_week === todayDow);
  const displayClasses = todayClasses.length > 0 ? todayClasses : schedules.slice(0, 4);

  // Find upcoming exam announcements
  const upcomingExams = announcements.filter((a) =>
    a.announcement_type.includes('EXAM')
  );

  return (
    <div className="space-y-6">
      {/* Student Profile Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
            <GraduationCap className="w-3.5 h-3.5 text-emerald-400" />
            Verified Student Profile • DDUGU
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome, {user?.full_name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
            Roll No: <strong>{user?.student_profile?.roll_number}</strong> • Branch: <strong>{user?.student_profile?.branch_name} ({user?.student_profile?.branch_code})</strong> • Year: <strong>{user?.student_profile?.year}</strong> • Section: <strong>{user?.student_profile?.section}</strong>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => onNavigate('student-timetable')}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/25 flex items-center gap-1.5 transition-all"
          >
            <Clock className="w-4 h-4" /> Weekly Timetable
          </button>

          <button
            onClick={() => onNavigate('student-report')}
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs border border-white/20 backdrop-blur-sm flex items-center gap-1.5 transition-all"
          >
            <AlertCircle className="w-4 h-4 text-amber-400" /> Report Discrepancy
          </button>
        </div>
      </div>

      {/* Two Column Grid: Today's Classes & Upcoming Examinations */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Today's Lectures */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" /> Today's Lectures & Labs
            </h3>
            <button
              onClick={() => onNavigate('student-timetable')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              Full Schedule <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {displayClasses.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No classes scheduled for today.
              </div>
            ) : (
              displayClasses.map((c) => (
                <div
                  key={c.id}
                  className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="font-bold text-xs text-slate-900">
                      {c.subject_code} - {c.subject_name}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-2">
                      <span className="font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Room {c.room_number} ({c.building_name})
                      </span>
                      <span>Faculty: {c.faculty_name}</span>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-lg bg-slate-200 text-slate-800 font-mono font-bold text-xs">
                    {c.start_time.slice(0, 5)} - {c.end_time.slice(0, 5)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Upcoming Examinations Allotments */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-600" /> Upcoming Examinations & Hall Tickets
            </h3>
            <button
              onClick={() => onNavigate('student-exams')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              All Exams <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {upcomingExams.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No active examination rosters published yet.
              </div>
            ) : (
              upcomingExams.map((exam) => (
                <div
                  key={exam.id}
                  className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-200/80 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="font-bold text-xs text-slate-900">{exam.title}</div>
                    <div className="text-[11px] text-indigo-900 mt-1 flex items-center gap-2">
                      {exam.room_number && (
                        <span className="font-bold bg-white px-2 py-0.5 rounded border border-indigo-200">
                          Venue: Room {exam.room_number} ({exam.building_name})
                        </span>
                      )}
                      {exam.date && <span>Date: {exam.date}</span>}
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-indigo-600 text-white">
                    v{exam.version}.0 Official
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Campus Announcements */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
          <Megaphone className="w-4 h-4 text-blue-600" /> Official Circulars & Notices
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {announcements.map((a) => (
            <div key={a.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-100 text-blue-800">
                {a.announcement_type.replace(/_/g, ' ')}
              </span>
              <div className="font-bold text-slate-900 mt-1">{a.title}</div>
              <p className="text-slate-600 mt-1 line-clamp-2 leading-relaxed">{a.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

