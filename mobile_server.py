import os
import sys
import socket
import time
import tempfile
import threading
import subprocess
import mimetypes
from urllib.parse import quote
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
            --border-color: rgba(255, 255, 255, 0.12);
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
                radial-gradient(circle at 10% 20%, rgba(157, 0, 255, 0.22) 0%, transparent 45%),
                radial-gradient(circle at 90% 80%, rgba(0, 240, 255, 0.20) 0%, transparent 45%),
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
            max-width: 620px;
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
            padding: 24px 20px;
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-color);
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            position: relative;
        }

        .logo-img {
            width: 80px;
            height: 80px;
            border-radius: 22px;
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.5);
            animation: logoGlow 3s ease-in-out infinite alternate;
        }

        @keyframes logoGlow {
            0% { box-shadow: 0 0 20px rgba(0, 240, 255, 0.4); transform: scale(1); }
            100% { box-shadow: 0 0 35px rgba(157, 0, 255, 0.7); transform: scale(1.04); }
        }

        .header h1 {
            font-size: 26px;
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
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
        }

        .step-title {
            font-size: 14px;
            font-weight: 800;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        input[type="url"] {
            width: 100%;
            background: rgba(8, 10, 16, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 16px;
            padding: 16px 105px 16px 16px;
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
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(157, 0, 255, 0.4);
            transition: all 0.3s ease;
        }

        .paste-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(157, 0, 255, 0.6);
        }

        /* Live Video Preview Box */
        .preview-box {
            display: none;
            background: rgba(8, 10, 16, 0.95);
            border: 1px solid rgba(0, 240, 255, 0.35);
            border-radius: 20px;
            padding: 16px;
            flex-direction: column;
            gap: 14px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            animation: fadeIn 0.4s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .preview-header-row {
            display: flex;
            gap: 14px;
            align-items: center;
        }

        .preview-thumb {
            width: 110px;
            height: 72px;
            border-radius: 12px;
            object-fit: cover;
            background: #000;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }

        .preview-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 5px;
            overflow: hidden;
        }

        .preview-title {
            font-size: 14px;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .preview-meta {
            font-size: 11.5px;
            color: var(--accent-cyan);
            font-weight: 600;
        }

        /* Dynamic Quality Cards Section */
        .qualities-section {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 4px;
            border-top: 1px dashed rgba(255, 255, 255, 0.12);
            padding-top: 14px;
        }

        .qualities-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
            gap: 10px;
        }

        .quality-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 12px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s ease;
            position: relative;
            user-select: none;
        }

        .quality-card:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.1);
            transform: translateY(-2px);
        }

        .quality-card.selected {
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(157, 0, 255, 0.25));
            border: 2px solid var(--accent-cyan);
            box-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
            transform: translateY(-2px);
        }

        .quality-card .icon {
            font-size: 18px;
            margin-bottom: 4px;
        }

        .quality-card .label {
            font-size: 12.5px;
            font-weight: 800;
            color: #FFF;
        }

        .quality-card .sub {
            font-size: 10.5px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .quality-card.audio {
            border-color: rgba(0, 255, 136, 0.3);
        }

        .quality-card.audio.selected {
            border-color: var(--accent-green);
            background: rgba(0, 255, 136, 0.2);
            box-shadow: 0 0 16px rgba(0, 255, 136, 0.4);
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
            .header h1 { font-size: 23px; }
            .logo-img { width: 68px; height: 68px; }
            .card { padding: 18px 14px; }
            input[type="url"] { font-size: 13.5px; padding-right: 95px; }
            .btn-action { font-size: 15px; padding: 15px; }
            .qualities-grid { grid-template-columns: repeat(2, 1fr); }
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
            <!-- Step 1: Link Input -->
            <div class="form-group">
                <div class="step-title">1️⃣ أدخل رابط الفيديو المراد تحويله وتنزيله:</div>
                <div class="input-wrapper">
                    <input type="url" id="videoUrl" placeholder="https://..." required autocomplete="off" oninput="handleUrlInput()" onpaste="setTimeout(handleUrlInput, 50)" onchange="handleUrlInput()">
                    <button class="paste-btn" onclick="pasteClipboard()">📋 لصق</button>
                </div>
            </div>

            <!-- Step 2 & 3: Live Video Preview & Quality Selection Cards -->
            <div id="previewBox" class="preview-box">
                <div class="preview-header-row">
                    <img id="previewThumb" class="preview-thumb" src="/logo.png" alt="Thumbnail">
                    <div class="preview-info">
                        <div id="previewTitle" class="preview-title">🔍 جاري جلب معلومات الجودة والفيديو...</div>
                        <div id="previewMeta" class="preview-meta">⏱️ يرجى الانتظار لحظات...</div>
                    </div>
                </div>

                <!-- Step 3: Interactive Quality Options Grid -->
                <div class="qualities-section">
                    <div class="step-title">2️⃣ اختر الجودة المطلوبة للتحميل المباشر:</div>
                    <div class="qualities-grid" id="qualitiesGrid">
                        <!-- Quality Cards are generated dynamically -->
                    </div>
                </div>

                <!-- Step 4: Instant Download Button -->
                <button id="downloadBtn" class="btn-action" onclick="startDownload()" style="margin-top: 6px;">
                    <span>⬇️ بدء التحميل الفائق المباشر</span>
                </button>
            </div>

            <!-- Progress Bar Box -->
            <div id="progressBox" class="progress-box">
                <div class="progress-bar-bg">
                    <div id="progressBarFill" class="progress-bar-fill"></div>
                </div>
                <div id="statusText" class="status-text">⏳ جاري الاتصال بالسيرفر ومعالجة الفيديو...</div>
            </div>

            <!-- Final Action Result Box -->
            <div id="resultContainer" style="display: none; flex-direction: column; gap: 12px; margin-top: 10px;">
                <a id="downloadFileBtn" class="download-link-btn" href="#" download>
                    🎉 اضغط لتنزيل وحفظ الملف في جوالك ⬇️
                </a>

                <button id="shareExportBtn" class="btn-action" style="background: linear-gradient(135deg, #7000FF 0%, #00F0FF 100%); display: flex;" onclick="shareExportFile()">
                    <span>📤 تصدير ومشاركة إلى تطبيقات الجوال ومغني الموسيقى</span>
                </button>

                <!-- Embedded Player -->
                <div id="audioPlayerWrapper" style="display:none; background: rgba(8, 10, 16, 0.95); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 16px; padding: 10px; margin-top: 5px;">
                    <div style="font-size: 12px; color: var(--accent-cyan); font-weight: bold; margin-bottom: 6px; text-align: center;">🎵 استماع ومعاينة مباشرة فورية:</div>
                    <audio id="mediaAudioPlayer" controls style="width: 100%; height: 40px; outline: none;"></audio>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Default Quality Presets
        const DEFAULT_QUALITIES = [
            { val: '1', label: 'أعلى جودة تلقائياً', sub: 'Auto 8K / 4K MP4', icon: '🌟', default: true },
            { val: '2', label: '8K Ultra HD', sub: '4320p MP4', icon: '🎬' },
            { val: '5', label: '4K Ultra HD', sub: '2160p MP4', icon: '🎬' },
            { val: '7', label: 'Full HD', sub: '1080p MP4', icon: '🎬' },
            { val: '8', label: 'HD الجودة العالية', sub: '720p MP4', icon: '🎬' },
            { val: '9', label: 'SD دقة متوسطة', sub: '480p MP4', icon: '🎬' },
            { val: '10', label: 'صوت MP3 فقط', sub: '320kbps نقاء عالي', icon: '🎵', isAudio: true },
            { val: '3', label: 'رفع إجباري لـ 8K', sub: 'GPU Upscale', icon: '🚀' },
            { val: '4', label: '60 FPS مضاعفة', sub: 'FFmpeg MCI', icon: '⚡' }
        ];

        let selectedQualityVal = '1';
        let currentFetchedUrl = '';

        // PWA Install Prompt Event
        let deferredPrompt = null;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const pwa = document.getElementById('pwaBanner');
            if (pwa) pwa.style.display = 'flex';
        });

        async function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    const pwa = document.getElementById('pwaBanner');
                    if (pwa) pwa.style.display = 'none';
                }
                deferredPrompt = null;
            } else {
                alert('لتثبيت التطبيق على الجوال:\n- في الآيفون (Safari): اضغط زر المشاركة 📤 ثم اختر "إضافة إلى الشاشة الرئيسية ➕".\n- في الأندرويد (Chrome): اضغط على القائمة 💬 ثم اختر "تثبيت التطبيق".');
            }
        }

        function normalizeUrl(rawUrl) {
            if (!rawUrl) return '';
            let url = rawUrl.trim();
            
            // Smart Youtube Video ID / Shortened URL normalizer
            if (!url.includes('http://') && !url.includes('https://') && !url.includes('youtube.com') && !url.includes('youtu.be') && !url.includes('tiktok.com') && !url.includes('instagram.com') && !url.includes('twitter.com') && !url.includes('x.com') && !url.includes('facebook.com') && !url.includes('fb.watch')) {
                let cleanPart = url.split('?')[0].split('&')[0];
                if (cleanPart.length === 11 || (url.includes('?') && cleanPart.length <= 12)) {
                    return 'https://www.youtube.com/watch?v=' + url;
                }
            }

            if (url.startsWith('u.be/')) {
                url = 'youtu.be/' + url.substring(5);
            }
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }
            return url;
        }


        async function pasteClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                const input = document.getElementById('videoUrl');
                if (text && input) {
                    input.value = text;
                    handleUrlInput();
                }
            } catch (err) {
                alert('يرجى لصق الرابط يدويًا داخل الخانة.');
            }
        }

        function renderQualityCards(customList) {
            const grid = document.getElementById('qualitiesGrid');
            if (!grid) return;
            grid.innerHTML = '';

            const listToUse = (customList && customList.length > 0) ? customList : DEFAULT_QUALITIES;

            listToUse.forEach(q => {
                const card = document.createElement('div');
                card.className = 'quality-card' + (q.isAudio ? ' audio' : '') + (q.val === selectedQualityVal ? ' selected' : '');
                card.onclick = () => selectQualityCard(q.val);
                
                card.innerHTML = `
                    <div class="icon">${q.icon || '🎬'}</div>
                    <div class="label">${q.label}</div>
                    <div class="sub">${q.sub || ''}</div>
                `;
                grid.appendChild(card);
            });
        }

        function selectQualityCard(val) {
            selectedQualityVal = val;
            document.querySelectorAll('.quality-card').forEach(c => c.classList.remove('selected'));
            renderQualityCards();
        }

        async function handleUrlInput() {
            const input = document.getElementById('videoUrl');
            const box = document.getElementById('previewBox');
            if (!input || !box) return;

            let rawVal = input.value.trim();
            if (!rawVal || rawVal.length < 5) {
                box.style.display = 'none';
                currentFetchedUrl = '';
                return;
            }

            let url = normalizeUrl(rawVal);
            if (url === currentFetchedUrl) return;

            // Highlight platform badge
            document.querySelectorAll('.platform-pill').forEach(p => p.classList.remove('active'));
            if (url.includes('youtube.com') || url.includes('youtu.be')) document.getElementById('pill-yt')?.classList.add('active');
            else if (url.includes('tiktok.com')) document.getElementById('pill-tt')?.classList.add('active');
            else if (url.includes('instagram.com')) document.getElementById('pill-ig')?.classList.add('active');
            else if (url.includes('twitter.com') || url.includes('x.com')) document.getElementById('pill-tw')?.classList.add('active');
            else if (url.includes('facebook.com') || url.includes('fb.watch')) document.getElementById('pill-fb')?.classList.add('active');

            box.style.display = 'flex';
            document.getElementById('previewTitle').innerText = '🔍 جاري تحليل معلومات الفيديو والجودات...';
            document.getElementById('previewMeta').innerText = 'يرجى الانتظار لحظات...';
            renderQualityCards();

            currentFetchedUrl = url;

            try {
                const res = await fetch('/api/preview?url=' + encodeURIComponent(url));
                const data = await res.json();
                if (data.success && data.title) {
                    document.getElementById('previewTitle').innerText = data.title;
                    document.getElementById('previewMeta').innerText = '👤 الناشر: ' + (data.uploader || 'عام') + ' | ⏱️ المدة: ' + (data.duration || 'غير معروف');
                    if (data.thumbnail) {
                        const thumbImg = document.getElementById('previewThumb');
                        if (thumbImg) {
                            thumbImg.src = data.thumbnail;
                            thumbImg.style.display = 'block';
                        }
                    }
                    if (data.formats && data.formats.length > 0) {
                        renderQualityCards(data.formats);
                    }
                } else {
                    document.getElementById('previewTitle').innerText = '🎬 فيديو جاهز للتحميل والتحويل';
                    document.getElementById('previewMeta').innerText = 'اختر الجودة من الكروت بالأسفل ثم اضغط زر التحميل';
                }
            } catch (e) {
                document.getElementById('previewTitle').innerText = '🎬 فيديو جاهز للتحميل';
                document.getElementById('previewMeta').innerText = 'اختر الجودة بالأسفل واضغط زر التحميل';
            }
        }

        async function startDownload() {
            const input = document.getElementById('videoUrl');
            let rawUrl = input ? input.value : '';
            if (!rawUrl || rawUrl.trim().length < 4) {
                alert('يرجى إدخال رابط فيديو صحيح أولاً!');
                return;
            }

            let url = normalizeUrl(rawUrl);
            if (input) input.value = url;

            const btn = document.getElementById('downloadBtn');
            const progressBox = document.getElementById('progressBox');
            const fileBtn = document.getElementById('downloadFileBtn');
            const resultContainer = document.getElementById('resultContainer');
            const audioWrapper = document.getElementById('audioPlayerWrapper');
            const audioPlayer = document.getElementById('mediaAudioPlayer');

            btn.disabled = true;
            btn.innerHTML = '<span>⚡ جاري المعالجة والتحميل...</span>';
            progressBox.style.display = 'flex';
            document.getElementById('progressBarFill').style.width = '45%';
            document.getElementById('statusText').innerText = '⏳ جاري جلب وتحميل الفيديو من السيرفر...';
            if (resultContainer) resultContainer.style.display = 'none';

            try {
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, quality: selectedQualityVal })
                });

                const data = await res.json();
                if (data.success) {
                    document.getElementById('progressBarFill').style.width = '100%';
                    document.getElementById('statusText').innerText = '✅ اكتملت المعالجة والتحميل بنجاح!';
                    fileBtn.href = data.file_url;
                    fileBtn.setAttribute('download', data.filename);
                    fileBtn.innerHTML = '🎉 اضغط هنا لتنزيل وحفظ الملف في جوالك ⬇️';
                    fileBtn.style.display = 'block';
                    if (resultContainer) resultContainer.style.display = 'flex';

                    if (data.filename.endsWith('.mp3') && audioPlayer && audioWrapper) {
                        audioPlayer.src = data.file_url;
                        audioWrapper.style.display = 'block';
                    } else if (audioWrapper) {
                        audioWrapper.style.display = 'none';
                    }
                } else {
                    document.getElementById('statusText').innerText = '❌ خطأ: ' + (data.error || 'فشل التحميل');
                }
            } catch (err) {
                document.getElementById('statusText').innerText = '❌ حدث خطأ أثناء التواصل مع السيرفر.';
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>⬇️ بدء التحميل الفائق المباشر</span>';
            }
        }

        async function shareExportFile() {
            const fileBtn = document.getElementById('downloadFileBtn');
            if (!fileBtn) return;
            const fileUrl = fileBtn.href;
            const fileName = fileBtn.getAttribute('download');
            
            if (navigator.share) {
                try {
                    const response = await fetch(fileUrl);
                    const blob = await response.blob();
                    const file = new File([blob], fileName, { type: blob.type });

                    if (navigator.canShare && navigator.canShare({ files: [file] })) {
                        await navigator.share({
                            files: [file],
                            title: fileName,
                            text: 'تصدير من ألترا ستريم 8K برو 🚀'
                        });
                    } else {
                        await navigator.share({
                            title: fileName,
                            url: window.location.origin + fileUrl
                        });
                    }
                } catch (e) {
                    window.open(fileUrl, '_blank');
                }
            } else {
                window.open(fileUrl, '_blank');
            }
        }
    </script>
