const API_BASE = '/api';

async function parseResponseJson(res, defaultErrMsg = 'Request failed') {
  let data;
  try {
    const text = await res.text();
    data = text ? JSON.parse(text) : {};
  } catch (e) {
    data = {};
  }
  if (!res.ok) {
    throw new Error(data.detail || data.message || `${defaultErrMsg} (Status ${res.status})`);
  }
  return data;
}

export async function fetchWeatherForecast(lat, lon, name = 'Selected Location') {
  try {
    const res = await fetch(`${API_BASE}/weather/forecast?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`);
    return await parseResponseJson(res, 'Weather fetch failed');
  } catch (err) {
    console.warn('Backend API unavailable, returning null for fallback handling:', err);
    return null;
  }
}

export async function sendChatMessage(message, location, language, conversation = []) {
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
    return await parseResponseJson(res, 'Chat request failed');
  } catch (err) {
    console.error('Chat API Error:', err);
    throw err;
  }
}

export async function fetchWeatherAlerts(lat, lon, name = 'Selected Location') {
  if (lat === undefined || lon === undefined || lat === null || lon === null) return null;
  try {
    const res = await fetch(`${API_BASE}/alerts?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`);
    return await parseResponseJson(res, 'Alerts fetch failed');
  } catch (err) {
    console.warn('Alerts API error:', err);
    return null;
  }
}

export async function searchLocations(query) {
  try {
    const res = await fetch(`${API_BASE}/location/search?q=${encodeURIComponent(query)}`);
    return await parseResponseJson(res, 'Location search failed');
  } catch (err) {
    console.warn('Location search API error:', err);
    return [];
  }
}

export async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(`${API_BASE}/location/reverse?lat=${lat}&lon=${lon}`);
    return await parseResponseJson(res, 'Reverse geocode failed');
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
  return await parseResponseJson(res, 'Signup failed');
}

export async function verifyOTP(email, otp) {
  const res = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  });
  return await parseResponseJson(res, 'OTP Verification failed');
}

export async function resendOTP(email) {
  const res = await fetch(`${API_BASE}/auth/resend-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return await parseResponseJson(res, 'Failed to resend OTP');
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return await parseResponseJson(res, 'Login failed');
}

export async function getCurrentUser(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });
  return await parseResponseJson(res, 'Invalid token');
}
