import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import LocationSearch from './components/LocationSearch';
import VoiceAssistant from './components/VoiceAssistant';
import WeatherCard from './components/WeatherCard';
import ForecastChart from './components/ForecastChart';
import AdvisoryCard from './components/AdvisoryCard';
import WeatherMap from './components/WeatherMap';
import AuthModal from './components/auth/AuthModal';
import { AuthProvider, useAuth } from './context/AuthContext';
import { fetchWeatherForecast, fetchWeatherAlerts } from './services/api';
import { getTranslation } from './constants/languages';
import { MapPin, Search, Loader2 } from 'lucide-react';

const LOCATION_STORAGE_KEY = 'weathergpt_active_location';
const LANGUAGE_STORAGE_KEY = 'weathergpt_language';

function MainAppContent() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  // 1. Single Source of Truth for Active Location (stored in localStorage)
  const [currentLocation, setCurrentLocation] = useState(() => {
    try {
      const saved = localStorage.getItem(LOCATION_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed.latitude === 'number' && typeof parsed.longitude === 'number' && (parsed.latitude !== 0 || parsed.longitude !== 0)) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to parse saved location from localStorage:', e);
    }
    return null; // Location Required State
  });

  // 2. Language Selection State (stored in localStorage)
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
    if (!loc || typeof loc.latitude !== 'number' || typeof loc.longitude !== 'number' || (loc.latitude === 0 && loc.longitude === 0)) {
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
    if (isAuthenticated) {
      loadLocationWeather(currentLocation);
    }
  }, [currentLocation, loadLocationWeather, isAuthenticated]);

  useEffect(() => {
    if (language) {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    }
  }, [language]);

  const handleLocationChange = (newLoc) => {
    if (!newLoc) {
      setCurrentLocation(null);
      return;
    }
    const formatted = {
      latitude: newLoc.latitude,
      longitude: newLoc.longitude,
      city: newLoc.city || newLoc.name || '',
      state: newLoc.state || newLoc.admin1 || '',
      country: newLoc.country || 'India',
      displayName: newLoc.displayName || newLoc.display_name || `${newLoc.name || newLoc.city}, ${newLoc.country || 'India'}`,
      source: newLoc.source || 'search',
      name: newLoc.name || newLoc.city,
      admin1: newLoc.admin1 || newLoc.state || ''
    };
    setCurrentLocation(formatted);
  };

  // Auth Loading Spinner
  if (authLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex flex-col items-center justify-center text-cyan-400">
        <Loader2 className="w-10 h-10 animate-spin mb-3" />
        <p className="font-semibold text-sm text-slate-300">Initializing WeatherGPT Auth...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-dark-900 text-slate-100">
      {/* Route Protection: Show Auth Modal if not logged in */}
      {!isAuthenticated && <AuthModal />}

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

        {/* Location Required State Banner if no location is set */}
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
            {currentLocation ? (
              <>
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
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <MapPin className="w-12 h-12 text-amber-400 mx-auto mb-3" />
                <p className="font-semibold text-lg text-white">Location required to view detailed dashboard & maps.</p>
                <p className="text-xs mt-1">Please select your location using the search bar above or click "Use My Location".</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Advisories & Active Safety Alerts */}
        {activeTab === 'alerts' && (
          <div>
            {currentLocation ? (
              <>
                {alertsData && (
                  <AdvisoryCard alerts={alertsData.alerts} />
                )}

                <WeatherCard
                  weatherData={weatherData}
                  location={currentLocation}
                />
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <MapPin className="w-12 h-12 text-amber-400 mx-auto mb-3" />
                <p className="font-semibold text-lg text-white">Location required to view weather advisories.</p>
                <p className="text-xs mt-1">Please select your location using the search bar above or click "Use My Location".</p>
              </div>
            )}
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

export default function App() {
  return (
    <AuthProvider>
      <MainAppContent />
    </AuthProvider>
  );
}
