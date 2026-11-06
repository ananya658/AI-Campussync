import React, { useState, useEffect } from 'react';
import { AnalyticsSummary, Booking, IssueReport } from '../../types';
import { api } from '../../services/api';
import { 
  Building2, Users, Calendar, AlertCircle, CheckCircle2, 
  Clock, ArrowUpRight, ShieldCheck, Wrench, Sparkles, Map 
} from 'lucide-react';

interface AdminDashboardProps {
  onNavigate: (view: string) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate }) => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [recentBookings, setRecentBookings] = useState<Booking[]>([]);
  const [pendingReports, setPendingReports] = useState<IssueReport[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [stats, bookings, reports] = await Promise.all([
        api.getAnalytics(),
        api.getBookings({ limit: 5 } as any),
        api.getReports('PENDING'),
      ]);
      setAnalytics(stats);
      setRecentBookings(bookings.slice(0, 5));
      setPendingReports(reports.slice(0, 4));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Campus Administration Console
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time infrastructure overview, room allocations, and student reports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('interactive-map')}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm flex items-center gap-1.5 transition-all"
          >
            <Map className="w-4 h-4" /> Open Campus Map
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Classrooms & Labs</span>
            <Building2 className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            {(analytics?.total_classrooms || 0) + (analytics?.total_laboratories || 0)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {analytics?.total_classrooms || 0} Halls • {analytics?.total_laboratories || 0} Labs
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Available Now</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-600">
            {analytics?.total_available_now || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Vacant for immediate booking
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Bookings</span>
            <Calendar className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-indigo-600">
            {analytics?.total_active_bookings || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Confirmed academic sessions
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Student Reports</span>
            <AlertCircle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-600">
            {analytics?.pending_student_reports || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Pending administrative review
          </div>
        </div>
      </div>

      {/* Blueprint Discrepancy Notification Banner */}
      <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-amber-600 text-white shrink-0 mt-0.5">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-amber-950">
              Deeksha Bhawan Blueprint Discrepancy Flag (LH13 & LH14)
            </h4>
            <p className="text-xs text-amber-800 mt-0.5 leading-relaxed">
              2 rooms on the structural floor plan are flagged as pending verification (Table 9 Ledger). They remain isolated from general booking until you authorize them.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('admin-reconciliation')}
            className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs shadow-sm transition-all whitespace-nowrap self-start md:self-auto"
          >
            Open Reconciliation Ledger (Table 9) →
          </button>
        </div>
      </div>

      {/* Two Column Grid: Recent Bookings & Pending Student Discrepancies */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Bookings */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Calendar className="w-4 h-4 text-blue-600" /> Recent Booking Requests
            </h3>
            <button
              onClick={() => onNavigate('admin-bookings')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {recentBookings.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">No bookings recorded yet.</div>
            ) : (
              recentBookings.map((b) => (
                <div key={b.id} className="py-3 flex items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-xs text-slate-900">{b.title}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                      <span className="font-medium text-blue-600">{b.room?.room_number}</span>
                      <span>•</span>
                      <span>{b.date} ({b.start_time.slice(0, 5)} - {b.end_time.slice(0, 5)})</span>
                      {b.is_test_data && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] bg-slate-100 text-slate-600 border border-slate-200 font-mono">
                          TEST DATA
                        </span>
                      )}
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
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

        {/* Pending Student Reports */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600" /> Student Discrepancy Tickets
            </h3>
            <button
              onClick={() => onNavigate('admin-reports')}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              Resolve tickets <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {pendingReports.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                All student reports are resolved. No pending tickets.
              </div>
            ) : (
              pendingReports.map((r) => (
                <div key={r.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-800">
                      {r.category.replace(/_/g, ' ')}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                      PENDING
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                    "{r.description}"
                  </p>
                  <div className="text-[10px] text-slate-400 mt-1.5 flex items-center gap-2">
                    <span>By: {r.reporter_name} ({r.reporter_roll})</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

