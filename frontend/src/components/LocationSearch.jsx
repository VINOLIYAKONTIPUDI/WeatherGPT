import React, { useState, useEffect } from 'react';
import { Search, MapPin, Navigation, Loader2 } from 'lucide-react';
import { searchLocations, reverseGeocode } from '../services/api';

const QUICK_CITIES = [
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867 },
  { name: 'Vijayawada', lat: 16.5062, lon: 80.6480 },
  { name: 'Delhi', lat: 28.6139, lon: 77.2090 },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
  { name: 'Bengaluru', lat: 12.9716, lon: 77.5946 },
  { name: 'Tadepalligudem', lat: 16.8123, lon: 81.5284 },
];

export default function LocationSearch({ currentLocation, onLocationSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
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
    onLocationSelect({
      latitude: loc.latitude,
      longitude: loc.longitude,
      name: loc.name,
      country: loc.country || 'India',
      admin1: loc.admin1 || ''
    });
    setQuery('');
    setShowDropdown(false);
  };

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const geoResult = await reverseGeocode(lat, lon);
        onLocationSelect(geoResult);
        setIsLocating(false);
      },
      (err) => {
        console.warn('Geolocation denied or failed:', err);
        alert('Could not access your location. Using default location.');
        setIsLocating(false);
      },
      { timeout: 8000 }
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
              placeholder="Search city (e.g. Hyderabad, Vijayawada, Delhi)..."
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
        >
          {isLocating ? (
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          ) : (
            <Navigation className="w-4 h-4 text-cyan-400 fill-cyan-400/20" />
          )}
          <span>{isLocating ? 'Locating...' : 'Use My Location'}</span>
        </button>
      </div>

      {/* Quick City Pills */}
      <div className="flex flex-wrap items-center gap-2 mt-3 text-xs">
        <span className="text-slate-400 font-medium">Popular Cities:</span>
        {QUICK_CITIES.map((city, idx) => (
          <button
            key={idx}
            onClick={() => handleSelect({ latitude: city.lat, longitude: city.lon, name: city.name, country: 'India' })}
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
