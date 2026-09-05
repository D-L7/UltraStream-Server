import os
import sys
import socket
import time
import tempfile
import threading
import subprocess
import mimetypes
from flask import Flask, render_template_string, request, jsonify, send_file
try:
    import qrcode
except Exception:
    qrcode = None

app = Flask(__name__)

# Import core downloader logic safely
try:
    import downloader
    ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file = downloader.find_binaries()
    gpu_encoder, gpu_label = downloader.detect_best_gpu_encoder(ffmpeg_exe_path)
except Exception:
    ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file = None, None, None, None
    gpu_encoder, gpu_label = "libx264", "CPU (Standard Software)"

def get_local_ip():
    """Get PC local IP address on WiFi/LAN"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Mobile Web Application HTML Template (Touch-optimized, Dark theme, Responsive for Android & iPhone)
MOBILE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ألترا ستريم 8K برو - UltraStream 8K Pro 🚀</title>
    <link rel="icon" href="/logo.png" type="image/png">
    <link rel="apple-touch-icon" sizes="180x180" href="/logo.png">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0A0B10">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="UltraStream">
    
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&family=Outfit:wght@400;600;800;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #06070B;
            --card-bg: rgba(15, 17, 28, 0.85);
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-cyan: #00F0FF;
            --accent-purple: #9D00FF;
            --accent-green: #00FF88;
            --accent-gold: #FFB800;
            --text-main: #FFFFFF;
            --text-muted: #94A3B8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Tajawal', 'Outfit', sans-serif;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg-primary);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(157, 0, 255, 0.2) 0%, transparent 45%),
                radial-gradient(circle at 90% 80%, rgba(0, 240, 255, 0.18) 0%, transparent 45%),
                linear-gradient(180deg, #06070B 0%, #0C0E17 100%);
            background-attachment: fixed;
            color: var(--text-main);
            padding: 20px 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 600px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* PWA Install Banner */
        .pwa-banner {
            display: none;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(157, 0, 255, 0.15));
            border: 1px solid var(--accent-cyan);
            border-radius: 16px;
            padding: 12px 16px;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
            animation: bounceIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        @keyframes bounceIn {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .pwa-text {
            font-size: 13px;
            font-weight: 700;
            color: #FFF;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .pwa-btn {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            color: #FFF;
            border: none;
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 12px;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 240, 255, 0.4);
        }

        /* Header */
        .header {
            text-align: center;
            padding: 28px 20px;
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-color);
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
            position: relative;
        }

        .logo-img {
            width: 85px;
            height: 85px;
            border-radius: 24px;
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.5);
            animation: logoGlow 3s ease-in-out infinite alternate;
        }

        @keyframes logoGlow {
            0% { box-shadow: 0 0 20px rgba(0, 240, 255, 0.4); transform: scale(1); }
            100% { box-shadow: 0 0 35px rgba(157, 0, 255, 0.7); transform: scale(1.04); }
        }

        .header h1 {
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(135deg, #FFFFFF 20%, var(--accent-cyan) 60%, var(--accent-purple) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .header p {
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        .platforms-bar {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }

        .platform-pill {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }

        .platform-pill.active {
            background: rgba(0, 240, 255, 0.2);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            font-weight: bold;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
            transform: translateY(-2px);
        }

        /* Status Bar */
        .badge-status {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }

        .badge-status .gpu {
            color: var(--accent-green);
            font-weight: 700;
        }

        .badge-status .aria {
            color: var(--accent-cyan);
            font-weight: 700;
        }

        /* Main Form Card */
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-color);
            border-radius: 28px;
            padding: 26px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-size: 13px;
            font-weight: 700;
            color: #E2E8F0;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        input[type="url"] {
            width: 100%;
            background: rgba(8, 10, 16, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            padding: 15px 105px 15px 15px;
            color: #FFFFFF;
            font-size: 14px;
            outline: none;
            direction: ltr;
            text-align: left;
            transition: all 0.3s ease;
        }

        input[type="url"]:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
            background: rgba(8, 10, 16, 0.95);
        }

        .paste-btn {
            position: absolute;
            left: 8px;
            background: linear-gradient(135deg, var(--accent-purple), #4F00B7);
            color: #FFFFFF;
            border: none;
            border-radius: 12px;
            padding: 9px 16px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(157, 0, 255, 0.4);
            transition: all 0.3s ease;
        }

        .paste-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(157, 0, 255, 0.6);
        }

        select {
            width: 100%;
            background: rgba(8, 10, 16, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            padding: 15px;
            color: #FFFFFF;
            font-size: 13.5px;
            outline: none;
            cursor: pointer;
            transition: all 0.3s ease;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2300F0FF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: left 16px center;
        }

        select:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 18px rgba(0, 240, 255, 0.25);
        }

        select option {
            background: #0E101A;
            color: #FFF;
            padding: 12px;
        }

        /* Live Preview Card */
        .preview-box {
            display: none;
            background: rgba(8, 10, 16, 0.95);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 18px;
            padding: 14px;
            gap: 14px;
            align-items: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.4s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .preview-thumb {
            width: 105px;
            height: 70px;
            border-radius: 12px;
            object-fit: cover;
            background: #000;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }

        .preview-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 4px;
            overflow: hidden;
        }

        .preview-title {
            font-size: 13.5px;
            font-weight: 700;
            color: var(--accent-cyan);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .preview-meta {
            font-size: 11.5px;
            color: var(--text-muted);
        }

        /* Neon Action Button */
        .btn-action {
            width: 100%;
            background: linear-gradient(135deg, #00F0FF 0%, #9D00FF 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 16px;
            padding: 18px;
            font-size: 16px;
            font-weight: 900;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 12px 35px rgba(0, 240, 255, 0.4);
        }

        .btn-action:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 45px rgba(0, 240, 255, 0.6);
        }

        .btn-action:active {
            transform: scale(0.98);
        }

        .btn-action:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Progress Bar */
        .progress-box {
            display: none;
            flex-direction: column;
            gap: 10px;
        }

        .progress-bar-bg {
            background: rgba(8, 10, 16, 0.95);
            height: 12px;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .progress-bar-fill {
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple), var(--accent-green));
            background-size: 200% 100%;
            height: 100%;
            width: 0%;
            transition: width 0.4s ease;
            animation: gradientMove 2s linear infinite;
        }

        @keyframes gradientMove {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }

        .status-text {
            font-size: 12.5px;
            color: var(--accent-green);
            text-align: center;
            font-weight: 700;
        }

        /* Download Link Button */
        .download-link-btn {
            display: none;
            background: linear-gradient(135deg, #00FF88 0%, #00B862 100%);
            color: #000000;
            text-decoration: none;
            padding: 18px;
            border-radius: 16px;
            text-align: center;
            font-weight: 900;
            font-size: 16px;
            box-shadow: 0 12px 35px rgba(0, 255, 136, 0.5);
            animation: pulseGlow 2s infinite ease-in-out;
        }

        @keyframes pulseGlow {
            0%, 100% { transform: scale(1); box-shadow: 0 12px 35px rgba(0, 255, 136, 0.5); }
            50% { transform: scale(1.02); box-shadow: 0 16px 45px rgba(0, 255, 136, 0.8); }
        }

        @media (max-width: 480px) {
            body { padding: 12px 10px; }
            .header h1 { font-size: 24px; }
            .logo-img { width: 70px; height: 70px; }
            .card { padding: 20px 15px; }
            input[type="url"] { font-size: 13.5px; padding-right: 95px; }
            .btn-action { font-size: 15px; padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- PWA Installation Banner -->
        <div id="pwaBanner" class="pwa-banner">
            <div class="pwa-text">📱 مثبت كـ تطبيق للجوال والكمبيوتر</div>
            <button class="pwa-btn" onclick="installPWA()">تثبيت الآن</button>
        </div>

        <!-- Header -->
        <div class="header">
            <img src="/logo.png" alt="UltraStream Logo" class="logo-img">
            <h1>UltraStream 8K Pro</h1>
            <p>منصة التحميل والمعالجة الذكية فائقة السرعة للجوال والكمبيوتر</p>
            
            <div class="platforms-bar">
                <div class="platform-pill" id="pill-yt">▶️ YouTube</div>
                <div class="platform-pill" id="pill-tt">🎵 TikTok</div>
                <div class="platform-pill" id="pill-ig">📸 Instagram</div>
                <div class="platform-pill" id="pill-tw">🪶 X / Twitter</div>
                <div class="platform-pill" id="pill-fb">📘 Facebook</div>
            </div>
        </div>

        <!-- Status Bar -->
        <div class="badge-status">
            <span class="gpu">⚡ تسريع كرت الشاشة: مفعّل تلقائياً</span>
            <span class="aria">🚀 16-Thread Engine</span>
        </div>

        <!-- Form Card -->
        <div class="card">
            <div class="form-group">
                <label>🔗 أدخل رابط الفيديو المراد تحويله وتنزيله:</label>
                <div class="input-wrapper">
                    <input type="url" id="videoUrl" placeholder="https://..." required autocomplete="off">
                    <button class="paste-btn" onclick="pasteClipboard()">📋 لصق</button>
                </div>
            </div>

            <!-- Live Video Preview -->
            <div id="previewBox" class="preview-box">
                <img id="previewThumb" class="preview-thumb" src="" alt="Thumbnail">
                <div class="preview-info">
                    <div id="previewTitle" class="preview-title">جاري جلب معلومات الفيديو...</div>
                    <div id="previewMeta" class="preview-meta">👤 القناة: -- | ⏱️ المدة: --</div>
                </div>
            </div>

            <div class="form-group">
                <label>⚙️ اختر جودة العرض ونمط المعالجة المطلوبة:</label>
                <select id="qualitySelect">
                    <option value="1">1. 🌟 أعلى جودة فائقة تلقائياً (Auto 8K / 4K MP4)</option>
                    <option value="2">2. 🎬 8K Ultra HD الأصلي (4320p MP4)</option>
                    <option value="3">3. 🚀 رفع إجباري إلى 8K MP4 (عبر كرت الشاشة)</option>
                    <option value="4">4. ⚡ مضاعفة الإطارات إلى 60FPS MP4 (FFmpeg MCI)</option>
                    <option value="5">5. 🎬 4K Ultra HD (2160p MP4)</option>
                    <option value="6">6. 🎬 2K Quad HD (1440p MP4)</option>
                    <option value="7">7. 🎬 Full HD (1080p MP4)</option>
                    <option value="8">8. 🎬 HD (720p MP4)</option>
                    <option value="9">9. 🎬 SD (480p / 360p MP4)</option>
                    <option value="10">10. 🎵 تحويل إلى صوت فقط MP3 (أعلى نقاء 320kbps)</option>
                </select>
            </div>

            <button id="downloadBtn" class="btn-action" onclick="startDownload()">
                <span>⬇️ بدء التحميل الفائق الآن</span>
            </button>

            <!-- Progress Bar Box -->
            <div id="progressBox" class="progress-box">
                <div class="progress-bar-bg">
                    <div id="progressBarFill" class="progress-bar-fill"></div>
                </div>
                <div id="statusText" class="status-text">⏳ جاري الاتصال بالسيرفر ومعالجة الفيديو...</div>
            </div>

            <!-- Final Direct Download Button -->
            <a id="downloadFileBtn" class="download-link-btn" href="#" download>
                🎉 اضغط هنا لتنزيل وتنسيق الملف مباشرة في جهازك
            </a>
        </div>
    </div>

    <script>
        // PWA Install Prompt Event
        let deferredPrompt = null;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('pwaBanner').style.display = 'flex';
        });

        async function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    document.getElementById('pwaBanner').style.display = 'none';
                }
                deferredPrompt = null;
            } else {
                alert('لتثبيت التطبيق على الجوال:\n- في الآيفون (Safari): اضغط زر المشاركة 📤 ثم اختر "إضافة إلى الشاشة الرئيسية ➕".\n- في الأندرويد (Chrome): اضغط على القائمة 💬 ثم اختر "تثبيت التطبيق".');
            }
        }

        // Auto platform highlight
        document.getElementById('videoUrl').addEventListener('input', function() {
            const url = this.value.toLowerCase();
            document.querySelectorAll('.platform-pill').forEach(p => p.classList.remove('active'));
            
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                document.getElementById('pill-yt').classList.add('active');
            } else if (url.includes('tiktok.com')) {
                document.getElementById('pill-tt').classList.add('active');
            } else if (url.includes('instagram.com')) {
                document.getElementById('pill-ig').classList.add('active');
            } else if (url.includes('twitter.com') || url.includes('x.com')) {
                document.getElementById('pill-tw').classList.add('active');
            } else if (url.includes('facebook.com') || url.includes('fb.watch')) {
                document.getElementById('pill-fb').classList.add('active');
            }
            fetchPreview();
        });

        async function pasteClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    const input = document.getElementById('videoUrl');
                    input.value = text;
                    input.dispatchEvent(new Event('input'));
                }
            } catch (err) {
                alert('يرجى لصق الرابط يدويًا داخل الخانة.');
            }
        }

        let previewTimer = null;
        function fetchPreview() {
            clearTimeout(previewTimer);
            const url = document.getElementById('videoUrl').value.trim();
            if (!url || url.length < 12) {
                document.getElementById('previewBox').style.display = 'none';
                return;
            }

            previewTimer = setTimeout(async () => {
                const box = document.getElementById('previewBox');
                box.style.display = 'flex';
                document.getElementById('previewTitle').innerText = '🔍 جاري تحليل معلومات الفيديو...';
                document.getElementById('previewMeta').innerText = 'يرجى الانتظار...';

                try {
                    const res = await fetch('/api/preview?url=' + encodeURIComponent(url));
                    const data = await res.json();
                    if (data.success) {
                        document.getElementById('previewTitle').innerText = data.title;
                        document.getElementById('previewMeta').innerText = '👤 الناشر: ' + data.uploader + ' | ⏱️ المدة: ' + data.duration;
                        if (data.thumbnail) {
                            document.getElementById('previewThumb').src = data.thumbnail;
                        }
                    }
                } catch (e) {}
            }, 500);
        }

        async function startDownload() {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url) {
                alert('يرجى إدخال رابط فيديو صحيح أولاً!');
                return;
            }

            const quality = document.getElementById('qualitySelect').value;
            const btn = document.getElementById('downloadBtn');
            const progressBox = document.getElementById('progressBox');
            const fileBtn = document.getElementById('downloadFileBtn');

            btn.disabled = true;
            btn.innerHTML = '<span>⚡ جاري المعالجة والتحميل...</span>';
            progressBox.style.display = 'flex';
            document.getElementById('progressBarFill').style.width = '35%';
            fileBtn.style.display = 'none';

            try {
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, quality: quality })
                });

                const data = await res.json();
                if (data.success) {
                    document.getElementById('progressBarFill').style.width = '100%';
                    document.getElementById('statusText').innerText = '✅ اكتملت المعالجة بنجاح!';
                    fileBtn.href = data.file_url;
                    fileBtn.setAttribute('download', data.filename);
                    fileBtn.innerHTML = '🎉 اضغط هنا لتنزيل الملف مباشرة في جهازك ⬇️';
                    fileBtn.style.display = 'block';
                } else {
                    document.getElementById('statusText').innerText = '❌ خطأ: ' + (data.error || 'فشل التحميل');
                }
            } catch (err) {
                document.getElementById('statusText').innerText = '❌ حدث خطأ أثناء التواصل مع السيرفر.';
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>⬇️ بدء التحميل الفائق الآن</span>';
            }
        }
    </script>
</body>
</html>
"""



