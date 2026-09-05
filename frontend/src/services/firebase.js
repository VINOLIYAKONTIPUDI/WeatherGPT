import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, isSupported } from 'firebase/messaging';

// User's Firebase Configuration
export const firebaseConfig = {
  apiKey: "AIzaSyCMuqyujZ3Rn0QOViEQZ-2_xXHBh7V0BnY",
  authDomain: "vinoliya-97dbd.firebaseapp.com",
  projectId: "vinoliya-97dbd",
  storageBucket: "vinoliya-97dbd.firebasestorage.app",
  messagingSenderId: "406663451647",
  appId: "1:406663451647:web:08073b8cc424de78660dca",
  measurementId: "G-YP6GQD1QMY"
};

// Initialize Firebase App
export const app = initializeApp(firebaseConfig);

let messagingInstance = null;

export const getFirebaseMessaging = async () => {
  if (typeof window === 'undefined') return null;
  if (messagingInstance) return messagingInstance;
  
  try {
    const supported = await isSupported();
    if (supported) {
      messagingInstance = getMessaging(app);
      return messagingInstance;
    }
  } catch (err) {
    console.warn('Firebase Messaging not supported in this environment:', err);
  }
  return null;
};

/**
 * Register Service Worker and Request Notification Permission
 */
export const requestPushNotificationPermission = async (vapidKey = null) => {
  if (typeof window === 'undefined' || !('Notification' in window)) {
    return { success: false, reason: 'Notifications not supported by this browser.' };
  }

  try {
    let permission;
    try {
      permission = await Notification.requestPermission();
    } catch (permErr) {
      console.warn('Notification.requestPermission failed (likely non-HTTPS origin):', permErr);
      return { success: false, reason: 'Notifications require a secure HTTPS connection or were blocked.' };
    }

    if (permission !== 'granted') {
      return { success: false, permission, reason: 'Notification permission denied by user.' };
    }

    // Register Firebase Service Worker if supported
    let swRegistration = null;
    if ('serviceWorker' in navigator) {
      try {
        swRegistration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
        console.log('WeatherGPT ServiceWorker registered:', swRegistration);
      } catch (swErr) {
        console.warn('Could not register /firebase-messaging-sw.js:', swErr);
      }
    }

    let token = null;
    try {
      const messaging = await getFirebaseMessaging();
      if (messaging && swRegistration) {
        const tokenOptions = {
          serviceWorkerRegistration: swRegistration
        };
        if (vapidKey) {
          tokenOptions.vapidKey = vapidKey;
        }
        token = await getToken(messaging, tokenOptions);
        console.log('Firebase Cloud Messaging Token acquired:', token);
      }
    } catch (tokenErr) {
      console.warn('FCM Token generation note:', tokenErr.message);
    }

    return {
      success: true,
      permission: 'granted',
      fcmToken: token,
      deviceReady: true
    };
  } catch (err) {
    console.error('Failed to request notification permission:', err);
    return { success: false, reason: err.message };
  }
};

/**
 * Listen for foreground emergency alert messages pushed via FCM
 */
export const onEmergencyForegroundMessage = async (callback) => {
  try {
    const messaging = await getFirebaseMessaging();
    if (!messaging) return () => {};

    return onMessage(messaging, (payload) => {
      console.log('Foreground emergency alert received from Firebase:', payload);
      if (callback) callback(payload);
    });
  } catch (e) {
    console.warn('onEmergencyForegroundMessage error:', e);
    return () => {};
  }
};

/**
 * Send an immediate Physical Device Push Alert & Vibration
 * 100% Free - Works on mobile Chrome/Firefox/Edge and desktop!
 */
export const triggerDeviceDisasterPush = async ({
  title = '🚨 CRITICAL WEATHER EMERGENCY ALERT',
  body = 'Severe thunderstorm & flash flood hazard in your location. Take shelter!',
  location = 'Your Area',
  vibratePattern = [500, 200, 500, 200, 800]
}) => {
  try {
    // 1. Hardware Phone Vibration
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      try {
        navigator.vibrate(vibratePattern);
      } catch (e) {
        console.warn('Hardware vibration failed:', e);
      }
    }

    // 2. System Push Notification
    if (typeof window !== 'undefined' && 'Notification' in window) {
      let isGranted = false;
      try {
        isGranted = Notification.permission === 'granted';
      } catch (e) {
        isGranted = false;
      }

      if (isGranted) {
        const options = {
          body: `📍 ${location}\n${body}`,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          vibrate: vibratePattern,
          tag: 'weathergpt-hazard-' + Date.now(),
          renotify: true,
          requireInteraction: true,
          data: {
            url: window.location.href,
            timestamp: Date.now()
          }
        };

        try {
          if ('serviceWorker' in navigator && navigator.serviceWorker.ready) {
            const reg = await navigator.serviceWorker.ready;
            if (reg && reg.showNotification) {
              await reg.showNotification(title, options);
              return true;
            }
          }
        } catch (swErr) {
          console.warn('SW notification fallback to window.Notification:', swErr);
        }

        try {
          new Notification(title, options);
          return true;
        } catch (notifErr) {
          console.warn('Native notification failed:', notifErr);
        }
      }
    }
  } catch (err) {
    console.warn('triggerDeviceDisasterPush caught error:', err);
  }

  return false;
};
