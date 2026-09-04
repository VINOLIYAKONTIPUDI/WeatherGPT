const API_BASE = '/api';

export async function fetchWeatherForecast(lat, lon, name = 'Selected Location') {
  try {
    const res = await fetch(`${API_BASE}/weather/forecast?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Backend API unavailable, returning null for fallback handling:', err);
    return null;
  }
}

export async function sendChatMessage(message, location, language = 'en-IN', conversation = []) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        location,
        language,
        conversation,
      }),
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Chat API Error:', err);
    throw err;
  }
}

export async function fetchWeatherAlerts(lat, lon, name = 'Selected Location') {
  if (lat === undefined || lon === undefined || lat === null || lon === null) return null;
  try {
    const res = await fetch(`${API_BASE}/alerts?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Alerts API error:', err);
    return null;
  }
}

export async function searchLocations(query) {
  try {
    const res = await fetch(`${API_BASE}/location/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Location search API error:', err);
    return [];
  }
}

export async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(`${API_BASE}/location/reverse?lat=${lat}&lon=${lon}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Reverse geocode API error:', err);
    return { latitude: lat, longitude: lon, name: 'Current Location', country: 'India' };
  }
}
