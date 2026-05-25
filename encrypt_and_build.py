import json, os, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Encrypt pilgrim data ──
with open('/Users/m/Documents/est3lam/pilgrims_data.json','r',encoding='utf-8') as f:
    records = json.load(f)

PASSWORD = b'112233'
data_bytes = json.dumps(records, ensure_ascii=False).encode('utf-8')

salt  = os.urandom(16)
nonce = os.urandom(12)

kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
key = kdf.derive(PASSWORD)

encrypted = AESGCM(key).encrypt(nonce, data_bytes, None)
PAYLOAD = base64.b64encode(salt + nonce + encrypted).decode()

print(f'Encrypted payload: {len(PAYLOAD)//1024} KB')

# ── Shared JS: decrypt + init ──
DECRYPT_JS = r"""
const PAYLOAD = '__PAYLOAD__';

async function decryptData(pass) {
  const raw = atob(PAYLOAD);
  const buf = new Uint8Array(raw.length);
  for (let i=0;i<raw.length;i++) buf[i]=raw.charCodeAt(i);
  const salt=buf.slice(0,16), nonce=buf.slice(16,28), data=buf.slice(28);
  const km = await crypto.subtle.importKey('raw',new TextEncoder().encode(pass),'PBKDF2',false,['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    {name:'PBKDF2',salt,iterations:100000,hash:'SHA-256'},
    km,{name:'AES-GCM',length:256},false,['decrypt']
  );
  const dec = await crypto.subtle.decrypt({name:'AES-GCM',iv:nonce},key,data);
  return JSON.parse(new TextDecoder().decode(dec));
}

async function tryPass() {
  const v = document.getElementById('passInput').value;
  const btn = document.querySelector('#lockScreen button');
  btn.textContent = '...جارٍ التحقق';
  btn.disabled = true;
  try {
    const d = await decryptData(v);
    window._DATA = d;
    sessionStorage.setItem('auth','1');
    sessionStorage.setItem('pass', v);
    document.getElementById('lockScreen').style.display='none';
    if(typeof onDataReady==='function') onDataReady(d);
  } catch(e) {
    const err=document.getElementById('passErr');
    err.style.display='block';
    document.getElementById('passInput').value='';
    btn.textContent='دخول 🕋';
    btn.disabled=false;
    setTimeout(()=>err.style.display='none',2500);
  }
}

async function initAuth() {
  if(sessionStorage.getItem('auth')==='1') {
    const p=sessionStorage.getItem('pass')||'';
    try {
      const d=await decryptData(p);
      window._DATA=d;
      document.getElementById('lockScreen').style.display='none';
      if(typeof onDataReady==='function') onDataReady(d);
    } catch{ sessionStorage.clear(); }
  }
}
""".replace('__PAYLOAD__', PAYLOAD)

LOCK_CSS = """
  #lockScreen{position:fixed;inset:0;z-index:9999;background:linear-gradient(135deg,#0d4f3c,#1a7a5e);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
  .lock-box{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-radius:24px;padding:36px 28px;width:100%;max-width:380px;text-align:center;backdrop-filter:blur(12px)}
  .lock-icon{font-size:3rem;margin-bottom:12px}
  .lock-box h2{color:#f5d06e;font-size:1.3rem;margin-bottom:6px}
  .lock-box p{color:rgba(255,255,255,.6);font-size:.85rem;margin-bottom:24px}
  #passInput{width:100%;padding:14px 18px;border-radius:14px;border:2px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);color:white;font-size:1.3rem;text-align:center;letter-spacing:6px;outline:none;margin-bottom:14px;font-family:inherit}
  #passInput::placeholder{letter-spacing:2px;font-size:.9rem;color:rgba(255,255,255,.4)}
  #passInput:focus{border-color:#f5d06e}
  #lockBtn{width:100%;padding:14px;border-radius:14px;border:none;background:#f5d06e;color:#0d4f3c;font-size:1rem;font-weight:800;cursor:pointer;font-family:inherit}
  #lockBtn:disabled{opacity:.6;cursor:default}
  .lock-err{color:#ff8080;font-size:.85rem;margin-top:10px;display:none}
"""