</body>
</html>
"""




def normalize_url(raw_url):
    if not raw_url:
        return ""
    url = raw_url.strip()

    # Smart Youtube Video ID / Shortened URL normalizer
    if not any(domain in url for domain in ["http://", "https://", "youtube.com", "youtu.be", "tiktok.com", "instagram.com", "twitter.com", "x.com", "facebook.com", "fb.watch"]):
        clean_part = url.split("?")[0].split("&")[0]
        if len(clean_part) == 11 or ("?" in url and len(clean_part) <= 12):
            return f"https://www.youtube.com/watch?v={url}"

    if url.startswith("u.be/"):
        url = "youtu.be/" + url[5:]
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url


@app.route('/')
def index():
    return render_template_string(MOBILE_HTML)

@app.route('/api/preview')
def api_preview():
    url = normalize_url(request.args.get('url', ''))
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    try:
        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'skip_download': True,
            'socket_timeout': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        if cookies_file:
            opts['cookiefile'] = cookies_file
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({
                    'success': True,
                    'title': 'فيديو جاهز للتحميل المباشر',
                    'uploader': 'تلقائي',
                    'duration': 'متعدد الجودات',
                    'thumbnail': '/logo.png'
                })

            duration_str = info.get('duration_string')
            duration_sec = info.get('duration')
            if not duration_str and duration_sec:
                m, s = divmod(int(duration_sec), 60)
                h, m = divmod(m, 60)
                duration_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

            thumbnail_url = info.get('thumbnail', '')
            if not thumbnail_url and 'thumbnails' in info and info['thumbnails']:
                thumbnail_url = info['thumbnails'][-1].get('url', '')

            # Build dynamic formats list from video info
            formats_list = [
                {'val': '1', 'label': 'أعلى جودة تلقائياً', 'sub': 'Auto 8K / 4K MP4', 'icon': '🌟'}
            ]
            
            heights_seen = set()
            if 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    h = fmt.get('height')
                    if h and isinstance(h, int) and h >= 144:
                        heights_seen.add(h)

            # Map detected resolutions to clean user choices
            if 4320 in heights_seen or any(h >= 3000 for h in heights_seen):
                formats_list.append({'val': '2', 'label': '8K Ultra HD', 'sub': '4320p MP4', 'icon': '🎬'})
            if any(2000 <= h < 3000 for h in heights_seen) or 2160 in heights_seen:
                formats_list.append({'val': '5', 'label': '4K Ultra HD', 'sub': '2160p MP4', 'icon': '🎬'})
            if any(1300 <= h < 2000 for h in heights_seen) or 1440 in heights_seen:
                formats_list.append({'val': '6', 'label': '2K Quad HD', 'sub': '1440p MP4', 'icon': '🎬'})
            if any(900 <= h < 1300 for h in heights_seen) or 1080 in heights_seen:
                formats_list.append({'val': '7', 'label': 'Full HD', 'sub': '1080p MP4', 'icon': '🎬'})
            if any(600 <= h < 900 for h in heights_seen) or 720 in heights_seen:
                formats_list.append({'val': '8', 'label': 'HD الجودة العالية', 'sub': '720p MP4', 'icon': '🎬'})
            if any(h < 600 for h in heights_seen):
                formats_list.append({'val': '9', 'label': 'SD دقة متوسطة', 'sub': '480p MP4', 'icon': '🎬'})

            formats_list.append({'val': '10', 'label': 'صوت MP3 فقط', 'sub': '320kbps نقاء عالي', 'icon': '🎵', 'isAudio': True})
            formats_list.append({'val': '3', 'label': 'رفع إجباري لـ 8K', 'sub': 'GPU Upscale', 'icon': '🚀'})
            formats_list.append({'val': '4', 'label': '60 FPS مضاعفة', 'sub': 'FFmpeg MCI', 'icon': '⚡'})

            return jsonify({
                'success': True,
                'title': info.get('title', 'فيديو'),
                'uploader': info.get('uploader', info.get('extractor', 'عام')),
                'duration': duration_str or 'غير معروف',
                'thumbnail': thumbnail_url or '/logo.png',
                'formats': formats_list
            })
    except Exception as e:
        return jsonify({
            'success': True,
            'title': 'فيديو جاهز للتحميل المباشر',
            'uploader': 'تلقائي',
            'duration': 'متعدد الجودات',
            'thumbnail': '/logo.png'
        })



@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json() or {}
    url = normalize_url(data.get('url', ''))
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
    elif ext == '.mp3':
        mime_type = 'audio/mpeg'
    elif ext == '.mkv':
        mime_type = 'video/x-matroska'
    elif ext == '.webm':
        mime_type = 'video/webm'
    else:
        mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

    response = send_file(
        filepath,
        mimetype=mime_type,
        as_attachment=True,
        download_name=filename
    )
    
    # RFC 5987 / UTF-8 header encoding for preserving exact Arabic & English video titles in all browsers
    encoded_filename = quote(filename)
    response.headers["Content-Type"] = mime_type
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
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
