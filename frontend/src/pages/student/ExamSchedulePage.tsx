import React, { useState, useEffect } from 'react';
import { Announcement } from '../../types';
import { api } from '../../services/api';
import { CheckSquare, Calendar, Clock, MapPin, AlertCircle, ShieldCheck } from 'lucide-react';

export const ExamSchedulePage: React.FC = () => {
  const [exams, setExams] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getAnnouncements();
        // Filter examination-related notices
        const examNotices = data.filter((a) =>
          a.announcement_type.includes('EXAM')
        );
        setExams(examNotices);
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
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Examination Hall Tickets & Room Allocations
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Official seating arrangements for Minor and Major Semester Examinations across IET and Deeksha Bhawan.
        </p>
      </div>

      <div className="space-y-4">
        {exams.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-xs text-slate-400">
            No active examination schedules currently published for your batch.
          </div>
        ) : (
          exams.map((exam) => (
            <div
              key={exam.id}
              className="p-6 rounded-3xl bg-white border border-indigo-200 shadow-md space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800 border border-indigo-200">
                    {exam.announcement_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    Official Sitting (v{exam.version}.0)
                  </span>
                </div>
                <span className="text-xs text-slate-400 font-mono">
                  Ref: EXAM-{exam.id}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900">{exam.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                  {exam.description}
                </p>
              </div>

              {/* Venue & Timing Grid */}
              <div className="grid sm:grid-cols-3 gap-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">
                    Assigned Room
                  </div>
                  <div className="font-extrabold text-base text-blue-700 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-blue-600" />
                    {exam.room_number ? `Room ${exam.room_number}` : 'Central Lecture Complex'}
                  </div>
                  <div className="text-[11px] text-slate-500">{exam.building_name}</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">
                    Exam Date
                  </div>
                  <div className="font-bold text-slate-900 flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-slate-500" />
                    {exam.date || 'TBA'}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">
                    Sitting Time
                  </div>
                  <div className="font-bold text-slate-900 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-slate-500" />
                    {exam.start_time ? `${exam.start_time.slice(0, 5)} - ${exam.end_time?.slice(0, 5)}` : 'As per schedule'}
                  </div>
                </div>
              </div>

              {/* Version History Alert if updated */}
              {exam.version > 1 && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    Notice venue was revised by administration (v{exam.version}.0). Displaying the verified seating allocation.
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
