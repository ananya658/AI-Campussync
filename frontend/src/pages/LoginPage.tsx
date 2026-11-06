import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Building2, Shield, User, GraduationCap, Lock, Mail, 
  ArrowRight, AlertCircle, CheckCircle2 
} from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const { login, loginAsDemoRole } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickDemo = async (role: 'admin' | 'faculty' | 'student') => {
    setError(null);
    setSubmitting(true);
    try {
      await loginAsDemoRole(role);
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-700 to-indigo-600 text-white shadow-lg shadow-blue-500/25 mb-3">
          <Building2 className="w-6 h-6" />
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          CampusSync AI
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Smart Campus. Smarter Scheduling. • DDUGU Portal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl shadow-slate-200/50 sm:rounded-2xl sm:px-10 border border-slate-200/80">
          {error && (
            <div className="mb-4 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                Email Address
              </label>
              <div className="mt-1.5 relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. admin@ddugu.ac.in"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                Password
              </label>
              <div className="mt-1.5 relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Authenticating...' : 'Sign In to Portal'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Sign-In Divider */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-slate-400 font-bold tracking-wider">
                  Or One-Click Test Login
                </span>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <button
                type="button"
                onClick={() => handleQuickDemo('admin')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-purple-200 bg-purple-50/60 hover:bg-purple-100/80 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-purple-600 text-white">
                    <Shield className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-purple-950">Dean / Admin Account</div>
                    <div className="text-[11px] text-purple-700">admin@ddugu.ac.in</div>
                  </div>
                </div>
                <span className="text-[11px] font-semibold text-purple-600 group-hover:translate-x-0.5 transition-transform">
                  Sign In →
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemo('faculty')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-blue-200 bg-blue-50/60 hover:bg-blue-100/80 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-blue-600 text-white">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-blue-950">Faculty Account (HOD CSE)</div>
                    <div className="text-[11px] text-blue-700">prof.sharma@ddugu.ac.in</div>
                  </div>
                </div>
                <span className="text-[11px] font-semibold text-blue-600 group-hover:translate-x-0.5 transition-transform">
                  Sign In →
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemo('student')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-emerald-200 bg-emerald-50/60 hover:bg-emerald-100/80 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-emerald-600 text-white">
                    <GraduationCap className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-emerald-950">Student (CSE Yr 3 Sec A)</div>
                    <div className="text-[11px] text-emerald-700">rahul.cse23@ddugu.ac.in</div>
                  </div>
                </div>
                <span className="text-[11px] font-semibold text-emerald-600 group-hover:translate-x-0.5 transition-transform">
                  Sign In →
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
