import React, { useState, useEffect } from 'react';
import { Search, MapPin, Navigation, Loader2, AlertCircle, RotateCcw, CheckCircle2 } from 'lucide-react';
import { searchLocations, reverseGeocode } from '../services/api';
import { getTranslation } from '../constants/languages';

const QUICK_CITIES = [
  { name: 'Vijayawada', lat: 16.5062, lon: 80.6480, admin1: 'Andhra Pradesh' },
  { name: 'Tadepalligudem', lat: 16.8123, lon: 81.5284, admin1: 'Andhra Pradesh' },
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, admin1: 'Telangana' },
  { name: 'Visakhapatnam', lat: 17.6868, lon: 83.2185, admin1: 'Andhra Pradesh' },
  { name: 'Delhi', lat: 28.6139, lon: 77.2090, admin1: 'Delhi' },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777, admin1: 'Maharashtra' },
  { name: 'Bengaluru', lat: 12.9716, lon: 77.5946, admin1: 'Karnataka' },
];

export default function LocationSearch({ currentLocation, onLocationSelect, language = 'en-IN' }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null); // { type: 'info'|'success'|'error', text: str }
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      const res = await searchLocations(query);
      setResults(res || []);
      setIsSearching(false);
      setShowDropdown(true);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (loc) => {
    setLocationStatus(null);
    const locationObj = {
      latitude: loc.latitude,
      longitude: loc.longitude,
      city: loc.city || loc.name,
      state: loc.state || loc.admin1 || '',
      country: loc.country || 'India',
      displayName: loc.displayName || loc.display_name || `${loc.name}, ${loc.admin1 || loc.country || 'India'}`,
      source: loc.source || 'search',
      name: loc.name || loc.city,
      admin1: loc.admin1 || loc.state || ''
    };

    onLocationSelect(locationObj);
    setQuery('');
    setShowDropdown(false);
  };

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus({
        type: 'error',
        text: 'Geolocation is not supported by your browser.'
      });
      return;
    }

    setIsLocating(true);
    setLocationStatus({
      type: 'info',
      text: 'Requesting your location...'
    });

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    };

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          // Perform Reverse Geocoding
          const geoResult = await reverseGeocode(lat, lon);
          
          const resolvedName = geoResult.city || geoResult.name || 'Current Location';
          setLocationStatus({
            type: 'success',
            text: `Location detected: ${resolvedName}`
          });

          const locationObj = {
            latitude: lat,
            longitude: lon,
            city: geoResult.city || geoResult.name || 'Current Location',
            state: geoResult.state || geoResult.admin1 || '',
            country: geoResult.country || 'India',
            displayName: geoResult.displayName || geoResult.display_name || `${resolvedName}, ${geoResult.country || 'India'}`,
            source: 'gps',
            name: resolvedName,
            admin1: geoResult.admin1 || geoResult.state || ''
          };

          onLocationSelect(locationObj);
        } catch (err) {
          console.error('Error during reverse geocoding:', err);
          setLocationStatus({
            type: 'error',
            text: 'Unable to determine your location name. Please try again.'
          });
        } finally {
          setIsLocating(false);
        }
      },
      (err) => {
        console.warn('Geolocation error code:', err.code, err.message);
        setIsLocating(false);
        
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setLocationStatus({
              type: 'error',
              text: 'Location permission was denied. Please allow location access in your browser settings.'
            });
            break;
          case err.POSITION_UNAVAILABLE:
            setLocationStatus({
              type: 'error',
              text: 'Your location could not be determined. Please check your device location services.'
            });
            break;
          case err.TIMEOUT:
            setLocationStatus({
              type: 'error',
              text: 'Location request timed out. Please try again.'
            });
            break;
          default:
            setLocationStatus({
              type: 'error',
              text: 'Unable to determine your location. Please try again.'
            });
            break;
        }
      },
      options
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-6 relative">
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Input Bar */}
        <div className="relative flex-1 w-full">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => query.length >= 2 && setShowDropdown(true)}
              placeholder={getTranslation(language, 'searchPlaceholder')}
              className="w-full pl-11 pr-10 py-3 rounded-2xl glass-input text-white text-sm focus:outline-none placeholder-slate-500"
            />
            {isSearching && (
              <Loader2 className="w-4 h-4 text-cyan-400 absolute right-4 animate-spin" />
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {showDropdown && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-dark-800 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden z-50 max-h-60 overflow-y-auto">
              {results.map((loc, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelect(loc)}
                  className="w-full px-4 py-3 text-left text-sm text-slate-200 hover:bg-cyan-500/15 hover:text-cyan-300 border-b border-slate-800/80 flex items-center justify-between transition-colors"
                >
                  <span className="font-semibold">{loc.name}</span>
                  <span className="text-xs text-slate-400">{loc.admin1 || loc.country}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* GPS Location Button */}
        <button
          onClick={handleUseMyLocation}
          disabled={isLocating}
          className="w-full sm:w-auto px-4 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700/80 text-cyan-400 text-xs font-semibold border border-cyan-500/30 flex items-center justify-center gap-2 transition-all shrink-0"
          id="btn-use-my-location"
        >
          {isLocating ? (
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          ) : (
            <Navigation className="w-4 h-4 text-cyan-400 fill-cyan-400/20" />
          )}
          <span>{isLocating ? 'Locating...' : getTranslation(language, 'useMyLocation')}</span>
        </button>
      </div>

      {/* Geolocation Status Feedback Banner */}
      {locationStatus && (
        <div
          className={`mt-3 p-3 rounded-xl text-xs flex items-center justify-between gap-3 border transition-all ${
            locationStatus.type === 'error'
              ? 'bg-red-500/10 border-red-500/30 text-red-300'
              : locationStatus.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300 animate-pulse'
          }`}
        >
          <div className="flex items-center gap-2">
            {locationStatus.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            ) : locationStatus.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <Loader2 className="w-4 h-4 text-cyan-400 shrink-0 animate-spin" />
            )}
            <span>{locationStatus.text}</span>
          </div>

          {locationStatus.type === 'error' && (
            <button
              onClick={handleUseMyLocation}
              className="px-2.5 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/40 text-[11px] font-semibold flex items-center gap-1 transition-all shrink-0"
            >
              <RotateCcw className="w-3 h-3" /> Try Again
            </button>
          )}
        </div>
      )}

      {/* Quick City Pills */}
      <div className="flex flex-wrap items-center gap-2 mt-3 text-xs">
        <span className="text-slate-400 font-medium">Quick Cities:</span>
        {QUICK_CITIES.map((city, idx) => (
          <button
            key={idx}
            onClick={() => handleSelect({ latitude: city.lat, longitude: city.lon, name: city.name, admin1: city.admin1, country: 'India', source: 'search' })}
            className={`px-3 py-1 rounded-full border transition-all ${
              currentLocation?.name?.toLowerCase() === city.name.toLowerCase()
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 font-bold'
                : 'bg-dark-800/60 hover:bg-slate-700/60 border-slate-700/60 text-slate-300'
            }`}
          >
            {city.name}
          </button>
        ))}
      </div>
    </div>
  );
}
