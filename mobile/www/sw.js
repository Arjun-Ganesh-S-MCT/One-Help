// Offline cache for the app shell. The big ONNX/wasm files are NOT precached.
const V = "oru-v1";
const SHELL = ["./", "index.html", "manifest.webmanifest", "css/fonts.css", "css/skeu.css", "css/app.css",
  "js/app.js", "js/i18n.js", "js/data.js", "js/icons.js", "js/complaint.js", "js/labels.js", "js/store.js", "js/crop.js", "js/assistant.js", "js/voice.js",
  "img/icon-192.png", "img/logo-wide-transparent.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== V).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.origin !== location.origin || /\.(wasm|onnx)$/.test(u.pathname) || u.pathname.includes("/vendor/")) return;
  e.respondWith(caches.match(r).then((hit) => hit || fetch(r).then((res) => { if (res.ok) { const cp = res.clone(); caches.open(V).then((c) => c.put(r, cp)); } return res; })));
});
