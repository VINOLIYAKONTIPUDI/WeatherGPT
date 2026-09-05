import React from 'react';
import { AlertTriangle, AlertCircle, ShieldCheck, Info, Umbrella, Sun, Zap, Wind } from 'lucide-react';

function getSeverityBadge(severity) {
  switch (severity) {
    case 'danger':
      return {
        bg: 'bg-red-500/10 border-red-500/30 text-red-300',
        badge: 'bg-red-500/20 text-red-400 border-red-500/40',
        icon: <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
      };
    case 'warning':
      return {
        bg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        icon: <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
      };
    case 'advisory':
      return {
        bg: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-200',
        badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
        icon: <Info className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
      };
    default:
      return {
        bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
        icon: <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
      };
  }
}

export default function AdvisoryCard({ alerts = [] }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 mb-8">
      <h3 className="text-xl font-bold text-white font-heading mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-amber-400" /> Weather Safety & Advisories
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {alerts.map((alert) => {
          const style = getSeverityBadge(alert.severity);
          return (
            <div
              key={alert.id}
              className={`p-5 rounded-2xl border ${style.bg} flex items-start gap-3.5 transition-all shadow-md`}
            >
              {style.icon}
              <div className="flex-1">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <h4 className="font-bold text-base text-white">{alert.title}</h4>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border uppercase ${style.badge}`}>
                    {alert.timeframe}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-2 leading-relaxed">{alert.description}</p>
                <div className="text-xs font-semibold text-slate-100 bg-dark-900/60 p-2.5 rounded-xl border border-white/5">
                  <span className="text-cyan-400 font-bold">Recommendation: </span>
                  {alert.recommendation}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
