import React, { useState } from 'react';
import { ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Calendar, Clock, CloudRain, Thermometer } from 'lucide-react';

export default function ForecastChart({ hourlyData = [], dailyData = [] }) {
  const [activeTab, setActiveTab] = useState('temp'); // 'temp' | 'rain'
  const [selectedDayIdx, setSelectedDayIdx] = useState(0); // Default to Today (Index 0)

  // Extract 24 hourly records for the selected day index (0..6)
  const startIdx = selectedDayIdx * 24;
  const dayHourlyData = hourlyData.slice(startIdx, startIdx + 24);
  
  // Fallback to first 24 if index slice is empty
  const activeHourly = dayHourlyData.length > 0 ? dayHourlyData : hourlyData.slice(0, 24);

  const formattedHourly = activeHourly.map(item => {
    let displayTime = item.time || '';
    if (displayTime.includes('T')) {
      displayTime = displayTime.split('T')[1].substring(0, 5);
    } else if (displayTime.includes(' ')) {
      displayTime = displayTime.split(' ')[1].substring(0, 5);
    }
    return {
      time: displayTime || item.time,
      temp: Math.round(item.temperature),
      pop: item.precipitation_probability,
      precip: item.precipitation,
      condition: item.condition,
    };
  });

  const selectedDayItem = dailyData[selectedDayIdx] || dailyData[0];
  const selectedDayLabel = selectedDayItem ? (selectedDayItem.date || selectedDayItem.day) : 'Today';

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 mb-8 transition-all">
      {/* Header & View Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-xl font-bold text-white font-heading flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyan-400" /> Hourly Forecast ({selectedDayLabel})
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">
            Showing hourly temperature & rain trend for {selectedDayLabel}
          </p>
        </div>

        <div className="flex items-center bg-dark-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('temp')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'temp'
                ? 'bg-cyan-500 text-black shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Thermometer className="w-3.5 h-3.5" /> Temperature
          </button>
          <button
            onClick={() => setActiveTab('rain')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'rain'
                ? 'bg-cyan-500 text-black shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <CloudRain className="w-3.5 h-3.5" /> Rain Chance
          </button>
        </div>
      </div>

      {/* Hourly Chart Display */}
      <div className="h-64 w-full mb-8">
        <ResponsiveContainer width="100%" height="100%">
          {activeTab === 'temp' ? (
            <AreaChart data={formattedHourly} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit="°" />
              <Tooltip
                contentStyle={{ background: '#111827', borderColor: '#374151', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                formatter={(value) => [`${value}°C`, 'Temperature']}
              />
              <Area type="monotone" dataKey="temp" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#tempGradient)" />
            </AreaChart>
          ) : (
            <BarChart data={formattedHourly} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: '#111827', borderColor: '#374151', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                formatter={(value) => [`${value}%`, 'Rain Probability']}
              />
              <Bar dataKey="pop" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* 7-Day Forecast Grid (Clickable Day Cards) */}
      {dailyData && dailyData.length > 0 && (
        <div className="pt-6 border-t border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-base font-bold text-white font-heading flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-400" /> 7-Day Weather Outlook
            </h4>
            <span className="text-[11px] text-cyan-400 font-semibold">
              💡 Click any day card to view its hourly forecast
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2.5">
            {dailyData.slice(0, 7).map((item, idx) => {
              const isSelected = selectedDayIdx === idx;
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedDayIdx(idx)}
                  className={`p-3 rounded-2xl border text-center flex flex-col items-center transition-all cursor-pointer relative ${
                    isSelected
                      ? 'bg-cyan-500/15 border-cyan-500 shadow-lg shadow-cyan-500/20 scale-[1.03] ring-1 ring-cyan-500/50'
                      : 'glass-card border-slate-800 glass-card-hover hover:border-cyan-500/40'
                  }`}
                >
                  <span className={`text-xs font-bold mb-1 ${isSelected ? 'text-cyan-300' : 'text-slate-300'}`}>
                    {item.date}
                  </span>
                  <span className="text-[11px] text-cyan-400 font-medium mb-2 truncate max-w-full">
                    {item.condition}
                  </span>
                  
                  <div className="flex items-center gap-1.5 text-xs mb-1">
                    <span className="font-bold text-white">{Math.round(item.temperature_max)}°</span>
                    <span className="text-slate-400">{Math.round(item.temperature_min)}°</span>
                  </div>

                  <div className={`text-[10px] px-2 py-0.5 rounded-full mt-1 border ${
                    isSelected
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-bold'
                      : 'bg-blue-500/10 text-blue-300 border-blue-500/20'
                  }`}>
                    🌧️ {item.precipitation_probability_max}%
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

