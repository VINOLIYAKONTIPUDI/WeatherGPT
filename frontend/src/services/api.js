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
async function parseJsonResponse(res, fallbackMessage = 'Request failed') {
  let data;
  try {
    data = await res.json();
  } catch (err) {
    if (!res.ok) {
      throw new Error(`Server Error (${res.status}): ${res.statusText || 'Internal Server Error'}`);
    }
    throw new Error('Invalid server response');
  }
  if (!res.ok) {
    throw new Error(data?.detail || fallbackMessage);
  }
  return data;
}

export async function signupUser(name, email, password, confirm_password) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password, confirm_password }),
  });
  return await parseJsonResponse(res, 'Signup failed.');
}

export async function verifyOTP(email, otp) {
  const res = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  });
  return await parseJsonResponse(res, 'OTP Verification failed.');
}

export async function resendOTP(email) {
  const res = await fetch(`${API_BASE}/auth/resend-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return await parseJsonResponse(res, 'Failed to resend OTP.');
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return await parseJsonResponse(res, 'Login failed.');
}

export async function getCurrentUser(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  return await parseJsonResponse(res, 'Invalid token.');
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
  return await parseJsonResponse(res, 'Failed to schedule notification.');
}

export async function fetchNotifications(token) {
  const res = await fetch(`${API_BASE}/notifications`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  return await parseJsonResponse(res, 'Failed to fetch notifications.');
}

export async function deleteNotification(token, notifId) {
  const res = await fetch(`${API_BASE}/notifications/${notifId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  return await parseJsonResponse(res, 'Failed to delete notification.');
}



