"""
Parse pilgrim CSV files → JSON for build_all.py
Usage: python3 parse_csv.py
"""
import csv, io, json, re

BASE = '/Users/m/Documents/est3lam'

CAMPAIGNS = [
    {
        'csv': '/Users/m/Downloads/المحيميد 02.CSV',
        'out': f'{BASE}/pilgrims_data.json',
    },
    {
        'csv': '/Users/m/Downloads/الرويس 02.CSV',
        'out': f'{BASE}/ruwais_data.json',
    },
]

# Column indices (0-based)
COL_OFFICE   = 0   # المكتب
COL_CAT      = 1   # الفئة (رجل/امرأة)
COL_BUS      = 4   # الحافلة  e.g. "008 {07} {16:50}"
COL_RESV     = 7   # الحجز
COL_NAME     = 9   # اسم الحاج كاملا
COL_GENDER   = 20  # الجنس (ذكر/أنثى)
COL_ID       = 27  # رقم الهوية
COL_CITY     = 28  # مدينة السكن
COL_PHONE    = 32  # الجوال
COL_UNIT     = 35  # الصالة/الوحدة  (مقعد الحافلة رقم الوحدة)
COL_LOC      = 36  # الموقع  (منى مخيم)
COL_DELETED  = 57  # محذوف

def normalize_phone(ph):
    n = re.sub(r'\D', '', ph or '')
    if not n:
        return ''
    if n.startswith('00966'):
        n = '0' + n[5:]
    elif n.startswith('966') and len(n) > 9:
        n = '0' + n[3:]
    if not n.startswith('0'):
        n = '0' + n
    return n

def parse_bus(raw):
    """'008 {07} {16:50}' → '8', '' → ''"""
    if not raw or not raw.strip():
        return ''
    m = re.match(r'^0*(\d+)', raw.strip())
    return m.group(1) if m else raw.strip()

def parse_mina(unit, loc):
    u = (unit or '').strip()
    l = (loc or '').strip()
    if l and u:
        return f'{l}-{u}'
    if u:
        return u
    return ''

def read_csv(path):
    with open(path, 'rb') as f:
        raw = f.read()
    # UTF-32 LE BOM: FF FE 00 00
    if raw[:4] == b'\xff\xfe\x00\x00':
        text = raw.decode('utf-32-le').lstrip('﻿')
    elif raw[:2] == b'\xff\xfe':
        text = raw.decode('utf-16-le').lstrip('﻿')
    else:
        text = raw.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(text), delimiter='\t')
    return list(reader)

def safe(row, col):
    try:
        return row[col].strip()
    except IndexError:
        return ''

for c in CAMPAIGNS:
    rows = read_csv(c['csv'])
    # find header row (has 'رقم الهوية' or 'الحجز')
    hdr_idx = None
    for i, row in enumerate(rows):
        if any('الحجز' in cell or 'الهوية' in cell for cell in row):
            hdr_idx = i
            break
    if hdr_idx is None:
        print(f"WARNING: header not found in {c['csv']}")
        hdr_idx = 3

    data = []
    for row in rows[hdr_idx + 1:]:
        if len(row) < 10:
            continue
        if safe(row, COL_DELETED) == 'نعم':
            continue
        name = safe(row, COL_NAME)
        if not name:
            continue
        resv = safe(row, COL_RESV)
        bus  = parse_bus(safe(row, COL_BUS))
        pid  = re.sub(r'\D', '', safe(row, COL_ID))
        phone = normalize_phone(safe(row, COL_PHONE))
        mina  = parse_mina(safe(row, COL_UNIT), safe(row, COL_LOC))
        office = safe(row, COL_OFFICE)
        gender = safe(row, COL_GENDER)   # ذكر / أنثى
        city   = safe(row, COL_CITY)
        rec = {'name': name, 'resv': resv, 'bus': bus, 'id': pid,
               'phone': phone, 'mina': mina}
        if office:
            rec['office'] = office
        if gender:
            rec['gender'] = gender
        if city:
            rec['city'] = city
        data.append(rec)

    with open(c['out'], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✅ {c['out']}: {len(data)} records")
