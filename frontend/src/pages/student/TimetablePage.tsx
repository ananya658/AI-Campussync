import React, { useState, useEffect } from 'react';
import { Schedule } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Clock, Calendar, MapPin, User, BookOpen } from 'lucide-react';

export const TimetablePage: React.FC = () => {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<number>(0); // 0=Monday

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getMySchedule();
        setSchedules(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const daySchedules = schedules.filter((s) => s.day_of_week === selectedDay);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Personalized Academic Timetable
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Official class schedule for {user?.student_profile?.branch_code || 'B.Tech'} Year {user?.student_profile?.year} Section {user?.student_profile?.section}.
          </p>
        </div>
      </div>

      {/* Day Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {days.map((day, idx) => (
          <button
            key={day}
            onClick={() => setSelectedDay(idx)}
            className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
              selectedDay === idx
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200'
            }`}
          >
            {day}
          </button>
        ))}
      </div>

      {/* Schedule Slots Timeline for Selected Day */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
        <h3 className="font-bold text-sm text-slate-800 pb-2 border-b border-slate-100 flex items-center justify-between">
          <span>{days[selectedDay]} Classes</span>
          <span className="text-xs text-slate-400 font-normal">
            {daySchedules.length} session{daySchedules.length === 1 ? '' : 's'} scheduled
          </span>
        </h3>

        {daySchedules.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No scheduled lectures or laboratories on {days[selectedDay]}.
          </div>
        ) : (
          daySchedules.map((slot) => {
            const isLab = slot.schedule_type === 'LAB';
            return (
              <div
                key={slot.id}
                className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  isLab
                    ? 'bg-indigo-50/50 border-indigo-200'
                    : 'bg-slate-50/70 border-slate-200/80 hover:bg-slate-50'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        isLab ? 'bg-indigo-600 text-white' : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {slot.schedule_type}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-700">
                      {slot.subject_code}
                    </span>
                  </div>

                  <h4 className="text-sm font-extrabold text-slate-900">
                    {slot.subject_name}
                  </h4>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-0.5">
                    <span className="flex items-center gap-1 font-bold text-blue-700">
                      <MapPin className="w-3.5 h-3.5" />
                      Room {slot.room_number} ({slot.building_name})
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1 font-medium">
                      <User className="w-3.5 h-3.5" />
                      {slot.faculty_name}
                    </span>
                  </div>
                </div>

                <div className="text-left sm:text-right shrink-0">
                  <div className="inline-block px-3 py-1.5 rounded-xl bg-white border border-slate-200 shadow-sm font-mono text-xs font-bold text-slate-900">
                    {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
