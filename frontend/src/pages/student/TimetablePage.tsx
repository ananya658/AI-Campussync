import React, { useState, useEffect } from 'react';
import { Schedule } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Clock, Calendar, MapPin, User, BookOpen, Grid, List, Printer } from 'lucide-react';

export const TimetablePage: React.FC = () => {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<number>(0); // 0=Monday
  const [viewMode, setViewMode] = useState<'day' | 'grid'>('day');

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const timeSlots = [
    { start: '09:00', end: '10:00', label: '9:00 - 10:00 AM' },
    { start: '10:00', end: '11:00', label: '10:00 - 11:00 AM' },
    { start: '11:00', end: '12:00', label: '11:00 - 12:00 PM' },
    { start: '12:00', end: '13:00', label: '12:00 - 1:00 PM' },
    { start: '14:00', end: '15:00', label: '2:00 - 3:00 PM' },
    { start: '15:00', end: '16:00', label: '3:00 - 4:00 PM' },
    { start: '16:00', end: '17:00', label: '4:00 - 5:00 PM' },
  ];

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

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Academic Timetable & Lecture Schedule
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {user?.role === 'STUDENT'
              ? `Personalized schedule for ${user?.student_profile?.branch_code || 'B.Tech'} Year ${user?.student_profile?.year} Section ${user?.student_profile?.section}.`
              : `Faculty teaching timetable for ${user?.full_name}.`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex items-center bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
            <button
              onClick={() => setViewMode('day')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'day' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <List className="w-3.5 h-3.5" /> Day View
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'grid' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Grid className="w-3.5 h-3.5" /> Weekly Grid
            </button>
          </div>

          <button
            onClick={handlePrint}
            title="Print Official Timetable"
            className="p-2 bg-white hover:bg-slate-50 text-slate-700 rounded-xl border border-slate-200 transition-colors shadow-sm"
          >
            <Printer className="w-4 h-4" />
          </button>
        </div>
      </div>

      {viewMode === 'day' ? (
        <>
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
        </>
      ) : (
        /* Full Weekly Matrix Grid View (Mon - Fri) */
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden p-4">
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse min-w-[700px]">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 text-[11px] uppercase tracking-wider">
                  <th className="p-3 text-left w-24">Day</th>
                  {timeSlots.map((ts) => (
                    <th key={ts.start} className="p-3 text-center border-l border-slate-200 font-semibold">
                      {ts.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {days.slice(0, 5).map((dayName, dIdx) => (
                  <tr key={dayName} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold text-slate-900 bg-slate-50/70 border-r border-slate-200">
                      {dayName}
                    </td>
                    {timeSlots.map((ts) => {
                      const slotClass = schedules.find(
                        (s) =>
                          s.day_of_week === dIdx &&
                          s.start_time.slice(0, 5) <= ts.start &&
                          s.end_time.slice(0, 5) > ts.start
                      );

                      if (!slotClass) {
                        return (
                          <td key={ts.start} className="p-2 border-l border-slate-100 text-center text-slate-300">
                            —
                          </td>
                        );
                      }

                      const isLab = slotClass.schedule_type === 'LAB';

                      return (
                        <td
                          key={ts.start}
                          className={`p-2 border-l border-slate-100 ${
                            isLab ? 'bg-indigo-50/70' : 'bg-blue-50/60'
                          }`}
                        >
                          <div className="p-2 rounded-xl bg-white border border-slate-200/80 shadow-xs text-left">
                            <div className="font-bold text-[11px] text-slate-900 truncate" title={slotClass.subject_name}>
                              {slotClass.subject_code}
                            </div>
                            <div className="text-[10px] text-blue-700 font-semibold truncate mt-0.5">
                              {slotClass.room_number}
                            </div>
                            <div className="text-[9px] text-slate-400 truncate">
                              {slotClass.faculty_name?.split(' ')[0]}
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
