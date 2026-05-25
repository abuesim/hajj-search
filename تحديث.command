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

# ── 1. تحقق من ملفات CSV ──
CSV_M="/Users/m/Downloads/المحيميد 01.CSV"
CSV_R="/Users/m/Downloads/الرويس 01.CSV"

if [ ! -f "$CSV_M" ]; then
  echo "❌ ملف المحيميد غير موجود:"
  echo "   $CSV_M"
  echo ""
  echo "   ضع الملف في Downloads باسم:  المحيميد 01.CSV"
  echo "   ثم شغّل السكريبت مجدداً"
  read -p "اضغط Enter للخروج..."
  exit 1
fi

if [ ! -f "$CSV_R" ]; then
  echo "❌ ملف الرويس غير موجود:"
  echo "   $CSV_R"
  echo ""
  echo "   ضع الملف في Downloads باسم:  الرويس 01.CSV"
  echo "   ثم شغّل السكريبت مجدداً"
  read -p "اضغط Enter للخروج..."
  exit 1
fi

echo "✅ ملفات CSV موجودة"
echo ""

# ── 2. تحليل البيانات ──
echo "⏳ جاري قراءة البيانات..."
python3 parse_csv.py
if [ $? -ne 0 ]; then
  echo "❌ فشل في قراءة الملفات"
  read -p "اضغط Enter للخروج..."
  exit 1
fi
echo ""

# ── 3. بناء الصفحات ──
echo "⏳ جاري بناء الصفحات..."
python3 build_all.py
if [ $? -ne 0 ]; then
  echo "❌ فشل في بناء الصفحات"
  read -p "اضغط Enter للخروج..."
  exit 1
fi
echo ""

# ── 4. رفع إلى GitHub ──
echo "⏳ جاري الرفع إلى GitHub..."
DATE=$(date '+%Y-%m-%d %H:%M')
git add pilgrims_data.json ruwais_data.json \
        muhaimeed.html manifest.html \
        ruwais.html ruwais-manifest.html \
        ruwais-reports.html reports.html \
        index.html scan.html ruwais-scan.html \
        dashboard.html ruwais-dashboard.html \
        card.html ruwais-card.html \
        app-m.webmanifest app-r.webmanifest \
        sw.js hajj_site.zip 2>/dev/null

git commit -m "تحديث البيانات — $DATE"
if [ $? -ne 0 ]; then
  echo "⚠️  لا يوجد تغييرات جديدة للرفع"
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
