// Offline shell for the cattle demo. Install caches only the small shell, so the worker becomes active at once;
// pictures and fonts are cached as they are used. Network first, so a new version arrives when there is signal.
var BASE = new URL('./', self.location).pathname; // '/cattle-demo/' on zamai.pro, '/' on ngombe.zamai.pro
var CACHE = 'cattle-demo-v65-' + BASE.replace(/\//g, '');
var SHELL = [BASE, BASE + 'index.html', BASE + 'manifest.webmanifest', BASE + 'icon-192.png', BASE + 'icon-512.png'];
var LATER = [BASE + 'icon-maskable-512.png', BASE + 'emblem.png',
  '/src/fonts/IBMPlexSans-400.woff2', '/src/fonts/IBMPlexSans-500.woff2',
  BASE + 'photos/a1.jpg', BASE + 'photos/a2.jpg', BASE + 'photos/a3.jpg', BASE + 'photos/a4.jpg', BASE + 'photos/a5.jpg',
  BASE + 'photos/a6.jpg', BASE + 'photos/a7.jpg', BASE + 'photos/a8.jpg', BASE + 'photos/a9.jpg', BASE + 'photos/a10.jpg',
  BASE + 'photos/c1.jpg', BASE + 'photos/c2.jpg', BASE + 'photos/c8.jpg', BASE + 'photos/k2.jpg', BASE + 'photos/m3.jpg', BASE + 'photos/m7.jpg', BASE + 'photos/m9.jpg', BASE + 'photos/f1.jpg', BASE + 'photos/d1.jpg', BASE + 'spec-sheet.html', BASE + 'spec-sheet.pdf', BASE + 'concept-note.pdf'];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return Promise.all(SHELL.map(function (u) { return c.add(u).catch(function () {}); }));
  }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }).then(function () {
    // fill the rest in the background, one by one, never blocking activation
    return caches.open(CACHE).then(function (c) {
      return LATER.reduce(function (p, u) { return p.then(function () { return c.add(u).catch(function () {}); }); }, Promise.resolve());
    });
  }));
});
self.addEventListener('fetch', function (e) {
  var u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (u.pathname.indexOf(BASE) !== 0 && u.pathname.indexOf('/src/fonts/') !== 0) return;
  e.respondWith(fetch(e.request).then(function (r) {
    if (r && r.ok) { var copy = r.clone(); caches.open(CACHE).then(function (c) { c.put(e.request, copy); }); }
    return r;
  }).catch(function () {
    return caches.match(e.request, { ignoreSearch: true }).then(function (m) { return m || caches.match(BASE); });
  }));
});
