import React, { useState, useEffect } from 'react';
import { 
  Building2, CheckCircle2, AlertTriangle, ShieldAlert, Sliders, 
  Upload, FileSpreadsheet, RefreshCw, Info, Edit3, ArrowRight, Save
} from 'lucide-react';
import api from '../../services/api';
import { Room, SystemSetting, ReconciliationItem } from '../../types';

export const AdminReconciliationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ledger' | 'rooms' | 'settings' | 'import'>('ledger');
  const [ledgerItems, setLedgerItems] = useState<ReconciliationItem[]>([]);
  const [flaggedRooms, setFlaggedRooms] = useState<Room[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [loading, setLoading] = useState(true);

  // Verification modal state
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [newStatus, setNewStatus] = useState<string>('OFFICIAL_VERIFIED');
  const [editCapacity, setEditCapacity] = useState<number>(75);
  const [editExamCapacity, setEditExamCapacity] = useState<number>(37);
  const [editNotes, setEditNotes] = useState<string>('');
  const [submittingVerify, setSubmittingVerify] = useState(false);

  // Settings edit state
  const [editingSettings, setEditingSettings] = useState<{ [key: string]: string }>({});
  const [savingSettings, setSavingSettings] = useState(false);

  // CSV Import state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  const fetchReconciliationData = async () => {
    try {
      setLoading(true);
      const [ledgerRes, settingsRes] = await Promise.all([
        api.get('/reconciliation/ledger'),
        api.get('/reconciliation/settings')
      ]);
      setLedgerItems(ledgerRes.data.table_9_reconciliations);
      setFlaggedRooms(ledgerRes.data.flagged_rooms);
      setSummary(ledgerRes.data.summary);
      setSettings(settingsRes.data);

      const initSettings: { [key: string]: string } = {};
      settingsRes.data.forEach((s: SystemSetting) => {
        initSettings[s.key] = s.value;
      });
      setEditingSettings(initSettings);
    } catch (err) {
      console.error('Failed to load reconciliation data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReconciliationData();
  }, []);

  const handleOpenVerifyModal = (r: Room) => {
    setSelectedRoom(r);
    setNewStatus(r.verification_status);
    setEditCapacity(r.capacity);
    setEditExamCapacity(r.exam_capacity || Math.floor(r.capacity * 0.5));
    setEditNotes(r.verification_notes || '');
  };

  const handleSaveRoomVerification = async () => {
    if (!selectedRoom) return;
    try {
      setSubmittingVerify(true);
      await api.post(`/reconciliation/rooms/${selectedRoom.id}/verify`, {
        verification_status: newStatus,
        capacity: editCapacity,
        exam_capacity: editExamCapacity,
        is_unconfirmed: false,
        verification_notes: editNotes
      });
      setSelectedRoom(null);
      await fetchReconciliationData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Verification update failed');
    } finally {
      setSubmittingVerify(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSavingSettings(true);
      for (const [key, val] of Object.entries(editingSettings)) {
        await api.put(`/reconciliation/settings/${key}`, { value: val });
      }
      alert('System configuration parameters saved successfully.');
      await fetchReconciliationData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save settings.');
    } finally {
      setSavingSettings(false);
    }
  };

  const handleUploadCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;

    const formData = new FormData();
    formData.append('file', csvFile);

    try {
      setImporting(true);
      const res = await api.post('/reconciliation/students/import-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(res.data);
      setCsvFile(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'CSV Import failed');
    } finally {
      setImporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16 text-slate-500 font-medium">
        <RefreshCw className="w-5 h-5 animate-spin mr-2 text-blue-600" />
        Loading Reconciliation Ledger & Policy Registry...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 border border-amber-500/20">
              DevOps & Design Specification Table 9
            </span>
            <span className="text-xs text-slate-400">|</span>
            <span className="text-xs font-medium text-slate-500">Corrected Campus Design v1.0</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Reconciliation Ledger & Governance
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Audit trail of structural discrepancies, unconfirmed room labels, and campus buffer calibration.
          </p>
        </div>

        <button
          onClick={fetchReconciliationData}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Registry
        </button>
      </div>

      {/* Metric Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Total Recorded Spaces</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{summary.total_recorded_spaces ?? 34}</p>
          <span className="text-[10px] text-slate-400">Appendix A Register</span>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-emerald-600">Bookable Rooms</p>
          <p className="text-2xl font-bold text-emerald-700 mt-1">{summary.total_bookable_rooms ?? 30}</p>
          <span className="text-[10px] text-emerald-600/80">Available for scheduling</span>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Non-Bookable Utilities</p>
          <p className="text-2xl font-bold text-slate-700 mt-1">{summary.total_non_bookable ?? 4}</p>
          <span className="text-[10px] text-slate-400">Offices (TO, DO, PC) & Store</span>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-amber-600">Unconfirmed Flags</p>
          <p className="text-2xl font-bold text-amber-700 mt-1">{summary.unconfirmed_count ?? 8}</p>
          <span className="text-[10px] text-amber-600/80">Blueprint assumption markers</span>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-purple-600">Admin Gated</p>
          <p className="text-2xl font-bold text-purple-700 mt-1">{summary.pending_verification_count ?? 2}</p>
          <span className="text-[10px] text-purple-600/80">LH13 & LH14 restricted</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('ledger')}
          className={`pb-3 border-b-2 flex items-center gap-2 ${
            activeTab === 'ledger'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Table 9 Ledger ({ledgerItems.length})
        </button>
        <button
          onClick={() => setActiveTab('rooms')}
          className={`pb-3 border-b-2 flex items-center gap-2 ${
            activeTab === 'rooms'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Flagged Spaces ({flaggedRooms.length})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`pb-3 border-b-2 flex items-center gap-2 ${
            activeTab === 'settings'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sliders className="w-4 h-4" />
          Campus Buffers & Constraints
        </button>
        <button
          onClick={() => setActiveTab('import')}
          className={`pb-3 border-b-2 flex items-center gap-2 ${
            activeTab === 'import'
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          Student CSV Import
        </button>
      </div>

      {/* TAB 1: TABLE 9 RECONCILIATION LEDGER */}
      {activeTab === 'ledger' && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200/80 rounded-xl flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-900 leading-relaxed">
              <span className="font-semibold">Authoritative Principle:</span> Stating structural disagreements openly in this ledger is strictly stronger than quietly resolving them, because each reconciliation records an explicit design decision that evaluation panelists and university administrators can audit.
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {ledgerItems.map((item) => (
              <div key={item.id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-slate-300 transition-all">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold">
                      {item.id}
                    </span>
                    <h3 className="text-base font-bold text-slate-900">{item.title}</h3>
                  </div>
                  <span className="self-start sm:self-auto px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                    {item.status}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-xs">
                  <div className="p-3 bg-red-50/60 rounded-lg border border-red-100">
                    <p className="font-semibold text-red-900 mb-1 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-600" /> Disagreement
                    </p>
                    <p className="text-slate-700 leading-relaxed">{item.disagreement}</p>
                  </div>
                  <div className="p-3 bg-emerald-50/60 rounded-lg border border-emerald-100">
                    <p className="font-semibold text-emerald-900 mb-1 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> System Decision
                    </p>
                    <p className="text-slate-700 leading-relaxed">{item.decision}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                    <p className="font-semibold text-slate-900 mb-1 flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-blue-600" /> Architectural Rationale
                    </p>
                    <p className="text-slate-600 leading-relaxed">{item.rationale}</p>
                  </div>
                </div>

                <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-medium text-slate-500">Affected Campus Units:</span>
                  {item.affected_rooms.map((rm) => (
                    <span key={rm} className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-100 text-slate-800 border border-slate-200">
                      {rm}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: FLAGGED SPACES ACTION CONSOLE */}
      {activeTab === 'rooms' && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Flagged Blueprint Spaces</h3>
                <p className="text-xs text-slate-500 mt-0.5">Rooms requiring verification, unconfirmed status confirmation, or capacity adjustments.</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Room Code</th>
                    <th className="py-3 px-4">Building / Floor</th>
                    <th className="py-3 px-4">Nominal Cap</th>
                    <th className="py-3 px-4">Spaced Exam Cap</th>
                    <th className="py-3 px-4">Verification Status</th>
                    <th className="py-3 px-4">Flag / Reason</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {flaggedRooms.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{r.room_number}</td>
                      <td className="py-3 px-4 text-slate-600">{r.building_code} • {r.floor_name}</td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{r.capacity} seats</td>
                      <td className="py-3 px-4 font-semibold text-blue-700">{r.exam_capacity ?? Math.floor(r.capacity * 0.5)} seats</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          r.verification_status === 'OFFICIAL_VERIFIED' 
                            ? 'bg-emerald-100 text-emerald-800' 
                            : r.verification_status === 'PENDING_ADMIN_VERIFICATION'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-200 text-slate-800'
                        }`}>
                          {r.verification_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500 max-w-xs truncate">
                        {r.unconfirmed_reason || r.verification_notes || 'Assumed capacity band'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenVerifyModal(r)}
                          className="px-2.5 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                        >
                          Verify & Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CAMPUS BUFFERS & CONSTRAINTS */}
      {activeTab === 'settings' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Campus Travel Buffers & Scheduling Policies</h3>
            <p className="text-xs text-slate-500 mt-1">
              Fine-tune the mathematical parameters that govern transit penalties, exam spacing ratios, and reservation durations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {settings.map((s) => (
              <div key={s.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-mono font-bold text-slate-800">{s.key}</label>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white text-slate-500 border border-slate-200">
                    {s.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">{s.description}</p>
                <div className="pt-2">
                  <input
                    type="text"
                    value={editingSettings[s.key] ?? s.value}
                    onChange={(e) => setEditingSettings({ ...editingSettings, [s.key]: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 font-mono"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleSaveSettings}
              disabled={savingSettings}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {savingSettings ? 'Saving...' : 'Apply System Policies'}
            </button>
          </div>
        </div>
      )}

      {/* TAB 4: STUDENT CSV IMPORT */}
      {activeTab === 'import' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Batch Student Enrollment (CSV Import)</h3>
            <p className="text-xs text-slate-500 mt-1">
              Upload institutional student records to initialize credentials, section cohorts, and personalized academic timetables.
            </p>
          </div>

          <form onSubmit={handleUploadCSV} className="space-y-4">
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-blue-400 transition-colors">
              <Upload className="w-10 h-10 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">Choose a CSV file containing student records</p>
              <p className="text-[11px] text-slate-400 mt-1">Headers required: email, full_name, roll_number, branch_code, year, section</p>

              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
                className="mt-4 text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {csvFile ? `Selected file: ${csvFile.name} (${Math.round(csvFile.size / 1024)} KB)` : 'No file selected.'}
              </span>
              <button
                type="submit"
                disabled={!csvFile || importing}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition-all flex items-center gap-2"
              >
                <Upload className="w-3.5 h-3.5" />
                {importing ? 'Processing Records...' : 'Import Students'}
              </button>
            </div>
          </form>

          {importResult && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Import Completed Successfully
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-slate-700">
                <div className="p-2.5 bg-white rounded-lg border border-emerald-100">
                  <span className="text-slate-400 text-[10px]">Imported Students</span>
                  <p className="text-lg font-bold text-emerald-700">{importResult.imported_records}</p>
                </div>
                <div className="p-2.5 bg-white rounded-lg border border-emerald-100">
                  <span className="text-slate-400 text-[10px]">Duplicates Skipped</span>
                  <p className="text-lg font-bold text-amber-700">{importResult.skipped_duplicates}</p>
                </div>
                <div className="p-2.5 bg-white rounded-lg border border-emerald-100">
                  <span className="text-slate-400 text-[10px]">Validation Errors</span>
                  <p className="text-lg font-bold text-slate-700">{importResult.validation_errors?.length || 0}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VERIFY ROOM MODAL */}
      {selectedRoom && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Verify Room {selectedRoom.room_number}</h3>
                <p className="text-xs text-slate-500">{selectedRoom.building_code} • {selectedRoom.room_name}</p>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-100 rounded text-slate-600">
                ID #{selectedRoom.id}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Verification Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="OFFICIAL_VERIFIED">OFFICIAL_VERIFIED (Cleared for Open Faculty Booking)</option>
                  <option value="PENDING_ADMIN_VERIFICATION">PENDING_ADMIN_VERIFICATION (Blueprint Discrepancy Gate)</option>
                  <option value="RESTRICTED">RESTRICTED (Administrative Clearance Only)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Nominal Capacity</label>
                  <input
                    type="number"
                    value={editCapacity}
                    onChange={(e) => setEditCapacity(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Spaced Exam Cap</label>
                  <input
                    type="number"
                    value={editExamCapacity}
                    onChange={(e) => setEditExamCapacity(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Administrative Verification Notes</label>
                <textarea
                  rows={3}
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Record justification, physical inspection date, or authority approval..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={() => setSelectedRoom(null)}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={submittingVerify}
                onClick={handleSaveRoomVerification}
                className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-all disabled:opacity-50"
              >
                {submittingVerify ? 'Saving...' : 'Confirm Verification'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
