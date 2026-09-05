import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, BellRing, PhoneCall, Volume2, VolumeX, Send, CheckCircle2, ShieldAlert, X, Radio, Loader2, Smartphone, Zap } from 'lucide-react';
import { broadcastEmergencySMS } from '../services/api';
import { requestPushNotificationPermission, triggerDeviceDisasterPush } from '../services/firebase';

export default function EmergencyBuzzModal({
  isOpen,
  onClose,
  currentLocation,
  criticalAlert = null
}) {
  const [phoneInput, setPhoneInput] = useState('');
  const [recipientList, setRecipientList] = useState([
    '+917993678737',
    '+919876543210',
    '+919848022338'
  ]);
  const [isSirenPlaying, setIsSirenPlaying] = useState(false);
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Firebase Web Push & Phone Vibration States (100% Free)
  const [pushPermission, setPushPermission] = useState(typeof window !== 'undefined' && 'Notification' in window ? Notification.permission : 'unsupported');
  const [isArmingPush, setIsArmingPush] = useState(false);
  const [pushStatusMsg, setPushStatusMsg] = useState('');

  const audioCtxRef = useRef(null);
  const oscRef1 = useRef(null);
  const oscRef2 = useRef(null);
  const gainNodeRef = useRef(null);

  const locName = currentLocation?.city || currentLocation?.name || 'Selected Area';
  const alertTitle = criticalAlert?.title || 'Severe Thunderstorm & Flash Flood Warning';
  const recommendation = criticalAlert?.recommendation || 'Seek immediate indoor shelter. Disconnect electrical equipment, avoid trees and open fields.';

  // Play Web Audio Emergency Alert Siren / Dual-Tone Buzz
  const startSirenBuzz = () => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;

      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioCtx();
      }

      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }

      const ctx = audioCtxRef.current;
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.connect(ctx.destination);
      gainNodeRef.current = gain;

      // Standard Emergency Alert System (EAS) dual-tone frequencies (853 Hz + 960 Hz)
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      osc1.type = 'sawtooth';
      osc2.type = 'sawtooth';
      osc1.frequency.setValueAtTime(853, ctx.currentTime);
      osc2.frequency.setValueAtTime(960, ctx.currentTime);

      osc1.connect(gain);
      osc2.connect(gain);

      osc1.start();
      osc2.start();

      oscRef1.current = osc1;
      oscRef2.current = osc2;
      setIsSirenPlaying(true);

      // Trigger phone vibration if supported
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate([500, 200, 500, 200, 800]);
      }
    } catch (e) {
      console.warn('Could not start emergency audio siren:', e);
    }
  };

  const stopSirenBuzz = () => {
    try {
      if (oscRef1.current) {
        oscRef1.current.stop();
        oscRef1.current.disconnect();
        oscRef1.current = null;
      }
      if (oscRef2.current) {
        oscRef2.current.stop();
        oscRef2.current.disconnect();
        oscRef2.current = null;
      }
      setIsSirenPlaying(false);
    } catch (e) {
      // ignore
    }
  };

  // Start emergency siren when modal opens
  useEffect(() => {
    if (isOpen) {
      startSirenBuzz();
    } else {
      stopSirenBuzz();
      setDispatchResult(null);
    }
    return () => stopSirenBuzz();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAddPhone = (e) => {
    e.preventDefault();
    if (!phoneInput.trim()) return;
    const formatted = phoneInput.trim();
    if (!recipientList.includes(formatted)) {
      setRecipientList(prev => [...prev, formatted]);
    }
    setPhoneInput('');
  };

  const handleRemovePhone = (phone) => {
    setRecipientList(prev => prev.filter(p => p !== phone));
  };

  const handleArmPushAlerts = async () => {
    setIsArmingPush(true);
    setPushStatusMsg('');
    setErrorMsg('');
    try {
      const res = await requestPushNotificationPermission();
      if (res.success) {
        setPushPermission('granted');
        setPushStatusMsg('✅ Free Firebase Web Push & Vibration armed on this device!');
        await triggerDeviceDisasterPush({
          title: '🚨 WEATHERGPT DISASTER ALARM ARMED',
          body: `High-priority alerts activated for ${locName}. Phone will vibrate and sound siren.`,
          location: locName
        });
        startSirenBuzz();
      } else {
        setPushPermission(res.permission || 'denied');
        setErrorMsg(res.reason || 'Failed to activate push notifications.');
      }
    } catch (e) {
      setErrorMsg('Error enabling push: ' + e.message);
    } finally {
      setIsArmingPush(false);
    }
  };

  const handleTestPhoneBuzz = async () => {
    startSirenBuzz();
    await triggerDeviceDisasterPush({
      title: `🚨 DISASTER ALERT: ${alertTitle}`,
      body: `Immediate emergency vibration & alarm test for ${locName}. Stay safe!`,
      location: locName
    });
    setPushStatusMsg('⚡ Phone buzz, vibration & lock-screen push notification triggered!');
  };

  const handleBroadcastSMS = async () => {
    if (recipientList.length === 0) {
      setErrorMsg('Please add at least one recipient phone number.');
      return;
    }

    setIsDispatching(true);
    setErrorMsg('');
    try {
      // 1. Dispatch Physical Device Push Alert & Vibration (100% Free Firebase/Web Push)
      triggerDeviceDisasterPush({
        title: `🚨 EAS EMERGENCY: ${alertTitle}`,
        body: `${recommendation} (Target: ${locName})`,
        location: locName
      });
      startSirenBuzz();

      // 2. Dispatch Cellular Broadcast SMS
      const res = await broadcastEmergencySMS(
        alertTitle,
        locName,
        recommendation,
        'danger',
        recipientList
      );
      setDispatchResult(res);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to dispatch emergency SMS broadcast.');
    } finally {
      setIsDispatching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-red-950/80 backdrop-blur-xl animate-fade-in">
      <div className="w-full max-w-xl glass-card rounded-3xl p-6 sm:p-8 shadow-2xl border-2 border-red-500/60 relative overflow-hidden text-slate-100">
        {/* Flashing Red Emergency Ambient Glow */}
        <div className="absolute -top-24 -left-24 w-72 h-72 bg-red-600/30 rounded-full blur-3xl animate-pulse pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-amber-600/25 rounded-full blur-3xl animate-pulse pointer-events-none" />

        {/* Close & Mute Header Controls */}
        <div className="flex items-center justify-between gap-2 mb-4 relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-500/20 border border-red-500/50 text-red-300 text-xs font-black uppercase tracking-wider animate-pulse">
            <Radio className="w-4 h-4 animate-spin text-red-400" />
            EAS Critical Disaster Broadcast
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={isSirenPlaying ? stopSirenBuzz : startSirenBuzz}
              className={`p-2 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 ${
                isSirenPlaying
                  ? 'bg-red-500/30 text-red-200 border-red-500/50 shadow-lg'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:text-white'
              }`}
              title={isSirenPlaying ? 'Mute Emergency Siren' : 'Unmute Siren'}
            >
              {isSirenPlaying ? <Volume2 className="w-4 h-4 animate-bounce" /> : <VolumeX className="w-4 h-4" />}
              <span>{isSirenPlaying ? 'Mute Siren' : 'Play Buzz'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Disaster Event Banner */}
        <div className="p-4 rounded-2xl bg-red-500/15 border border-red-500/40 mb-5 relative z-10">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-600/30 border border-red-500/60 flex items-center justify-center text-red-400 shrink-0">
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h3 className="text-lg font-black text-white font-heading tracking-tight">
                {alertTitle}
              </h3>
              <p className="text-xs text-red-200 font-semibold mt-0.5">
                📍 Target Area: <strong>{locName}</strong>
              </p>
              <p className="text-xs text-slate-300 mt-2 bg-dark-900/60 p-2.5 rounded-xl border border-red-500/20 leading-relaxed">
                <span className="text-amber-300 font-bold">Recommended Citizen Action: </span>
                {recommendation}
              </p>
            </div>
          </div>
        </div>

        {/* Recipients Group Section */}
        <div className="mb-5 relative z-10">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <PhoneCall className="w-3.5 h-3.5 text-cyan-400" />
            Emergency Broadcast Test Group (Citizens & First Responders)
          </label>

          <form onSubmit={handleAddPhone} className="flex gap-2 mb-3">
            <input
              type="text"
              value={phoneInput}
              onChange={(e) => setPhoneInput(e.target.value)}
              placeholder="Add mobile number (e.g. +919876543210)..."
              className="flex-1 px-3.5 py-2.5 rounded-xl glass-input text-white text-xs placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs transition-all shrink-0"
            >
              + Add Phone
            </button>
          </form>

          {/* Active Contacts Pills */}
          <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto pr-1">
            {recipientList.map((phone, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-dark-900/90 border border-slate-700 text-cyan-300 text-xs font-mono"
              >
                📱 {phone}
                <button
                  type="button"
                  onClick={() => handleRemovePhone(phone)}
                  className="text-slate-400 hover:text-red-400 font-bold ml-1"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* 100% Free Firebase & Physical Device Push Section */}
        <div className="mb-5 p-4 rounded-2xl bg-dark-900/80 border border-cyan-500/40 relative z-10">
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-bold text-cyan-300 flex items-center gap-1.5 uppercase tracking-wider">
              <Smartphone className="w-3.5 h-3.5 text-cyan-400" />
              100% Free Phone Push & Vibration (Firebase Ready)
            </span>
            <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
              pushPermission === 'granted'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
            }`}>
              {pushPermission === 'granted' ? '⚡ Armed & Ready' : 'Permission Required'}
            </span>
          </div>

          <p className="text-[11px] text-slate-300 mb-3 leading-relaxed">
            Direct lock-screen disaster push alerts & hardware phone vibration without cellular SMS charges (₹0 Free Forever).
          </p>

          <div className="flex flex-wrap items-center gap-2">
            {pushPermission !== 'granted' ? (
              <button
                type="button"
                onClick={handleArmPushAlerts}
                disabled={isArmingPush}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-black text-xs transition-all flex items-center gap-1.5 shadow-lg shadow-cyan-500/20"
              >
                {isArmingPush ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                <span>Arm Free Phone Vibration & Push</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleTestPhoneBuzz}
                className="px-4 py-2 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/50 font-extrabold text-xs transition-all flex items-center gap-1.5"
              >
                <Zap className="w-3.5 h-3.5 text-emerald-400 animate-bounce" />
                <span>Test Phone Vibration & Push Notification</span>
              </button>
            )}
          </div>

          {pushStatusMsg && (
            <div className="mt-2.5 text-[11px] text-emerald-300 font-semibold flex items-center gap-1.5 animate-fade-in">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>{pushStatusMsg}</span>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-200 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Live Dispatch Success Report */}
        {dispatchResult && (
          <div className="mb-5 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/40 relative z-10 animate-fade-in">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs mb-2">
              <CheckCircle2 className="w-4 h-4" />
              Emergency SMS Alert Broadcast Successfully Dispatched!
            </div>
            <div className="text-[11px] text-slate-300 space-y-1 font-mono">
              <p>📡 <strong>Mode:</strong> {dispatchResult.broadcast_mode}</p>
              <p>👥 <strong>Recipients:</strong> {dispatchResult.recipient_count} phone numbers</p>
              <p>⏱️ <strong>Timestamp:</strong> {new Date(dispatchResult.dispatched_at).toLocaleTimeString()}</p>
            </div>
            <div className="mt-2.5 p-2 rounded-xl bg-dark-900/80 border border-emerald-500/20 text-[11px] text-emerald-300">
              💬 <em>"{dispatchResult.message_preview.slice(0, 100)}..."</em>
            </div>
          </div>
        )}

        {/* Trigger Emergency Broadcast Button */}
        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={handleBroadcastSMS}
            disabled={isDispatching || recipientList.length === 0}
            className="flex-1 py-3.5 px-4 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white font-black text-sm uppercase tracking-wider transition-all shadow-xl shadow-red-600/40 flex items-center justify-center gap-2 transform active:scale-98 disabled:opacity-50"
          >
            {isDispatching ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Broadcasting to Cell Towers...</span>
              </>
            ) : (
              <>
                <BellRing className="w-4 h-4 animate-bounce text-white" />
                <span>Broadcast Emergency SMS & Buzz Alert</span>
                <Send className="w-3.5 h-3.5 ml-1" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
