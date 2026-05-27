# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Hajj pilgrim management web app for two companies: **المحيميد** (green theme) and **الرويس** (charcoal/gold theme). It is a fully static site deployed to GitHub Pages at `https://abuesim.github.io/hajj-search/`. All HTML files are self-contained: pilgrim data is AES-GCM encrypted and embedded inline; there is no server.

## Build workflow

### Full update (normal use)
Double-click **`تحديث.command`** — it auto-detects the latest CSV files in `~/Downloads`, runs the pipeline, commits, and pushes.

### Manual steps
```bash
# 1. Parse CSV exports (placed in ~/Downloads as "المحيميد XX.CSV" and "الرويس XX.CSV")
python3 parse_csv.py        # → pilgrims_data.json, ruwais_data.json

# 2. Build all HTML files
python3 build_all.py        # → all *.html, icons, webmanifests, sw.js, hajj_site.zip
```

Python dependencies: `cryptography`, `Pillow`

## Architecture

### Data pipeline
```
CSV files (~/Downloads)
  └─ parse_csv.py  →  pilgrims_data.json / ruwais_data.json
       └─ build_all.py  →  all HTML + assets
```

`build_all.py` is the core: it reads JSON data, encrypts it with PBKDF2+AES-GCM, and generates every HTML page as a Python f-string template. Each page embeds the encrypted payload directly in its `<script>`.

### Page inventory (generated per campaign)

| File | Purpose | Auth |
|------|---------|------|
| `muhaimeed.html` / `ruwais.html` | Pilgrim text search + inline barcode scan | PIN `112233` |
| `manifest.html` / `ruwais-manifest.html` | Full passenger list (supervisor view) | PIN `111222` |
| `scan.html` / `ruwais-scan.html` | Dedicated continuous barcode scan page | PIN `112233` |
| `dashboard.html` / `ruwais-dashboard.html` | Stats + bus drill-down | PIN `999000` |
| `supervisors.html` / `ruwais-supervisors.html` | Supervisor directory | PIN `112233` |
| `reports.html` / `ruwais-reports.html` | Complaints tracker | redirects to search if not authed |
| `card.html` / `ruwais-card.html` | Public pilgrim card (no auth, reads `?b=&g=` URL params) | none |
| `index.html` | Entry point / legacy search | PIN `112233` |

### Theming
المحيميد is the native green theme. الرويس is built by calling `apply_theme(html, THEME_RUWAIS)` which replaces a fixed set of hex color values (green → charcoal). When editing styles, edit the محيميد version; the رويس version derives automatically.

### Shared JS snippets (defined in `build_all.py`)
- `CLOUD_JS` — Supabase cloud sync (reports/complaints); data is encrypted client-side before upload
- `WA_JS` — WhatsApp link helper (normalises Saudi numbers to `966…`)
- `LOCK_CSS` / `LOCK_HTML` / `make_decrypt_js()` — 6-digit PIN pad with PBKDF2+AES-GCM decryption via WebCrypto
- `WA_SVG` / `RPT_SVG` / `RPT_CSS` — inline SVG icons and report button styles
- `SWITCH_CSS` / `switcher()` — top campaign-switcher bar

### `gen_manifest.py`
Generates the `manifest.html` template — an interactive passenger list builder where supervisors can compose and print A4 forms. It embeds a letterhead image (`Form A4.png`) as a base64 JPEG.

### PWA
`build_all.py` also generates Kaaba-icon PNGs (`icon-m-*`, `icon-r-*`), `.webmanifest` files, and `sw.js` for offline caching.

### Pilgrim record fields
`name`, `resv` (booking number), `bus`, `id` (national ID digits only), `phone` (normalised to `0XXXXXXXXX`), `mina` (camp location `loc-unit`), `office`, `gender` (`ذكر`/`أنثى`), `city`

### Card URL scheme
`card.html?b=<bus>&g=<base64>` — `g` is a base64-encoded UTF-8 JSON array where index 0 is the main pilgrim (`{name, mina, supervisor, main:true}`) and the rest are companions (`{name, mina, gender}`).

## Key constraints
- `pilgrims_data.json` and `ruwais_data.json` are git-ignored (contain real personal data).
- All HTML is generated — never edit generated `.html` files directly; edit the templates in `build_all.py` or `gen_manifest.py` and rebuild.
- The Supabase key in `build_all.py` is a publishable/anon key; it is intentionally embedded in client HTML.
