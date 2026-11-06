import React from 'react';
import { 
  Building2, Sparkles, ShieldCheck, Clock, Users, ArrowRight, 
  Map, CheckCircle2, AlertTriangle, Layers, Calendar 
} from 'lucide-react';
import { DemoLoginBar } from '../components/DemoLoginBar';

interface LandingPageProps {
  onGetStarted: () => void;
  onExploreMap: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onExploreMap }) => {
  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 px-4 md:px-8 max-w-7xl mx-auto">
        {/* Subtle background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-xs font-bold uppercase tracking-wider shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            GDG BUILD WITH AI 2026 • DDU GORAKHPUR UNIVERSITY
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
            Smart Campus.{' '}
            <span className="bg-gradient-to-r from-blue-700 via-indigo-600 to-violet-600 bg-clip-text text-transparent">
              Smarter Scheduling.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto font-normal">
            A centralized AI-powered academic scheduling platform engineered for Deen Dayal Upadhyaya Gorakhpur University (DDUGU). Eliminates classroom booking overlaps, resolves blueprint discrepancies, and automates timetable sync.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={onGetStarted}
              className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center gap-2 transition-all hover:scale-[1.02]"
            >
              Launch Portal Now <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onExploreMap}
              className="px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-slate-800 font-semibold text-sm border border-slate-200/90 shadow-sm flex items-center gap-2 transition-all"
            >
              <Map className="w-4 h-4 text-blue-600" /> View Interactive Floor Plans
            </button>
          </div>

          {/* Quick Demo Credentials Bar */}
          <div className="pt-6">
            <DemoLoginBar onSuccess={onGetStarted} />
          </div>
        </div>

        {/* Live Metrics Row */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-center">
            <div className="text-3xl font-extrabold text-slate-900">2 Buildings</div>
            <div className="text-xs text-slate-500 font-medium mt-1">IET & Deeksha Bhawan</div>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-center">
            <div className="text-3xl font-extrabold text-blue-600">25 Rooms</div>
            <div className="text-xs text-slate-500 font-medium mt-1">Labs, Halls & Classrooms</div>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-center">
            <div className="text-3xl font-extrabold text-emerald-600">0 Overlaps</div>
            <div className="text-xs text-slate-500 font-medium mt-1">Mathematical Conflict Engine</div>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-center">
            <div className="text-3xl font-extrabold text-indigo-600">AI Powered</div>
            <div className="text-xs text-slate-500 font-medium mt-1">NLP Search & Scoring</div>
          </div>
        </div>
      </section>

      {/* Actual Campus Infrastructure Section */}
      <section className="py-16 bg-white border-t border-slate-200/80 px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Real University Campus Blueprint Modeling
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Faithfully digitizes official structural layouts from the DDUGU engineering master plans.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* IET Building Card */}
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 hover:border-blue-300 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-blue-600 text-white font-bold text-xs">IET</div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Institute of Engineering & Technology</h3>
                    <p className="text-xs text-slate-500">Engineering Complex • 3 Floors</p>
                  </div>
                </div>
                <span className="text-xs font-semibold px-2 py-1 rounded bg-blue-100 text-blue-800">
                  Ground, 1st & 2nd
                </span>
              </div>
              <ul className="text-xs text-slate-600 space-y-2 leading-relaxed">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                  <strong>Ground Floor:</strong> Central Library (180 cap), Teachers' Lounge, Directorate, Placement Cell.
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                  <strong>1st Floor:</strong> CSE, ME, ECE, IT Laboratories and Classrooms IET 17, 18, 19, 20 (75 cap each).
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                  <strong>2nd Floor:</strong> Seminar Hall IET32 (200 cap) and Lecture Rooms IET 24, 25, 28, 29, 30.
                </li>
              </ul>
            </div>

            {/* Deeksha Bhawan Card */}
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 hover:border-indigo-300 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-indigo-600 text-white font-bold text-xs">DB</div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Deeksha Bhawan</h3>
                    <p className="text-xs text-slate-500">Lecture Complex (100m from IET) • 2 Floors</p>
                  </div>
                </div>
                <span className="text-xs font-semibold px-2 py-1 rounded bg-indigo-100 text-indigo-800">
                  LH01 to LH14
                </span>
              </div>
              <ul className="text-xs text-slate-600 space-y-2 leading-relaxed">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  <strong>Ground Floor:</strong> Major Lecture Halls LH01 to LH07 (90 cap each).
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  <strong>1st Floor:</strong> Lecture Halls LH08 to LH12 (official bookable rooms).
                </li>
                <li className="flex items-center gap-2 text-amber-800 bg-amber-50 p-2 rounded-lg border border-amber-200">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <strong>LH13 & LH14 Blueprint Discrepancy:</strong> Configurable records subject to administrative authorization before official booking.
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

