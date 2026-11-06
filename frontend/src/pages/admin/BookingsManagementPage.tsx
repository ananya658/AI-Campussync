import React, { useState, useEffect } from 'react';
import { Booking } from '../../types';
import { api } from '../../services/api';
import { 
  Calendar, CheckCircle2, XCircle, Clock, Search, 
  Filter, AlertCircle, Ban, ArrowUpRight 
} from 'lucide-react';

export const BookingsManagementPage: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [cancellingBooking, setCancellingBooking] = useState<Booking | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const loadBookings = async () => {
    setLoading(true);
    try {
      const data = await api.getBookings({ status: statusFilter || undefined });
      setBookings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBookings();
  }, [statusFilter]);

  const handleApprove = async (id: number) => {
    try {
      await api.updateBookingStatus(id, 'CONFIRMED', 'Approved by administrator');
      loadBookings();
    } catch (err: any) {
      alert(err.message || 'Approval failed');
    }
  };

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancellingBooking || !cancelReason.trim()) return;
    try {
      await api.cancelBooking(cancellingBooking.id, cancelReason);
      setCancellingBooking(null);
      setCancelReason('');
      loadBookings();
    } catch (err: any) {
      alert(err.message || 'Cancellation failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Classroom Reservations & Bookings
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Review live campus bookings, audit cancellations, and resolve pending approval requests.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {['', 'CONFIRMED', 'PENDING_APPROVAL', 'CANCELLED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              statusFilter === st
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200'
            }`}
          >
            {st === '' ? 'All Bookings' : st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Bookings Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Ref / Purpose</th>
                <th className="py-3 px-4">Room & Building</th>
                <th className="py-3 px-4">Date & Time Slot</th>
                <th className="py-3 px-4">Booked By</th>
                <th className="py-3 px-4">Cohort / Target</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {bookings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No bookings found matching filter.
                  </td>
                </tr>
              ) : (
                bookings.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-mono text-[10px] text-blue-600 font-bold">{b.booking_reference}</div>
                      <div className="font-semibold text-slate-900 mt-0.5">{b.title}</div>
                      <span className="text-[10px] text-slate-400">{b.purpose.replace(/_/g, ' ')}</span>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-800">
                      <div>{b.room?.room_number}</div>
                      <div className="text-[10px] text-slate-400 font-normal">{b.room?.building_name}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900">{b.date}</div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {b.start_time.slice(0, 5)} - {b.end_time.slice(0, 5)}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900">{b.booked_by_name || 'Faculty Member'}</div>
                      <div className="text-[10px] text-slate-400">{b.booked_by_email}</div>
                    </td>
                    <td className="py-3.5 px-4 text-[11px] text-slate-600">
                      {b.academic_year ? `Year ${b.academic_year} ${b.section ? `Sec ${b.section}` : ''}` : 'General / Open'}
                      <div className="text-[10px] text-slate-400">{b.expected_students} expected</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          b.status === 'CONFIRMED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : b.status === 'CANCELLED'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {b.status}
                      </span>
                      {b.cancellation_reason && (
                        <div className="text-[10px] text-rose-600 mt-1 max-w-xs truncate" title={b.cancellation_reason}>
                          Reason: {b.cancellation_reason}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {b.status === 'PENDING_APPROVAL' && (
                          <button
                            onClick={() => handleApprove(b.id)}
                            className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px]"
                          >
                            Approve
                          </button>
                        )}
                        {b.status !== 'CANCELLED' && (
                          <button
                            onClick={() => setCancellingBooking(b)}
                            className="px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-[10px] border border-rose-200"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cancellation Modal with Recorded Reason */}
      {cancellingBooking && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center gap-2 text-rose-700 font-bold text-base mb-2">
              <Ban className="w-5 h-5 text-rose-600" />
              Cancel Booking: {cancellingBooking.booking_reference}
            </div>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Cancelling will instantly free up <strong>{cancellingBooking.room?.room_number}</strong> for the slot ({cancellingBooking.start_time.slice(0, 5)} - {cancellingBooking.end_time.slice(0, 5)}) and dispatch notifications to affected faculty and students.
            </p>

            <form onSubmit={handleCancelSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Cancellation Reason (Mandatory for Audit Trail)
                </label>
                <textarea
                  rows={3}
                  required
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Schedule revised by Dean Office due to University Syndicate Meeting."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCancellingBooking(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-500/20"
                >
                  Confirm & Log Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

