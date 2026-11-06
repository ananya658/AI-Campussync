import React, { useState, useEffect } from 'react';
import { Announcement } from '../../types';
import { api } from '../../services/api';
import { 
  Megaphone, Plus, History, Calendar, Clock, MapPin, 
  Users, AlertCircle, Edit, CheckCircle2 
} from 'lucide-react';

export const AnnouncementsPage: React.FC = () => {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [viewingVersions, setViewingVersions] = useState<Announcement | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [announcementType, setAnnouncementType] = useState('MINOR_EXAM');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  // Editing state
  const [editingAnn, setEditingAnn] = useState<Announcement | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [changeSummary, setChangeSummary] = useState('');

  const loadAnnouncements = async () => {
    setLoading(true);
    try {
      const data = await api.getAnnouncements();
      setAnnouncements(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createAnnouncement({
        title,
        description,
        announcement_type: announcementType,
        date: date || undefined,
        start_time: startTime || undefined,
        end_time: endTime || undefined,
        status: 'PUBLISHED',
      });
      setIsCreateOpen(false);
      setTitle('');
      setDescription('');
      loadAnnouncements();
    } catch (err: any) {
      alert(err.message || 'Failed to publish notice');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAnn) return;
    try {
      await api.updateAnnouncement(editingAnn.id, {
        title: editTitle,
        description: editDesc,
        change_summary: changeSummary || 'Notice revised',
      });
      setEditingAnn(null);
      loadAnnouncements();
    } catch (err: any) {
      alert(err.message || 'Failed to update notice');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Academic Notices & Examination Rosters
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Publish official university announcements, examination venues, and maintain immutable version history.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center gap-1.5 transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> Publish Official Notice
        </button>
      </div>

      {/* Announcements List */}
      <div className="space-y-4">
        {announcements.map((a) => {
          const isExam = a.announcement_type.includes('EXAM');
          return (
            <div
              key={a.id}
              className={`p-5 rounded-2xl bg-white border transition-all ${
                isExam ? 'border-indigo-200 shadow-sm' : 'border-slate-200'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        isExam ? 'bg-indigo-100 text-indigo-800' : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {a.announcement_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      Version {a.version}.0
                    </span>
                    <span className="text-xs text-slate-400">
                      Published by {a.creator_name || 'Academic Office'}
                    </span>
                  </div>

                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    {a.title}
                  </h3>

                  <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                    {a.description}
                  </p>

                  {/* Schedule Details if Exam/Session */}
                  {(a.date || a.room_number) && (
                    <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-600">
                      {a.date && (
                        <div className="flex items-center gap-1.5 font-medium">
                          <Calendar className="w-3.5 h-3.5 text-blue-600" />
                          {a.date}
                        </div>
                      )}
                      {a.start_time && (
                        <div className="flex items-center gap-1.5 font-medium">
                          <Clock className="w-3.5 h-3.5 text-blue-600" />
                          {a.start_time.slice(0, 5)} - {a.end_time?.slice(0, 5)}
                        </div>
                      )}
                      {a.room_number && (
                        <div className="flex items-center gap-1.5 font-bold text-indigo-700">
                          <MapPin className="w-3.5 h-3.5" />
                          Room {a.room_number} ({a.building_name})
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 pt-2 md:pt-0">
                  <button
                    onClick={() => {
                      setEditingAnn(a);
                      setEditTitle(a.title);
                      setEditDesc(a.description);
                      setChangeSummary('');
                    }}
                    className="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-blue-50 border border-slate-200 text-xs font-semibold flex items-center gap-1"
                    title="Edit and create new version"
                  >
                    <Edit className="w-3.5 h-3.5" /> Edit
                  </button>

                  <button
                    onClick={() => setViewingVersions(a)}
                    className="p-2 rounded-xl text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 border border-slate-200 text-xs font-semibold flex items-center gap-1"
                    title="View version history"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span>{a.versions.length || a.version} Versions</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Announcement Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <Megaphone className="w-5 h-5 text-blue-600" />
              Publish Official Campus Notice
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Notices are broadcasted to affected students and recorded with versioning.
            </p>

            <form onSubmit={handleCreate} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Notice Type
                </label>
                <select
                  value={announcementType}
                  onChange={(e) => setAnnouncementType(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                >
                  <option value="MINOR_EXAM">Minor Examination</option>
                  <option value="MAJOR_EXAM">Major Examination</option>
                  <option value="EXTRA_LECTURE">Extra Lecture Notice</option>
                  <option value="PRACTICAL_EXAM">Practical Examination</option>
                  <option value="SCHEDULE_CHANGE">Schedule Change</option>
                  <option value="ACADEMIC_EVENT">Academic Event</option>
                  <option value="IMPORTANT_NOTICE">Important Circular</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. B.Tech Odd Semester Minor Exam Venue Allotment"
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter detailed notification body, instructions, and room arrangements."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Date</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">End Time</label>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                >
                  Publish Notice
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit / New Version Modal */}
      {editingAnn && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <Edit className="w-5 h-5 text-blue-600" />
              Update Notice (Creating Version {editingAnn.version + 1}.0)
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Updating will increment version number, notify affected students, and preserve the previous version.
            </p>

            <form onSubmit={handleEditSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  required
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Revision Summary (Mandatory for Version History)
                </label>
                <input
                  type="text"
                  required
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  placeholder="e.g. Venue upgraded from IET17 to Deeksha Bhawan LH01 for extra capacity"
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setEditingAnn(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                >
                  Save & Publish Revision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Drawer / Modal */}
      {viewingVersions && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-indigo-600" />
                  Notice Version Audit Trail
                </h3>
                <p className="text-xs text-slate-500">{viewingVersions.title}</p>
              </div>
              <button
                onClick={() => setViewingVersions(null)}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100"
              >
                Close
              </button>
            </div>

            <div className="overflow-y-auto py-4 space-y-4">
              {viewingVersions.versions.map((ver) => (
                <div key={ver.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                      Version {ver.version}.0
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {new Date(ver.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-800">{ver.title}</div>
                  <p className="text-slate-600 mt-1 leading-relaxed">{ver.description}</p>
                  <div className="mt-2 pt-2 border-t border-slate-200 text-indigo-700 font-medium">
                    Change Note: {ver.change_summary}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