LOCK_HTML = """
<div id="lockScreen">
  <div class="lock-box">
    <div class="lock-icon">🔐</div>
    <h2>بحث حجاج يسر مساند</h2>
    <p>أدخل كلمة المرور للدخول</p>
    <input type="password" id="passInput" placeholder="كلمة المرور" inputmode="numeric" maxlength="20"
      onkeydown="if(event.key==='Enter')tryPass()">
    <button id="lockBtn" onclick="tryPass()">دخول 🕋</button>
    <div class="lock-err" id="passErr">كلمة المرور غير صحيحة</div>
  </div>
</div>
"""

# ════════════════════════════════════════
# BUILD index.html
# ════════════════════════════════════════
INDEX_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>بحث حجاج يسر مساند</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:linear-gradient(135deg,#0d4f3c 0%,#1a7a5e 50%,#0d4f3c 100%);min-height:100vh;padding:0 0 40px}
  header{background:rgba(0,0,0,.25);padding:16px 16px 14px;text-align:center;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.1)}
  .hdr-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  header h1{color:#f5d06e;font-size:1.15rem;font-weight:700;display:flex;align-items:center;gap:8px}
  .nav-link{background:rgba(255,255,255,.15);color:#f5d06e;border-radius:10px;padding:6px 11px;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid rgba(245,208,110,.3)}
  .search-wrap{position:relative}
  #searchInput{width:100%;padding:14px 48px 14px 16px;border-radius:14px;border:2px solid rgba(245,208,110,.4);background:rgba(255,255,255,.95);font-size:1.05rem;color:#1a1a1a;font-family:inherit;outline:none;text-align:right;transition:.2s}
  #searchInput:focus{border-color:#f5d06e;box-shadow:0 0 0 3px rgba(245,208,110,.2)}
  #searchInput::placeholder{color:#999;font-size:.95rem}
  .search-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#1a7a5e;font-size:1.2rem;pointer-events:none}
  .clear-btn{position:absolute;right:12px;top:50%;transform:translateY(-50%);background:#ddd;border:none;border-radius:50%;width:26px;height:26px;font-size:.85rem;cursor:pointer;display:none;align-items:center;justify-content:center;color:#666}
  .clear-btn.visible{display:flex}
  .hint{color:rgba(255,255,255,.6);font-size:.75rem;margin-top:8px;text-align:center}
  #results{padding:16px;max-width:600px;margin:0 auto}
  .state-msg{text-align:center;color:rgba(255,255,255,.7);margin-top:60px;font-size:1rem}
  .state-msg .icon{font-size:3rem;display:block;margin-bottom:12px}
  .result-card{background:white;border-radius:18px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.18);margin-bottom:20px;animation:fadeUp .25s ease}
  @keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
  .card-header{background:linear-gradient(135deg,#1a7a5e,#0d4f3c);padding:18px 18px 14px;color:white}
  .pilgrim-name{font-size:1.2rem;font-weight:700;line-height:1.4;color:#f5d06e;margin-bottom:4px}
  .pilgrim-label{font-size:.75rem;color:rgba(255,255,255,.6);letter-spacing:1px}
  .card-body{padding:16px 18px;display:flex;gap:12px}
  .info-box{flex:1;background:#f8fffe;border-radius:12px;padding:12px 14px;text-align:center;border:1.5px solid #e0f5ef}
  .info-box .label{font-size:.7rem;color:#888;display:block;margin-bottom:4px;font-weight:600;letter-spacing:.5px}
  .info-box .value{font-size:1.35rem;font-weight:800;color:#0d4f3c;direction:ltr;display:block}
  .info-box.bus .value{font-size:2rem;color:#e07b00}
  .info-box.bus{border-color:#fde8c0;background:#fffbf3}
  .group-banner{background:linear-gradient(90deg,#e07b00,#f5a623);color:white;text-align:center;padding:8px 16px;font-size:.82rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:6px}
  .group-list{padding:10px 14px 14px}
  .group-member{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;border-bottom:1px solid #f0f0f0}
  .group-member:last-child{border-bottom:none}
  .group-member.is-self{background:#edfaf5}
  .member-num{width:26px;height:26px;border-radius:50%;background:#1a7a5e;color:white;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .member-num.self{background:#f5d06e;color:#0d4f3c}
  .member-name{font-size:.92rem;color:#1a1a1a;font-weight:500;flex:1}
  .you-badge{font-size:.65rem;background:#1a7a5e;color:white;padding:2px 7px;border-radius:20px;font-weight:700}
  .no-result{text-align:center;margin-top:60px;color:rgba(255,255,255,.8);animation:fadeUp .25s ease}
  .no-result .icon{font-size:3rem;display:block;margin-bottom:12px}
  .count-badge{display:inline-block;background:rgba(255,255,255,.15);border-radius:20px;padding:3px 10px;font-size:.78rem;color:rgba(255,255,255,.9);margin-bottom:8px}
  LOCK_CSS_PLACEHOLDER
</style>
</head>
<body>
LOCK_HTML_PLACEHOLDER
<header>
  <div class="hdr-row">
    <h1>🕋 بحث حجاج يسر مساند</h1>
    <a href="manifest.html" class="nav-link">📋 بيانات الركاب</a>
  </div>
  <div class="search-wrap">
    <input type="search" id="searchInput" placeholder="ابحث بالاسم أو الهوية أو الجوال..." autocomplete="off" autocorrect="off" spellcheck="false" inputmode="search">
    <span class="search-icon">🔍</span>
    <button class="clear-btn" id="clearBtn" onclick="clearSearch()">✕</button>
  </div>
  <div class="hint">اكتب أي جزء من الاسم أو رقم الهوية أو رقم الجوال</div>
</header>
<div id="results">
  <div class="state-msg"><span class="icon">🔍</span><p>ابحث عن الحاج للعثور على معلومات الحجز والباص</p></div>
</div>
<script>
let DATA=[];
const byId={},byPhone={},byResv={};

function onDataReady(d){
  DATA=d;
  DATA.forEach(p=>{
    if(p.id)(byId[p.id]=byId[p.id]||[]).push(p);
    if(p.phone)(byPhone[p.phone]=byPhone[p.phone]||[]).push(p);
    if(p.resv)(byResv[p.resv]=byResv[p.resv]||[]).push(p);
  });
}

const input=document.getElementById('searchInput');
const clearBtn=document.getElementById('clearBtn');
const resultsDiv=document.getElementById('results');
let deb;

input.addEventListener('input',()=>{
  clearTimeout(deb);deb=setTimeout(doSearch,200);
  clearBtn.classList.toggle('visible',input.value.length>0);
});

function clearSearch(){input.value='';clearBtn.classList.remove('visible');showEmpty();input.focus()}

function norm(s){return(s||'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').toLowerCase().trim()}

function doSearch(){
  const q=input.value.trim();
  if(!q){showEmpty();return}
  if(q.length<2){resultsDiv.innerHTML='<div class="state-msg"><span class="icon">✍️</span><p>اكتب أكثر...</p></div>';return}
  let m=[];
  if(byId[q])m=[...byId[q]];
  if(!m.length&&byPhone[q])m=[...byPhone[q]];
  if(!m.length){const alt=q.startsWith('0')?q.slice(1):'0'+q;if(byPhone[alt])m=[...byPhone[alt]]}
  if(!m.length){const nq=norm(q);m=DATA.filter(p=>norm(p.name).includes(nq))}
  if(!m.length&&/^\\d+$/.test(q))m=DATA.filter(p=>p.id.includes(q));
  const seen=new Set();
  m=m.filter(p=>{const k=p.name+p.resv;if(seen.has(k))return false;seen.add(k);return true});
  if(!m.length){resultsDiv.innerHTML=`<div class="no-result"><span class="icon">😔</span><p>لا نتائج لـ "<strong>${q}</strong>"</p><small>تأكد من الاسم أو رقم الهوية أو الجوال</small></div>`;return}
  let html='';
  if(m.length>1)html+=`<div style="text-align:center;margin-bottom:12px"><span class="count-badge">تم العثور على <strong>${m.length}</strong> نتيجة</span></div>`;
  m.slice(0,20).forEach(p=>{
    const grp=byResv[p.resv]||[];
    html+=`<div class="result-card"><div class="card-header"><div class="pilgrim-label">الحاج / الحاجة</div><div class="pilgrim-name">${p.name}</div></div><div class="card-body"><div class="info-box"><span class="label">رقم الحجز</span><span class="value" style="font-size:1.15rem">${p.resv||'—'}</span></div><div class="info-box bus"><span class="label">الباص</span><span class="value">${p.bus||'—'}</span></div></div>`;
    if(grp.length>1){
      html+=`<div class="group-banner"><span>👥</span> رفقاء الحجز · ${grp.length} أشخاص</div><div class="group-list">`;
      grp.forEach((mem,i)=>{const s=mem.name===p.name;html+=`<div class="group-member${s?' is-self':''}"><div class="member-num${s?' self':''}">${i+1}</div><div class="member-name">${mem.name}</div>${s?'<span class="you-badge">أنت</span>':''}</div>`});
      html+='</div>';
    }
    html+='</div>';
  });
  if(m.length>20)html+=`<p style="text-align:center;color:rgba(255,255,255,.6);font-size:.85rem">يُعرض أول 20 نتيجة</p>`;
  resultsDiv.innerHTML=html;
}
function showEmpty(){resultsDiv.innerHTML='<div class="state-msg"><span class="icon">🔍</span><p>ابحث عن الحاج للعثور على معلومات الحجز والباص</p></div>'}

DECRYPT_JS_PLACEHOLDER
initAuth();
</script>
</body>
</html>"""

index_html = (INDEX_HTML
  .replace('LOCK_CSS_PLACEHOLDER', LOCK_CSS)
  .replace('LOCK_HTML_PLACEHOLDER', LOCK_HTML)
  .replace('DECRYPT_JS_PLACEHOLDER', DECRYPT_JS))

with open('/Users/m/Documents/est3lam/index.html','w',encoding='utf-8') as f:
    f.write(index_html)
print(f'index.html: {len(index_html)//1024} KB')

# ════════════════════════════════════════
# BUILD manifest.html (inject encrypted data)
# ════════════════════════════════════════
# Read existing manifest.html and replace the inline DATA with encrypted version
with open('/Users/m/Documents/est3lam/manifest.html','r',encoding='utf-8') as f:
    manifest = f.read()

# Replace the plaintext data block with encrypted version
OLD_DATA = 'const DATA = __DATA__;'

MANIFEST_INIT = """
let DATA=[];
const byId={},byPhone={},byResv={};
function onDataReady(d){
  DATA=d;
  DATA.forEach(p=>{
    if(p.id)(byId[p.id]=byId[p.id]||[]).push(p);
    if(p.phone)(byPhone[p.phone]=byPhone[p.phone]||[]).push(p);
    if(p.resv)(byResv[p.resv]=byResv[p.resv]||[]).push(p);
  });
  renderDash();
}
"""

# Also need to replace the DATA indexes block in the manifest since it used DATA directly
# Find and replace the data initialization section
import re

# Replace: const DATA = [...]; + the index building code
manifest_new = re.sub(
    r'const DATA = \[.*?\];.*?byResv\[p\.resv\] = byResv\[p\.resv\]\|\|\[\]\)\.push\(p\);\s*\}\);',
    MANIFEST_INIT.strip(),
    manifest,
    flags=re.DOTALL
)

# Add decrypt JS + lock CSS/HTML
# Insert LOCK_CSS before </style>
manifest_new = manifest_new.replace('</style>', LOCK_CSS + '\n</style>', 1)
# Insert LOCK_HTML after <body>
manifest_new = manifest_new.replace('<div id="app">', LOCK_HTML + '\n<div id="app">', 1)
# Insert DECRYPT_JS before renderDash() at the end
manifest_new = manifest_new.replace('renderDash();\n</script>', DECRYPT_JS + '\ninitAuth();\n</script>', 1)
# Remove the old renderDash() that was after data init (now called from onDataReady)
manifest_new = manifest_new.replace('\nrenderDash();\n</script>', '\ninitAuth();\n</script>')

with open('/Users/m/Documents/est3lam/manifest.html','w',encoding='utf-8') as f:
    f.write(manifest_new)
print(f'manifest.html: {len(manifest_new)//1024} KB')

# Rebuild zip
import zipfile
with zipfile.ZipFile('/Users/m/Documents/est3lam/hajj_site.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write('/Users/m/Documents/est3lam/index.html','index.html')
    z.write('/Users/m/Documents/est3lam/manifest.html','manifest.html')
print(f'hajj_site.zip ready')
