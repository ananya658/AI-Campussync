import React, { useState, useEffect } from 'react';
import { Building, BookingPrefill, Room } from '../../types';
import { api } from '../../services/api';
import { 
  Search, Calendar, Clock, Users, Building2, Layers, 
  Sparkles, CheckCircle2, AlertCircle, Wrench, ArrowRight 
} from 'lucide-react';

const getLocalDate = () => {
  const current = new Date();
  current.setMinutes(current.getMinutes() - current.getTimezoneOffset());
  return current.toISOString().slice(0, 10);
};

interface RoomFinderPageProps {
  onBookRoom: (room: Room, booking?: BookingPrefill) => void;
}

export const RoomFinderPage: React.FC<RoomFinderPageProps> = ({ onBookRoom }) => {
  const [bookingDate, setBookingDate] = useState(getLocalDate());
  const [startTime, setStartTime] = useState('11:00');
  const [endTime, setEndTime] = useState('12:00');
  const [capacity, setCapacity] = useState<number>(60);
  const [buildingId, setBuildingId] = useState<string>('');
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [roomType, setRoomType] = useState<string>('');
  const [facility, setFacility] = useState<string>('');
  const [purpose, setPurpose] = useState('EXTRA_LECTURE');

  const [results, setResults] = useState<Array<{ room: Room; is_available: boolean; status: string; conflict_reason?: string }>>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const data = await api.queryRoomAvailability({
        booking_date: bookingDate,
        start_time: startTime,
        end_time: endTime,
        required_capacity: capacity || undefined,
        building_id: buildingId ? parseInt(buildingId) : undefined,
        room_type: roomType || undefined,
        facility_needed: facility || undefined,
        purpose,
      });
      setResults(data);
    } catch (err: any) {
      alert(err.message || 'Availability search failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.getBuildings().then(setBuildings).catch((err) => console.error('Failed to load buildings', err));
    handleSearch();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Smart Classroom Finder
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Search vacant lecture halls and computing labs across IET and Deeksha Bhawan with instant conflict verification.
        </p>
      </div>

      {/* Filter Form Card */}
      <form onSubmit={handleSearch} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3">
          {/* Date */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Date
            </label>
            <input
              type="date"
              required
              value={bookingDate}
              onChange={(e) => setBookingDate(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            />
          </div>

          {/* Start Time */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Start Time
            </label>
            <input
              type="time"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            />
          </div>

          {/* End Time */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              End Time
            </label>
            <input
              type="time"
              required
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            />
          </div>

          {/* Required Capacity */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Students Count
            </label>
            <input
              type="number"
              min={1}
              max={300}
              value={capacity}
              onChange={(e) => setCapacity(parseInt(e.target.value) || 0)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            />
          </div>

          {/* Building */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Building
            </label>
            <select
              value={buildingId}
              onChange={(e) => setBuildingId(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            >
              <option value="">Any Campus Building</option>
              {buildings.map((building) => (
                <option key={building.id} value={building.id}>{building.name}</option>
              ))}
            </select>
          </div>

          {/* Room Type */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Room Type
            </label>
            <select
              value={roomType}
              onChange={(e) => setRoomType(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
            >
              <option value="">Any Type</option>
              <option value="LECTURE_HALL">Lecture Hall</option>
              <option value="LAB">Laboratory</option>
              <option value="SEMINAR_HALL">Seminar Hall</option>
            </select>
          </div>
        </div>

        <div className="max-w-xs">
          <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
            Booking Purpose
          </label>
          <select
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
          >
            <option value="EXTRA_LECTURE">Extra lecture</option>
            <option value="MINOR_EXAM">Minor examination</option>
            <option value="MAJOR_EXAM">Major examination</option>
            <option value="PRACTICAL_EXAM">Practical examination</option>
            <option value="PRACTICAL_SESSION">Practical session</option>
            <option value="SEMINAR">Seminar</option>
            <option value="WORKSHOP">Workshop</option>
            <option value="ACADEMIC_EVENT">Academic event</option>
          </select>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Quick Facility Filter:</span>
            {['PROJECTOR', 'AC', 'LAB_COMPUTERS', 'SMART_BOARD'].map((fac) => (
              <button
                type="button"
                key={fac}
                onClick={() => setFacility(facility === fac ? '' : fac)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                  facility === fac
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {fac.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 transition-all"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Querying Database...' : 'Check Availability'}
          </button>
        </div>
      </form>

      {/* Results Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map(({ room, is_available, status, conflict_reason }) => (
          <div
            key={room.id}
            className={`p-5 rounded-2xl bg-white border transition-all flex flex-col justify-between ${
              is_available
                ? 'border-emerald-200 hover:border-emerald-400 hover:shadow-md'
                : 'border-slate-200 bg-slate-50/50 opacity-90'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-blue-600">
                    {room.building_name} • {room.floor_name}
                  </div>
                  <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                    {room.room_number}
                  </h3>
                  <div className="text-xs text-slate-500 font-medium">{room.room_name}</div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                    is_available
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {is_available ? 'AVAILABLE' : 'UNAVAILABLE'}
                </span>
              </div>

              {/* Capacity and Type */}
              <div className="flex items-center gap-3 text-xs text-slate-600 pt-1">
                <span className="flex items-center gap-1 font-semibold text-slate-900">
                  <Users className="w-3.5 h-3.5 text-blue-600" /> {
                    ['MINOR_EXAM', 'MAJOR_EXAM', 'PRACTICAL_EXAM'].includes(purpose)
                      ? (room.exam_capacity ?? Math.floor(room.capacity * 0.5))
                      : room.capacity
                  } seats
                </span>
                <span>•</span>
                <span className="font-medium">{room.room_type.replace('_', ' ')}</span>
              </div>

              {/* Conflict reason if not available */}
              {!is_available && conflict_reason && (
                <div className="p-2.5 rounded-xl bg-rose-50 text-rose-800 text-[11px] leading-relaxed border border-rose-200">
                  {conflict_reason}
                </div>
              )}

              {/* Facilities tags */}
              <div className="flex flex-wrap gap-1 pt-1">
                {room.facilities.slice(0, 3).map((f) => (
                  <span
                    key={f.id}
                    className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600"
                  >
                    {f.facility_name.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-mono">
                {bookingDate} • {startTime}
              </span>

              {is_available ? (
                <button
                  onClick={() => onBookRoom(room, {
                    date: bookingDate,
                    start_time: startTime,
                    end_time: endTime,
                    expected_students: capacity,
                    purpose: purpose as BookingPrefill['purpose'],
                  })}
                  className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all"
                >
                  Book Room <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <span className="text-xs text-slate-400 font-medium">Slot Occupied</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

