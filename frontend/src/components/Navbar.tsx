import React from 'react';
import { useAuth } from '../context/AuthContext';
import { NotificationCenter } from './NotificationCenter';
import { 
  Building2, LogOut, User, Shield, GraduationCap, 
  Menu, Sparkles, ChevronDown 
} from 'lucide-react';

interface NavbarProps {
  onToggleSidebar?: () => void;
  onNavigateLanding?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar, onNavigateLanding }) => {
  const { user, logout, loginAsDemoRole } = useAuth();

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
            <Shield className="w-3 h-3 text-purple-600" /> ADMIN
          </span>
        );
      case 'FACULTY':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <User className="w-3 h-3 text-blue-600" /> FACULTY
          </span>
        );
      case 'STUDENT':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <GraduationCap className="w-3 h-3 text-emerald-600" /> STUDENT
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 px-4 md:px-8 py-3.5">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Brand & Mobile Sidebar Toggle */}
        <div className="flex items-center gap-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl"
              aria-label="Toggle Navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div
            onClick={onNavigateLanding}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-700 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base md:text-lg tracking-tight text-slate-900 font-sans">
                  CampusSync<span className="text-blue-600">AI</span>
                </span>
                <span className="hidden sm:inline px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 rounded border border-blue-200">
                  DDUGU
                </span>
              </div>
              <p className="hidden md:block text-[11px] text-slate-400 font-medium -mt-0.5">
                Smart Campus. Smarter Scheduling.
              </p>
            </div>
          </div>
        </div>

        {/* Right: Notifications, Quick Role Switcher & User Profile */}
        <div className="flex items-center gap-3">
          {/* Quick switch test accounts dropdown */}
          <div className="hidden md:flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium">
            <span className="px-2 text-[10px] uppercase font-bold text-slate-400">Switch:</span>
            <button
              onClick={() => loginAsDemoRole('admin')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                user?.role === 'ADMIN' ? 'bg-white text-blue-700 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Admin
            </button>
            <button
              onClick={() => loginAsDemoRole('faculty')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                user?.role === 'FACULTY' ? 'bg-white text-blue-700 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Faculty
            </button>
            <button
              onClick={() => loginAsDemoRole('student')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                user?.role === 'STUDENT' ? 'bg-white text-blue-700 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Student
            </button>
          </div>

          {/* In-app Notification Center */}
          <NotificationCenter />

          {/* User Profile Chip */}
          {user ? (
            <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
              <div className="hidden sm:block text-right">
                <div className="flex items-center justify-end gap-1.5">
                  <span className="text-xs font-bold text-slate-800 truncate max-w-[140px]">
                    {user.full_name}
                  </span>
                  {getRoleBadge(user.role)}
                </div>
                <div className="text-[11px] text-slate-400 truncate max-w-[160px]">
                  {user.student_profile
                    ? `${user.student_profile.branch_code} Yr ${user.student_profile.year}-${user.student_profile.section}`
                    : user.department || user.email}
                </div>
              </div>

              <button
                onClick={logout}
                title="Sign out"
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => loginAsDemoRole('admin')}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-all shadow-sm"
            >
              Log In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
