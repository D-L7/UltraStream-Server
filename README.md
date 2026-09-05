# UltraStream 8K Pro 🚀 (ألترا ستريم 8K برو)

تطبيق ويب وموبايل احترافي لتحميل الفيديوهات بأعلى جودة (4K/8K) ودعم الدمج التلقائي باستخدام Python, Flask, yt-dlp و FFmpeg.

## 🌟 المميزات
- 🎬 تحميل من جميع مواقع الفيديوهات العالمية (يوتيوب، تيك توك، إنستغرام، تويتر، الخ).
- ⚡ دعم التسريع باستخدام `aria2c` للتحميل فائق السرعة.
- 🎨 واجهة مستخدم عصرية ومتجاوبة للهواتف الذكية والأجهزة المحمولة.
- 🐳 دعم التشغيل والرفع التلقائي عبر Docker / Fly.io / Render.

## 🛠️ التشغيل المحلي (Local Development)
```bash
pip install -r requirements.txt
python mobile_server.py
```

## 🐳 التشغيل باستخدام Docker
```bash
docker build -t ultrastream .
docker run -p 8080:8080 ultrastream
```
