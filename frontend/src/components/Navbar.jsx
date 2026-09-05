import React from 'react';
import { Mic, LayoutDashboard, AlertTriangle, CloudSun, MapPin, LogOut, UserCheck, ShieldAlert } from 'lucide-react';
import { getTranslation } from '../constants/languages';
import { useAuth } from '../context/AuthContext';

export default function Navbar({
  activeTab,
  setActiveTab,
  alertCount = 0,
  currentLocation,
  language = 'en-IN',
  setLanguage,
  onOpenEmergencyModal
}) {
  const { user, logout, isAuthenticated } = useAuth();

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

        {/* Right Section: Language Switcher, User Profile & Tab Navigation */}
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

          {/* User Profile Chip & Logout Button */}
          {isAuthenticated && user && (
            <div className="flex items-center gap-2 bg-dark-800/90 p-1 pl-2.5 pr-1.5 rounded-2xl border border-slate-800 text-xs">
              <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-white font-bold flex items-center justify-center text-[11px] shadow-sm shrink-0">
                {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="font-semibold text-slate-200 hidden sm:inline max-w-[100px] truncate" title={user.name}>
                {user.name}
              </span>
              <button
                onClick={logout}
                className="p-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-300 hover:text-red-200 border border-red-500/30 transition-all flex items-center gap-1"
                title="Logout from WeatherGPT"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden md:inline text-[11px] font-bold">Logout</span>
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

          {/* Emergency Alert & SMS Buzz Broadcast Trigger Button */}
          {onOpenEmergencyModal && (
            <button
              onClick={onOpenEmergencyModal}
              className="px-3 py-1.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white font-extrabold text-xs transition-all shadow-lg shadow-red-600/30 flex items-center gap-1.5 border border-red-400/40 animate-pulse shrink-0"
              title="Trigger Emergency Weather Disaster Broadcast & Siren"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-white" />
              <span className="hidden sm:inline">🚨 Alert SMS</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
