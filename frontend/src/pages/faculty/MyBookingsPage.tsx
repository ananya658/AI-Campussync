import React, { useState, useEffect } from 'react';
import { Booking } from '../../types';
import { api } from '../../services/api';
import { 
  Calendar, Clock, Ban, CheckCircle2, ArrowRight, 
  MapPin, AlertCircle 
} from 'lucide-react';

interface MyBookingsPageProps {
  onNewBookingClick: () => void;
}

export const MyBookingsPage: React.FC<MyBookingsPageProps> = ({ onNewBookingClick }) => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingBooking, setCancellingBooking] = useState<Booking | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const loadBookings = async () => {
    setLoading(true);
    try {
      const data = await api.getBookings({ my_bookings_only: true });
      setBookings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBookings();
  }, []);

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancellingBooking || !cancelReason.trim()) return;
    try {
      await api.cancelBooking(cancellingBooking.id, cancelReason);
      setCancellingBooking(null);
      setCancelReason('');
      loadBookings();
    } catch (err: any) {
      alert(err.message || 'Failed to cancel reservation');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            My Classroom Reservations
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your booked lecture rooms, modify sessions, or release slots back to the faculty pool.
          </p>
        </div>

        <button
          onClick={onNewBookingClick}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center gap-1.5 transition-all self-start sm:self-auto"
        >
          + Reserve New Room
        </button>
      </div>

      <div className="space-y-4">
        {bookings.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-xs text-slate-400">
            No classroom reservations found. Click above to reserve a room.
          </div>
        ) : (
          bookings.map((b) => (
            <div
              key={b.id}
              className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] font-bold text-blue-600">
                    {b.booking_reference}
                  </span>
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
                  {b.is_test_data && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-100 text-slate-500 font-mono">
                      TEST DATA
                    </span>
                  )}
                </div>

                <h3 className="text-base font-bold text-slate-900">{b.title}</h3>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1 font-semibold text-slate-800">
                    <MapPin className="w-3.5 h-3.5 text-blue-600" />
                    Room {b.room?.room_number} ({b.room?.building_name})
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {b.date}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {b.start_time.slice(0, 5)} - {b.end_time.slice(0, 5)}
                  </span>
                </div>

                {b.cancellation_reason && (
                  <div className="text-xs text-rose-600 font-medium pt-1">
                    Cancellation Reason: {b.cancellation_reason}
                  </div>
                )}
              </div>

              {b.status !== 'CANCELLED' && (
                <button
                  onClick={() => setCancellingBooking(b)}
                  className="px-3.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs border border-rose-200 transition-all self-start md:self-center"
                >
                  Cancel Booking
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Cancellation Dialog */}
      {cancellingBooking && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <Ban className="w-5 h-5 text-rose-600" />
              Release Reserved Slot
            </h3>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Are you sure you want to cancel booking <strong>{cancellingBooking.booking_reference}</strong>? The room will immediately become available for other faculty.
            </p>

            <form onSubmit={handleCancelSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Reason for Cancellation *
                </label>
                <textarea
                  rows={3}
                  required
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Rescheduling practical session to next week."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCancellingBooking(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Keep Booking
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-500/20"
                >
                  Confirm Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
