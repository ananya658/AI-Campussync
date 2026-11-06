import React, { useState } from 'react';
import { AISearchResponse, Room } from '../../types';
import { api } from '../../services/api';
import { 
  Sparkles, Send, CheckCircle2, Clock, MapPin, 
  Users, ArrowRight, AlertTriangle, Layers, HelpCircle 
} from 'lucide-react';

interface AIAssistantPageProps {
  onBookRoom: (room: Room) => void;
}

export const AIAssistantPage: React.FC<AIAssistantPageProps> = ({ onBookRoom }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AISearchResponse | null>(null);

  const samplePrompts = [
    'Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM',
    'Find a laboratory for an IT practical session tomorrow at 2 PM',
    'Find a seminar hall for 150 students with projector and audio system',
    'Find a lecture hall in Deeksha Bhawan for 80 students tomorrow at 10 AM',
  ];

  const handleSearch = async (textToSearch?: string) => {
    const q = textToSearch || query;
    if (!q.trim()) return;
    setLoading(true);
    try {
      const data = await api.aiSearch(q);
      setResult(data);
    } catch (err: any) {
      alert(err.message || 'AI assistant search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold uppercase tracking-wider mb-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          CampusSync AI Assistant
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Natural Language Classroom Allocator
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Ask in plain English. The AI parses your constraints, cross-checks actual database booking records, and computes scored recommendations.
        </p>
      </div>

      {/* Query Bar */}
      <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="flex items-center gap-3"
        >
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM"
              className="w-full text-xs sm:text-sm p-3.5 pl-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:bg-white transition-all font-medium"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-indigo-500/20 flex items-center gap-2 transition-all disabled:opacity-50 shrink-0"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Analyzing DB...
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" /> Recommend
              </span>
            )}
          </button>
        </form>

        {/* Quick Sample Prompts */}
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1">
            Try asking:
          </span>
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(p);
                handleSearch(p);
              }}
              className="text-left text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
            >
              "{p}"
            </button>
          ))}
        </div>
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {/* Interpreted Constraints Strip */}
          <div className="p-4 rounded-2xl bg-slate-900 text-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Interpreted Parameters:
            </div>
            <div className="flex flex-wrap items-center gap-3 text-[11px]">
              <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Date: <strong>{result.interpreted_query.date}</strong>
              </span>
              <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Slot: <strong>{result.interpreted_query.start_time} - {result.interpreted_query.end_time}</strong>
              </span>
              <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Cap: <strong>{result.interpreted_query.required_capacity} seats</strong>
              </span>
              <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Building: <strong>{result.interpreted_query.building}</strong>
              </span>
            </div>
          </div>

          {/* AI Explanation Summary */}
          <div className="p-4 rounded-2xl bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-950 flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{result.raw_ai_explanation}</p>
          </div>

          {/* Primary Recommendation Card */}
          {result.primary_recommendation ? (
            <div className="p-6 rounded-3xl bg-white border-2 border-blue-600 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      Top Verified Match
                    </span>
                    <span className="text-xs text-slate-400">
                      {result.primary_recommendation.room.building_name} • {result.primary_recommendation.room.floor_name}
                    </span>
                  </div>
                  <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2">
                    {result.primary_recommendation.room.room_number}
                    <span className="text-sm font-semibold text-slate-500">
                      ({result.primary_recommendation.room.room_name})
                    </span>
                  </h2>
                </div>

                <div className="text-right">
                  <div className="text-3xl font-black text-blue-600">
                    {result.primary_recommendation.match_score}%
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Recommendation Score
                  </div>
                </div>
              </div>

              {/* Natural language explanation */}
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
                {result.primary_recommendation.explanation}
              </p>

              {/* Details & CTA */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
                <div className="flex items-center gap-4 text-xs text-slate-600">
                  <span className="flex items-center gap-1 font-bold text-slate-900">
                    <Users className="w-4 h-4 text-blue-600" />
                    Capacity: {result.primary_recommendation.room.capacity} students
                  </span>
                  <span>•</span>
                  <span>Buffer: +{result.primary_recommendation.capacity_difference} seats</span>
                </div>

                <button
                  onClick={() => onBookRoom(result.primary_recommendation!.room)}
                  className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
                >
                  Book {result.primary_recommendation.room.room_number} Now <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            /* No direct room available: Suggest alternative time slots */
            result.alternative_time_slots.length > 0 && (
              <div className="p-6 rounded-3xl bg-white border border-amber-200 shadow-sm space-y-4">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  Suggested Alternative Time Slots (No Overlap)
                </div>
                <p className="text-xs text-slate-600">
                  The requested time slot is occupied. The AI scheduling engine calculated these vacant slots:
                </p>
                <div className="grid sm:grid-cols-3 gap-3">
                  {result.alternative_time_slots.map((alt, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      <div className="font-bold text-slate-900">{alt.room_number}</div>
                      <div className="text-[11px] text-slate-500">{alt.building_name}</div>
                      <div className="font-semibold text-blue-700 mt-2">{alt.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {/* Alternative Rooms List */}
          {result.alternative_rooms.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">
                Alternative Verified Rooms
              </h3>
              <div className="grid sm:grid-cols-2 gap-3">
                {result.alternative_rooms.map((alt) => (
                  <div
                    key={alt.room.id}
                    className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-between gap-3 hover:border-blue-300 transition-all"
                  >
                    <div>
                      <div className="font-bold text-sm text-slate-900 flex items-center gap-2">
                        {alt.room.room_number}
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">
                          {alt.match_score}%
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {alt.room.building_name} • {alt.room.capacity} seats
                      </div>
                    </div>

                    <button
                      onClick={() => onBookRoom(alt.room)}
                      className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-blue-600 hover:text-white text-slate-700 font-semibold text-xs transition-all"
                    >
                      Book →
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
