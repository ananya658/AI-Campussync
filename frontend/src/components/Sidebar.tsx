import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, Map, Search, CalendarPlus, Calendar, 
  Sparkles, Megaphone, AlertCircle, ShieldAlert, BarChart3, 
  Building2, Clock, CheckSquare, Layers, FileText
} from 'lucide-react';

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  isOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  isOpen = false,
  onCloseMobile
}) => {
  const { user } = useAuth();
  if (!user) return null;

  interface NavItem {
    id: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
  }

  let navItems: NavItem[] = [];

  if (user.role === 'ADMIN') {
    navItems = [
      { id: 'admin-dashboard', label: 'Overview Dashboard', icon: LayoutDashboard },
      { id: 'interactive-map', label: 'Interactive Floor Map', icon: Map },
      { id: 'admin-buildings', label: 'Buildings & Rooms', icon: Building2 },
      { id: 'admin-bookings', label: 'Booking Requests', icon: Calendar },
      { id: 'admin-schedules', label: 'Academic Timetables', icon: Clock },
      { id: 'admin-announcements', label: 'Notices & Exams', icon: Megaphone },
      { id: 'admin-reports', label: 'Student Discrepancies', icon: AlertCircle },
      { id: 'admin-audit', label: 'Security Audit Logs', icon: ShieldAlert },
      { id: 'admin-analytics', label: 'Capacity Analytics', icon: BarChart3 },
    ];
  } else if (user.role === 'FACULTY') {
    navItems = [
      { id: 'faculty-dashboard', label: 'Faculty Dashboard', icon: LayoutDashboard },
      { id: 'room-finder', label: 'Smart Room Finder', icon: Search },
      { id: 'interactive-map', label: 'Campus Floor Map', icon: Map },
      { id: 'create-booking', label: 'Book a Classroom', icon: CalendarPlus },
      { id: 'my-bookings', label: 'My Reservations', icon: Calendar },
      { id: 'faculty-schedule', label: 'My Teaching Schedule', icon: Clock },
      { id: 'ai-assistant', label: 'CampusSync AI Assistant', icon: Sparkles, badge: 'AI' },
      { id: 'announcements-view', label: 'Notices & Updates', icon: Megaphone },
    ];
  } else if (user.role === 'STUDENT') {
    navItems = [
      { id: 'student-dashboard', label: 'Student Dashboard', icon: LayoutDashboard },
      { id: 'interactive-map', label: 'Campus Floor Map', icon: Map },
      { id: 'student-timetable', label: 'My Weekly Timetable', icon: Clock },
      { id: 'student-exams', label: 'Exam Room Allotments', icon: CheckSquare },
      { id: 'student-announcements', label: 'Notices & Circulars', icon: Megaphone },
      { id: 'student-report', label: 'Report Discrepancy', icon: AlertCircle },
    ];
  }

  const handleItemClick = (id: string) => {
    onNavigate(id);
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Workspace Portal Header */}
        <div className="p-5 border-b border-slate-800">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            PORTAL CONTEXT
          </div>
          <div className="font-bold text-white text-base mt-0.5">
            {user.role === 'ADMIN'
              ? 'Administration Portal'
              : user.role === 'FACULTY'
              ? 'Faculty Academic Portal'
              : 'Student Academic Portal'}
          </div>
          <div className="text-xs text-blue-400 font-medium mt-0.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            DDUGU Live Network
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleItemClick(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-bold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-indigo-500 text-white">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500">
          <div>GDG BUILD WITH AI 2026</div>
          <div className="text-slate-400 font-medium">CampusSync AI v1.0.0</div>
        </div>
      </aside>
    </>
  );
};

