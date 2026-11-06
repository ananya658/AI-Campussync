import React, { useState, useEffect } from 'react';
import { AnalyticsSummary } from '../../types';
import { api } from '../../services/api';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend, CartesianGrid 
} from 'recharts';
import { BarChart3, TrendingUp, Building2, Clock, Users } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getAnalytics();
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading || !data) {
    return (
      <div className="p-12 text-center text-xs text-slate-400">
        Loading real-time campus analytics...
      </div>
    );
  }

  // Distribution chart data
  const roomTypeDistribution = [
    { name: 'Lecture Halls', value: data.total_classrooms, color: '#3B82F6' },
    { name: 'Laboratories', value: data.total_laboratories, color: '#6366F1' },
    { name: 'Seminar Halls', value: data.total_seminar_halls, color: '#8B5CF6' },
  ];

  // Occupancy donut data
  const occupancyData = [
    { name: 'Available Now', value: data.total_available_now, color: '#10B981' },
    { name: 'Occupied Now', value: data.total_occupied_now, color: '#EF4444' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Campus Capacity & Utilization Analytics
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Real-time metrics computed directly from university classroom reservations and academic timetables.
        </p>
      </div>

      {/* Primary KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Overall Campus Utilization
          </span>
          <div className="text-3xl font-extrabold text-blue-600 mt-2">
            {data.overall_room_utilization_pct}%
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Real-time active occupancy</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Active Bookings
          </span>
          <div className="text-3xl font-extrabold text-slate-900 mt-2">
            {data.total_active_bookings}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Confirmed classroom reservations</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Upcoming Exams
          </span>
          <div className="text-3xl font-extrabold text-indigo-600 mt-2">
            {data.upcoming_examinations}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Minor & Major exam sittings</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Pending Approval
          </span>
          <div className="text-3xl font-extrabold text-amber-600 mt-2">
            {data.pending_booking_requests}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Awaiting admin authorization</p>
        </div>
      </div>

      {/* Chart Row 1: Peak Booking Hours & Real-Time Availability Donut */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Peak Booking Hours Bar Chart */}
        <div className="lg:col-span-2 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" /> Peak Academic Booking Hours (8 AM - 6 PM)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Classroom booking density across operational hours.
              </p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.peak_booking_hours}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="label" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderRadius: '12px',
                    color: '#FFF',
                    fontSize: '12px',
                    border: 'none',
                  }}
                />
                <Bar dataKey="bookings" fill="#3B82F6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Real-time Occupancy Status */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" /> Current Room Occupancy
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Live status snapshot right now.</p>
          </div>

          <div className="h-52 w-full my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={occupancyData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {occupancyData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
            {data.total_available_now} rooms currently available
          </div>
        </div>
      </div>

      {/* Building-wise Utilization Comparison */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="font-bold text-slate-900 text-sm mb-4 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-600" /> Building-Wise Occupancy Breakdown
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          {data.building_wise_utilization.map((b) => (
            <div key={b.building_id} className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-xs text-slate-900">{b.building_name}</span>
                <span className="text-xs font-extrabold text-blue-600">{b.utilization_pct}%</span>
              </div>
              <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-blue-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${b.utilization_pct}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                <span>Total Rooms: {b.total_rooms}</span>
                <span>Occupied: {b.occupied_rooms}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
