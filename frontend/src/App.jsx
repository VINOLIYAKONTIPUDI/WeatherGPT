import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import LocationSearch from './components/LocationSearch';
import VoiceAssistant from './components/VoiceAssistant';
import WeatherCard from './components/WeatherCard';
import ForecastChart from './components/ForecastChart';
import AdvisoryCard from './components/AdvisoryCard';
import WeatherMap from './components/WeatherMap';
import { fetchWeatherForecast, fetchWeatherAlerts } from './services/api';
import { getTranslation } from './constants/languages';
import { MapPin, Search } from 'lucide-react';

const LOCATION_STORAGE_KEY = 'weathergpt_active_location';
const LANGUAGE_STORAGE_KEY = 'weathergpt_language';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  // Load saved location on app startup or null if not set
  const [currentLocation, setCurrentLocation] = useState(() => {
    try {
      const saved = localStorage.getItem(LOCATION_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed.latitude === 'number' && typeof parsed.longitude === 'number') {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to parse saved location from localStorage:', e);
    }
    return null;
  });

  // Load saved language on app startup or default to en-IN
  const [language, setLanguage] = useState(() => {
    try {
      const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (saved) return saved;
    } catch (e) {}
    return 'en-IN';
  });

  const [weatherData, setWeatherData] = useState(null);
  const [alertsData, setAlertsData] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);

  // Load weather & advisories when location changes
  const loadLocationWeather = useCallback(async (loc) => {
    if (!loc || typeof loc.latitude !== 'number' || typeof loc.longitude !== 'number') {
      setWeatherData(null);
      setAlertsData(null);
      return;
    }

    setLoadingWeather(true);
    try {
      const locName = loc.city || loc.name || 'Selected Location';
      const data = await fetchWeatherForecast(loc.latitude, loc.longitude, locName);
      if (data) {
        setWeatherData(data);
      }

      const alerts = await fetchWeatherAlerts(loc.latitude, loc.longitude, locName);
      if (alerts) {
        setAlertsData(alerts);
      }
    } catch (err) {
      console.warn('Error loading weather data:', err);
    } finally {
      setLoadingWeather(false);
    }
  }, []);

  useEffect(() => {
    if (currentLocation) {
      localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(currentLocation));
    } else {
      localStorage.removeItem(LOCATION_STORAGE_KEY);
    }
    loadLocationWeather(currentLocation);
  }, [currentLocation, loadLocationWeather]);

  useEffect(() => {
    if (language) {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    }
  }, [language]);

  const handleLocationChange = (newLoc) => {
    setCurrentLocation(newLoc);
  };

  return (
    <div className="min-h-screen flex flex-col bg-dark-900 text-slate-100">
      {/* Top Header Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        alertCount={alertsData?.count || 0}
        currentLocation={currentLocation}
        language={language}
        setLanguage={setLanguage}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 pb-16">
        {/* Global Location Search Bar */}
        <LocationSearch
          currentLocation={currentLocation}
          onLocationSelect={handleLocationChange}
          language={language}
        />

        {/* Location Required State Banner if no location is selected */}
        {!currentLocation && (
          <div className="w-full max-w-4xl mx-auto mb-8 p-6 sm:p-8 rounded-3xl bg-dark-800/90 border border-amber-500/30 shadow-2xl text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
            
            <div className="relative z-10 flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-full bg-amber-500/15 border border-amber-500/40 flex items-center justify-center text-amber-400 mb-1">
                <MapPin className="w-7 h-7" />
              </div>

              <h2 className="text-xl sm:text-2xl font-extrabold text-white font-heading">
                {getTranslation(language, 'locationRequiredTitle')}
              </h2>
              
              <p className="text-sm text-slate-300 max-w-lg leading-relaxed">
                {getTranslation(language, 'locationRequiredMessage')}
              </p>

              <div className="flex flex-wrap items-center justify-center gap-3 mt-3">
                <button
                  onClick={() => {
                    const btn = document.getElementById('btn-use-my-location');
                    if (btn) btn.click();
                  }}
                  className="px-5 py-2.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs transition-all shadow-lg flex items-center gap-2"
                >
                  {getTranslation(language, 'useMyLocation')}
                </button>
                <button
                  onClick={() => {
                    const input = document.querySelector('input[type="text"]');
                    if (input) input.focus();
                  }}
                  className="px-5 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 font-bold text-xs transition-all flex items-center gap-2"
                >
                  {getTranslation(language, 'searchLocation')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 1: Voice Hero View (Primary Experience) */}
        {activeTab === 'dashboard' && (
          <div>
            <VoiceAssistant
              currentLocation={currentLocation}
              onWeatherUpdate={handleLocationChange}
              language={language}
              setLanguage={setLanguage}
            />

            {weatherData && (
              <WeatherCard
                weatherData={weatherData}
                location={currentLocation}
              />
            )}

            {alertsData && alertsData.alerts.length > 0 && (
              <AdvisoryCard alerts={alertsData.alerts} />
            )}

            {weatherData && (
              <ForecastChart
                hourlyData={weatherData.hourly}
                dailyData={weatherData.daily}
              />
            )}
          </div>
        )}

        {/* Tab 2: Dashboard & Forecast Deep Dive */}
        {activeTab === 'forecast' && (
          <div>
            <WeatherCard
              weatherData={weatherData}
              location={currentLocation}
            />

            {weatherData && (
              <ForecastChart
                hourlyData={weatherData.hourly}
                dailyData={weatherData.daily}
              />
            )}

            <WeatherMap
              location={currentLocation}
              currentWeather={weatherData?.current}
            />
          </div>
        )}

        {/* Tab 3: Advisories & Active Safety Alerts */}
        {activeTab === 'alerts' && (
          <div>
            {alertsData && (
              <AdvisoryCard alerts={alertsData.alerts} />
            )}

            <WeatherCard
              weatherData={weatherData}
              location={currentLocation}
            />
          </div>
        )}
      </main>

      {/* Modern Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>© 2026 WeatherGPT — Conversational Voice-First Weather Intelligence Platform</p>
          <p className="text-cyan-500 font-semibold">Powered by Open-Meteo & Web Speech API</p>
        </div>
      </footer>
    </div>
  );
}
