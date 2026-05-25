#!/bin/bash
# ══════════════════════════════════════════
#  تحديث بيانات الحجاج ورفعها إلى GitHub
# ══════════════════════════════════════════

cd "$(dirname "$0")"

echo ""
echo "╔════════════════════════════════╗"
echo "║   تحديث بيانات حجاج يسر مساند  ║"
echo "╚════════════════════════════════╝"
echo ""

# ── 1. ابحث عن آخر ملف CSV في Downloads ──
CSV_M=$(ls -t "/Users/m/Downloads/المحيميد"*.CSV 2>/dev/null | head -1)
CSV_R=$(ls -t "/Users/m/Downloads/الرويس"*.CSV 2>/dev/null | head -1)

if [ -z "$CSV_M" ]; then
  echo "❌ ما في ملف المحيميد في Downloads"
  echo "   المطلوب: المحيميد 01.CSV (أو 02 أو 03...)"
  read -p "اضغط Enter للخروج..."
  exit 1
fi

if [ -z "$CSV_R" ]; then
  echo "❌ ما في ملف الرويس في Downloads"
  echo "   المطلوب: الرويس 01.CSV (أو 02 أو 03...)"
  read -p "اضغط Enter للخروج..."
  exit 1
fi

echo "✅ المحيميد: $(basename "$CSV_M")"
echo "✅ الرويس:   $(basename "$CSV_R")"
echo ""

# ── 2. حدّث مسارات parse_csv.py ──
python3 - <<PYEOF
import re
txt = open('parse_csv.py', encoding='utf-8').read()
txt = re.sub(r"'csv': '/Users/m/Downloads/المحيميد[^']*'",
             f"'csv': '${CSV_M}'", txt)
txt = re.sub(r"'csv': '/Users/m/Downloads/الرويس[^']*'",
             f"'csv': '${CSV_R}'", txt)
open('parse_csv.py', 'w', encoding='utf-8').write(txt)
print("✅ parse_csv.py محدّث")
PYEOF

# ── 3. تحليل البيانات ──
echo "⏳ جاري قراءة البيانات..."
python3 parse_csv.py
if [ $? -ne 0 ]; then
  echo "❌ فشل في قراءة الملفات"
  read -p "اضغط Enter للخروج..."
  exit 1
fi
echo ""

# ── 4. بناء الصفحات ──
echo "⏳ جاري بناء الصفحات..."
python3 build_all.py
if [ $? -ne 0 ]; then
  echo "❌ فشل في بناء الصفحات"
  read -p "اضغط Enter للخروج..."
  exit 1
fi
echo ""

# ── 5. رفع إلى GitHub ──
echo "⏳ جاري الرفع إلى GitHub..."
DATE=$(date '+%Y-%m-%d %H:%M')
M_NAME=$(basename "$CSV_M" .CSV)
R_NAME=$(basename "$CSV_R" .CSV)

git add pilgrims_data.json ruwais_data.json \
        muhaimeed.html manifest.html \
        ruwais.html ruwais-manifest.html \
        ruwais-reports.html reports.html \
        index.html scan.html ruwais-scan.html \
        dashboard.html ruwais-dashboard.html \
        card.html ruwais-card.html \
        app-m.webmanifest app-r.webmanifest \
        sw.js hajj_site.zip parse_csv.py 2>/dev/null

git commit -m "تحديث البيانات — $M_NAME + $R_NAME — $DATE"
if [ $? -ne 0 ]; then
  echo "⚠️  لا يوجد تغييرات جديدة"
  read -p "اضغط Enter للخروج..."
  exit 0
fi

git push
if [ $? -ne 0 ]; then
  echo "❌ فشل الرفع — تحقق من الإنترنت"
  read -p "اضغط Enter للخروج..."
  exit 1
fi

echo ""
echo "╔══════════════════════════════════╗"
echo "║   ✅ تم الرفع بنجاح إلى GitHub   ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "الموقع: https://abuesim.github.io/hajj-search/"
echo ""
read -p "اضغط Enter للإغلاق..."
