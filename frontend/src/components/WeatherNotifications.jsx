import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { scheduleNotification, fetchNotifications, deleteNotification } from '../services/api';
import { Bell, Calendar, Clock, CloudRain, Thermometer, CheckCircle2, Trash2, Loader2, AlertCircle } from 'lucide-react';

export default function WeatherNotifications({ currentLocation }) {
  const { user, token } = useAuth();
  
  const [targetDate, setTargetDate] = useState('Tomorrow');
  const [targetTime, setTargetTime] = useState(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 2); // Default to 2 minutes in the future for fast testing
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  });
  const [notifType, setNotifType] = useState('full'); // 'rain' | 'temperature' | 'full'
  
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const loadSchedules = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const items = await fetchNotifications(token);
      setSchedules(items || []);
    } catch (err) {
      console.warn('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules();
    // Refresh schedule status every 10 seconds
    const timer = setInterval(() => {
      if (token) loadSchedules();
    }, 10000);
    return () => clearInterval(timer);
  }, [token]);

  const handleSchedule = async (e) => {
    e.preventDefault();
    if (!token || !user) {
      setStatusMsg({ type: 'error', text: 'Please log in to schedule weather notifications.' });
      return;
    }

    setSubmitting(true);
    setStatusMsg(null);

    try {
      await scheduleNotification(token, targetDate, targetTime, notifType, currentLocation);
      setStatusMsg({ type: 'success', text: `✅ Weather notification scheduled for ${targetDate} at ${targetTime}!` });
      await loadSchedules();
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to schedule notification.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!token) return;
    try {
      await deleteNotification(token, id);
      setSchedules(prev => prev.filter(item => item.id !== id));
      setStatusMsg({ type: 'success', text: 'Notification cancelled successfully.' });
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to cancel notification.' });
    }
  };

  const setQuickTimeMinutes = (mins) => {
    const d = new Date();
    d.setMinutes(d.getMinutes() + mins);
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    setTargetDate('Today');
    setTargetTime(`${hh}:${mm}`);
  };

  if (!user) {
    return (
      <div className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-800 text-center mb-8">
        <Bell className="w-10 h-10 text-cyan-400 mx-auto mb-3 animate-bounce" />
        <h3 className="text-xl font-bold text-white font-heading">Scheduled Weather Notifications</h3>
        <p className="text-slate-400 text-xs mt-1 max-w-md mx-auto">
          Log in to receive automated email forecasts and rain alerts sent directly to your email at your preferred time.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-2xl mb-8">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-xl font-bold text-white font-heading flex items-center gap-2">
            <Bell className="w-6 h-6 text-cyan-400" /> Scheduled Weather Email Notifications
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            Automated weather alerts sent to <span className="text-cyan-400 font-semibold">{user.email}</span> for {currentLocation?.displayName || currentLocation?.name || 'Selected Location'}
          </p>
        </div>
      </div>

      {/* Status Alert Banner */}
      {statusMsg && (
        <div className={`p-4 rounded-2xl mb-6 text-xs font-semibold flex items-center justify-between transition-all ${
          statusMsg.type === 'success'
            ? 'bg-emerald-500/15 border border-emerald-500/40 text-emerald-300'
            : 'bg-rose-500/15 border border-rose-500/40 text-rose-300'
        }`}>
          <span>{statusMsg.text}</span>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-white font-bold ml-2">✕</button>
        </div>
      )}

      {/* Scheduling Form */}
      <form onSubmit={handleSchedule} className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        {/* Date Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Select Date
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['Today', 'Tomorrow', 'Day After Tomorrow'].map((dateOpt) => (
              <button
                key={dateOpt}
                type="button"
                onClick={() => setTargetDate(dateOpt)}
                className={`py-2 px-2 rounded-xl text-[11px] font-bold transition-all border ${
                  targetDate === dateOpt
                    ? 'bg-cyan-500 text-black border-cyan-400 shadow-md shadow-cyan-500/20'
                    : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:border-cyan-500/50'
                }`}
              >
                {dateOpt === 'Day After Tomorrow' ? 'Day After' : dateOpt}
              </button>
            ))}
          </div>
        </div>

        {/* Time Selector */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400" /> Exact Time
            </label>
            <button
              type="button"
              onClick={() => setQuickTimeMinutes(2)}
              className="text-[10px] text-cyan-400 hover:underline font-semibold"
            >
              +2 Mins (Quick Test)
            </button>
          </div>
          <input
            type="time"
            value={targetTime}
            onChange={(e) => setTargetTime(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl px-3 py-2 text-sm font-semibold focus:outline-none focus:border-cyan-500 transition-all"
            required
          />
        </div>

        {/* Type Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-300 mb-2">
            Notification Type
          </label>
          <select
            value={notifType}
            onChange={(e) => setNotifType(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-cyan-500 transition-all"
          >
            <option value="full">🌦️ Full Weather Intelligence Briefing</option>
            <option value="rain">🌧️ Rain & Precipitation Alert</option>
            <option value="temperature">🌡️ Temperature Forecast</option>
          </select>
        </div>

        {/* Submit Button (Full Width) */}
        <div className="md:col-span-3 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="w-full sm:w-auto px-8 py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs transition-all shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Scheduling...
              </>
            ) : (
              <>
                <Bell className="w-4 h-4" /> Schedule Weather Alert
              </>
            )}
          </button>
        </div>
      </form>

      {/* Active Schedules List */}
      <div className="pt-6 border-t border-slate-800">
        <h4 className="text-sm font-bold text-white font-heading mb-4 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" /> Active Notification Schedules ({schedules.length})
          </span>
          {loading && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
        </h4>

        {schedules.length === 0 ? (
          <div className="text-center py-6 text-slate-500 text-xs bg-slate-900/50 rounded-2xl border border-slate-800/80">
            No scheduled weather alerts yet. Pick a time above to schedule your first alert!
          </div>
        ) : (
          <div className="space-y-3">
            {schedules.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-4 transition-all hover:border-slate-700"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-base border ${
                    item.type === 'rain' ? 'bg-blue-500/10 text-blue-400 border-blue-500/30' :
                    item.type === 'temperature' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                    'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  }`}>
                    {item.type === 'rain' ? '🌧️' : item.type === 'temperature' ? '🌡️' : '🌦️'}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-xs">
                        {item.type === 'rain' ? 'Rain Alert' : item.type === 'temperature' ? 'Temp Forecast' : 'Full Weather'}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        item.status === 'sent' ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' :
                        item.status === 'processing' ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse' :
                        item.status === 'failed' ? 'bg-rose-500/15 text-rose-300 border-rose-500/30' :
                        'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                      }`}>
                        {item.status.toUpperCase()}
                      </span>
                    </div>

                    <p className="text-slate-400 text-[11px] mt-0.5">
                      📅 <strong>{item.target_date}</strong> at <strong>{item.target_time}</strong> ({item.location_name})
                    </p>
                  </div>
                </div>

                {item.status === 'pending' && (
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                    title="Cancel Schedule"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
