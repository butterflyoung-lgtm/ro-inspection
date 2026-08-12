// Service Worker for RO/EDI Offline Inspection App Support
const CACHE_NAME = 'ro-edi-inspection-v4';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/styles.css?v=4.4',
    '/app.js?v=4.4',
    '/api/buildings'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((k) => {
                    if (k !== CACHE_NAME) return caches.delete(k);
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const url = e.request.url;

    // API calls for inspection submission, ping heartbeat, or listings -> Network only (never cache ping!)
    if (url.includes('/api/ping') || url.includes('/api/inspections') || url.includes('/api/trends') || url.includes('/api/login')) {
        return;
    }

    // Static assets & building schema -> Network first, fallback to Cache
    e.respondWith(
        fetch(e.request)
            .then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200 && e.request.method === 'GET') {
                    const cloned = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(e.request, cloned));
                }
                return networkResponse;
            })
            .catch(() => {
                return caches.match(e.request).then((cached) => {
                    if (cached) return cached;
                    if (e.request.mode === 'navigate') {
                        return caches.match('/index.html');
                    }
                });
            })
    );
});
