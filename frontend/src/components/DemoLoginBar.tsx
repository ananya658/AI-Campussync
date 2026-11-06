import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, GraduationCap, UserCheck } from 'lucide-react';

interface DemoLoginBarProps {
  onSuccess?: () => void;
}

export const DemoLoginBar: React.FC<DemoLoginBarProps> = ({ onSuccess }) => {
  const { loginAsDemoRole } = useAuth();

  const handleDemoClick = async (role: 'admin' | 'faculty' | 'student') => {
    try {
      await loginAsDemoRole(role);
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error('Demo login error', err);
    }
  };

  return (
    <div className="bg-slate-900/95 backdrop-blur-md text-white p-3.5 rounded-2xl border border-slate-800 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Quick 1-Click Role Switcher (Hackathon Test Accounts):
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleDemoClick('admin')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-sm transition-all"
          >
            <Shield className="w-3.5 h-3.5" />
            Admin (Dean Academics)
          </button>

          <button
            onClick={() => handleDemoClick('faculty')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-sm transition-all"
          >
            <UserCheck className="w-3.5 h-3.5" />
            Faculty (HOD CSE)
          </button>

          <button
            onClick={() => handleDemoClick('student')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-sm transition-all"
          >
            <GraduationCap className="w-3.5 h-3.5" />
            Student (CSE 3rd Yr)
          </button>
        </div>
      </div>
    </div>
  );
};

