"""
Single build script: reads pilgrim data, encrypts, generates both HTML files.
Run: python3 build_all.py
"""
import json, os, base64, zipfile
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE = '/Users/m/Documents/est3lam'
import re, subprocess, sys
import gen_manifest
PASSWORD_SEARCH   = b'112233'   # same for all campaigns
PASSWORD_MANIFEST = b'111222'

def make_payload(data_bytes, password):
    salt  = os.urandom(16)
    nonce = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = kdf.derive(password)
    enc = AESGCM(key).encrypt(nonce, data_bytes, None)
    return base64.b64encode(salt + nonce + enc).decode()

def load_data_bytes(path):
    with open(path,'r',encoding='utf-8') as f:
        records = json.load(f)
    for r in records:   # strip leading zero from mina: 001-1001 → 1-1001
        m = r.get('mina','')
        if m and m != '-' and '-' in m:
            parts = m.split('-'); parts[0] = parts[0].lstrip('0') or '0'; r['mina'] = '-'.join(parts)
    return json.dumps(records, ensure_ascii=False).encode('utf-8')

# Theme: templates are natively green (المحيميد). الرويس = charcoal/gold (green→charcoal, gold kept).
THEME_RUWAIS = {
    '#0d4f3c':'#2b3039', '#1a7a5e':'#4a525e',
    '#f5fdf8':'#f7f8fa', '#d4eee4':'#e4e7ec', '#e0f5ef':'#e4e7ec',
    '#edfaf5':'#f2f4f7', '#f8fffe':'#fafbfc',
}
def apply_theme(html, theme):
    for a,b in (theme or {}).items():
        html = html.replace(a,b)
    return html

# ── PWA (installable mobile app) ──
from PIL import Image, ImageDraw

