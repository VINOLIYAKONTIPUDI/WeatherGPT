import React from 'react';
import { Mic, LayoutDashboard, AlertTriangle, CloudSun, MapPin } from 'lucide-react';
import { getTranslation } from '../constants/languages';

export default function Navbar({
  activeTab,
  setActiveTab,
  alertCount = 0,
  currentLocation,
  language = 'en-IN',
  setLanguage
}) {
  const displayLocation = currentLocation
    ? `${currentLocation.city || currentLocation.name || 'Selected Location'}${
        currentLocation.state || currentLocation.admin1
          ? `, ${currentLocation.state || currentLocation.admin1}`
          : ''
      }`
    : getTranslation(language, 'locationNotSet');

  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-dark-900/80 border-b border-slate-800/80 mb-6">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3">
        {/* Brand Logo & Location Indicator */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 shrink-0">
            <CloudSun className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-white font-heading tracking-tight flex items-center gap-1.5">
              WeatherGPT
              <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-bold">
                SIH MVP
              </span>
            </h1>
            
            {/* Prominent Active Location Indicator */}
            <div className="flex items-center gap-1.5 text-[11px] font-semibold mt-0.5">
              <MapPin className={`w-3.5 h-3.5 ${currentLocation ? 'text-cyan-400' : 'text-amber-400 animate-pulse'}`} />
              <span className={currentLocation ? 'text-cyan-300' : 'text-amber-300 font-bold'}>
                {displayLocation}
              </span>
              {currentLocation ? (
                <button
                  onClick={() => {
                    const input = document.querySelector('input[type="text"]');
                    if (input) input.focus();
                  }}
                  className="text-[10px] text-slate-400 hover:text-cyan-300 underline ml-1"
                >
                  ({getTranslation(language, 'changeLocation')})
                </button>
              ) : (
                <button
                  onClick={() => {
                    const btn = document.getElementById('btn-use-my-location');
                    if (btn) btn.click();
                  }}
                  className="text-[10px] bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 px-2 py-0.5 rounded-full border border-amber-500/40 ml-1 transition-all"
                >
                  {getTranslation(language, 'setLocation')}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Section: Language Switcher & Tab Navigation */}
        <div className="flex items-center gap-3">
          {/* Header Language Selector: English | हिंदी | తెలుగు */}
          {setLanguage && (
            <div className="flex items-center bg-dark-800/90 p-1 rounded-2xl border border-slate-800 text-xs">
              <button
                onClick={() => setLanguage('en-IN')}
                className={`px-2.5 py-1 rounded-xl font-semibold transition-all ${
                  language === 'en-IN'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('hi-IN')}
                className={`px-2.5 py-1 rounded-xl font-semibold transition-all ${
                  language === 'hi-IN'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                हिंदी
              </button>
              <button
                onClick={() => setLanguage('te-IN')}
                className={`px-2.5 py-1 rounded-xl font-semibold transition-all ${
                  language === 'te-IN'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                తెలుగు
              </button>
            </div>
          )}

          {/* Tab Navigation */}
          <nav className="flex items-center gap-1 bg-dark-800/90 p-1 rounded-2xl border border-slate-800">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Mic className="w-3.5 h-3.5" /> Voice Hero
            </button>

            <button
              onClick={() => setActiveTab('forecast')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                activeTab === 'forecast'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" /> Dashboard
            </button>

            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all relative ${
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
      </div>
    </header>
  );
}
