import React, { useState, useEffect } from 'react';
import { IssueReport } from '../../types';
import { api } from '../../services/api';
import { 
  AlertCircle, Send, CheckCircle2, Clock, MapPin, 
  ShieldAlert, HelpCircle 
} from 'lucide-react';

export const ReportIssuePage: React.FC = () => {
  const [reports, setMyReports] = useState<IssueReport[]>([]);
  const [loading, setLoading] = useState(true);

  // Form fields
  const [category, setCategory] = useState('WRONG_CLASSROOM');
  const [description, setDescription] = useState('');
  const [scheduledDate, setScheduledDate] = useState(new Date().toISOString().split('T')[0]);
  const [scheduledTime, setScheduledTime] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await api.getReports();
      setMyReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createReport({
        category,
        description,
        scheduled_date: scheduledDate || undefined,
        scheduled_time: scheduledTime || undefined,
      });
      setSuccessMsg(true);
      setDescription('');
      loadReports();
      setTimeout(() => setSuccessMsg(false), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to submit report');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Report Schedule or Classroom Discrepancy
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Notice a conflicting lecture venue, door notice mismatch, or outdated timetable timing? Submit an official report for Dean Office verification.
        </p>
      </div>

      {/* Mandatory Permission Restriction Notice */}
      <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Official University Policy: </span>
          Students are strictly prohibited from directly modifying official bookings or academic master schedules. All reports are dispatched directly to the Academic Administration dashboard for investigation and resolution.
        </div>
      </div>

      {/* Report Form */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm">
        {successMsg && (
          <div className="mb-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Your report has been submitted to administration. You will be notified upon review.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Discrepancy Category *
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="WRONG_CLASSROOM">Wrong Classroom (Door Sign vs Timetable)</option>
              <option value="INCORRECT_TIMING">Incorrect Timing</option>
              <option value="CANCELLED_CLASS">Cancelled Class / Unannounced Absence</option>
              <option value="INCORRECT_EXAMINATION_INFO">Incorrect Examination Information</option>
              <option value="MISSING_ANNOUNCEMENT">Missing Official Announcement</option>
              <option value="OUTDATED_SCHEDULE">Outdated Schedule Information</option>
            </select>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Relevant Date (Optional)
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Relevant Time Slot (Optional)
              </label>
              <input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Detailed Description of Discrepancy *
            </label>
            <textarea
              rows={4}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please describe exactly which room, subject, or professor schedule is in conflict. E.g. Timetable listed CS-301 in IET17, but a notice on the door says it moved to IET18."
              className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {submitting ? 'Submitting Report...' : 'File Official Discrepancy Report'}
            </button>
          </div>
        </form>
      </div>

      {/* Tracking My Submitted Reports */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-600" /> My Filed Reports ({reports.length})
        </h3>

        {reports.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            You have not filed any discrepancy reports.
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <div
                key={r.id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-bold text-xs text-slate-900">
                    {r.category.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      r.status === 'RESOLVED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : r.status === 'REJECTED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {r.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  "{r.description}"
                </p>

                {r.admin_resolution_note && (
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                    <div className="font-bold flex items-center gap-1 text-emerald-800">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Resolution from Administration:
                    </div>
                    <p className="mt-1 text-emerald-700">{r.admin_resolution_note}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

