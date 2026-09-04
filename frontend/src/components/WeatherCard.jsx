import React from 'react';
import { Sun, Cloud, CloudRain, CloudLightning, Wind, Droplets, Umbrella, SunMedium, Compass, Sunrise, Sunset } from 'lucide-react';

function getWeatherIcon(condition = '', isDay = 1) {
  const cond = condition.toLowerCase();
  if (cond.includes('thunder')) return <CloudLightning className="w-10 h-10 text-amber-400" />;
  if (cond.includes('rain') || cond.includes('drizzle') || cond.includes('shower')) return <CloudRain className="w-10 h-10 text-cyan-400" />;
  if (cond.includes('cloud') || cond.includes('overcast')) return <Cloud className="w-10 h-10 text-slate-300" />;
  return <Sun className="w-10 h-10 text-amber-300 animate-spin-slow" />;
}

export default function WeatherCard({ weatherData, location }) {
  if (!weatherData) return null;

  const current = weatherData.current;
  const loc = weatherData.location || location;

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 relative overflow-hidden mb-8">
      {/* Background Subtle Gradient */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
        {/* Left Column: Location & Main Temp */}
        <div>
          <div className="flex items-center gap-2 text-slate-400 text-sm font-medium mb-1">
            <span className="text-cyan-400 font-bold">📍 {loc?.name || 'Selected Location'}</span>
            {loc?.admin1 && <span>, {loc.admin1}</span>}
            {loc?.country && <span>, {loc.country}</span>}
          </div>
          
          <div className="flex items-baseline gap-4 my-2">
            <span className="text-5xl sm:text-6xl font-extrabold text-white font-heading tracking-tight">
              {Math.round(current.temperature)}°C
            </span>
            <div className="flex items-center gap-2">
              {getWeatherIcon(current.condition, current.is_day)}
              <span className="text-xl font-medium text-slate-200">{current.condition}</span>
            </div>
          </div>

          <p className="text-slate-400 text-sm">
            Feels like <span className="text-slate-200 font-semibold">{Math.round(current.apparent_temperature)}°C</span>
          </p>
        </div>

        {/* Right Grid: Weather Telemetry Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full md:w-auto">
          {/* Humidity */}
          <div className="glass-card p-3.5 rounded-2xl border border-slate-800/80 flex flex-col items-start">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
              <Droplets className="w-3.5 h-3.5 text-cyan-400" />
              Humidity
            </div>
            <span className="text-lg font-bold text-white">{current.relative_humidity}%</span>
          </div>

          {/* Wind Speed */}
          <div className="glass-card p-3.5 rounded-2xl border border-slate-800/80 flex flex-col items-start">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
              <Wind className="w-3.5 h-3.5 text-blue-400" />
              Wind Speed
            </div>
            <span className="text-lg font-bold text-white">{current.wind_speed} km/h</span>
          </div>

          {/* Rain Probability */}
          <div className="glass-card p-3.5 rounded-2xl border border-slate-800/80 flex flex-col items-start">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
              <Umbrella className="w-3.5 h-3.5 text-indigo-400" />
              Rain Chance
            </div>
            <span className="text-lg font-bold text-white">{current.rain_probability}%</span>
          </div>

          {/* UV Index */}
          <div className="glass-card p-3.5 rounded-2xl border border-slate-800/80 flex flex-col items-start">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
              <SunMedium className="w-3.5 h-3.5 text-amber-400" />
              UV Index
            </div>
            <span className="text-lg font-bold text-white">{current.uv_index}</span>
          </div>
        </div>
      </div>

      {/* Footer Sunrise & Sunset Info */}
      {(current.sunrise || current.sunset) && (
        <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Sunrise className="w-4 h-4 text-amber-300" />
            <span>Sunrise: <strong className="text-slate-200">{current.sunrise}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <Sunset className="w-4 h-4 text-rose-400" />
            <span>Sunset: <strong className="text-slate-200">{current.sunset}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
}
