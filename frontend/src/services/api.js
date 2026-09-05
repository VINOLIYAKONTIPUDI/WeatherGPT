const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

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

// Authentication API Services
export async function signupUser(name, email, password, confirm_password) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password, confirm_password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Signup failed.');
  return data;
}

export async function verifyOTP(email, otp) {
  const res = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'OTP Verification failed.');
  return data;
}

export async function resendOTP(email) {
  const res = await fetch(`${API_BASE}/auth/resend-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to resend OTP.');
  return data;
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed.');
  return data;
}

export async function getCurrentUser(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Invalid token.');
  return data;
}

export async function fetchCropAdvisory(crop, stage, weatherData = null) {
  try {
    const res = await fetch(`${API_BASE}/advisory/crop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ crop, stage, weather_data: weatherData }),
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Crop advisory API unavailable, returning fallback:', err);
    return null;
  }
}

// Scheduled Weather Notifications API
export async function scheduleNotification(token, targetDate, targetTime, type, location) {
  const res = await fetch(`${API_BASE}/notifications/schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      target_date: targetDate,
      target_time: targetTime,
      type,
      location
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to schedule notification.');
  return data;
}

export async function fetchNotifications(token) {
  const res = await fetch(`${API_BASE}/notifications`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to fetch notifications.');
  return data;
}

export async function deleteNotification(token, notifId) {
  const res = await fetch(`${API_BASE}/notifications/${notifId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to delete notification.');
  return data;
}



