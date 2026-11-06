import React from 'react';
import { Room } from '../../types';
import { 
  X, Users, Sparkles, AlertTriangle, ShieldCheck, 
  Clock, MapPin, Calendar, CheckCircle2, AlertCircle, Wrench 
} from 'lucide-react';

interface RoomDetailDrawerProps {
  room: Room | null;
  onClose: () => void;
  onBookRoom?: (room: Room) => void;
  userRole?: string;
}

export const RoomDetailDrawer: React.FC<RoomDetailDrawerProps> = ({
  room,
  onClose,
  onBookRoom,
  userRole
}) => {
  if (!room) return null;

  const getStatusBadge = () => {
    switch (room.current_status) {
      case 'AVAILABLE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Available Now
          </span>
        );
      case 'BOOKED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            Currently Booked
          </span>
        );
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Pending Approval
          </span>
        );
      case 'MAINTENANCE':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-200 text-slate-800 border border-slate-300">
            <Wrench className="w-3 h-3 text-slate-600" />
            Maintenance / Restricted
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white shadow-2xl border-l border-slate-200 flex flex-col transform transition-transform duration-300 ease-in-out">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600">
              {room.building_name || 'Campus Building'}
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-xs text-slate-500 font-medium">{room.floor_name}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            {room.room_number}
            {room.verification_status === 'PENDING_ADMIN_VERIFICATION' && (
              <span className="text-xs font-normal bg-amber-100 text-amber-800 px-2 py-0.5 rounded border border-amber-300 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                Unverified Room
              </span>
            )}
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">{room.room_name}</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-full transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Status card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-600">Current Allocation</span>
          {getStatusBadge()}
        </div>

        {/* Blueprint Discrepancy Alert for Deeksha Bhawan LH13 / LH14 */}
        {room.verification_status === 'PENDING_ADMIN_VERIFICATION' && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900">
            <div className="flex items-center gap-2 font-semibold text-sm mb-1 text-amber-800">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              Administrative Verification Discrepancy
            </div>
            <p className="text-xs text-amber-700 leading-relaxed">
              This space ({room.room_number}) is physically present on architectural floor plans but pending official verification in the academic registry. It cannot be booked without Dean/Admin clearance.
            </p>
          </div>
        )}

        {/* Capacity & Type Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100">
            <div className="flex items-center gap-2 text-blue-700 text-xs font-semibold mb-1 uppercase tracking-wider">
              <Users className="w-4 h-4" /> Capacity
            </div>
            <div className="text-2xl font-extrabold text-blue-900">{room.capacity}</div>
            <div className="text-xs text-blue-600 font-medium">Students Max</div>
          </div>

          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-100">
            <div className="flex items-center gap-2 text-indigo-700 text-xs font-semibold mb-1 uppercase tracking-wider">
              <MapPin className="w-4 h-4" /> Type
            </div>
            <div className="text-base font-bold text-indigo-900 truncate">
              {room.room_type.replace('_', ' ')}
            </div>
            <div className="text-xs text-indigo-600 font-medium">Official Classification</div>
          </div>
        </div>

        {/* Current Active Booking Details */}
        {room.active_booking && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900">
            <div className="flex items-center gap-2 text-xs font-bold text-rose-800 uppercase tracking-wider mb-2">
              <Clock className="w-4 h-4 text-rose-600" /> Ongoing Reservation
            </div>
            <div className="font-semibold text-sm">{room.active_booking.title}</div>
            <div className="text-xs text-rose-700 mt-1 flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5" />
              Slot: {room.active_booking.start} - {room.active_booking.end}
            </div>
            {room.active_booking.booking_ref && (
              <div className="text-xs font-mono text-rose-600 mt-1">
                Ref: {room.active_booking.booking_ref}
              </div>
            )}
          </div>
        )}

        {/* Permitted Uses */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            Permitted Academic Uses
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {room.permitted_uses.split(',').map((u, i) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
              >
                {u.trim()}
              </span>
            ))}
          </div>
        </div>

        {/* Facilities & Equipment */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center justify-between">
            <span>Installed Facilities</span>
            <span className="text-[11px] text-slate-400 font-normal">
              {room.facilities.length} available
            </span>
          </h4>
          {room.facilities.length > 0 ? (
            <div className="space-y-2">
              {room.facilities.map((fac) => (
                <div
                  key={fac.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 text-xs"
                >
                  <div className="flex items-center gap-2 font-medium text-slate-800">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    {fac.facility_name.replace(/_/g, ' ')}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold text-[10px]">
                      x{fac.quantity}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-semibold">
                      {fac.condition}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">Standard classroom furnishing only.</p>
          )}
        </div>
      </div>

      {/* Footer / Action */}
      <div className="p-6 border-t border-slate-100 bg-slate-50">
        {userRole === 'STUDENT' ? (
          <div className="text-center py-2 text-xs text-slate-500 bg-slate-100 rounded-lg border border-slate-200">
            Student view only. Bookings are managed by Faculty and Academic Administration.
          </div>
        ) : room.verification_status === 'PENDING_ADMIN_VERIFICATION' ? (
          <div className="text-center py-2 text-xs text-amber-800 bg-amber-100/70 rounded-lg border border-amber-200 font-medium">
            Booking restricted until administrative verification is complete.
          </div>
        ) : (
          <button
            onClick={() => onBookRoom && onBookRoom(room)}
            className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
          >
            <Calendar className="w-4 h-4" />
            Book {room.room_number} Now
          </button>
        )}
      </div>
    </div>
  );
};
