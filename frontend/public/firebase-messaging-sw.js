// Firebase Web Push Service Worker for WeatherGPT
// Receives emergency disaster alerts even when app is closed/minimized

importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyCMuqyujZ3Rn0QOViEQZ-2_xXHBh7V0BnY",
  authDomain: "vinoliya-97dbd.firebaseapp.com",
  projectId: "vinoliya-97dbd",
  storageBucket: "vinoliya-97dbd.firebasestorage.app",
  messagingSenderId: "406663451647",
  appId: "1:406663451647:web:08073b8cc424de78660dca",
  measurementId: "G-YP6GQD1QMY"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[WeatherGPT Service Worker] Received background disaster alert push:', payload);

  const title = payload.notification?.title || payload.data?.title || '🚨 CRITICAL WEATHER DISASTER ALERT';
  const body = payload.notification?.body || payload.data?.body || 'Severe weather emergency in your immediate area. Seek safe shelter!';
  
  const options = {
    body: body,
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    vibrate: [500, 200, 500, 200, 800],
    tag: 'critical-weather-disaster',
    renotify: true,
    requireInteraction: true,
    data: {
      url: payload.data?.click_action || '/',
      receivedAt: Date.now()
    }
  };

  self.registration.showNotification(title, options);
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (let client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
