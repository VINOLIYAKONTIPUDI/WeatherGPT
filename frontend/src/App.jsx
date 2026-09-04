import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import LocationSearch from './components/LocationSearch';
import VoiceAssistant from './components/VoiceAssistant';
import WeatherCard from './components/WeatherCard';
import ForecastChart from './components/ForecastChart';
import AdvisoryCard from './components/AdvisoryCard';
import WeatherMap from './components/WeatherMap';
import { fetchWeatherForecast, fetchWeatherAlerts } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentLocation, setCurrentLocation] = useState({
    latitude: 17.3850,
    longitude: 78.4867,
    name: 'Hyderabad',
    country: 'India',
    admin1: 'Telangana'
  });

  const [weatherData, setWeatherData] = useState(null);
  const [alertsData, setAlertsData] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(true);

  // Load weather & advisories when location changes
  const loadLocationWeather = useCallback(async (loc) => {
    if (!loc || !loc.latitude || !loc.longitude) return;
    setLoadingWeather(true);

    try {
      const data = await fetchWeatherForecast(loc.latitude, loc.longitude, loc.name);
      if (data) {
        setWeatherData(data);
      }

      const alerts = await fetchWeatherAlerts(loc.latitude, loc.longitude, loc.name);
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
    loadLocationWeather(currentLocation);
  }, [currentLocation, loadLocationWeather]);

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
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 pb-16">
        {/* Global Location Search Bar */}
        <LocationSearch
          currentLocation={currentLocation}
          onLocationSelect={handleLocationChange}
        />

        {/* Tab 1: Voice Hero View (Primary Experience) */}
        {activeTab === 'dashboard' && (
          <div>
            <VoiceAssistant
              currentLocation={currentLocation}
              onWeatherUpdate={handleLocationChange}
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
            {weatherData && (
              <WeatherCard
                weatherData={weatherData}
                location={currentLocation}
              />
            )}

            {weatherData && (
              <ForecastChart
                hourlyData={weatherData.hourly}
                dailyData={weatherData.daily}
              />
            )}

            {weatherData && (
              <WeatherMap
                location={currentLocation}
                currentWeather={weatherData.current}
              />
            )}
          </div>
        )}

        {/* Tab 3: Advisories & Active Safety Alerts */}
        {activeTab === 'alerts' && (
          <div>
            {alertsData && (
              <AdvisoryCard alerts={alertsData.alerts} />
            )}

            {weatherData && (
              <WeatherCard
                weatherData={weatherData}
                location={currentLocation}
              />
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
