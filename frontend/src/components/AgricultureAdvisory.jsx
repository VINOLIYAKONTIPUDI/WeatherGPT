import React, { useState, useEffect } from 'react';
import { Sprout, Droplets, Wind, Thermometer, ShieldAlert, Sparkles, CheckCircle2, AlertTriangle, XCircle, CloudRain, Bug, Wheat } from 'lucide-react';
import { fetchCropAdvisory } from '../services/api';

const CROPS = [
  { id: 'Paddy', label: '🌾 Paddy', icon: '🌾' },
  { id: 'Cotton', label: '☁️ Cotton', icon: '☁️' },
  { id: 'Maize', label: '🌽 Maize', icon: '🌽' },
  { id: 'Groundnut', label: '🥜 Groundnut', icon: '🥜' },
  { id: 'Wheat', label: '🍞 Wheat', icon: '🍞' },
];

const STAGES = [
  { id: 'Sowing', label: '🌱 Sowing' },
  { id: 'Vegetative', label: '🌿 Vegetative' },
  { id: 'Flowering', label: '🌸 Flowering' },
  { id: 'Harvest', label: '🌾 Harvest' },
];

// Fallback rule engine for offline / client-side calculation
function computeLocalAdvisory(crop, stage, weatherData) {
  const cur = weatherData?.current || weatherData || {};
  const temp = Number(cur.temperature ?? 28);
  const humidity = Number(cur.humidity ?? 65);
  const rainProb = Number(cur.rain_probability ?? cur.pop ?? 20);
  const rainfall = Number(cur.precipitation ?? 0);
  const windSpeed = Number(cur.wind_speed ?? 10);

  // Irrigation
  let irrigation = '';
  if (rainProb >= 50 || rainfall >= 5) {
    irrigation = `Avoid irrigation today. Adequate moisture expected from incoming rainfall (${rainProb}% rain probability).`;
  } else if (temp >= 35 && humidity < 50) {
    irrigation = `Provide light, frequent irrigation during early morning or late evening to combat heat stress (${temp}°C).`;
  } else {
    irrigation = `Provide normal scheduled irrigation suitable for the ${stage} stage of ${crop}.`;
  }

  // Fertilizer
  let fertilizer = '';
  if (rainProb >= 60 || rainfall >= 5) {
    fertilizer = `Postpone fertilizer application. High risk of rain-induced nutrient leaching and surface runoff (${rainProb}% rain chance).`;
  } else if (windSpeed >= 20) {
    fertilizer = `Delay top-dressing fertilizer due to strong gusty winds (${windSpeed} km/h).`;
  } else {
    fertilizer = `Favorable calm weather for soil fertilizer application and nutrient top-dressing.`;
  }

  // Spraying
  let spraying = '';
  if (windSpeed >= 15) {
    spraying = `Avoid pesticide/fungicide spraying due to chemical drift risk (wind speed ${windSpeed} km/h exceeds 15 km/h limit).`;
  } else if (rainProb >= 50 || rainfall >= 2) {
    spraying = `Postpone crop spraying. Expected rain (${rainProb}% chance) will wash away applied chemicals.`;
  } else {
    spraying = `Favorable clear weather window for pesticide and fungicide application.`;
  }

  // Pest & Fungal Disease Risk
  const diseases = {
    Paddy: 'Blast & Sheath Blight',
    Cotton: 'Boll Rot & Leaf Curl Virus',
    Maize: 'Fall Armyworm & Turcicum Blight',
    Groundnut: 'Tikka Leaf Spot & Rust',
    Wheat: 'Stripe Rust & Powdery Mildew',
  };
  const targetDisease = diseases[crop] || 'Fungal & Pest Attack';
  let pestDiseaseRisk = '';

  if (humidity >= 75 && temp >= 20 && temp <= 33) {
    pestDiseaseRisk = `HIGH Risk of ${targetDisease} due to elevated humidity (${humidity}%) and warm temperatures (${temp}°C). Monitor fields closely.`;
  } else {
    pestDiseaseRisk = `Low to Moderate disease risk for ${crop}. Maintain routine crop field surveillance.`;
  }

  // Harvesting
  let harvesting = '';
  if (stage === 'Harvest') {
    if (rainProb >= 40 || rainfall >= 2) {
      harvesting = `Delay harvesting and threshing due to rain risk (${rainProb}% chance). Keep harvested produce covered.`;
    } else {
      harvesting = `Optimal clear weather window for harvesting, threshing, and sun-drying ${crop}.`;
    }
  } else {
    harvesting = `Crop is currently in ${stage} stage. Ensure good field drainage and timely weed control.`;
  }

  // Risk Level
  let overallRisk = 'Low';
  let summary = `Favorable agricultural weather for ${crop} during ${stage} stage.`;
  if (rainProb >= 70 || rainfall >= 10 || windSpeed >= 30 || (humidity >= 80 && temp >= 25)) {
    overallRisk = 'High';
    summary = `Severe weather conditions detected for ${crop} (${stage} stage). High risk of rain, wind, or fungal stress.`;
  } else if (rainProb >= 40 || rainfall >= 3 || windSpeed >= 18 || humidity >= 70) {
    overallRisk = 'Moderate';
    summary = `Moderate weather factors present for ${crop}. Review specific domain recommendations below.`;
  }

  return {
    crop,
    stage,
    overall_risk: overallRisk,
    summary,
    recommendations: {
      irrigation,
      fertilizer,
      spraying,
      pest_disease_risk: pestDiseaseRisk,
      harvesting,
    },
    weather_factors: {
      rain_probability: rainProb,
      rainfall_mm: rainfall,
      temperature_c: temp,
      humidity_percent: humidity,
      wind_speed_kmh: windSpeed,
    },
    disclaimer: 'Agricultural advice is derived from meteorological forecasts and agronomic best practices.',
  };
}

