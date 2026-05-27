import json, base64, io
from PIL import Image

def _form_bg(form_png):
    """Official letterhead → embedded JPEG for print background."""
    img = Image.open(form_png).convert('RGB').resize((1240, 1754), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format='JPEG', quality=88, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

HTML = r'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>بيانات الركاب — المحيميد للحج</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--g:#0d4f3c;--gl:#1a7a5e;--gold:#c9a44e;--goldbg:#fdf6e8}
body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:#f0f4f0;min-height:100vh}
.btn{display:inline-flex;align-items:center;gap:5px;padding:8px 16px;border-radius:10px;border:none;font-family:inherit;font-size:.88rem;cursor:pointer;font-weight:700;transition:.15s}
.btn-gold{background:var(--gold);color:#fff}
.btn-green{background:var(--g);color:#fff}
.btn-ghost{background:rgba(255,255,255,.15);color:#fff}
.btn-danger{background:#fee2e2;color:#dc2626}
.btn-sm{padding:5px 10px;font-size:.78rem;border-radius:8px}
.app-header{background:linear-gradient(135deg,var(--g),var(--gl));padding:13px 16px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200;box-shadow:0 2px 10px rgba(0,0,0,.2)}
.app-header h1{color:var(--gold);font-size:1.05rem;display:flex;align-items:center;gap:8px}
#view-dashboard{padding:16px;max-width:680px;margin:0 auto}
.dash-stats{display:flex;gap:10px;margin-bottom:16px}
.stat-card{flex:1;background:white;border-radius:12px;padding:12px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.06)}
.stat-num{font-size:1.6rem;font-weight:800;color:var(--g)}
.stat-lbl{font-size:.72rem;color:#888}
.dash-empty{text-align:center;color:#888;margin-top:60px}
.dash-empty .icon{font-size:3rem;display:block;margin-bottom:12px}
.manifest-card{background:white;border-radius:14px;padding:14px 16px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;align-items:center;gap:12px;cursor:pointer;transition:.15s;border-right:5px solid var(--g)}
.manifest-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.12)}
.manifest-badge{background:var(--g);color:var(--gold);border-radius:10px;padding:8px 11px;font-weight:800;font-size:.82rem;white-space:nowrap;flex-shrink:0;text-align:center;min-width:70px}
.manifest-info{flex:1;min-width:0}
.manifest-info h3{font-size:.92rem;color:#1a1a1a;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.manifest-info p{font-size:.75rem;color:#777}
.manifest-actions{display:flex;gap:6px;flex-shrink:0}
#view-builder{display:none}
.builder-meta{background:var(--g);padding:10px 14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:2px solid var(--gold)}
.meta-chip{background:rgba(255,255,255,.1);border-radius:8px;padding:6px 10px;display:flex;flex-direction:column;gap:2px}
.meta-chip label{color:rgba(255,255,255,.6);font-size:.65rem;font-weight:700}
.meta-chip input,.meta-chip span{background:none;border:none;color:white;font-family:inherit;font-size:.88rem;font-weight:700;outline:none;width:90px}
.meta-chip.wide input{width:130px}
.meta-id-badge{background:var(--gold);color:var(--g);border-radius:8px;padding:6px 12px;font-weight:900;font-size:.9rem;flex-shrink:0}
.builder-body{padding:14px;max-width:680px;margin:0 auto;padding-bottom:90px}
.section-title{font-size:.78rem;font-weight:800;color:#555;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;display:flex;align-items:center;gap:6px}
.search-box{position:relative;margin-bottom:4px}
.search-box input{width:100%;padding:12px 44px 12px 14px;border-radius:12px;border:2px solid #ddd;font-size:.98rem;font-family:inherit;outline:none;background:white;text-align:right;transition:.2s}
.search-box input:focus{border-color:var(--gl)}
.search-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#888;font-size:1.1rem;pointer-events:none}
.result-row{background:white;border-radius:10px;padding:10px 12px;margin-bottom:5px;display:flex;align-items:center;gap:10px;box-shadow:0 1px 4px rgba(0,0,0,.06);animation:fadeUp .18s ease}
.result-row.done{opacity:.45;pointer-events:none}
.result-info{flex:1;min-width:0}
.result-name{font-size:.9rem;font-weight:700;color:#1a1a1a}
.result-sub{font-size:.73rem;color:#888;margin-top:2px}
.group-pill{display:inline-block;padding:2px 7px;border-radius:20px;font-size:.67rem;font-weight:700;border:1.5px solid;margin-right:4px}
.add-btn{width:32px;height:32px;border-radius:50%;border:none;background:var(--g);color:white;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s}
.add-btn:hover{background:var(--gl)}
.done-icon{color:#22c55e;font-size:1.2rem;flex-shrink:0}
.selected-wrap{margin-top:14px}
.selected-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.selected-count-badge{background:var(--g);color:white;border-radius:20px;padding:2px 10px;font-size:.75rem;font-weight:800}
.sel-item{border-radius:10px;padding:8px 12px;margin-bottom:5px;display:flex;align-items:center;gap:8px;border-right:4px solid;animation:fadeUp .18s ease}
.sel-num{width:22px;height:22px;border-radius:50%;font-size:.7rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sel-name{flex:1;font-size:.88rem;font-weight:600}
.sel-resv{font-size:.7rem;color:#888;flex-shrink:0}
.rm-btn{background:none;border:none;color:#dc2626;font-size:1rem;cursor:pointer;padding:2px 5px;border-radius:6px}
.rm-btn:hover{background:#fee2e2}
.wa-btn{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:8px;background:#25D366;flex-shrink:0;text-decoration:none;box-shadow:0 1px 3px rgba(0,0,0,.15)}
.wa-btn svg{width:18px;height:18px;fill:#fff}
.wa-btn:active{transform:scale(.9)}
.builder-footer{position:fixed;bottom:0;left:0;right:0;background:white;padding:10px 14px;box-shadow:0 -2px 12px rgba(0,0,0,.1);display:flex;gap:10px;z-index:100}
.builder-footer .btn{flex:1;justify-content:center;padding:12px}
#print-area{display:none}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
__LOCK_CSS__
@media print{
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
  @page{size:A4 portrait;margin:0}
  html,body{width:210mm;height:auto;min-height:0!important;margin:0!important;padding:0!important;background:#fff!important}
  body>*:not(#print-area){display:none!important}
  #print-area{display:block!important;width:210mm;margin:0;padding:0}
  .a4{width:210mm;height:296.8mm;position:relative;overflow:hidden;background:#fff url('__FORM_BG__') no-repeat;background-size:210mm 296.8mm;page-break-after:always}
  .a4:last-child{page-break-after:auto}
  .pat-l{position:absolute;left:0;top:0;width:28mm;height:100%;background-color:#fdf6e8;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='38' height='38'%3E%3Crect width='38' height='38' fill='%23fdf6e8'/%3E%3Cpath d='M19 1.5L36.5 19L19 36.5L1.5 19Z' fill='none' stroke='%23c4a44a' stroke-width='1.2'/%3E%3Cpath d='M19 9L29 19L19 29L9 19Z' fill='none' stroke='%23c4a44a' stroke-width='.7'/%3E%3Ccircle cx='19' cy='19' r='3.5' fill='%23c4a44a' opacity='.45'/%3E%3Ccircle cx='0' cy='0' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='38' cy='0' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='0' cy='38' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='38' cy='38' r='3' fill='%23c4a44a' opacity='.35'/%3E%3C/svg%3E");background-size:13mm 13mm}
  .pat-b{position:absolute;left:0;bottom:0;width:100%;height:30mm;background-color:#fdf6e8;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='38' height='38'%3E%3Crect width='38' height='38' fill='%23fdf6e8'/%3E%3Cpath d='M19 1.5L36.5 19L19 36.5L1.5 19Z' fill='none' stroke='%23c4a44a' stroke-width='1.2'/%3E%3Cpath d='M19 9L29 19L19 29L9 19Z' fill='none' stroke='%23c4a44a' stroke-width='.7'/%3E%3Ccircle cx='19' cy='19' r='3.5' fill='%23c4a44a' opacity='.45'/%3E%3Ccircle cx='0' cy='0' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='38' cy='0' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='0' cy='38' r='3' fill='%23c4a44a' opacity='.35'/%3E%3Ccircle cx='38' cy='38' r='3' fill='%23c4a44a' opacity='.35'/%3E%3C/svg%3E");background-size:13mm 13mm;z-index:2}
  .company-area{position:absolute;bottom:6mm;right:8mm;z-index:5;display:flex;align-items:center;gap:3mm;direction:rtl}
  .co-text{text-align:right}
  .co-ar{font-size:10pt;font-weight:800;color:#5a3e0a;display:block}
  .co-en{font-size:7pt;color:#8b6914;display:block}
  .co-logo{width:16mm;height:16mm;border:2px solid #8b6914;border-radius:3mm;display:flex;align-items:center;justify-content:center;font-size:8pt;font-weight:900;color:#8b6914;text-align:center;line-height:1.2;flex-shrink:0}
  .content-rect{position:absolute;left:13mm;top:15mm;right:13mm;bottom:36mm;border-radius:6mm;overflow:hidden;background:transparent;z-index:3;display:flex;flex-direction:column}
  .pr-head{padding:3.5mm 5mm 3mm;border-bottom:1.5px solid #333;flex-shrink:0}
  .pr-title{font-size:13pt;font-weight:800;text-align:center;margin-bottom:2mm;color:#0d4f3c}
  .pr-meta{display:flex;flex-wrap:wrap;gap:2mm 4mm;font-size:8pt;color:#333;justify-content:space-between}
  .pr-meta span b{color:#0d4f3c}
  .pr-table{width:100%;border-collapse:collapse;font-size:7.8pt}
  .pr-table th{background:#0d4f3c;color:white;padding:1.8mm 2mm;text-align:right;font-weight:700;border:1px solid #0d4f3c;font-size:7.5pt}
  .pr-table td{padding:1.5mm 2mm;border:.5px solid #ccc;vertical-align:middle;height:7mm;color:#111;background:transparent}
  .pr-table td.c{text-align:center}
  .pr-table td.n{text-align:center;font-weight:800;color:#0d4f3c}
  .pr-foot{border-top:1px solid #ccc;padding:2mm 5mm;display:flex;justify-content:space-between;align-items:center;font-size:7pt;color:#555;flex-shrink:0;margin-top:auto}
}
</style>
</head>
<body>
__LOCK_HTML__
<div id="app">
<div class="app-header">
  <div style="display:flex;align-items:center;gap:8px">
    <a href="index.html" style="background:rgba(255,255,255,.15);color:var(--gold);border-radius:8px;padding:5px 10px;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid rgba(255,255,255,.2)">🔍 بحث الحجاج</a>
    <h1>📋 بيانات الركاب <span style="font-size:.6em;opacity:.6;font-weight:400">v3.7</span></h1>
  </div>
  <div style="display:flex;gap:8px">
    <button class="btn btn-ghost" id="btn-back" onclick="goDash()" style="display:none">← رجوع</button>
    <button class="btn btn-gold" onclick="newManifest()" id="btn-new">+ بيان جديد</button>
  </div>
</div>
<div id="view-dashboard">
  <div style="padding:16px;max-width:680px;margin:0 auto">
    <div class="dash-stats">
      <div class="stat-card"><div class="stat-num" id="stat-total">0</div><div class="stat-lbl">إجمالي البيانات</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-pax">0</div><div class="stat-lbl">إجمالي الركاب</div></div>
    </div>
    <div id="manifest-list"></div>
    <div id="dash-empty" class="dash-empty" style="display:none">
      <span class="icon">📋</span><p>لا توجد بيانات ركاب</p>
      <p style="margin-top:6px;font-size:.82rem;color:#aaa">اضغط «+ بيان جديد» للبدء</p>
    </div>
  </div>
</div>
<div id="view-builder">
  <div class="builder-meta">
    <div class="meta-id-badge" id="meta-id-label">—</div>
    <div class="meta-chip"><label>الباص</label><input type="number" id="m-bus" placeholder="رقم" min="1" max="99" style="width:60px"></div>
    <div class="meta-chip"><label>التاريخ</label><input type="date" id="m-date" style="width:120px"></div>
    <div class="meta-chip wide"><label>المشرف</label><input type="text" id="m-driver" placeholder="اسم المشرف"></div>
  </div>
  <div class="builder-body">
    <div class="section-title">🔍 بحث وإضافة ركاب</div>
    <div class="search-box">
      <input type="search" id="bsearch" placeholder="ابحث بالاسم أو الهوية أو الجوال..." autocomplete="off" oninput="bSearch(this.value)">
      <span class="search-icon">🔍</span>
    </div>
    <div id="search-results"></div>
    <div class="selected-wrap" id="sel-wrap" style="display:none">
      <div class="selected-header">
        <div class="section-title" style="margin:0">✅ الركاب المضافون</div>
        <span class="selected-count-badge" id="sel-count">0</span>
      </div>
      <div id="sel-list"></div>
    </div>
  </div>
  <div class="builder-footer">
    <button class="btn btn-green" onclick="saveManifest()">💾 حفظ</button>
    <button class="btn btn-gold" onclick="printManifest()">🖨️ طباعة PDF</button>
  </div>
</div>
</div>
<div id="print-area"></div>
<script>
__DECRYPT_JS__

let DATA=[],cur=null,colorIdx=0,resvCol={};
const byId={},byPhone={},byResv={};

function onDataReady(d){
  DATA=d;
  DATA.forEach(p=>{
    if(p.id)(byId[p.id]=byId[p.id]||[]).push(p);
    if(p.phone)(byPhone[p.phone]=byPhone[p.phone]||[]).push(p);
    if(p.resv)(byResv[p.resv]=byResv[p.resv]||[]).push(p);
  });
  renderDash();
  pullManifests();
}

const COLORS=[
  {bg:'#dbeafe',b:'#3b82f6',t:'#1e40af'},{bg:'#dcfce7',b:'#22c55e',t:'#15803d'},
  {bg:'#fce7f3',b:'#ec4899',t:'#9d174d'},{bg:'#fef9c3',b:'#ca8a04',t:'#78350f'},
  {bg:'#ede9fe',b:'#8b5cf6',t:'#5b21b6'},{bg:'#ffedd5',b:'#f97316',t:'#9a3412'},
  {bg:'#d1fae5',b:'#10b981',t:'#065f46'},{bg:'#e0f2fe',b:'#0ea5e9',t:'#075985'},
];

const LS='hajj_manifests',LC='hajj_mc';
function loadAll(){try{return JSON.parse(localStorage.getItem(LS)||'[]')}catch{return[]}}
function saveAll(l){localStorage.setItem(LS,JSON.stringify(l));if(typeof cloudSet==='function')cloudSet(LS,l);}
async function pullManifests(){if(typeof cloudGet!=='function')return;try{const c=await cloudGet(LS);if(Array.isArray(c)){localStorage.setItem(LS,JSON.stringify(c));renderDash();}}catch(e){}}
function nextId(){const n=(+localStorage.getItem(LC)||0)+1;localStorage.setItem(LC,n);return'بيان-'+String(n).padStart(3,'0')}

function renderDash(){
  const all=loadAll();
  document.getElementById('stat-total').textContent=all.length;
  document.getElementById('stat-pax').textContent=all.reduce((s,m)=>s+m.passengers.length,0);
  const c=document.getElementById('manifest-list');
  const e=document.getElementById('dash-empty');
  if(!all.length){c.innerHTML='';e.style.display='';return}
  e.style.display='none';
  c.innerHTML=all.map((m,i)=>`
    <div class="manifest-card" onclick="editManifest(${i})">
      <div class="manifest-badge">${m.id}</div>
      <div class="manifest-info"><h3>باص ${m.bus||'—'} · ${m.driver||''}</h3><p>🗓 ${m.date||'—'} | 👥 ${m.passengers.length} راكب</p></div>
      <div class="manifest-actions" onclick="event.stopPropagation()">
        <button class="btn btn-gold btn-sm" onclick="quickPrint(${i})">🖨️</button>
        <button class="btn btn-danger btn-sm" onclick="delManifest(event,${i})">🗑</button>
      </div>
    </div>`).join('');
}

function delManifest(e,i){e.stopPropagation();if(!confirm('حذف هذا البيان؟'))return;const l=loadAll();l.splice(i,1);saveAll(l);renderDash()}
function quickPrint(i){loadBuilder(loadAll()[i]);setTimeout(printManifest,200)}
function editManifest(i){loadBuilder(loadAll()[i])}

function goDash(){
  document.getElementById('view-dashboard').style.display='block';
  document.getElementById('view-builder').style.display='none';
  document.getElementById('btn-back').style.display='none';
  document.getElementById('btn-new').style.display='';
  renderDash();
}
function showBuilder(){
  document.getElementById('view-dashboard').style.display='none';
  document.getElementById('view-builder').style.display='block';
  document.getElementById('btn-back').style.display='';
  document.getElementById('btn-new').style.display='none';
}

function newManifest(){
  cur={id:nextId(),bus:'',date:new Date().toISOString().slice(0,10),driver:'',passengers:[]};
  colorIdx=0;resvCol={};fillMeta();
  document.getElementById('bsearch').value='';
  document.getElementById('search-results').innerHTML='';
  renderSel();showBuilder();
}
function loadBuilder(m){
  cur=JSON.parse(JSON.stringify(m));colorIdx=0;resvCol={};
  cur.passengers.forEach(p=>{if(p.resv&&!resvCol[p.resv]){resvCol[p.resv]=COLORS[colorIdx%COLORS.length];colorIdx++}});
  fillMeta();document.getElementById('bsearch').value='';
  document.getElementById('search-results').innerHTML='';
  renderSel();showBuilder();
}
function fillMeta(){
  document.getElementById('meta-id-label').textContent=cur.id;
  document.getElementById('m-bus').value=cur.bus||'';
  document.getElementById('m-date').value=cur.date||'';
  document.getElementById('m-driver').value=cur.driver||'';
}
function readMeta(){cur.bus=document.getElementById('m-bus').value;cur.date=document.getElementById('m-date').value;cur.driver=document.getElementById('m-driver').value}

function norm(s){return(s||'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').trim()}
let debT;
function bSearch(q){clearTimeout(debT);debT=setTimeout(()=>doSearch(q),220)}
function doSearch(q){
  const c=document.getElementById('search-results');
  q=q.trim();if(q.length<2){c.innerHTML='';return}
  let m=[];
  if(byId[q])m=[...byId[q]];
  if(!m.length&&byPhone[q])m=[...byPhone[q]];
  if(!m.length){const alt=q.startsWith('0')?q.slice(1):'0'+q;if(byPhone[alt])m=[...byPhone[alt]]}
  if(!m.length){const nq=norm(q);m=DATA.filter(p=>norm(p.name).includes(nq))}
  if(!m.length&&/^\d+$/.test(q))m=DATA.filter(p=>p.id.includes(q));
  const seen=new Set();
  m=m.filter(p=>{const k=p.name+p.resv;if(seen.has(k))return false;seen.add(k);return true}).slice(0,30);
  if(!m.length){c.innerHTML='<p style="text-align:center;padding:14px;color:#888;font-size:.88rem">لا توجد نتائج</p>';return}
  const added=new Set(cur.passengers.map(p=>p.name+p.resv));
  c.innerHTML=m.map(p=>{
    const grp=byResv[p.resv]||[];
    const col=resvCol[p.resv];
    const pill=grp.length>1?`<span class="group-pill" style="background:${col?.bg||'#eee'};border-color:${col?.b||'#ccc'};color:${col?.t||'#333'}">مجموعة ${grp.length}</span>`:'';
    const done=added.has(p.name+p.resv);
    const pd=JSON.stringify(p).replace(/'/g,"&#39;");
    return`<div class="result-row${done?' done':''}">
      <div class="result-info"><div class="result-name">${p.name}</div><div class="result-sub">حجز: ${p.resv} · باص: ${p.bus} ${pill}</div></div>
      ${done?'<span class="done-icon">✓</span>':`<button class="add-btn" onclick='addGroup(${pd})'>+</button>`}
    </div>`;
  }).join('');
}

function addGroup(p){
  const resv=p.resv;const grp=byResv[resv]||[p];
  if(!resvCol[resv]){resvCol[resv]=COLORS[colorIdx%COLORS.length];colorIdx++}
  const col=resvCol[resv];
  const added=new Set(cur.passengers.map(x=>x.name+x.resv));
  grp.forEach(m=>{if(!added.has(m.name+m.resv))cur.passengers.push({...m,_col:col})});
  renderSel();const q=document.getElementById('bsearch').value;if(q.length>=2)doSearch(q);
}
function rmPax(i){cur.passengers.splice(i,1);renderSel();const q=document.getElementById('bsearch').value;if(q.length>=2)doSearch(q)}
const WA_SVG='<svg viewBox="0 0 24 24"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38c1.45.79 3.08 1.21 4.79 1.21h.01c5.46 0 9.9-4.45 9.9-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0012.04 2zm5.8 14.04c-.24.68-1.42 1.31-1.96 1.39-.5.07-1.13.1-1.83-.11-.42-.13-.96-.31-1.65-.61-2.9-1.25-4.8-4.17-4.95-4.36-.14-.19-1.18-1.57-1.18-2.99s.75-2.12 1.01-2.41c.26-.29.57-.36.76-.36.19 0 .38 0 .54.01.18.01.41-.07.64.49.24.57.81 1.97.88 2.11.07.14.12.31.02.5-.09.19-.14.31-.28.47-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.17.28.74 1.22 1.59 1.98 1.1.97 2.02 1.27 2.3 1.42.28.14.45.12.61-.07.17-.19.7-.82.89-1.1.18-.28.37-.23.61-.14.25.09 1.57.74 1.84.88.27.14.45.2.51.31.07.11.07.63-.17 1.31z"/></svg>';
function waLink(ph){let n=(ph||'').replace(/\D/g,'');if(!n)return'';if(n[0]==='0')n=n.slice(1);if(n.indexOf('966')!==0)n='966'+n;return'https://wa.me/'+n;}
function renderSel(){
  const l=cur.passengers;
  document.getElementById('sel-wrap').style.display=l.length?'':'none';
  document.getElementById('sel-count').textContent=l.length;
  document.getElementById('sel-list').innerHTML=l.map((p,i)=>{
    const c=p._col||{bg:'#f0f0f0',b:'#ccc',t:'#333'};
    return`<div class="sel-item" style="background:${c.bg};border-right-color:${c.b}">
      <div class="sel-num" style="background:${c.b};color:white">${i+1}</div>
      <div class="sel-name" style="color:${c.t}">${p.name}</div>
      <span class="sel-resv">${p.resv}</span>
      ${p.phone?`<a class="wa-btn" href="${waLink(p.phone)}" target="_blank" rel="noopener" title="مراسلة واتساب">${WA_SVG}</a>`:''}
      <button class="rm-btn" onclick="rmPax(${i})">✕</button>
    </div>`;
  }).join('');
}

function saveManifest(){
  readMeta();const all=loadAll();const idx=all.findIndex(m=>m.id===cur.id);
  if(idx>=0)all[idx]=cur;else all.unshift(cur);saveAll(all);
  const t=document.createElement('div');
  t.style.cssText='position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#0d4f3c;color:white;padding:10px 20px;border-radius:10px;font-size:.9rem;font-weight:700;z-index:999;box-shadow:0 4px 14px rgba(0,0,0,.2)';
  t.textContent='✅ تم حفظ البيان';document.body.appendChild(t);setTimeout(()=>t.remove(),2000);
}

const RPP=25;
function printManifest(){
  readMeta();const pax=cur.passengers;
  if(!pax.length){alert('أضف ركاباً أولاً');return}
  // Auto color-by-reservation: alternate booking groups colored / white
  const rc={};let gi=0;
  pax.forEach(p=>{if(p.resv&&!(p.resv in rc)){rc[p.resv]=(gi%2)?'#ffffff':COLORS[(gi>>1)%COLORS.length].bg;gi++}});
  const total=Math.ceil(pax.length/RPP);let out='';
  for(let pg=1;pg<=total;pg++){
    const sl=pax.slice((pg-1)*RPP,pg*RPP);
    const rows=sl.map((p,i)=>`<tr style="background:${rc[p.resv]||p._col?.bg||'white'}">
      <td class="n">${(pg-1)*RPP+i+1}</td><td style="font-weight:600">${p.name}</td>
      <td class="c">${p.resv}</td><td class="c" style="direction:ltr">${p.id}</td>
      <td class="c" style="direction:ltr">${p.phone?`<a href="${waLink(p.phone)}" style="color:inherit;text-decoration:none">${p.phone}</a>`:''}</td><td></td></tr>`).join('');
    out+=`<div class="a4">
      <div class="content-rect">
        <div class="pr-head"><div class="pr-title">🕋 بيان ركاب الباص</div>
          <div class="pr-meta">
            <span><b>رقم البيان:</b> ${cur.id}</span><span><b>رقم الباص:</b> ${cur.bus||'—'}</span>
            <span><b>المشرف:</b> ${cur.driver||'—'}</span><span><b>التاريخ:</b> ${cur.date||'—'}</span>
            <span><b>الإجمالي:</b> ${pax.length} راكب</span>
          </div>
        </div>
        <table class="pr-table"><thead><tr>
          <th style="width:7mm;text-align:center">م</th><th style="width:52mm">الاسم الكامل</th>
          <th style="width:22mm;text-align:center">رقم الحجز</th><th style="width:27mm;text-align:center">رقم الهوية</th>
          <th style="width:27mm;text-align:center">الجوال</th><th>ملاحظات</th>
        </tr></thead><tbody>${rows}</tbody></table>
        <div class="pr-foot"><span>الإجمالي: ${pax.length} راكب</span><span>صفحة ${pg} من ${total}</span></div>
      </div>
    </div>`;
  }
  document.getElementById('print-area').innerHTML=out;setTimeout(()=>window.print(),150);
}

document.getElementById('m-date').value=new Date().toISOString().slice(0,10);
initAuth();
</script>
</body>
</html>'''

def generate(data_file, form_png, title='بيانات الركاب — المحيميد للحج', search_link='index.html', manifests_key='hajj_manifests'):
    """Return the PLAIN manifest HTML (data inline, lock/decrypt placeholders empty).
    build_all.py then injects the encrypted payload + lock screen + theme."""
    with open(data_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    data_js = json.dumps(records, ensure_ascii=False)
    html = HTML.replace('__LOCK_CSS__','').replace('__LOCK_HTML__','').replace('__DECRYPT_JS__','const DATA=__RAW_DATA__;function onDataReady(){}function initAuth(){onDataReady(DATA)}')
    html = html.replace('__RAW_DATA__', data_js)
    html = html.replace('__FORM_BG__', _form_bg(form_png))
    html = html.replace('<title>بيانات الركاب — المحيميد للحج</title>', f'<title>{title}</title>')
    html = html.replace('href="index.html"', f'href="{search_link}"')
    html = html.replace("const LS='hajj_manifests'", f"const LS='{manifests_key}'")
    return html

if __name__ == '__main__':
    BASE = '/Users/m/Documents/est3lam'
    html = generate(f'{BASE}/pilgrims_data.json', f'{BASE}/Form A4.png')
    with open(f'{BASE}/manifest.html','w',encoding='utf-8') as f:
        f.write(html)
    print(f'manifest.html (plain): {len(html)//1024} KB')