def gen_icon(path, c_dark, c_med, gold, size=512):
    dk=tuple(int(c_dark[i:i+2],16) for i in (1,3,5))
    md=tuple(int(c_med[i:i+2],16) for i in (1,3,5))
    gd=tuple(int(gold[i:i+2],16) for i in (1,3,5))
    img=Image.new('RGB',(size,size),dk); d=ImageDraw.Draw(img)
    for y in range(size):  # vertical gradient
        t=y/size
        d.line([(0,y),(size,y)],fill=tuple(int(dk[k]*(1-t)+md[k]*t) for k in range(3)))
    cx=cy=size//2; s=int(size*0.40); x0=cx-s//2; y0=cy-s//2
    d.rounded_rectangle([x0,y0,x0+s,y0+s],radius=int(s*0.06),fill=(20,20,20),outline=gd,width=max(3,size//110))  # kaaba cube
    by=y0+int(s*0.27); d.rectangle([x0,by,x0+s,by+int(s*0.11)],fill=gd)  # kiswa band
    dw=int(s*0.17); dh=int(s*0.30); d.rectangle([cx-dw//2,y0+s-dh,cx+dw//2,y0+s],fill=gd)  # door
    img.save(path)

def write_icons(prefix, c_dark, c_med, gold):
    gen_icon(f'{BASE}/{prefix}-512.png', c_dark, c_med, gold, 512)
    img=Image.open(f'{BASE}/{prefix}-512.png')
    img.resize((192,192),Image.LANCZOS).save(f'{BASE}/{prefix}-192.png')
    img.resize((180,180),Image.LANCZOS).save(f'{BASE}/{prefix}-180.png')

def webmanifest_json(app_name, short_name, start_url, theme, bg, prefix):
    return json.dumps({
        "name":app_name,"short_name":short_name,"start_url":start_url,"scope":"./",
        "display":"standalone","orientation":"portrait","background_color":bg,
        "theme_color":theme,"dir":"rtl","lang":"ar",
        "icons":[
            {"src":f"{prefix}-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
            {"src":f"{prefix}-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"},
        ]}, ensure_ascii=False)

def pwa_head(webmanifest, theme, app_name, icon180):
    return ('<link rel="manifest" href="'+webmanifest+'">'
            '<meta name="theme-color" content="'+theme+'">'
            '<meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
            '<meta name="apple-mobile-web-app-title" content="'+app_name+'">'
            '<link rel="apple-touch-icon" href="'+icon180+'">')

SW_JS = """const C='hajj-v1';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;e.respondWith(fetch(r).then(resp=>{const cp=resp.clone();caches.open(C).then(c=>c.put(r,cp));return resp}).catch(()=>caches.match(r)))});"""
SW_REG = "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('sw.js').catch(()=>{})}</script>"

# ── Campaign switcher (persistent top bar) ──
def switcher(active):
    m = 'active' if active=='muhaimeed' else ''
    r = 'active' if active=='ruwais' else ''
    return ('<div class="campaign-switch">'
            f'<a href="muhaimeed.html" class="camp-btn {m}">شركة المحيميد</a>'
            f'<a href="ruwais.html" class="camp-btn {r}">شركة الرويس</a>'
            '</div>')
SWITCH_CSS = (".campaign-switch{display:flex;gap:8px;margin-bottom:12px}"
    ".camp-btn{flex:1;text-align:center;padding:9px 10px;border-radius:10px;font-size:.85rem;font-weight:700;text-decoration:none;"
    "border:1.5px solid rgba(245,208,110,.45);color:#f5d06e;background:rgba(255,255,255,.08);transition:.15s}"
    ".camp-btn.active{background:#f5d06e;color:#0d4f3c;border-color:#f5d06e}"
    ".camp-btn:active{transform:scale(.97)}")

# WhatsApp helper for search results (number normalized to 966)
WA_JS = ("const WA_SVG='<svg viewBox=\"0 0 24 24\"><path d=\"M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38c1.45.79 3.08 1.21 4.79 1.21h.01c5.46 0 9.9-4.45 9.9-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0012.04 2zm5.8 14.04c-.24.68-1.42 1.31-1.96 1.39-.5.07-1.13.1-1.83-.11-.42-.13-.96-.31-1.65-.61-2.9-1.25-4.8-4.17-4.95-4.36-.14-.19-1.18-1.57-1.18-2.99s.75-2.12 1.01-2.41c.26-.29.57-.36.76-.36.19 0 .38 0 .54.01.18.01.41-.07.64.49.24.57.81 1.97.88 2.11.07.14.12.31.02.5-.09.19-.14.31-.28.47-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.17.28.74 1.22 1.59 1.98 1.1.97 2.02 1.27 2.3 1.42.28.14.45.12.61-.07.17-.19.7-.82.89-1.1.18-.28.37-.23.61-.14.25.09 1.57.74 1.84.88.27.14.45.2.51.31.07.11.07.63-.17 1.31z\"/></svg>';"
    "function waLink(ph){let n=(ph||'').replace(/\\D/g,'');if(!n)return'';if(n[0]==='0')n=n.slice(1);if(n.indexOf('966')!==0)n='966'+n;return'https://wa.me/'+n;}")

# ── Cloud sync (Supabase) — all values AES-encrypted client-side before upload (zero-knowledge) ──
SUPABASE_URL = 'https://crpcgsznwqrphgfapthw.supabase.co'
SUPABASE_KEY = 'sb_publishable_6l1ngkrRbe6UwQjiaj5O3Q_hLa4QCjG'
CLOUD_JS = ("const SUPA_URL='"+SUPABASE_URL+"';const SUPA_KEY='"+SUPABASE_KEY+"';"
    "const SUPA_H={apikey:SUPA_KEY,Authorization:'Bearer '+SUPA_KEY,'Content-Type':'application/json'};"
    "async function _ckey(p,salt){const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(p),'PBKDF2',false,['deriveKey']);"
    "return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:100000,hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);}"
    "async function encB64(o,p){const s=crypto.getRandomValues(new Uint8Array(16)),n=crypto.getRandomValues(new Uint8Array(12));const k=await _ckey(p,s);"
    "const e=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv:n},k,new TextEncoder().encode(JSON.stringify(o))));"
    "const b=new Uint8Array(28+e.length);b.set(s);b.set(n,16);b.set(e,28);let x='';b.forEach(c=>x+=String.fromCharCode(c));return btoa(x);}"
    "async function decB64(b64,p){const r=atob(b64);const b=new Uint8Array(r.length);for(let i=0;i<r.length;i++)b[i]=r.charCodeAt(i);"
    "const k=await _ckey(p,b.slice(0,16));const d=await crypto.subtle.decrypt({name:'AES-GCM',iv:b.slice(16,28)},k,b.slice(28));return JSON.parse(new TextDecoder().decode(d));}"
    "function _cpass(){return sessionStorage.getItem('pass')||'';}"
    "async function cloudGet(k){try{const r=await fetch(SUPA_URL+'/rest/v1/app_data?select=v&k=eq.'+encodeURIComponent(k),{headers:SUPA_H});"
    "if(!r.ok)return null;const a=await r.json();if(!a[0])return null;return await decB64(a[0].v,_cpass());}catch(e){return null;}}"
    "async function cloudSet(k,o){try{const v=await encB64(o,_cpass());"
    "const r=await fetch(SUPA_URL+'/rest/v1/app_data',{method:'POST',headers:Object.assign({},SUPA_H,{Prefer:'resolution=merge-duplicates'}),"
    "body:JSON.stringify([{k:k,v:v,updated_at:new Date().toISOString()}])});return r.ok;}catch(e){return false;}}")

# ── Reports / complaints (بلاغات) ──
RPT_SVG = ('<svg viewBox="0 0 24 24"><rect x="2.5" y="5" width="19" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.7"/>'
    '<line x1="6" y1="10" x2="12.5" y2="10" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="13.5" x2="10" y2="13.5" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M14.5 9.5l4 4m0-4l-4 4" stroke="#ef4444" stroke-width="1.9" stroke-linecap="round"/></svg>')

def reports_js(key, link):
    return ("const RPT_SVG='"+RPT_SVG+"';"
        "const RPT_KEY='"+key+"';"
        "async function report(p){let a=[];try{a=JSON.parse(localStorage.getItem(RPT_KEY)||'[]')}catch(e){}"
        "try{const c=await cloudGet(RPT_KEY);if(Array.isArray(c))a=c;}catch(e){}"
        "const id=(p.id||'')+'_'+(p.resv||'');"
        "if(!a.some(r=>r._id===id))a.unshift({_id:id,name:p.name,resv:p.resv||'',bus:p.bus||'',mina:p.mina||'',phone:p.phone||'',resolved:false,ts:Date.now()});"
        "localStorage.setItem(RPT_KEY,JSON.stringify(a));try{await cloudSet(RPT_KEY,a);}catch(e){}location.href='"+link+"';}")

RPT_CSS = (".rpt-btn-ic{display:inline-flex;align-items:center;justify-content:center;width:40px;background:rgba(255,255,255,.18);border:1.5px solid rgba(255,255,255,.35);border-radius:10px;color:#fff;cursor:pointer;flex-shrink:0;margin-top:2px;padding:7px 6px;line-height:1}"
    ".rpt-btn-ic svg{width:20px;height:20px}.rpt-btn-ic:active{transform:scale(.92)}"
    ".rpt-mini{width:30px;height:30px;background:#fff;border:1px solid #f0c8c8;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;color:#666;padding:0}"
    ".rpt-mini svg{width:18px;height:18px}")

def make_reports(RPT_KEY, SEARCH_LINK, SWITCHER):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>البلاغات</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c 0%,#1a7a5e 50%,#0d4f3c 100%);min-height:100vh;padding:0 0 40px}}
  header{{background:rgba(0,0,0,.25);padding:16px;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.1)}}
  {SWITCH_CSS}
  .hdr-row{{display:flex;align-items:center;justify-content:space-between;margin-top:4px}}
  header h1{{color:#f5d06e;font-size:1.15rem;font-weight:700}}
  .nav-link{{background:rgba(255,255,255,.15);color:#f5d06e;border-radius:10px;padding:6px 11px;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid rgba(245,208,110,.3)}}
  .summary{{text-align:center;color:rgba(255,255,255,.85);font-size:.88rem;margin:14px 0 4px}}
  .summary b{{color:#f5d06e}}
  #list{{padding:12px 16px;max-width:600px;margin:0 auto}}
  .rpt-card{{background:white;border-radius:16px;box-shadow:0 4px 18px rgba(0,0,0,.18);margin-bottom:14px;overflow:hidden;border-right:5px solid #e07b00;animation:fadeUp .2s ease}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
  .rpt-card.done{{border-right-color:#22c55e;opacity:.72}}
  .rpt-top{{padding:14px 16px 10px}}
  .rpt-name{{font-size:1.05rem;font-weight:700;color:#0d4f3c;margin-bottom:7px}}
  .rpt-card.done .rpt-name{{text-decoration:line-through;color:#888}}
  .rpt-meta{{display:flex;flex-wrap:wrap;gap:6px}}
  .rpt-chip{{font-size:.72rem;background:#f0f4f0;color:#444;border-radius:6px;padding:3px 8px;font-weight:600;direction:ltr}}
  .rpt-bar{{display:flex;gap:8px;padding:10px 12px;background:#fafafa;border-top:1px solid #eee}}
  .rpt-btn{{border:none;border-radius:9px;padding:9px;font-size:.82rem;font-weight:700;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;justify-content:center;gap:5px}}
  .b-resolve{{flex:1;background:#dcfce7;color:#15803d}}
  .rpt-card.done .b-resolve{{background:#22c55e;color:#fff}}
  .b-wa{{background:#25D366;width:46px}}
  .b-wa svg{{width:20px;height:20px;fill:#fff}}
  .b-del{{background:#fee2e2;color:#dc2626;width:46px;font-size:1rem}}
  .empty{{text-align:center;color:rgba(255,255,255,.7);margin-top:70px}}
  .empty .icon{{font-size:3.2rem;display:block;margin-bottom:10px}}
</style>
</head>
<body>
<header>
  {SWITCHER}
  <div class="hdr-row">
    <h1>🚩 البلاغات</h1>
    <a href="{SEARCH_LINK}" class="nav-link">🔍 بحث الحجاج</a>
  </div>
</header>
<div class="summary" id="summary"></div>
<div id="list"></div>
<script>
{CLOUD_JS}
{WA_JS}
const RPT_KEY='{RPT_KEY}';
let _reports=[];
function _local(){{try{{return JSON.parse(localStorage.getItem(RPT_KEY)||'[]')}}catch(e){{return[]}}}}
function _saveLocal(a){{localStorage.setItem(RPT_KEY,JSON.stringify(a))}}
async function _persist(){{_saveLocal(_reports);try{{await cloudSet(RPT_KEY,_reports)}}catch(e){{}}}}
function toggle(id){{const r=_reports.find(x=>x._id===id);if(r)r.resolved=!r.resolved;_persist();render()}}
function del(id){{if(!confirm('حذف البلاغ؟'))return;_reports=_reports.filter(x=>x._id!==id);_persist();render()}}
function render(){{
  const a=_reports;const done=a.filter(r=>r.resolved).length;
  document.getElementById('summary').innerHTML=a.length?`<b>${{a.length}}</b> بلاغ · <b>${{done}}</b> تم حلها`:'';
  const l=document.getElementById('list');
  if(!a.length){{l.innerHTML='<div class="empty"><span class="icon">✅</span><p>لا توجد بلاغات</p></div>';return}}
  l.innerHTML=a.map(r=>`<div class="rpt-card${{r.resolved?' done':''}}">
    <div class="rpt-top"><div class="rpt-name">${{r.name}}</div>
      <div class="rpt-meta">${{r.resv?`<span class="rpt-chip">حجز ${{r.resv}}</span>`:''}}${{r.bus?`<span class="rpt-chip">باص ${{r.bus}}</span>`:''}}${{r.mina?`<span class="rpt-chip">سكن ${{r.mina}}</span>`:''}}</div>
    </div>
    <div class="rpt-bar">
      <button class="rpt-btn b-resolve" onclick="toggle('${{r._id}}')">${{r.resolved?'✓ تم الحل':'وضع كمحلول'}}</button>
      ${{r.phone?`<a class="rpt-btn b-wa" href="${{waLink(r.phone)}}" target="_blank" rel="noopener">${{WA_SVG}}</a>`:''}}
      <button class="rpt-btn b-del" onclick="del('${{r._id}}')">🗑</button>
    </div>
  </div>`).join('');
}}
async function init(){{
  if(sessionStorage.getItem('auth')!=='1'){{location.href='{SEARCH_LINK}';return;}}
  _reports=_local();render();
  const c=await cloudGet(RPT_KEY);if(Array.isArray(c)){{_reports=c;_saveLocal(c);render();}}
}}
init();
</script>
</body>
</html>"""

# ── Shared pieces ──
LOCK_CSS = """
  #lockScreen{position:fixed;inset:0;z-index:9999;background:linear-gradient(135deg,#0d4f3c,#1a7a5e);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
  .lock-box{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-radius:24px;padding:32px 24px 28px;width:100%;max-width:320px;text-align:center;backdrop-filter:blur(12px)}
  .lock-icon{font-size:2.8rem;margin-bottom:10px}
  .lock-box h2{color:#f5d06e;font-size:1.25rem;margin-bottom:6px}
  .lock-page{display:inline-block;background:rgba(245,208,110,.15);border:1px solid rgba(245,208,110,.4);color:#f5d06e;font-size:.9rem;font-weight:700;border-radius:20px;padding:5px 16px;margin-bottom:12px}
  .lock-box p{color:rgba(255,255,255,.6);font-size:.82rem;margin-bottom:20px}
  .pin-display{display:flex;gap:14px;justify-content:center;margin-bottom:6px}
  .pin-dot{width:15px;height:15px;border-radius:50%;border:2px solid rgba(255,255,255,.4);background:transparent;transition:background .12s,border-color .12s}
  .pin-dot.filled{background:#f5d06e;border-color:#f5d06e}
  .lock-err{color:#ff8080;font-size:.8rem;margin:8px 0 4px;min-height:1.1em;display:none}
  .pin-pad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px;direction:ltr}
  .pin-pad button{background:rgba(255,255,255,.13);border:1.5px solid rgba(255,255,255,.2);border-radius:14px;color:white;font-size:1.55rem;font-weight:500;padding:15px 8px;cursor:pointer;font-family:inherit;transition:background .1s,transform .08s;-webkit-tap-highlight-color:transparent;line-height:1}
  .pin-pad button:active{background:rgba(255,255,255,.3);transform:scale(.92)}
  .pin-del{font-size:1.15rem !important}
  .pin-empty{visibility:hidden !important;pointer-events:none}
  @keyframes shake{0%,100%{transform:translateX(0)}20%,60%{transform:translateX(-7px)}40%,80%{transform:translateX(7px)}}
  .pin-shake{animation:shake .35s ease}"""

LOCK_HTML = """<div id="lockScreen">
  <div class="lock-box">
    <div class="lock-icon">🔐</div>
    <h2>يسر مساند</h2>
    <div class="lock-page">__PAGETYPE__</div>
    <p>أدخل كلمة المرور</p>
    <div id="pinDisplay" class="pin-display">
      <span class="pin-dot" id="pd0"></span>
      <span class="pin-dot" id="pd1"></span>
      <span class="pin-dot" id="pd2"></span>
      <span class="pin-dot" id="pd3"></span>
      <span class="pin-dot" id="pd4"></span>
      <span class="pin-dot" id="pd5"></span>
    </div>
    <div class="lock-err" id="passErr">كلمة المرور غير صحيحة ❌</div>
    <div class="pin-pad">
      <button onclick="pinKey('1')">1</button>
      <button onclick="pinKey('2')">2</button>
      <button onclick="pinKey('3')">3</button>
      <button onclick="pinKey('4')">4</button>
      <button onclick="pinKey('5')">5</button>
      <button onclick="pinKey('6')">6</button>
      <button onclick="pinKey('7')">7</button>
      <button onclick="pinKey('8')">8</button>
      <button onclick="pinKey('9')">9</button>
      <button class="pin-empty" disabled></button>
      <button onclick="pinKey('0')">0</button>
      <button class="pin-del" onclick="pinDel()">⌫</button>
    </div>
  </div>
</div>"""

def make_decrypt_js(payload):
    return ("""
const __PAYLOAD = '""" + payload + """';
let _pin='';
function _upd(){for(let i=0;i<6;i++)document.getElementById('pd'+i).classList.toggle('filled',i<_pin.length);}
function pinKey(d){if(_pin.length>=6)return;_pin+=d;_upd();if(_pin.length===6)tryPass();}
function pinDel(){if(!_pin.length)return;_pin=_pin.slice(0,-1);_upd();}
async function decryptData(pass){
  const raw=atob(__PAYLOAD);const buf=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)buf[i]=raw.charCodeAt(i);
  const salt=buf.slice(0,16),nonce=buf.slice(16,28),data=buf.slice(28);
  const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pass),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:100000,hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['decrypt']);
  const dec=await crypto.subtle.decrypt({name:'AES-GCM',iv:nonce},key,data);
  return JSON.parse(new TextDecoder().decode(dec));
}
async function tryPass(){
  const v=_pin;
  try{
    const d=await decryptData(v);window._DATA=d;
    sessionStorage.setItem('auth','1');sessionStorage.setItem('pass',v);
    document.getElementById('lockScreen').style.display='none';
    if(typeof onDataReady==='function')onDataReady(d);
  }catch(e){
    const err=document.getElementById('passErr');err.style.display='block';
    document.getElementById('pinDisplay').classList.add('pin-shake');
    _pin='';_upd();
    setTimeout(()=>{err.style.display='none';document.getElementById('pinDisplay').classList.remove('pin-shake');},2000);
  }
}
async function initAuth(){
  if(sessionStorage.getItem('auth')==='1'){
    try{const d=await decryptData(sessionStorage.getItem('pass')||'');window._DATA=d;document.getElementById('lockScreen').style.display='none';if(typeof onDataReady==='function')onDataReady(d);}
    catch{sessionStorage.clear();}
  }
}""")

# ════════════════════════════════
# index.html  (search) — built per campaign
# ════════════════════════════════
def make_index(DECRYPT_JS, LOCK_HTML, H1, NAV, QR, CARDFILE, SWITCHER, REPORTS_JS, REPORTS_LINK, SCAN_LINK, DASH_LINK=''):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>بحث حجاج يسر مساند</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c 0%,#1a7a5e 50%,#0d4f3c 100%);min-height:100vh;padding:0 0 40px}}
  header{{background:rgba(0,0,0,.25);padding:16px 16px 14px;text-align:center;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.1)}}
  .hdr-row{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
  header h1{{color:#f5d06e;font-size:1.15rem;font-weight:700;display:flex;align-items:center;gap:8px}}
  .nav-link{{background:rgba(255,255,255,.15);color:#f5d06e;border-radius:10px;padding:6px 11px;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid rgba(245,208,110,.3)}}
  {SWITCH_CSS}
  .search-wrap{{position:relative}}
  #searchInput{{width:100%;padding:14px 48px 14px 16px;border-radius:14px;border:2px solid rgba(245,208,110,.4);background:rgba(255,255,255,.95);font-size:1.05rem;color:#1a1a1a;font-family:inherit;outline:none;text-align:right;transition:.2s}}
  #searchInput:focus{{border-color:#f5d06e;box-shadow:0 0 0 3px rgba(245,208,110,.2)}}
  #searchInput::placeholder{{color:#999;font-size:.95rem}}
  .search-icon{{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#1a7a5e;font-size:1.2rem;pointer-events:none}}
  .clear-btn{{position:absolute;right:12px;top:50%;transform:translateY(-50%);background:#ddd;border:none;border-radius:50%;width:26px;height:26px;font-size:.85rem;cursor:pointer;display:none;align-items:center;justify-content:center;color:#666}}
  .clear-btn.visible{{display:flex}}
  .search-actions{{display:flex;gap:8px;margin-top:10px}}
  .btn-scan{{flex:1;display:flex;align-items:center;justify-content:center;gap:7px;background:#f5d06e;color:#0d4f3c;border:none;border-radius:12px;padding:12px 10px;font-size:.93rem;font-weight:800;cursor:pointer;font-family:inherit;transition:.15s}}
  .btn-scan:active{{transform:scale(.97)}}
  .btn-adv{{display:flex;align-items:center;justify-content:center;gap:6px;background:rgba(255,255,255,.15);color:#f5d06e;border:1.5px solid rgba(245,208,110,.4);border-radius:12px;padding:12px 14px;font-size:.88rem;font-weight:700;cursor:pointer;font-family:inherit;white-space:nowrap;transition:.15s}}
  .btn-adv.active{{background:#f5d06e;color:#0d4f3c;border-color:#f5d06e}}
  .btn-adv:active{{transform:scale(.97)}}
  .adv-panel{{display:none;background:rgba(0,0,0,.18);border-radius:14px;padding:14px;margin-top:10px;border:1px solid rgba(255,255,255,.1)}}
  .adv-panel.open{{display:block;animation:fadeUp .18s ease}}
  .adv-row{{display:flex;gap:8px;margin-bottom:10px;align-items:flex-end}}
  .adv-row:last-child{{margin-bottom:0}}
  .adv-field{{flex:1;display:flex;flex-direction:column;gap:4px}}
  .adv-label{{color:rgba(255,255,255,.65);font-size:.72rem;font-weight:700}}
  .adv-input{{padding:9px 12px;border-radius:10px;border:1.5px solid rgba(255,255,255,.2);background:rgba(255,255,255,.92);font-size:.95rem;color:#1a1a1a;font-family:inherit;outline:none;width:100%;direction:ltr}}
  .adv-input:focus{{border-color:#f5d06e}}
  .adv-select{{padding:9px 12px;border-radius:10px;border:1.5px solid rgba(255,255,255,.2);background:rgba(255,255,255,.92);font-size:.88rem;color:#1a1a1a;font-family:inherit;outline:none;width:100%;appearance:none;-webkit-appearance:none;direction:rtl}}
  .adv-select:focus{{border-color:#f5d06e}}
  .gender-grp{{display:flex;gap:6px}}
  .gender-btn{{flex:1;padding:8px 6px;border-radius:9px;border:1.5px solid rgba(255,255,255,.25);background:rgba(255,255,255,.12);color:rgba(255,255,255,.85);font-size:.82rem;font-weight:700;cursor:pointer;font-family:inherit;transition:.15s;text-align:center}}
  .gender-btn.active{{background:#f5d06e;color:#0d4f3c;border-color:#f5d06e}}
  .adv-clear{{background:rgba(239,68,68,.25);color:#fca5a5;border:1.5px solid rgba(239,68,68,.35);border-radius:9px;padding:9px 13px;font-size:.82rem;font-weight:700;cursor:pointer;font-family:inherit;white-space:nowrap}}
  .adv-clear:active{{transform:scale(.97)}}
  .adv-badge{{display:inline-block;background:#ef4444;color:#fff;border-radius:50%;width:16px;height:16px;font-size:.62rem;font-weight:800;text-align:center;line-height:16px;margin-right:2px}}
  #results{{padding:16px;max-width:600px;margin:0 auto}}
  .state-msg{{text-align:center;color:rgba(255,255,255,.7);margin-top:60px;font-size:1rem}}
  .state-msg .icon{{font-size:3rem;display:block;margin-bottom:12px}}
  .result-card{{background:white;border-radius:18px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.18);margin-bottom:20px;animation:fadeUp .25s ease}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
  .card-header{{background:linear-gradient(135deg,#1a7a5e,#0d4f3c);padding:18px 18px 14px;color:white}}
  .pilgrim-name{{font-size:1.2rem;font-weight:700;line-height:1.4;color:#f5d06e;margin-bottom:4px}}
  .pilgrim-label{{font-size:.75rem;color:rgba(255,255,255,.6);letter-spacing:1px}}
  .card-body{{padding:16px 18px;display:flex;gap:12px}}
  .info-box{{flex:1;background:#f8fffe;border-radius:12px;padding:12px 14px;text-align:center;border:1.5px solid #e0f5ef}}
  .info-box .label{{font-size:.7rem;color:#888;display:block;margin-bottom:4px;font-weight:600;letter-spacing:.5px}}
  .info-box .value{{font-size:1.35rem;font-weight:800;color:#0d4f3c;direction:ltr;display:block}}
  .info-box.bus .value{{font-size:2rem;color:#e07b00}}
  .info-box.bus{{border-color:#fde8c0;background:#fffbf3}}
  .info-box.mina .value{{font-size:1.05rem;color:#1a4a7a;direction:ltr}}
  .info-box.mina{{border-color:#c0d8fd;background:#f3f8ff}}
  .qr-btn{{background:rgba(255,255,255,.18);border:1.5px solid rgba(255,255,255,.35);border-radius:10px;padding:7px 10px;color:white;font-size:1.15rem;cursor:pointer;flex-shrink:0;margin-top:2px;line-height:1}}
  .qr-modal{{display:none;position:fixed;inset:0;z-index:9990;background:rgba(0,0,0,.88);align-items:center;justify-content:center;padding:24px}}
  .qr-box{{background:white;border-radius:24px;padding:28px 24px 22px;text-align:center;max-width:320px;width:100%}}
  .qr-pname{{font-size:1rem;font-weight:700;color:#0d4f3c;margin-bottom:16px;line-height:1.5}}
  .qr-img{{width:220px;height:220px;border-radius:12px;display:block;margin:0 auto 10px}}
  .qr-hint{{font-size:.75rem;color:#888;margin-bottom:16px}}
  .qr-close{{background:#0d4f3c;color:white;border:none;border-radius:12px;padding:10px 32px;font-size:.9rem;font-weight:700;cursor:pointer;font-family:inherit}}
  .scan-modal{{display:none;position:fixed;inset:0;z-index:9991;background:rgba(0,0,0,.92);flex-direction:column;align-items:center;justify-content:flex-start;padding:20px 16px}}
  .scan-modal.open{{display:flex;animation:fadeUp .2s ease}}
  .scan-hdr{{width:100%;max-width:480px;display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
  .scan-title{{color:#f5d06e;font-size:1.05rem;font-weight:700}}
  .scan-close{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:white;border-radius:10px;padding:8px 14px;font-size:.85rem;font-weight:700;cursor:pointer;font-family:inherit}}
  #scanReader{{border-radius:18px;overflow:hidden;border:3px solid rgba(245,208,110,.55);background:#111;width:100%;max-width:480px}}
  #scanHint{{color:rgba(255,255,255,.8);font-size:.9rem;margin-top:12px;text-align:center;max-width:360px;line-height:1.6}}
  .group-banner{{background:linear-gradient(90deg,#e07b00,#f5a623);color:white;text-align:center;padding:8px 16px;font-size:.82rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:6px}}
  .group-list{{padding:10px 14px 14px}}
  .group-member{{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;border-bottom:1px solid #f0f0f0}}
  .group-member:last-child{{border-bottom:none}}
  .group-member.is-self{{background:#edfaf5}}
  .member-num{{width:26px;height:26px;border-radius:50%;background:#1a7a5e;color:white;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .member-num.self{{background:#f5d06e;color:#0d4f3c}}
  .member-name{{font-size:.92rem;color:#1a1a1a;font-weight:500;flex:1}}
  .you-badge{{font-size:.65rem;background:#1a7a5e;color:white;padding:2px 7px;border-radius:20px;font-weight:700}}
  .member-mina{{font-size:.72rem;color:#1a4a7a;font-weight:700;background:#eef4ff;border-radius:6px;padding:2px 7px;direction:ltr;white-space:nowrap;margin-right:auto}}
  .wa-ic{{display:inline-flex;align-items:center;justify-content:center;background:#25D366;border-radius:10px;text-decoration:none;flex-shrink:0;box-shadow:0 1px 3px rgba(0,0,0,.2)}}
  .wa-ic svg{{fill:#fff}}
  .wa-card{{padding:0 16px;align-self:stretch}}
  .wa-card svg{{width:26px;height:26px}}
  .wa-mini{{width:30px;height:30px}}
  .wa-mini svg{{width:18px;height:18px}}
  {RPT_CSS}
  .no-result{{text-align:center;margin-top:60px;color:rgba(255,255,255,.8);animation:fadeUp .25s ease}}
  .no-result .icon{{font-size:3rem;display:block;margin-bottom:12px}}
  .count-badge{{display:inline-block;background:rgba(255,255,255,.15);border-radius:20px;padding:3px 10px;font-size:.78rem;color:rgba(255,255,255,.9);margin-bottom:8px}}
  {LOCK_CSS}
</style>
</head>
<body>
{LOCK_HTML}
<header>
  {SWITCHER}
  <div class="hdr-row">
    <h1>🕋 {H1} <span style="font-size:.55em;opacity:.6;font-weight:400">v1.2</span></h1>
    <div style="display:flex;gap:5px;flex-shrink:0">{'<a href="'+DASH_LINK+'" class="nav-link">📊 لوحة</a>' if DASH_LINK else ''}<a href="{REPORTS_LINK}" class="nav-link">🚩 بلاغات</a><a href="{NAV}" class="nav-link">📋 بيانات</a></div>
  </div>
  <div class="search-wrap">
    <input type="search" id="searchInput" placeholder="ابحث بالاسم أو الهوية أو الجوال..." autocomplete="off" autocorrect="off" spellcheck="false" inputmode="search">
    <span class="search-icon">🔍</span>
    <button class="clear-btn" id="clearBtn" onclick="clearSearch()">✕</button>
  </div>
  <div class="search-actions">
    <button class="btn-scan" onclick="openScan()">📷 مسح باركود الهوية</button>
    <button class="btn-adv" id="advToggle" onclick="toggleAdv()">⚙️ بحث متقدم <span id="advBadge" style="display:none" class="adv-badge">0</span></button>
  </div>
  <div class="adv-panel" id="advPanel">
    <div class="adv-row">
      <div class="adv-field">
        <span class="adv-label">🚌 رقم الباص</span>
        <input class="adv-input" id="fBus" type="number" min="1" placeholder="مثال: 8" oninput="doSearch()">
      </div>
      <div class="adv-field">
        <span class="adv-label">🏙️ المكتب</span>
        <select class="adv-select" id="fOffice" onchange="doSearch()">
          <option value="">الكل</option>
        </select>
      </div>
    </div>
    <div class="adv-row">
      <div class="adv-field">
        <span class="adv-label">👤 الجنس</span>
        <div class="gender-grp">
          <button class="gender-btn active" id="gAll" onclick="setGender('')">الكل</button>
          <button class="gender-btn" id="gM" onclick="setGender('ذكر')">رجال</button>
          <button class="gender-btn" id="gF" onclick="setGender('أنثى')">نساء</button>
        </div>
      </div>
      <button class="adv-clear" onclick="clearAdv()">✕ مسح الفلاتر</button>
    </div>
  </div>
</header>
<div id="results">
  <div class="state-msg"><span class="icon">🔍</span><p>ابحث عن الحاج للعثور على معلومات الحجز والباص</p></div>
</div>
<div id="qrModal" class="qr-modal" onclick="closeQR()">
  <div class="qr-box" onclick="event.stopPropagation()">
    <div id="qrModalName" class="qr-pname"></div>
    <img id="qrImg" src="" alt="QR" class="qr-img">
    <p class="qr-hint">📷 امسح بكاميرا الجوال لعرض البطاقة</p>
    <button class="qr-close" onclick="closeQR()">إغلاق</button>
  </div>
</div>
<div id="scanModal" class="scan-modal">
  <div class="scan-hdr">
    <span class="scan-title">📷 مسح باركود الهوية</span>
    <button class="scan-close" onclick="closeScan()">إغلاق ✕</button>
  </div>
  <div id="scanReader"></div>
  <div id="scanHint">وجّه الكاميرا على باركود الهوية الوطنية أو الإقامة</div>
</div>
<script src="html5-qrcode.min.js"></script>
<script>
{DECRYPT_JS}
let DATA=[],searchResults=[];const byId={{}},byPhone={{}},byResv={{}};
let _fGender='';
{WA_JS}
{CLOUD_JS}
{REPORTS_JS}
function makeCardUrl(p){{const grp=byResv[p.resv]||[p];const main={{name:p.name,mina:p.mina||'',main:true}};const rest=grp.filter(m=>m.name!==p.name).map(m=>({{name:m.name,mina:m.mina||''}}));const group=[main,...rest];let bin='';new TextEncoder().encode(JSON.stringify(group)).forEach(b=>bin+=String.fromCharCode(b));const g=btoa(bin);return 'https://abuesim.github.io/hajj-search/{CARDFILE}?b='+encodeURIComponent(p.bus||'')+'&g='+encodeURIComponent(g);}}
function showQRModal(i){{const p=searchResults[i];if(!p)return;const u=makeCardUrl(p);document.getElementById('qrModalName').textContent=p.name;document.getElementById('qrImg').src='https://api.qrserver.com/v1/create-qr-code/?size=220x220&color={QR}&bgcolor=ffffff&qzone=2&data='+encodeURIComponent(u);document.getElementById('qrModal').style.display='flex';}}
function closeQR(){{document.getElementById('qrModal').style.display='none';}}
function onDataReady(d){{
  DATA=d;
  DATA.forEach(p=>{{
    if(p.id)(byId[p.id]=byId[p.id]||[]).push(p);
    if(p.phone)(byPhone[p.phone]=byPhone[p.phone]||[]).push(p);
    if(p.resv)(byResv[p.resv]=byResv[p.resv]||[]).push(p);
  }});
  const offices=[...new Set(d.map(p=>p.office||'').filter(Boolean))].sort();
  const sel=document.getElementById('fOffice');
  offices.forEach(o=>{{const op=document.createElement('option');op.value=o;op.textContent=o;sel.appendChild(op);}});
}}
const input=document.getElementById('searchInput');
const clearBtn=document.getElementById('clearBtn');
const resultsDiv=document.getElementById('results');
let deb;
input.addEventListener('input',()=>{{clearTimeout(deb);deb=setTimeout(doSearch,200);clearBtn.classList.toggle('visible',input.value.length>0)}});
function clearSearch(){{input.value='';clearBtn.classList.remove('visible');doSearch();input.focus()}}
function norm(s){{return(s||'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').toLowerCase().trim()}}
function getFilters(){{return{{bus:(document.getElementById('fBus').value||'').trim(),office:(document.getElementById('fOffice').value||''),gender:_fGender}};}}
function hasFilters(){{const f=getFilters();return!!(f.bus||f.office||f.gender);}}
function applyFilters(arr){{
  const f=getFilters();
  return arr.filter(p=>{{
    if(f.bus&&p.bus!==f.bus)return false;
    if(f.office&&(p.office||'')!==f.office)return false;
    if(f.gender&&(p.gender||'')!==f.gender)return false;
    return true;
  }});
}}
function updateAdvBadge(){{
  const f=getFilters();const n=[f.bus,f.office,f.gender].filter(Boolean).length;
  const b=document.getElementById('advBadge');b.style.display=n?'inline-block':'none';b.textContent=n;
  document.getElementById('advToggle').classList.toggle('active',n>0);
}}
function setGender(v){{
  _fGender=v;
  ['gAll','gM','gF'].forEach(id=>document.getElementById(id).classList.remove('active'));
  document.getElementById(v===''?'gAll':v==='ذكر'?'gM':'gF').classList.add('active');
  updateAdvBadge();doSearch();
}}
function toggleAdv(){{const p=document.getElementById('advPanel');p.classList.toggle('open');}}
function clearAdv(){{document.getElementById('fBus').value='';document.getElementById('fOffice').value='';setGender('');updateAdvBadge();doSearch();}}
function doSearch(){{
  updateAdvBadge();
  const q=input.value.trim();
  const filters=hasFilters();
  if(!q&&!filters){{showEmpty();return}}
  if(q.length===1&&!filters){{resultsDiv.innerHTML='<div class="state-msg"><span class="icon">✍️</span><p>اكتب أكثر...</p></div>';return}}
  let m=[];
  if(q){{
    if(byId[q])m=[...byId[q]];
    if(!m.length&&byPhone[q])m=[...byPhone[q]];
    if(!m.length){{const alt=q.startsWith('0')?q.slice(1):'0'+q;if(byPhone[alt])m=[...byPhone[alt]]}}
    if(!m.length){{const nq=norm(q);m=DATA.filter(p=>norm(p.name).includes(nq))}}
    if(!m.length&&/^\\d+$/.test(q))m=DATA.filter(p=>p.id.includes(q));
  }}else{{m=[...DATA];}}
  if(filters)m=applyFilters(m);
  const seen=new Set();m=m.filter(p=>{{const k=p.name+p.resv;if(seen.has(k))return false;seen.add(k);return true}});
  if(!m.length){{resultsDiv.innerHTML=`<div class="no-result"><span class="icon">😔</span><p>${{q?'لا نتائج لـ "<strong>'+q+'</strong>"':'لا نتائج للفلاتر المحددة'}}</p><small>تأكد من البيانات المدخلة</small></div>`;return}}
  let html='';
  if(m.length>1)html+=`<div style="text-align:center;margin-bottom:12px"><span class="count-badge">تم العثور على <strong>${{m.length}}</strong> نتيجة</span></div>`;
  searchResults=m.slice(0,30);
  searchResults.forEach((p,i)=>{{
    const grp=byResv[p.resv]||[];
    const minaBox=p.mina?`<div class="info-box mina"><span class="label">سكن منى</span><span class="value" style="font-size:1.05rem">${{p.mina}}</span></div>`:'';
    const waBtn=p.phone?`<a class="wa-ic wa-card" href="${{waLink(p.phone)}}" target="_blank" rel="noopener" title="مراسلة واتساب">${{WA_SVG}}</a>`:'';
    html+=`<div class="result-card"><div class="card-header" style="display:flex;align-items:flex-start;justify-content:space-between"><div><div class="pilgrim-label">الحاج / الحاجة</div><div class="pilgrim-name">${{p.name}}</div></div><div style="display:flex;gap:6px"><button class="rpt-btn-ic" onclick="report(searchResults[${{i}}])" title="بلاغ">${{RPT_SVG}}</button><button class="qr-btn" onclick="showQRModal(${{i}})">📱</button></div></div><div class="card-body"><div class="info-box"><span class="label">رقم الحجز</span><span class="value" style="font-size:1.15rem">${{p.resv||'—'}}</span></div><div class="info-box bus"><span class="label">الباص</span><span class="value">${{p.bus||'—'}}</span></div>${{minaBox}}${{waBtn}}</div>`;
    if(grp.length>1){{
      html+=`<div class="group-banner"><span>👥</span> رفقاء الحجز · ${{grp.length}} أشخاص</div><div class="group-list">`;
      grp.forEach((mem,i)=>{{const s=mem.name===p.name;const md=JSON.stringify(mem).replace(/'/g,'&#39;');html+=`<div class="group-member${{s?' is-self':''}}"><div class="member-num${{s?' self':''}}">${{i+1}}</div><div class="member-name">${{mem.name}}</div>${{mem.mina?`<span class="member-mina">${{mem.mina}}</span>`:''}}${{mem.phone?`<a class="wa-ic wa-mini" href="${{waLink(mem.phone)}}" target="_blank" rel="noopener" title="مراسلة واتساب">${{WA_SVG}}</a>`:''}}<button class="rpt-mini" onclick='report(${{md}})' title="بلاغ">${{RPT_SVG}}</button>${{s?'<span class="you-badge">أنت</span>':''}}</div>`}});
      html+='</div>';
    }}
    html+='</div>';
  }});
  if(m.length>30)html+=`<p style="text-align:center;color:rgba(255,255,255,.6);font-size:.85rem">يُعرض أول 30 نتيجة من ${{m.length}}</p>`;
  resultsDiv.innerHTML=html;
}}
function showEmpty(){{resultsDiv.innerHTML='<div class="state-msg"><span class="icon">🔍</span><p>ابحث عن الحاج للعثور على معلومات الحجز والباص</p></div>'}}
// ── Inline barcode scan ──
let _h5=null,_scanning=false;
function openScan(){{
  document.getElementById('scanModal').classList.add('open');
  if(typeof Html5Qrcode==='undefined'){{document.getElementById('scanHint').innerHTML='⚠️ تعذّر تحميل أداة المسح';return;}}
  if(!_h5)_h5=new Html5Qrcode('scanReader');
  if(_scanning)return;
  _h5.start({{facingMode:'environment'}},{{fps:10,qrbox:{{width:240,height:180}}}},_onScan,()=>{{}})
    .then(()=>{{_scanning=true;}})
    .catch(e=>{{document.getElementById('scanHint').innerHTML='⚠️ يحتاج إذن الكاميرا. تأكد من السماح وأن الرابط https<br><small>'+e+'</small>';}});
}}
function closeScan(){{
  document.getElementById('scanModal').classList.remove('open');
  if(_h5&&_scanning){{_h5.stop().catch(()=>{{}});_scanning=false;}}
}}
function _findId(t){{
  if(byId[t])return t;
  const d=(t||'').replace(/\\D/g,'');
  if(byId[d])return d;
  const m=(t||'').match(/\\d{{10}}/);
  if(m&&byId[m[0]])return m[0];
  return d;
}}
function _onScan(t){{
  const id=_findId(t);
  const hits=byId[id];
  if(!hits||!hits.length){{document.getElementById('scanHint').innerHTML='❌ غير مسجّل: '+id+'<br><small>حاول مرة أخرى</small>';return;}}
  if(navigator.vibrate)navigator.vibrate(90);
  closeScan();
  input.value=id;
  clearBtn.classList.add('visible');
  doSearch();
}}
initAuth();
</script>
</body>
</html>"""

# ════════════════════════════════
# manifest.html — inject encrypted payload + lock screen into gen_manifest template
# ════════════════════════════════
def build_manifest(plain, DECRYPT_JS_MANIFEST, LOCK_HTML, SWITCHER_HTML):
    manifest = re.sub(
        r'const DATA=\[.*?\];function onDataReady\(\)\{\}function initAuth\(\)\{onDataReady\(DATA\)\}',
        lambda m: CLOUD_JS + '\n' + DECRYPT_JS_MANIFEST.strip(),
        plain, flags=re.DOTALL)
    manifest = manifest.replace('</style>', LOCK_CSS + '\n' + SWITCH_CSS + '\n</style>', 1)
    manifest = manifest.replace('<div id="app">',
        LOCK_HTML + '\n<div id="app">\n<div style="padding:10px 14px 0">' + SWITCHER_HTML + '</div>', 1)
    return manifest

# ════════════════════════════════
# card.html  — public, no auth, reads URL params
# ════════════════════════════════
CARD = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>بطاقة ركاب</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c,#1a7a5e);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{background:white;border-radius:24px;overflow:hidden;max-width:380px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.35)}
  .card-top{background:linear-gradient(135deg,#1a7a5e,#0d4f3c);padding:20px 24px;text-align:center}
  .co{color:rgba(255,255,255,.65);font-size:.72rem;letter-spacing:1px;margin-bottom:8px}
  .bus-lbl{color:rgba(255,255,255,.6);font-size:.68rem;margin-bottom:2px}
  .bus-num{color:#f5d06e;font-size:2.8rem;font-weight:800;line-height:1.1}
  .main-sec{padding:16px 20px 14px;background:#f5fdf8;border-bottom:2px solid #d4eee4}
  .main-lbl{font-size:.64rem;color:#888;font-weight:600;letter-spacing:.5px;margin-bottom:4px}
  .main-name{font-size:1.2rem;font-weight:700;color:#0d4f3c;line-height:1.4;margin-bottom:8px}
  .main-mina{display:inline-flex;align-items:center;gap:6px;background:#e8f4ff;border-radius:8px;padding:5px 12px}
  .mina-lbl{font-size:.65rem;color:#666;font-weight:600}
  .mina-val{font-size:.95rem;font-weight:800;color:#1a4a7a;direction:ltr}
  .comp-sec{padding:10px 18px 14px}
  .sec-title{font-size:.66rem;color:#aaa;font-weight:600;letter-spacing:.5px;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #f0f0f0}
  .mrow{display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px solid #f5f5f5}
  .mrow:last-child{border-bottom:none}
  .mnum{width:22px;height:22px;border-radius:50%;background:#1a7a5e;color:white;font-size:.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .mname{font-size:.88rem;color:#333;font-weight:500;flex:1;line-height:1.3}
  .mmina{font-size:.74rem;color:#1a4a7a;font-weight:700;background:#eef4ff;border-radius:5px;padding:2px 7px;direction:ltr;flex-shrink:0;white-space:nowrap}
  .foot{background:#f7f7f7;padding:9px 20px;text-align:center;border-top:1px solid #eee;font-size:.62rem;color:#bbb}
</style>
</head>
<body>
<div class="card">
  <div class="card-top">
    <div class="co">🕋 __CO__</div>
    <div class="bus-lbl">الباص</div>
    <div class="bus-num" id="cbus">—</div>
  </div>
  <div class="main-sec">
    <div class="main-lbl">الحاج / الحاجة</div>
    <div class="main-name" id="mainName">—</div>
    <div class="main-mina" id="mainMinaBox">
      <span class="mina-lbl">سكن منى</span>
      <span class="mina-val" id="mainMina">—</span>
    </div>
  </div>
  <div class="comp-sec" id="compSec">
    <div class="sec-title">المرافقون · سكن منى</div>
    <div id="compList"></div>
  </div>
  <div class="foot">__FOOTER__</div>
</div>
<script>
  const p=new URLSearchParams(location.search);
  document.getElementById('cbus').textContent=p.get('b')||'—';
  const gRaw=p.get('g');
  if(gRaw){
    try{
      const bytes=Uint8Array.from(atob(gRaw),c=>c.charCodeAt(0));
      const group=JSON.parse(new TextDecoder().decode(bytes));
      const main=group[0];
      document.getElementById('mainName').textContent=main.name||'—';
      if(main.mina){document.getElementById('mainMina').textContent=main.mina;}
      else{document.getElementById('mainMinaBox').style.display='none';}
      const companions=group.slice(1);
      if(companions.length>0){
        const list=document.getElementById('compList');
        companions.forEach((m,i)=>{
          const row=document.createElement('div');
          row.className='mrow';
          row.innerHTML='<span class="mnum">'+(i+1)+'</span><span class="mname">'+m.name+'</span>'+(m.mina?'<span class="mmina">'+m.mina+'</span>':'');
          list.appendChild(row);
        });
      } else {
        document.getElementById('compSec').style.display='none';
      }
    }catch(e){document.getElementById('mainName').textContent='خطأ في تحميل البيانات';}
  }
</script>
</body>
</html>"""

# ════════════════════════════════
# Quick Search — camera barcode/QR scan → instant pilgrim card
# ════════════════════════════════
def make_scan(DECRYPT_JS, LOCK_HTML, SWITCHER, SEARCH_LINK):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>البحث السريع</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c 0%,#1a7a5e 50%,#0d4f3c 100%);min-height:100vh;padding:0 0 40px}}
  header{{background:rgba(0,0,0,.25);padding:14px 16px;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.1)}}
  {SWITCH_CSS}
  .hdr-row{{display:flex;align-items:center;justify-content:space-between;margin-top:4px}}
  header h1{{color:#f5d06e;font-size:1.1rem;font-weight:700}}
  .nav-link{{background:rgba(255,255,255,.15);color:#f5d06e;border-radius:10px;padding:6px 11px;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid rgba(245,208,110,.3)}}
  #scanWrap{{max-width:480px;margin:16px auto 0;padding:0 16px}}
  #reader{{border-radius:18px;overflow:hidden;border:3px solid rgba(245,208,110,.55);background:#000;min-height:140px}}
  #scanHint{{text-align:center;color:rgba(255,255,255,.9);font-size:.95rem;margin-top:14px;background:rgba(0,0,0,.22);padding:12px;border-radius:12px;line-height:1.6}}
  #result{{max-width:480px;margin:0 auto;padding:0 16px}}
  .result-card{{background:white;border-radius:18px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.22);animation:fadeUp .25s ease;margin-top:16px}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
  .card-header{{background:linear-gradient(135deg,#1a7a5e,#0d4f3c);padding:18px;color:white}}
  .pilgrim-name{{font-size:1.35rem;font-weight:700;color:#f5d06e}}
  .pilgrim-label{{font-size:.75rem;color:rgba(255,255,255,.6)}}
  .card-body{{padding:16px 18px;display:flex;gap:12px;flex-wrap:wrap}}
  .info-box{{flex:1;min-width:88px;background:#f8fffe;border-radius:12px;padding:12px;text-align:center;border:1.5px solid #e0f5ef}}
  .info-box .label{{font-size:.7rem;color:#888;display:block;margin-bottom:4px;font-weight:600}}
  .info-box .value{{font-size:1.3rem;font-weight:800;color:#0d4f3c;direction:ltr;display:block}}
  .info-box.bus .value{{color:#e07b00;font-size:2rem}}
  .info-box.mina .value{{font-size:1.15rem;color:#1a4a7a}}
  .group-banner{{background:linear-gradient(90deg,#e07b00,#f5a623);color:white;text-align:center;padding:8px;font-size:.82rem;font-weight:700}}
  .group-list{{padding:10px 14px}}
  .group-member{{display:flex;align-items:center;gap:10px;padding:9px 6px;border-bottom:1px solid #f0f0f0}}
  .group-member:last-child{{border-bottom:none}}
  .member-num{{width:26px;height:26px;border-radius:50%;background:#1a7a5e;color:white;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .member-name{{font-size:.92rem;color:#1a1a1a;font-weight:500;flex:1}}
  .member-mina{{font-size:.72rem;color:#1a4a7a;font-weight:700;background:#eef4ff;border-radius:6px;padding:2px 7px;direction:ltr;white-space:nowrap}}
  .wa-ic{{display:inline-flex;width:30px;height:30px;background:#25D366;border-radius:8px;align-items:center;justify-content:center;flex-shrink:0}}
  .wa-ic svg{{width:18px;height:18px;fill:#fff}}
  .rescan-btn{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:16px;background:#f5d06e;color:#0d4f3c;border:none;border-radius:14px;padding:17px;font-size:1.1rem;font-weight:800;cursor:pointer;font-family:inherit}}
  .rescan-btn:active{{transform:scale(.97)}}
  {LOCK_CSS}
</style>
</head>
<body>
{LOCK_HTML}
<header>
  {SWITCHER}
  <div class="hdr-row"><h1>📷 البحث السريع</h1><a href="{SEARCH_LINK}" class="nav-link">🔍 بحث عادي</a></div>
</header>
<div id="scanWrap"><div id="reader"></div><div id="scanHint">📷 وجّه الكاميرا على باركود الهوية</div></div>
<div id="result"></div>
<script src="html5-qrcode.min.js"></script>
<script>
{DECRYPT_JS}
{WA_JS}
let DATA=[];const byId={{}},byResv={{}};
let h5=null,scanning=false;
function setHint(t){{const e=document.getElementById('scanHint');if(e)e.innerHTML=t;}}
function startScan(){{
  document.getElementById('result').innerHTML='';
  document.getElementById('scanWrap').style.display='block';
  setHint('📷 وجّه الكاميرا على باركود الهوية');
  if(typeof Html5Qrcode==='undefined'){{setHint('⚠️ تعذّر تحميل أداة المسح');return;}}
  if(!h5)h5=new Html5Qrcode("reader");
  if(scanning)return;
  h5.start({{facingMode:"environment"}},{{fps:10,qrbox:{{width:240,height:240}}}},onScan,()=>{{}})
    .then(()=>{{scanning=true;}})
    .catch(e=>{{setHint('⚠️ تعذّر تشغيل الكاميرا.<br>تأكد من السماح بالوصول للكاميرا، وأن الموقع يفتح عبر https.<br><small>'+e+'</small>');}});
}}
async function stopScan(){{if(h5&&scanning){{try{{await h5.stop();}}catch(e){{}}scanning=false;}}}}
function findId(t){{if(byId[t])return t;const d=(t||'').replace(/\\D/g,'');if(byId[d])return d;const m=(t||'').match(/\\d{{10}}/);if(m&&byId[m[0]])return m[0];return d;}}
function onScan(t){{
  const id=findId(t);const m=byId[id];
  if(!m||!m.length){{setHint('❌ غير مسجّل: '+id+'<br>حاول مرة أخرى');return;}}
  if(navigator.vibrate)navigator.vibrate(90);
  stopScan();document.getElementById('scanWrap').style.display='none';showResult(m[0]);
}}
function showResult(p){{
  const grp=byResv[p.resv]||[p];
  const mina=p.mina?`<div class="info-box mina"><span class="label">سكن منى</span><span class="value">${{p.mina}}</span></div>`:'';
  let h=`<div class="result-card"><div class="card-header"><div class="pilgrim-label">الحاج / الحاجة</div><div class="pilgrim-name">${{p.name}}</div></div><div class="card-body"><div class="info-box"><span class="label">رقم الحجز</span><span class="value" style="font-size:1.1rem">${{p.resv||'—'}}</span></div><div class="info-box bus"><span class="label">الباص</span><span class="value">${{p.bus||'—'}}</span></div>${{mina}}</div>`;
  if(grp.length>1){{
    h+=`<div class="group-banner">👥 رفقاء الحجز · ${{grp.length}} أشخاص</div><div class="group-list">`;
    grp.forEach((mem,i)=>{{const s=mem.name===p.name;h+=`<div class="group-member" style="${{s?'background:#edfaf5':''}}"><div class="member-num">${{i+1}}</div><div class="member-name">${{mem.name}}${{s?' <b style="color:#1a7a5e">(أنت)</b>':''}}</div>${{mem.mina?`<span class="member-mina">${{mem.mina}}</span>`:''}}${{mem.phone?`<a class="wa-ic" href="${{waLink(mem.phone)}}" target="_blank" rel="noopener">${{WA_SVG}}</a>`:''}}</div>`;}});
    h+='</div>';
  }}
  h+='</div><button class="rescan-btn" onclick="startScan()">📷 مسح باركود جديد</button>';
  document.getElementById('result').innerHTML=h;
}}
function onDataReady(d){{DATA=d;d.forEach(p=>{{if(p.id)(byId[p.id]=byId[p.id]||[]).push(p);if(p.resv)(byResv[p.resv]=byResv[p.resv]||[]).push(p);}});startScan();}}
initAuth();
</script>
</body>
</html>"""

# ════════════════════════════════
# Dashboard — stats + bus/office drill-down
# ════════════════════════════════
def make_dashboard(DECRYPT_JS, LOCK_HTML, H1, SEARCH_LINK, REPORTS_LINK, MANIFEST_LINK, SWITCHER):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>لوحة التحكم</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c 0%,#1a7a5e 50%,#0d4f3c 100%);min-height:100vh;padding:0 0 50px}}
  header{{background:rgba(0,0,0,.25);padding:14px 16px;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.1)}}
  {SWITCH_CSS}
  .hdr-row{{display:flex;align-items:center;justify-content:space-between;margin-top:6px}}
  header h1{{color:#f5d06e;font-size:1.1rem;font-weight:700}}
  .nav-link{{background:rgba(255,255,255,.15);color:#f5d06e;border-radius:9px;padding:6px 10px;font-size:.76rem;font-weight:700;text-decoration:none;border:1px solid rgba(245,208,110,.3)}}
  .content{{max-width:600px;margin:0 auto;padding:14px 14px 0}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
  .stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}}
  .stat-card{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.15);border-radius:14px;padding:12px 8px;text-align:center}}
  .stat-num{{font-size:1.7rem;font-weight:800;color:#f5d06e;line-height:1.1}}
  .stat-lbl{{font-size:.65rem;color:rgba(255,255,255,.65);margin-top:3px;font-weight:600}}
  .section-hdr{{color:rgba(255,255,255,.9);font-size:.82rem;font-weight:700;margin:16px 0 8px;display:flex;align-items:center;gap:6px}}
  .office-chips{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px}}
  .office-chip{{padding:7px 14px;border-radius:20px;border:1.5px solid rgba(255,255,255,.25);background:rgba(255,255,255,.1);color:rgba(255,255,255,.85);font-size:.82rem;font-weight:700;cursor:pointer;transition:.15s}}
  .office-chip.active{{background:#f5d06e;color:#0d4f3c;border-color:#f5d06e}}
  .buses-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
  .bus-card{{background:white;border-radius:14px;padding:13px 10px;text-align:center;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.15);transition:.15s;border-bottom:4px solid #e07b00;animation:fadeUp .2s ease}}
  .bus-card:active{{transform:scale(.96)}}
  .bus-card.expanded{{border-bottom-color:#0d4f3c;border-radius:14px 14px 0 0}}
  .bus-num{{font-size:2rem;font-weight:800;color:#e07b00;line-height:1}}
  .bus-cnt{{font-size:.72rem;color:#666;margin-top:3px;font-weight:600}}
  .bus-expand{{display:none;background:white;border-radius:0 0 14px 14px;margin-top:-2px;box-shadow:0 6px 14px rgba(0,0,0,.15);grid-column:1/-1;overflow:hidden}}
  .bus-expand.open{{display:block;animation:fadeUp .18s ease}}
  .bx-hdr{{background:linear-gradient(90deg,#0d4f3c,#1a7a5e);padding:10px 14px;display:flex;align-items:center;justify-content:space-between}}
  .bx-title{{color:#f5d06e;font-weight:700;font-size:.9rem}}
  .bx-close{{background:rgba(255,255,255,.2);border:none;color:white;border-radius:8px;padding:5px 10px;font-size:.78rem;cursor:pointer;font-family:inherit}}
  .pax-list{{max-height:320px;overflow-y:auto}}
  .pax-row{{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid #f0f0f0}}
  .pax-row:last-child{{border-bottom:none}}
  .pax-num{{width:24px;height:24px;border-radius:50%;background:#e0f0e8;color:#0d4f3c;font-size:.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .pax-name{{flex:1;font-size:.9rem;color:#1a1a1a;font-weight:500}}
  .pax-mina{{font-size:.7rem;color:#1a4a7a;font-weight:700;background:#eef4ff;border-radius:5px;padding:2px 7px;direction:ltr;white-space:nowrap}}
  .pax-wa{{display:inline-flex;width:28px;height:28px;background:#25D366;border-radius:8px;align-items:center;justify-content:center;text-decoration:none;flex-shrink:0}}
  .pax-wa svg{{width:16px;height:16px;fill:#fff}}
  .no-bus{{text-align:center;color:rgba(255,255,255,.6);font-size:.9rem;margin-top:40px}}
  {LOCK_CSS}
</style>
</head>
<body>
{LOCK_HTML}
<header>
  {SWITCHER}
  <div class="hdr-row">
    <h1>📊 {H1}</h1>
    <div style="display:flex;gap:5px;flex-shrink:0">
      <a href="{SEARCH_LINK}" class="nav-link">🔍 بحث</a>
      <a href="{REPORTS_LINK}" class="nav-link">🚩 بلاغات</a>
      <a href="{MANIFEST_LINK}" class="nav-link">📋 بيانات</a>
    </div>
  </div>
</header>
<div class="content">
  <div class="stats-row" id="statsRow">
    <div class="stat-card"><div class="stat-num" id="sTotal">—</div><div class="stat-lbl">إجمالي الحجاج</div></div>
    <div class="stat-card"><div class="stat-num" id="sMale">—</div><div class="stat-lbl">رجال</div></div>
    <div class="stat-card"><div class="stat-num" id="sFemale">—</div><div class="stat-lbl">نساء</div></div>
    <div class="stat-card"><div class="stat-num" id="sBuses">—</div><div class="stat-lbl">باصات</div></div>
  </div>
  <div class="section-hdr">🏙️ تصفية حسب المكتب</div>
  <div class="office-chips" id="officeChips"></div>
  <div class="section-hdr">🚌 الباصات</div>
  <div class="buses-grid" id="busesGrid"></div>
</div>
<script>
{DECRYPT_JS}
{WA_JS}
let DATA=[];let _office='';let _openBus=null;
function onDataReady(d){{
  DATA=d;
  buildOffices();
  render();
}}
function buildOffices(){{
  const offices=[...new Set(DATA.map(p=>p.office||'').filter(Boolean))].sort();
  const chips=document.getElementById('officeChips');
  [['','الكل'],...offices.map(o=>[o,o])].forEach(([v,lbl])=>{{
    const b=document.createElement('button');
    b.className='office-chip'+(v===''?' active':'');
    b.textContent=lbl;b.onclick=()=>setOffice(v);
    chips.appendChild(b);
  }});
}}
function setOffice(v){{
  _office=v;_openBus=null;
  document.querySelectorAll('.office-chip').forEach(c=>c.classList.toggle('active',c.textContent===(v||'الكل')));
  render();
}}
function render(){{
  const src=_office?DATA.filter(p=>(p.office||'')===_office):DATA;
  const unique=dedup(src);
  document.getElementById('sTotal').textContent=unique.length;
  document.getElementById('sMale').textContent=unique.filter(p=>p.gender==='ذكر').length;
  document.getElementById('sFemale').textContent=unique.filter(p=>p.gender==='أنثى').length;
  const buses=[...new Set(unique.map(p=>p.bus||'').filter(Boolean))];
  document.getElementById('sBuses').textContent=buses.length;
  renderBuses(unique,buses);
}}
function dedup(arr){{
  const seen=new Set();return arr.filter(p=>{{const k=p.name+p.resv;if(seen.has(k))return false;seen.add(k);return true}});
}}
function renderBuses(src,buses){{
  const grid=document.getElementById('busesGrid');
  if(!buses.length){{grid.innerHTML='<div class="no-bus" style="grid-column:1/-1">لا توجد باصات</div>';return}}
  // sort numerically
  buses.sort((a,b)=>+a-+b||(a>b?1:-1));
  let html='';
  buses.forEach(bus=>{{
    const pax=dedup(src.filter(p=>p.bus===bus));
    const isOpen=_openBus===bus;
    html+=`<div class="bus-card${{isOpen?' expanded':''}}" id="bc_${{bus}}" onclick="toggleBus('${{bus}}')" style="grid-column:auto">
      <div class="bus-num">${{bus}}</div>
      <div class="bus-cnt">${{pax.length}} حاج</div>
    </div>`;
    if(isOpen){{
      html+=`<div class="bus-expand open" id="bx_${{bus}}">
        <div class="bx-hdr">
          <span class="bx-title">🚌 باص ${{bus}} · ${{pax.length}} حاج</span>
          <button class="bx-close" onclick="event.stopPropagation();toggleBus('${{bus}}')">✕</button>
        </div>
        <div class="pax-list">`;
      pax.forEach((p,i)=>{{
        html+=`<div class="pax-row">
          <div class="pax-num">${{i+1}}</div>
          <div class="pax-name">${{p.name}}</div>
          ${{p.mina?`<span class="pax-mina">${{p.mina}}</span>`:''}}
          ${{p.phone?`<a class="pax-wa" href="${{waLink(p.phone)}}" target="_blank" rel="noopener">${{WA_SVG}}</a>`:''}}
        </div>`;
      }});
      html+=`</div></div>`;
    }}
  }});
  grid.innerHTML=html;
}}
function toggleBus(bus){{
  _openBus=_openBus===bus?null:bus;
  render();
  if(_openBus){{
    setTimeout(()=>{{const el=document.getElementById('bc_'+bus);if(el)el.scrollIntoView({{behavior:'smooth',block:'nearest'}});}},50);
  }}
}}
initAuth();
</script>
</body>
</html>"""

# ════════════════════════════════
# Landing page (home) — public; two campaigns, each with بحث + بيان الإركاب
# ════════════════════════════════
def make_landing(campaigns):
    cards = ''
    for c in campaigns:
        cards += ('<div class="camp-card" style="background:linear-gradient(135deg,'+c['pwa_dark']+','+c['pwa_med']+')">'
            '<div class="camp-name">'+c['company']+'</div>'
            '<div class="camp-actions">'
            '<a href="'+c['scan_out']+'" class="camp-act"><span class="ca-ic">📷</span><span>مسح سريع</span></a>'
            '<a href="'+c['search_out']+'" class="camp-act"><span class="ca-ic">🔍</span><span>بحث الحجاج</span></a>'
            '<a href="'+c['dash_out']+'" class="camp-act"><span class="ca-ic">📊</span><span>لوحة التحكم</span></a>'
            '<a href="'+c['manifest_out']+'" class="camp-act"><span class="ca-ic">📋</span><span>بيان الإركاب</span></a>'
            '</div></div>')
    return ('<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">'
        '<title>حملات الحج — يسر مساند</title>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        "body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(160deg,#0d4f3c,#173a3a 55%,#2b3039);min-height:100vh;padding:34px 18px;display:flex;flex-direction:column;align-items:center}"
        '.home-head{text-align:center;margin:14px 0 26px}'
        '.home-head .k{font-size:2.6rem;display:block;margin-bottom:8px}'
        '.home-head h1{font-size:1.45rem;font-weight:800;color:#f5d06e}'
        '.home-head p{color:rgba(255,255,255,.6);font-size:.9rem;margin-top:6px}'
        '.cards{display:flex;flex-direction:column;gap:18px;width:100%;max-width:440px}'
        '.camp-card{border-radius:22px;padding:22px 20px;box-shadow:0 10px 30px rgba(0,0,0,.32);border:1px solid rgba(255,255,255,.1)}'
        '.camp-name{color:#fff;font-size:1.25rem;font-weight:800;text-align:center;margin-bottom:18px}'
        '.camp-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}'
        '.camp-act{flex:1;background:rgba(255,255,255,.96);border-radius:15px;padding:18px 10px;text-decoration:none;color:#1a3a2e;display:flex;flex-direction:column;align-items:center;gap:8px;font-weight:700;font-size:.92rem;transition:transform .12s}'
        '.camp-act:active{transform:scale(.95)}'
        '.ca-ic{font-size:1.9rem}'
        '.foot{margin-top:30px;color:rgba(255,255,255,.4);font-size:.72rem}'
        '</style></head><body>'
        '<div class="home-head"><span class="k">🕋</span><h1>حملات الحج</h1><p>اختر الحملة والخدمة</p></div>'
        '<div class="cards">'+cards+'</div>'
        '<div class="foot">يسر مساند</div>'
        '</body></html>')

# ════════════════════════════════
# Build all campaigns
# ════════════════════════════════
CAMPAIGNS = [
    {   'key':'muhaimeed',
        'data':f'{BASE}/pilgrims_data.json', 'form':f'{BASE}/Form A4.png',
        'search_out':'muhaimeed.html', 'manifest_out':'manifest.html', 'card_out':'card.html', 'company':'شركة المحيميد للحج', 'scan_out':'scan.html',
        'dash_out':'dashboard.html',
        'h1':'بحث حجاج يسر مساند', 'brand':'يسر مساند',
        'manifest_title':'بيانات الركاب — المحيميد للحج',
        'card_co':'يسر مساند', 'card_foot':'الحملة المحيمد للحج والعمرة',
        'qr':'0d4f3c', 'theme':None,
        'app_name':'حجاج المحيميد', 'short_name':'المحيميد',
        'webmanifest':'app-m.webmanifest', 'icon_prefix':'icon-m',
        'pwa_dark':'#0d4f3c', 'pwa_med':'#1a7a5e',
        'reports_out':'reports.html', 'reports_key':'reports_muhaimeed',
        'manifests_key':'manifests_muhaimeed',
    },
    {   'key':'ruwais',
        'data':f'{BASE}/ruwais_data.json', 'form':f'{BASE}/Form A4 R.png',
        'search_out':'ruwais.html', 'manifest_out':'ruwais-manifest.html', 'card_out':'ruwais-card.html', 'company':'شركة الرويس للحج', 'scan_out':'ruwais-scan.html',
        'dash_out':'ruwais-dashboard.html',
        'h1':'بحث حجاج الرويس', 'brand':'حملة الرويس',
        'manifest_title':'بيانات الركاب — الرويس',
        'card_co':'حملة الرويس', 'card_foot':'حملة الرويس للحج والعمرة',
        'qr':'2b3039', 'theme':THEME_RUWAIS,
        'app_name':'حجاج الرويس', 'short_name':'الرويس',
        'webmanifest':'app-r.webmanifest', 'icon_prefix':'icon-r',
        'pwa_dark':'#2b3039', 'pwa_med':'#4a525e',
        'reports_out':'ruwais-reports.html', 'reports_key':'reports_ruwais',
        'manifests_key':'manifests_ruwais',
    },
]
open(f'{BASE}/sw.js','w',encoding='utf-8').write(SW_JS)

outputs = []
for c in CAMPAIGNS:
    data_bytes = load_data_bytes(c['data'])
    ps = make_payload(data_bytes, PASSWORD_SEARCH)
    pm = make_payload(data_bytes, PASSWORD_MANIFEST)
    _lh = LOCK_HTML.replace('<h2>يسر مساند</h2>', f"<h2>{c['brand']}</h2>")
    LH_SEARCH   = _lh.replace('__PAGETYPE__', 'البحث عن الحجاج')
    LH_MANIFEST = _lh.replace('__PAGETYPE__', 'بيان الإركاب')
    LH_SCAN     = _lh.replace('__PAGETYPE__', 'البحث السريع')
    LH_DASH     = _lh.replace('__PAGETYPE__', 'لوحة التحكم')
    # PWA app assets
    write_icons(c['icon_prefix'], c['pwa_dark'], c['pwa_med'], '#f5d06e')
    open(f"{BASE}/{c['webmanifest']}",'w',encoding='utf-8').write(
        webmanifest_json(c['app_name'], c['short_name'], c['search_out'], c['pwa_dark'], c['pwa_dark'], c['icon_prefix']))
    HEAD = pwa_head(c['webmanifest'], c['pwa_dark'], c['app_name'], f"{c['icon_prefix']}-180.png")
    def addpwa(h):
        return h.replace('</head>', HEAD+'\n</head>', 1).replace('</body>', SW_REG+'\n</body>', 1)
    # search
    idx = apply_theme(make_index(make_decrypt_js(ps), LH_SEARCH, c['h1'], c['manifest_out'], c['qr'], c['card_out'], switcher(c['key']), reports_js(c['reports_key'], c['reports_out']), c['reports_out'], c['scan_out'], c['dash_out']), c['theme'])
    open(f"{BASE}/{c['search_out']}",'w',encoding='utf-8').write(addpwa(idx))
    # reports page
    rpt = apply_theme(make_reports(c['reports_key'], c['search_out'], switcher(c['key'])), c['theme'])
    open(f"{BASE}/{c['reports_out']}",'w',encoding='utf-8').write(rpt.replace('</body>', SW_REG+'\n</body>'))
    # quick-search (camera/barcode) page
    scn = apply_theme(make_scan(make_decrypt_js(ps), LH_SCAN, switcher(c['key']), c['search_out']), c['theme'])
    open(f"{BASE}/{c['scan_out']}",'w',encoding='utf-8').write(addpwa(scn))
    # dashboard
    dash = apply_theme(make_dashboard(make_decrypt_js(ps), LH_DASH, 'لوحة التحكم', c['search_out'], c['reports_out'], c['manifest_out'], switcher(c['key'])), c['theme'])
    open(f"{BASE}/{c['dash_out']}",'w',encoding='utf-8').write(addpwa(dash))
    print(f"  {c['dash_out']}: built ({c['key']})")
    # manifest
    plain = gen_manifest.generate(c['data'], c['form'], c['manifest_title'], c['search_out'], c['manifests_key'])
    man = apply_theme(build_manifest(plain, make_decrypt_js(pm), LH_MANIFEST, switcher(c['key'])), c['theme'])
    open(f"{BASE}/{c['manifest_out']}",'w',encoding='utf-8').write(addpwa(man))
    # card
    card = apply_theme(CARD.replace('__CO__', c['card_co']).replace('__FOOTER__', c['card_foot']), c['theme'])
    open(f"{BASE}/{c['card_out']}",'w',encoding='utf-8').write(card)
    outputs += [c['search_out'], c['manifest_out'], c['card_out'], c['reports_out'], c['scan_out'], c['dash_out'],
                c['webmanifest'], f"{c['icon_prefix']}-192.png", f"{c['icon_prefix']}-512.png", f"{c['icon_prefix']}-180.png"]
    # clean check — no plaintext PII fields leaked
    for fn in (c['search_out'], c['manifest_out']):
        txt = open(f'{BASE}/{fn}',encoding='utf-8').read()
        bad = ('"resv":' in txt) or ('"phone":' in txt)
        print(f"  {fn}: {'PLAINTEXT ❌' if bad else 'CLEAN ✅'} ({len(txt)//1024} KB)")
    print(f"  {c['card_out']}: built ({c['key']})")

# Landing page → index.html (root)
open(f'{BASE}/index.html','w',encoding='utf-8').write(make_landing(CAMPAIGNS).replace('</body>', SW_REG+'</body>'))
print('  index.html: landing page (2 campaigns)')

# Zip everything (+ shared service worker + landing + scan lib)
outputs.append('sw.js')
outputs.append('index.html')
outputs.append('html5-qrcode.min.js')
with zipfile.ZipFile(f'{BASE}/hajj_site.zip','w',zipfile.ZIP_DEFLATED) as z:
    for fn in outputs:
        z.write(f'{BASE}/{fn}', fn)
print(f'hajj_site.zip: {os.path.getsize(BASE+"/hajj_site.zip")//1024} KB ({len(outputs)} files)')
