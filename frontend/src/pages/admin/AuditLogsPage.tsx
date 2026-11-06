import React, { useState, useEffect } from 'react';
import { AuditLogItem } from '../../types';
import { api } from '../../services/api';
import { ShieldAlert, Clock, Search, Filter, Shield, User } from 'lucide-react';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({
        action_type: actionFilter || undefined,
        entity_type: entityFilter || undefined,
      });
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [actionFilter, entityFilter]);

  const getActionColor = (action: string) => {
    switch (action) {
      case 'CREATE':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'CANCEL':
      case 'DELETE':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'APPROVE':
      case 'RESOLVE':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'UPDATE':
      default:
        return 'bg-amber-100 text-amber-800 border-amber-200';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Security & Academic Audit Trail
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Immutable log recording every booking creation, cancellation, schedule change, room modification, and report resolution.
          </p>
        </div>
      </div>

      {/* Filter Options */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Action Type
          </label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700"
          >
            <option value="">All Actions</option>
            <option value="CREATE">CREATE</option>
            <option value="CANCEL">CANCEL</option>
            <option value="UPDATE">UPDATE</option>
            <option value="RESOLVE">RESOLVE</option>
            <option value="APPROVE">APPROVE</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Entity Type
          </label>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700"
          >
            <option value="">All Entities</option>
            <option value="BOOKING">BOOKING</option>
            <option value="SCHEDULE">SCHEDULE</option>
            <option value="ANNOUNCEMENT">ANNOUNCEMENT</option>
            <option value="ROOM">ROOM</option>
            <option value="REPORT">REPORT</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">User & Role</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Reason / Notes</th>
                <th className="py-3 px-4">Snapshot Changes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono text-[11px]">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 font-sans">
                    No audit logs matching current filter.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                      {new Date(l.created_at).toLocaleString([], {
                        month: 'short',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-4 font-sans font-medium text-slate-900">
                      <div>{l.user_name || 'System Automated'}</div>
                      <span className="text-[10px] text-blue-600 font-bold uppercase">{l.user_role}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getActionColor(l.action_type)}`}>
                        {l.action_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      {l.entity_type} #{l.entity_id}
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-600 max-w-xs truncate" title={l.reason || ''}>
                      {l.reason || '—'}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-[10px] text-slate-500">
                      {l.new_value || l.previous_value || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