export default function AgricultureAdvisory({ weatherData, location }) {
  const [selectedCrop, setSelectedCrop] = useState('Paddy');
  const [selectedStage, setSelectedStage] = useState('Vegetative');
  const [advisory, setAdvisory] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadAdvisory() {
      try {
        const res = await fetchCropAdvisory(selectedCrop, selectedStage, weatherData?.current || weatherData);
        if (isMounted && res && res.recommendations) {
          setAdvisory(res);
          return;
        }
      } catch (e) {
        console.warn('API crop advisory failed, using client-side calculation:', e);
      }
      
      if (isMounted) {
        setAdvisory(computeLocalAdvisory(selectedCrop, selectedStage, weatherData));
      }
    }

    loadAdvisory();
    return () => { isMounted = false; };
  }, [selectedCrop, selectedStage, weatherData]);

  if (!advisory) return null;

  const { overall_risk, summary, recommendations, weather_factors } = advisory;

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'High':
        return (
          <span className="px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-extrabold text-xs flex items-center gap-1.5 shadow-sm">
            <XCircle className="w-4 h-4 text-rose-400" /> High Weather Risk
          </span>
        );
      case 'Moderate':
        return (
          <span className="px-3 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-extrabold text-xs flex items-center gap-1.5 shadow-sm">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Moderate Weather Risk
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-extrabold text-xs flex items-center gap-1.5 shadow-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Low Weather Risk
          </span>
        );
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto my-6 p-6 sm:p-8 rounded-3xl bg-dark-800/90 border border-slate-800/90 shadow-2xl backdrop-blur-xl text-slate-100 relative overflow-hidden transition-all">
      {/* Background Decorative Blur */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Card Header */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 shrink-0">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white font-heading tracking-tight flex items-center gap-2">
              Agriculture Advisory
              <span className="text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold">
                Smart Farm Insights
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Precision weather-based advice for {location?.city || location?.name || 'your region'}
            </p>
          </div>
        </div>

        {/* Overall Risk Badge */}
        <div>{getRiskBadge(overall_risk)}</div>
      </div>

      {/* Selection Section: Crop & Growth Stage */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-6 my-6">
        {/* Crop Selector */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
            <Wheat className="w-4 h-4 text-emerald-400" /> Select Crop
          </label>
          <div className="flex flex-wrap gap-2">
            {CROPS.map((crop) => (
              <button
                key={crop.id}
                onClick={() => setSelectedCrop(crop.id)}
                className={`px-3.5 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  selectedCrop === crop.id
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20 scale-105'
                    : 'bg-dark-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800'
                }`}
              >
                <span>{crop.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Growth Stage Selector */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-cyan-400" /> Select Growth Stage
          </label>
          <div className="flex flex-wrap gap-2">
            {STAGES.map((stage) => (
              <button
                key={stage.id}
                onClick={() => setSelectedStage(stage.id)}
                className={`px-3.5 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  selectedStage === stage.id
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20 scale-105'
                    : 'bg-dark-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800'
                }`}
              >
                <span>{stage.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Relevant Weather Factors Bar */}
      <div className="relative z-10 bg-dark-900/90 rounded-2xl p-4 border border-slate-800/90 mb-6">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
          <Droplets className="w-3.5 h-3.5 text-cyan-400" /> Weather Factors Behind Advice
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div className="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 block font-medium">Rain Chance</span>
            <span className="text-sm font-extrabold text-cyan-300">{weather_factors.rain_probability}%</span>
          </div>
          <div className="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 block font-medium">Temperature</span>
            <span className="text-sm font-extrabold text-amber-300">{weather_factors.temperature_c}°C</span>
          </div>
          <div className="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 block font-medium">Humidity</span>
            <span className="text-sm font-extrabold text-teal-300">{weather_factors.humidity_percent}%</span>
          </div>
          <div className="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 block font-medium">Wind Speed</span>
            <span className="text-sm font-extrabold text-indigo-300">{weather_factors.wind_speed_kmh} km/h</span>
          </div>
        </div>
      </div>

      {/* Summary Headline */}
      <div className="relative z-10 mb-6 bg-slate-800/40 p-4 rounded-2xl border border-slate-700/50 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <p className="text-xs sm:text-sm font-semibold text-slate-200 leading-relaxed">
          {summary}
        </p>
      </div>

      {/* 5 Domain Action Cards */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. Irrigation */}
        <div className="bg-dark-900/80 p-4 rounded-2xl border border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                <Droplets className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Irrigation</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations.irrigation}
            </p>
          </div>
        </div>

        {/* 2. Fertilizer */}
        <div className="bg-dark-900/80 p-4 rounded-2xl border border-slate-800 hover:border-emerald-500/40 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <Sprout className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Fertilizer</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations.fertilizer}
            </p>
          </div>
        </div>

        {/* 3. Spraying */}
        <div className="bg-dark-900/80 p-4 rounded-2xl border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Wind className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Pesticide Spraying</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations.spraying}
            </p>
          </div>
        </div>

        {/* 4. Pest & Disease Risk */}
        <div className="bg-dark-900/80 p-4 rounded-2xl border border-slate-800 hover:border-amber-500/40 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
                <Bug className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Pest / Fungal Risk</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations.pest_disease_risk}
            </p>
          </div>
        </div>

        {/* 5. Harvesting */}
        <div className="bg-dark-900/80 p-4 rounded-2xl border border-slate-800 hover:border-teal-500/40 transition-all flex flex-col justify-between md:col-span-2 lg:col-span-2">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 shrink-0">
                <Wheat className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Harvesting & Moisture</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations.harvesting}
            </p>
          </div>
        </div>
      </div>

      {/* Footer Disclaimer */}
      <div className="relative z-10 mt-6 pt-4 border-t border-slate-800/80 text-[10px] text-slate-400 text-center">
        {advisory.disclaimer}
      </div>
    </div>
  );
}
