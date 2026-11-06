import React, { useState, useEffect } from 'react';
import { Building, Room } from '../../types';
import { api } from '../../services/api';
import { 
  Building2, Layers, ShieldCheck, AlertTriangle, Wrench, 
  CheckCircle2, Users, Edit3, Sparkles 
} from 'lucide-react';

export const BuildingsRoomsPage: React.FC = () => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState<number>(1);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyingRoom, setVerifyingRoom] = useState<Room | null>(null);
  const [verificationNotes, setVerificationNotes] = useState('');
  const [verifyStatus, setVerifyStatus] = useState('OFFICIAL_VERIFIED');

  const loadData = async () => {
    try {
      const bList = await api.getBuildings();
      setBuildings(bList);
      if (bList.length > 0) {
        setSelectedBuildingId(bList[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRooms = async () => {
    if (!selectedBuildingId) return;
    try {
      const rList = await api.getRooms({ building_id: selectedBuildingId });
      setRooms(rList);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadRooms();
  }, [selectedBuildingId]);

  const handleToggleMaintenance = async (room: Room) => {
    try {
      await api.updateRoom(room.id, { is_maintenance: !room.is_maintenance });
      loadRooms();
    } catch (err) {
      alert('Failed to update maintenance status');
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyingRoom) return;
    try {
      await api.verifyRoomDiscrepancy(verifyingRoom.id, verifyStatus, verificationNotes);
      setVerifyingRoom(null);
      setVerificationNotes('');
      loadRooms();
    } catch (err: any) {
      alert(err.message || 'Verification update failed');
    }
  };

  const activeBuilding = buildings.find((b) => b.id === selectedBuildingId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Campus Infrastructure Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Configure buildings, floors, room capacities, facilities, and blueprint discrepancy authorizations.
          </p>
        </div>
      </div>

      {/* Building Tabs */}
      <div className="flex items-center gap-3">
        {buildings.map((b) => (
          <button
            key={b.id}
            onClick={() => setSelectedBuildingId(b.id)}
            className={`flex items-center gap-2.5 px-5 py-3 rounded-2xl font-bold text-xs sm:text-sm transition-all ${
              b.id === selectedBuildingId
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>{b.name}</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-white/20">
              {b.code}
            </span>
          </button>
        ))}
      </div>

      {/* Discrepancy Notice for Deeksha Bhawan */}
      {activeBuilding?.code === 'DB' && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900">
          <div className="flex items-center gap-2 font-bold text-sm text-amber-800 mb-1">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Official Discrepancy Policy: LH13 & LH14
          </div>
          <p className="text-xs text-amber-700 leading-relaxed">
            The university written specification identified LH01–LH12, whereas structural floor blueprints clearly show LH01–LH14 across 2 floors. Use the <strong>"Verify Discrepancy"</strong> action below to audit and authorize these rooms for classroom scheduling once safety inspections are satisfied.
          </p>
        </div>
      )}

      {/* Rooms Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <span className="font-bold text-xs uppercase tracking-wider text-slate-700">
            {activeBuilding?.name} • Room Directory ({rooms.length} Spaces)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Room No.</th>
                <th className="py-3 px-4">Floor</th>
                <th className="py-3 px-4">Name / Purpose</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4 text-center">Capacity</th>
                <th className="py-3 px-4">Verification Status</th>
                <th className="py-3 px-4">Maintenance</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {rooms.map((r) => {
                const isDiscrepancy = r.verification_status === 'PENDING_ADMIN_VERIFICATION';
                return (
                  <tr key={r.id} className={`hover:bg-slate-50/80 transition-colors ${isDiscrepancy ? 'bg-amber-50/40' : ''}`}>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {r.room_number}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-medium">
                      {r.floor_name}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800">{r.room_name}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-xs">{r.permitted_uses}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        {r.room_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-slate-900">
                      {r.capacity} seats
                    </td>
                    <td className="py-3.5 px-4">
                      {r.verification_status === 'OFFICIAL_VERIFIED' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Official
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                          <AlertTriangle className="w-3 h-3 text-amber-600" /> Pending Verification
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <button
                        onClick={() => handleToggleMaintenance(r)}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                          r.is_maintenance
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        }`}
                      >
                        {r.is_maintenance ? 'Under Maintenance' : 'Operational'}
                      </button>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {(r.room_number === 'LH13' || r.room_number === 'LH14' || isDiscrepancy) ? (
                        <button
                          onClick={() => {
                            setVerifyingRoom(r);
                            setVerifyStatus(r.verification_status === 'OFFICIAL_VERIFIED' ? 'RESTRICTED' : 'OFFICIAL_VERIFIED');
                            setVerificationNotes(r.verification_notes || '');
                          }}
                          className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-[10px] shadow-sm transition-all"
                        >
                          Verify Discrepancy
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-400">Standard</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Discrepancy Verification Modal */}
      {verifyingRoom && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center gap-2 text-amber-800 mb-2 font-bold text-base">
              <ShieldCheck className="w-5 h-5 text-amber-600" />
              Administrative Verification: {verifyingRoom.room_number}
            </div>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Resolve the blueprint discrepancy for <strong>{verifyingRoom.room_name}</strong>. Officially verified rooms can be scheduled by faculty and departments.
            </p>

            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Authorization Decision
                </label>
                <select
                  value={verifyStatus}
                  onChange={(e) => setVerifyStatus(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                >
                  <option value="OFFICIAL_VERIFIED">
                    Authorize as Official Bookable Classroom (OFFICIAL_VERIFIED)
                  </option>
                  <option value="RESTRICTED">
                    Keep Restricted / Exclude from Scheduling (RESTRICTED)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Administrative Inspection Notes
                </label>
                <textarea
                  rows={3}
                  required
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  placeholder="e.g. Physically inspected by Dean Office. Dual doors, projector, and 90-student bench seating confirmed operational."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setVerifyingRoom(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                >
                  Commit Official Verification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
