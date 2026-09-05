import React from 'react';
import { AlertTriangle, AlertCircle, ShieldCheck, Info, ShieldAlert, Navigation, Activity } from 'lucide-react';

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

function getRiskColor(level) {
  switch (level) {
    case 'Severe Risk':
      return {
        badge: 'bg-red-500/20 text-red-300 border-red-500/40',
        bar: 'bg-gradient-to-r from-orange-500 to-red-600',
        text: 'text-red-400',
        bg: 'bg-red-950/40 border-red-500/40'
      };
    case 'High Risk':
      return {
        badge: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
        bar: 'bg-gradient-to-r from-amber-500 to-orange-600',
        text: 'text-orange-400',
        bg: 'bg-orange-950/30 border-orange-500/40'
      };
    case 'Advisory':
      return {
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        bar: 'bg-gradient-to-r from-yellow-400 to-amber-500',
        text: 'text-amber-400',
        bg: 'bg-amber-950/20 border-amber-500/30'
      };
    default:
      return {
        badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
        bar: 'bg-gradient-to-r from-cyan-400 to-emerald-500',
        text: 'text-emerald-400',
        bg: 'bg-emerald-950/20 border-emerald-500/30'
      };
  }
}

export default function AdvisoryCard({ alerts = [], smartAlert = null }) {
  if ((!alerts || alerts.length === 0) && !smartAlert) return null;

  const riskScore = smartAlert?.risk_score ?? 15;
  const riskLevel = smartAlert?.risk_level ?? 'Normal';
  const riskStyle = getRiskColor(riskLevel);

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-800 mb-8">
      {/* Header */}
      <h3 className="text-xl font-bold text-white font-heading mb-6 flex items-center justify-between">
        <span className="flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-amber-400" /> Smart Safety Alerts & Advisories
        </span>
        <span className="text-xs text-slate-400 font-normal">Real-Time Risk Intelligence</span>
      </h3>

      {/* Smart Safety Alert Dashboard Banner */}
      {smartAlert && (
        <div className={`p-6 rounded-2xl border ${riskStyle.bg} mb-8 shadow-xl relative overflow-hidden transition-all`}>
          {/* Risk Level Header & Gauge */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-extrabold uppercase px-3 py-1 rounded-full border ${riskStyle.badge}`}>
                  {riskLevel}
                </span>
                <span className="text-xs text-slate-400 font-semibold flex items-center gap-1">
                  <Activity className="w-3.5 h-3.5 text-cyan-400" /> Weather Risk Index
                </span>
              </div>
              <h4 className="text-2xl font-black text-white font-heading mt-1">
                Risk Score: <span className={riskStyle.text}>{riskScore}%</span>
              </h4>
            </div>

            {/* Visual Risk Gauge Progress Bar */}
            <div className="w-full sm:w-48">
              <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
                <span>0% Safe</span>
                <span className={riskStyle.text}>{riskScore}%</span>
                <span>100% Critical</span>
              </div>
              <div className="w-full h-3 bg-slate-900/80 rounded-full overflow-hidden border border-slate-700/80 p-0.5">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${riskStyle.bar}`}
                  style={{ width: `${Math.max(5, riskScore)}%` }}
                />
              </div>
            </div>
          </div>

          {/* What is Happening & Detected Hazards */}
          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-200">
              <span className="font-bold text-cyan-300 block mb-1">ℹ️ What is happening:</span>
              {smartAlert.event_description}
            </div>

            {/* Safety Advice */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-200">
              <span className="font-bold text-emerald-400 block mb-1">🛡️ Clear Safety Advice:</span>
              {smartAlert.safety_advice}
            </div>

            {/* Travel Warning */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-200 flex items-start gap-2">
              <Navigation className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-amber-300 block mb-0.5">Travel Advisory:</span>
                {smartAlert.travel_warning}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Individual Detailed Advisories List */}
      {alerts && alerts.length > 0 && (
        <div>
          <h4 className="text-sm font-bold text-slate-300 font-heading mb-4">
            Active Category Advisories ({alerts.length})
          </h4>
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
      )}
    </div>
  );
}
