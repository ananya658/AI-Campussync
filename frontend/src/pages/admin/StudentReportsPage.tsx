import React, { useState, useEffect } from 'react';
import { IssueReport } from '../../types';
import { api } from '../../services/api';
import { 
  AlertCircle, CheckCircle2, Clock, Filter, Check, 
  X, MessageSquare, ShieldCheck, MapPin 
} from 'lucide-react';

export const StudentReportsPage: React.FC = () => {
  const [reports, setReports] = useState<IssueReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [resolvingReport, setResolvingReport] = useState<IssueReport | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState<string>('RESOLVED');
  const [resolutionNote, setResolutionNote] = useState('');

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await api.getReports(statusFilter || undefined);
      setReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [statusFilter]);

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingReport || !resolutionNote.trim()) return;
    try {
      await api.resolveReport(resolvingReport.id, resolutionStatus, resolutionNote);
      setResolvingReport(null);
      setResolutionNote('');
      loadReports();
    } catch (err: any) {
      alert(err.message || 'Failed to update ticket');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Student Timetable Discrepancy Tickets
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Review student-submitted reports regarding venue mismatch, outdated timings, and schedule errors.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {['', 'PENDING', 'RESOLVED', 'REJECTED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              statusFilter === st
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200'
            }`}
          >
            {st === '' ? 'All Reports' : st}
          </button>
        ))}
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {reports.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200 text-xs">
            No discrepancy reports matching selected filter.
          </div>
        ) : (
          reports.map((r) => (
            <div key={r.id} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-200">
                      {r.category.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-bold text-slate-800">
                      Student: {r.reporter_name} ({r.reporter_roll})
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="text-xs text-slate-800 font-medium leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                    "{r.description}"
                  </p>

                  {/* Context Venue */}
                  {(r.room_number || r.building_name) && (
                    <div className="text-xs text-slate-500 flex items-center gap-1.5 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-blue-600" />
                      Referenced Venue: {r.room_number} ({r.building_name})
                    </div>
                  )}

                  {/* Resolution note if already resolved */}
                  {r.admin_resolution_note && (
                    <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs mt-2">
                      <div className="flex items-center gap-1.5 font-bold mb-0.5 text-emerald-800">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        Admin Resolution Note (by {r.resolved_by_name || 'Dean Office'}):
                      </div>
                      <p className="text-emerald-700 leading-relaxed">{r.admin_resolution_note}</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 pt-2 md:pt-0">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold ${
                      r.status === 'RESOLVED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : r.status === 'REJECTED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {r.status}
                  </span>

                  {r.status === 'PENDING' && (
                    <button
                      onClick={() => {
                        setResolvingReport(r);
                        setResolutionStatus('RESOLVED');
                        setResolutionNote('');
                      }}
                      className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition-all"
                    >
                      Resolve Ticket
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Resolution Modal */}
      {resolvingReport && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
              Resolve Student Discrepancy Ticket
            </h3>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Ticket category: <strong>{resolvingReport.category.replace(/_/g, ' ')}</strong> filed by <strong>{resolvingReport.reporter_name}</strong>.
            </p>

            <form onSubmit={handleResolveSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Resolution Decision
                </label>
                <select
                  value={resolutionStatus}
                  onChange={(e) => setResolutionStatus(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                >
                  <option value="RESOLVED">Acknowledge & Mark Resolved (RESOLVED)</option>
                  <option value="REJECTED">Dismiss as Invalid / Duplicate (REJECTED)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Official Administrative Note (Dispatched to Student)
                </label>
                <textarea
                  rows={3}
                  required
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="e.g. Verified room notice. Classroom IET18 is the official venue for CS-301. Door signage updated."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResolvingReport(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                >
                  Submit & Notify Student
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
