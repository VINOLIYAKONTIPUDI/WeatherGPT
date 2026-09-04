import React from 'react';
import { Mic, LayoutDashboard, AlertTriangle, CloudSun, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, alertCount = 0 }) {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-dark-900/80 border-b border-slate-800/80 mb-6">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
        {/* Brand Logo & Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <CloudSun className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-white font-heading tracking-tight flex items-center gap-1.5">
              WeatherGPT
              <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-bold">
                SIH MVP
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 hidden sm:block">Conversational Weather Intelligence Platform</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-1 bg-dark-800/90 p-1 rounded-2xl border border-slate-800">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Mic className="w-3.5 h-3.5" /> Voice Hero
          </button>

          <button
            onClick={() => setActiveTab('forecast')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'forecast'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" /> Dashboard
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all relative ${
              activeTab === 'alerts'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" /> Advisories
            {alertCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-amber-500 text-black text-[10px] font-bold flex items-center justify-center shrink-0">
                {alertCount}
              </span>
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}
