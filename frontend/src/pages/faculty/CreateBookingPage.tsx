import React, { useState, useEffect } from 'react';
import { Room, Building } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  CalendarPlus, ShieldCheck, AlertCircle, Clock, 
  Users, CheckCircle2, Building2, MapPin 
} from 'lucide-react';

interface CreateBookingPageProps {
  initialRoom?: Room | null;
  onBookingSuccess: () => void;
}

export const CreateBookingPage: React.FC<CreateBookingPageProps> = ({
  initialRoom,
  onBookingSuccess,
}) => {
  const { user } = useAuth();
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState<number>(initialRoom?.building_id || 1);
  const [selectedRoomId, setSelectedRoomId] = useState<number>(initialRoom?.id || 0);

  // Form fields
  const [title, setTitle] = useState('');
  const [purpose, setPurpose] = useState('EXTRA_LECTURE');
  const [bookingDate, setBookingDate] = useState(new Date().toISOString().split('T')[0]);
  const [startTime, setStartTime] = useState('14:00');
  const [endTime, setEndTime] = useState('15:00');
  const [expectedStudents, setExpectedStudents] = useState<number>(60);
  const [branchId, setBranchId] = useState<string>('1'); // CSE
  const [academicYear, setAcademicYear] = useState<string>('3'); // 3rd Year
  const [section, setSection] = useState<string>('A');
  const [requirements, setRequirements] = useState('');
  const [isTestData, setIsTestData] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedRef, setConfirmedRef] = useState<string | null>(null);

  // Load buildings & rooms
  useEffect(() => {
    const load = async () => {
      try {
        const bList = await api.getBuildings();
        setBuildings(bList);
        const rList = await api.getRooms({ building_id: selectedBuildingId });
        setRooms(rList);
        if (!selectedRoomId && rList.length > 0) {
          setSelectedRoomId(rList[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, [selectedBuildingId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.createBooking({
        room_id: selectedRoomId,
        title,
        purpose,
        date: bookingDate,
        start_time: startTime,
        end_time: endTime,
        expected_students: expectedStudents,
        branch_id: branchId ? parseInt(branchId) : undefined,
        academic_year: academicYear ? parseInt(academicYear) : undefined,
        section: section || undefined,
        additional_requirements: requirements || undefined,
        is_test_data: isTestData,
      });

      setConfirmedRef(res.booking_reference);
    } catch (err: any) {
      setError(err.message || 'Booking conflict or capacity exceeded. Please check room availability.');
    } finally {
      setLoading(false);
    }
  };

  const selectedRoomObj = rooms.find((r) => r.id === selectedRoomId);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Reserve Classroom / Lab
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Automated conflict prevention engine verifies zero timetable overlap and enforces capacity limits.
        </p>
      </div>

      {confirmedRef ? (
        <div className="p-8 rounded-3xl bg-white border border-emerald-200 shadow-xl text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900">
            Booking Confirmed Successfully!
          </h2>
          <div className="inline-block px-4 py-2 rounded-xl bg-slate-100 font-mono font-bold text-sm text-blue-700">
            Reference: {confirmedRef}
          </div>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Your booking has been permanently locked in the database. Relevant academic schedules and affected student timetables have been updated.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <button
              onClick={() => {
                setConfirmedRef(null);
                setTitle('');
              }}
              className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-all"
            >
              Book Another Room
            </button>
            <button
              onClick={onBookingSuccess}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 transition-all"
            >
              View My Bookings
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Reservation Conflict Detected: </span>
                {error}
              </div>
            </div>
          )}

          {/* Step 1: Session Details */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 mb-3 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px]">1</span>
              Lecture / Event Purpose
            </h3>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Session Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Graph Algorithms Revision & Doubt Solving"
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Official Purpose *
                </label>
                <select
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                >
                  <option value="EXTRA_LECTURE">Extra Lecture</option>
                  <option value="MINOR_EXAM">Minor Examination</option>
                  <option value="PRACTICAL_SESSION">Practical Session / Lab</option>
                  <option value="SEMINAR">Seminar / Guest Lecture</option>
                  <option value="ACADEMIC_EVENT">Academic Event</option>
                  <option value="WORKSHOP">Workshop</option>
                  <option value="OTHER">Other Academic Activity</option>
                </select>
              </div>
            </div>
          </div>

          {/* Step 2: Room & Venue */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 mb-3 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px]">2</span>
              Campus Venue & Room Selection
            </h3>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Building
                </label>
                <select
                  value={selectedBuildingId}
                  onChange={(e) => setSelectedBuildingId(parseInt(e.target.value))}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
                >
                  {buildings.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Specific Room
                </label>
                <select
                  value={selectedRoomId}
                  onChange={(e) => setSelectedRoomId(parseInt(e.target.value))}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-semibold"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.room_number} — {r.room_name} (Cap: {r.capacity})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedRoomObj && (
              <div className="mt-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200/80 flex items-center justify-between">
                <span>Selected: {selectedRoomObj.room_number} ({selectedRoomObj.room_name})</span>
                <span className="font-semibold text-slate-800">Capacity: {selectedRoomObj.capacity} students</span>
              </div>
            )}
          </div>

          {/* Step 3: Date & Time Slot */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 mb-3 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px]">3</span>
              Date & Time Slot
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Date</label>
                <input
                  type="date"
                  required
                  value={bookingDate}
                  onChange={(e) => setBookingDate(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Start Time</label>
                <input
                  type="time"
                  required
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">End Time</label>
                <input
                  type="time"
                  required
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-medium"
                />
              </div>
            </div>
          </div>

          {/* Step 4: Audience & Students */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 mb-3 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px]">4</span>
              Student Cohort & Expected Headcount
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Expected Count *</label>
                <input
                  type="number"
                  min={1}
                  required
                  value={expectedStudents}
                  onChange={(e) => setExpectedStudents(parseInt(e.target.value) || 0)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Branch</label>
                <select
                  value={branchId}
                  onChange={(e) => setBranchId(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
                >
                  <option value="1">CSE (Computer Science)</option>
                  <option value="2">AIML (AI & Machine Learning)</option>
                  <option value="3">AIDS (AI & Data Science)</option>
                  <option value="4">ECE (Electronics)</option>
                  <option value="5">ME (Mechanical)</option>
                  <option value="6">IT (Information Tech)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Year</label>
                <select
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
                >
                  <option value="1">1st Year</option>
                  <option value="2">2nd Year</option>
                  <option value="3">3rd Year</option>
                  <option value="4">4th Year</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Section</label>
                <select
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900"
                >
                  <option value="A">Section A</option>
                  <option value="B">Section B</option>
                  <option value="ALL">Combined (A + B)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Test Data Flag (Hackathon Requirement) */}
          <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200">
            <input
              type="checkbox"
              id="testDataCheckbox"
              checked={isTestData}
              onChange={(e) => setIsTestData(e.target.checked)}
              className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
            />
            <label htmlFor="testDataCheckbox" className="text-xs text-slate-700 font-medium cursor-pointer">
              Tag as <strong>TEST DATA</strong> (Clearly distinguishes hackathon demonstration records from permanent university records)
            </label>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <CalendarPlus className="w-5 h-5" />
              {loading ? 'Validating Conflicts & Booking...' : 'Confirm Classroom Reservation'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

