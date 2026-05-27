const C='hajj-v38';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;e.respondWith(fetch(r).then(resp=>{const cp=resp.clone();caches.open(C).then(c=>c.put(r,cp));return resp}).catch(()=>caches.match(r)))});