@app.route('/')
def index():
    return render_template_string(MOBILE_HTML)

@app.route('/api/preview')
def api_preview():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    try:
        import yt_dlp
        opts = {'quiet': True, 'nocheckcertificate': True}
        if cookies_file:
            opts['cookiefile'] = cookies_file
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration_string', 'N/A'),
                'thumbnail': info.get('thumbnail', '')
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    quality = data.get('quality', '1')

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    try:
        platform_name = downloader.get_platform_folder(url)
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads", platform_name)
        os.makedirs(download_dir, exist_ok=True)

        downloader.download_video(
            url,
            quality,
            ffmpeg_bin_dir,
            ffmpeg_exe_path,
            aria2_path,
            cookies_file,
            gpu_encoder
        )

        files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if not f.startswith('temp_')]
        if not files:
            return jsonify({'success': False, 'error': 'Downloaded file not found.'})

        latest_file = max(files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)

        file_url = f"/download_file/{platform_name}/{filename}"
        return jsonify({
            'success': True,
            'filename': filename,
            'file_url': file_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_file/<platform>/<filename>')
def download_file(platform, filename):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads", platform)
    filepath = os.path.join(folder, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    ext = os.path.splitext(filename)[1].lower()
    if ext == '.mp4':
        mime_type = 'video/mp4'
        safe_filename = f"video_{int(time.time())}.mp4"
    elif ext == '.mp3':
        mime_type = 'audio/mpeg'
        safe_filename = f"audio_{int(time.time())}.mp3"
    elif ext == '.mkv':
        mime_type = 'video/x-matroska'
        safe_filename = f"video_{int(time.time())}.mkv"
    else:
        mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        safe_filename = filename

    response = send_file(
        filepath,
        mimetype=mime_type,
        as_attachment=True,
        download_name=safe_filename
    )
    response.headers["Content-Type"] = mime_type
    response.headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
    return response

@app.route('/logo.png')
def get_app_logo():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
    if os.path.exists(logo_path):
        return send_file(logo_path, mimetype='image/png')
    return "", 404

@app.route('/manifest.json')
def get_manifest():
    return jsonify({
        "name": "UltraStream 8K Pro",
        "short_name": "UltraStream",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0A0B10",
        "theme_color": "#00F0FF",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/logo.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })


def generate_qr_code_file(url):
    """Generate high quality QR code image file safely across all Windows system paths"""
    qr = qrcode.QRCode(version=1, box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Primary safe path in system temp directory to prevent Windows path encoding errors
    temp_qr_path = os.path.join(tempfile.gettempdir(), "mobile_qr.png")
    try:
        with open(temp_qr_path, "wb") as f:
            img.save(f, format="PNG")
        return temp_qr_path
    except Exception:
        pass

    # Fallback to local directory using explicit open handle
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_qr_path = os.path.join(script_dir, "mobile_qr.png")
    try:
        with open(local_qr_path, "wb") as f:
            img.save(f, format="PNG")
        return local_qr_path
    except Exception:
        # Ultimate fallback using tempfile NamedTemporaryFile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img.save(tmp, format="PNG")
            return tmp.name

public_remote_url = None

def start_public_tunnel(port=5000):
    """Start 100% free remote HTTPS tunnel using built-in Windows OpenSSH via localhost.run"""
    global public_remote_url
    try:
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:localhost:{port}", "nokey@localhost.run"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        if proc.stdout is not None:
            for line in iter(proc.stdout.readline, ''):
                if "https://" in line and ".lhr.life" in line:
                    for word in line.split():
                        if word.startswith("https://") and ".lhr.life" in word:
                            public_remote_url = word.strip()
                            break
                if public_remote_url:
                    break
    except Exception:
        pass

def start_server():
    ip = get_local_ip()
    port = 5000
    mobile_url = f"http://{ip}:{port}"
    
    # Start background free remote tunnel
    tunnel_thread = threading.Thread(target=start_public_tunnel, args=(port,), daemon=True)
    tunnel_thread.start()
    time.sleep(2)  # Wait briefly for tunnel link

    active_qr_url = public_remote_url if public_remote_url else mobile_url
    qr_path = generate_qr_code_file(active_qr_url)

    os.system('cls' if os.name == 'nt' else 'clear')
    print("==========================================================================")
    print("      🚀 UltraStream 8K Pro Mobile App / ألترا ستريم 8K برو للجوال      ")
    print("==========================================================================")
    print("\n[+] Scan the QR Code below with your Phone Camera (iPhone / Android):\n")

    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=2)
        qr.add_data(active_qr_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        pass

    print(f"\n🏠 Local WiFi URL (Home): \033[96m\033[1m{mobile_url}\033[0m")
    if public_remote_url:
        print(f"🌍 24/7 Remote Global URL (Anywhere 4G/5G): \033[92m\033[1m{public_remote_url}\033[0m")
    else:
        print(f"🌍 Remote Global Tunnel: Connecting in background...")
    print("==========================================================================")
    
    try:
        if sys.platform == 'win32':
            os.startfile(qr_path)
    except Exception:
        pass

    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start_server()
