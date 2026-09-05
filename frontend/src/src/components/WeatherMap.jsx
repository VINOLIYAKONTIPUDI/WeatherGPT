import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Compass, MapPin } from 'lucide-react';

const customMarkerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function MapRecenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, 10);
    }
  }, [center, map]);
  return null;
}

export default function WeatherMap({ location, currentWeather }) {
  if (!location || !location.latitude || !location.longitude) {
    return (
      <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 mb-8 text-center">
        <div className="flex flex-col items-center justify-center py-6 gap-2">
          <Compass className="w-8 h-8 text-cyan-400 opacity-60" />
          <h3 className="text-lg font-bold text-white">Interactive Location Map</h3>
          <p className="text-xs text-slate-400">Select your active location to anchor map telemetry.</p>
        </div>
      </div>
    );
  }

  const position = [location.latitude, location.longitude];

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 mb-8">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-xl font-bold text-white font-heading flex items-center gap-2">
            <Compass className="w-5 h-5 text-cyan-400" /> Interactive Location Map
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Live coordinates & weather station anchor</p>
        </div>
        <div className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
          📍 {location.name || location.city || 'Active Location'} ({position[0].toFixed(2)}°, {position[1].toFixed(2)}°)
        </div>
      </div>

      <div className="h-80 w-full rounded-2xl overflow-hidden border border-slate-700/60 shadow-inner relative z-0">
        <MapContainer center={position} zoom={10} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position} icon={customMarkerIcon}>
            <Popup>
              <div className="text-slate-900 p-1">
                <strong className="text-sm font-bold block">{location.name || location.city || 'Selected Location'}</strong>
                {currentWeather && (
                  <span className="text-xs font-medium text-slate-700 block mt-1">
                    🌡️ {Math.round(currentWeather.temperature)}°C — {currentWeather.condition}
                  </span>
                )}
              </div>
            </Popup>
          </Marker>
          <MapRecenter center={position} />
        </MapContainer>
      </div>
    </div>
  );
}
