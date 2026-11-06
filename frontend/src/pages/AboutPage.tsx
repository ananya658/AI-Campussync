import React from 'react';
import { 
  Building2, Sparkles, ShieldCheck, Clock, Map, 
  CheckCircle2, AlertTriangle, Layers, BookOpen 
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-bold uppercase tracking-wider mb-2">
          <BookOpen className="w-3.5 h-3.5" />
          Technical Architecture & Campus Context
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          About CampusSync AI
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Designed and developed for GDG on Campus "BUILD WITH AI: DevOps 2026" at Deen Dayal Upadhyaya Gorakhpur University (DDUGU).
        </p>
      </div>

      {/* 1. Problem & Mission */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-blue-600" />
          Problem Statement & University Context
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          At DDUGU, faculty frequently struggled to find vacant classrooms for extra lectures, bookings overlapped unpredictably, and students occasionally arrived at outdated examination venues. CampusSync AI provides a single source of truth across the university campus, synchronizing schedules, room locks, and notices in real time.
        </p>
      </div>

      {/* 2. Campus Infrastructure & Floor Plan Discrepancy Solution */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-600" />
          Actual Campus Infrastructure & Architectural Blueprint Modeling
        </h2>

        <div className="grid md:grid-cols-2 gap-4 pt-1">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-900">
              1. Institute of Engineering & Technology (IET)
            </h3>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Ground Floor:</strong> Central Library (180 capacity), Teachers' Lounge, Directorate, Placement Cell.</li>
              <li><strong>First Floor:</strong> CSE, ME, ECE, IT Laboratories and Classrooms IET 17, 18, 19, 20 (~75 seats each).</li>
              <li><strong>Second Floor:</strong> Seminar Hall IET32 (~200 capacity) and Classrooms IET 24, 25, 28, 29, 30.</li>
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-900">
              2. Deeksha Bhawan Complex (~100m from IET)
            </h3>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Ground Floor:</strong> Major Lecture Halls LH01 to LH07 (90 capacity each).</li>
              <li><strong>First Floor:</strong> Lecture Halls LH08 to LH12 (official bookable halls).</li>
              <li><strong>LH13 & LH14 Discrepancy:</strong> Visible in structural blueprints but omitted from written registry. Handled via formal administrative authorization.</li>
            </ul>
          </div>
        </div>

        {/* Highlight on Discrepancy Resolution */}
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
          <div className="font-bold flex items-center gap-1.5 text-amber-800">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            Hackathon Mandatory Requirement: Deeksha Bhawan Blueprint Discrepancy
          </div>
          <p className="text-amber-700 leading-relaxed">
            Rather than silently discarding LH13 and LH14, CampusSync AI treats room records as configurable with a distinct <code>PENDING_ADMIN_VERIFICATION</code> state. Administrators can conduct physical safety inspections and verify or restrict them with recorded audit logs before treating them as bookable classrooms.
          </p>
        </div>
      </div>

      {/* 3. Mathematical Conflict Prevention Engine */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          Conflict Prevention Engine
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Bookings are checked using the strict mathematical interval condition:
        </p>
        <div className="p-3 rounded-xl bg-slate-900 text-white font-mono text-xs">
          existing_start &lt; new_end AND existing_end &gt; new_start
        </div>
        <p className="text-xs text-slate-500 leading-relaxed">
          This condition is enforced at both the application layer and via atomic database transactions, preventing race conditions even when concurrent faculty members attempt simultaneous reservations.
        </p>
      </div>

      {/* 4. AI Recommendation Scoring */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600" />
          Multi-Attribute AI Recommendation Engine
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          When natural language queries are received ("Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM"), the system extracts structured parameters, runs real-time availability checks, and scores valid rooms using weighted utility:
        </p>
        <ul className="text-xs text-slate-600 space-y-1 list-disc pl-5">
          <li><strong>Capacity Fitness (45%):</strong> Maximizes comfort while penalizing excessive space wastage.</li>
          <li><strong>Building Preference (25%):</strong> Matches requested building proximity.</li>
          <li><strong>Floor Accessibility (15%):</strong> Ground and 1st floor accessibility priority.</li>
          <li><strong>Facility Match (15%):</strong> Projector, AC, smart boards, computing terminals.</li>
        </ul>
      </div>
    </div>
  );
};
