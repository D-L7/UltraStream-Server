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
    <link rel="apple-touch-icon" href="/logo.png">
    <link rel="manifest" href="data:application/json,{ %22name%22:%22UltraStream 8K Pro%22, %22short_name%22:%22UltraStream%22, %22display%22:%22standalone%22, %22theme_color%22:%22%230F0F17%22 }">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Tajawal', sans-serif;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: #0F0F17;
            color: #FFFFFF;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: 100%;
            max-width: 480px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .header {
            text-align: center;
            padding: 15px 0;
            border-bottom: 1px solid #1F1F30;
        }

        .header h1 {
            font-size: 22px;
            font-weight: 900;
            color: #00ADB5;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .header p {
            font-size: 12px;
            color: #8888AA;
            margin-top: 4px;
        }

        .badge-status {
            background: #181826;
            border: 1px solid #28283E;
            border-radius: 12px;
            padding: 10px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }

        .badge-status .gpu {
            color: #00FFCC;
            font-weight: bold;
        }

        .badge-status .aria {
            color: #39A7FF;
        }

        .card {
            background: #181826;
            border: 1px solid #242438;
            border-radius: 16px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }

        label {
            font-size: 13px;
            font-weight: 700;
            color: #EEEEEE;
        }

        .input-group {
            display: flex;
            gap: 8px;
        }

        input[type="url"] {
            flex: 1;
            background: #10101A;
            border: 1px solid #2A2A40;
            border-radius: 10px;
            padding: 12px;
            color: #FFF;
            font-size: 14px;
            outline: none;
            direction: ltr;
            text-align: left;
        }

        input[type="url"]:focus {
            border-color: #00ADB5;
        }

        .btn {
            background: #00ADB5;
            color: #FFF;
            border: none;
            border-radius: 10px;
            padding: 12px 18px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: 0.2s;
        }

        .btn:active {
            transform: scale(0.97);
            opacity: 0.9;
        }

        .btn-secondary {
            background: #2D3238;
        }

        select {
            background: #10101A;
            border: 1px solid #2A2A40;
            border-radius: 10px;
            padding: 12px;
            color: #FFF;
            font-size: 14px;
            outline: none;
            width: 100%;
        }

        .preview-box {
            display: none;
            background: #10101A;
            border-radius: 12px;
            padding: 12px;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .preview-thumb {
            width: 90px;
            height: 60px;
            border-radius: 8px;
            object-fit: cover;
            background: #000;
        }

        .preview-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 4px;
            overflow: hidden;
        }

        .preview-title {
            font-size: 12px;
            font-weight: bold;
            color: #00ADB5;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .preview-meta {
            font-size: 11px;
            color: #8888AA;
        }

        .progress-box {
            display: none;
            flex-direction: column;
            gap: 8px;
        }

        .progress-bar-bg {
            background: #10101A;
            height: 10px;
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar-fill {
            background: #00ADB5;
            height: 100%;
            width: 0%;
            transition: width 0.3s;
        }

        .status-text {
            font-size: 12px;
            color: #00FFCC;
            text-align: center;
        }

        .download-link-btn {
            display: none;
            background: #28a745;
            color: white;
            text-decoration: none;
            padding: 14px;
            border-radius: 12px;
            text-align: center;
            font-weight: bold;
            font-size: 15px;
            margin-top: 10px;
            box-shadow: 0 4px 15px rgba(40,167,69,0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="/logo.png" alt="UltraStream Logo" style="width: 80px; height: 80px; border-radius: 20px; margin-bottom: 10px; box-shadow: 0 4px 20px rgba(0,173,181,0.5);">
            <h1>UltraStream 8K Pro</h1>
            <p>ألترا ستريم 8K برو - أداة التحميل والتنزيل الذكية للجوال</p>
        </div>

        <div class="badge-status">
            <span class="gpu">🎮 تسريع كرت الشاشة: مفعّل</span>
            <span class="aria">🚀 16-Thread Speed</span>
        </div>

        <div class="card">
            <label>🔗 أدخل رابط الفيديو (يوتيوب، تيك توك، انستقرام، تويتر):</label>
            <div class="input-group">
                <input type="url" id="videoUrl" placeholder="https://..." required>
                <button class="btn btn-secondary" onclick="pasteClipboard()">📋 لصق</button>
            </div>

            <div id="previewBox" class="preview-box" style="display:none;">
                <img id="previewThumb" class="preview-thumb" src="" alt="Thumbnail">
                <div class="preview-info">
                    <div id="previewTitle" class="preview-title">جاري التحميل...</div>
                    <div id="previewMeta" class="preview-meta">👤 القناة: -- | ⏱️ المدة: --</div>
                </div>
            </div>

            <label>⚙️ اختر الجودة ونمط المعالجة:</label>
            <select id="qualitySelect">
                <option value="1">1. 🌟 أعلى جودة فائقة تلقائياً (Auto 8K / 4K MP4)</option>
                <option value="2">2. 🎬 8K Ultra HD الأصلي (4320p MP4)</option>
                <option value="3">3. 🚀 رفع إجباري إلى 8K MP4 (عبر كرت الشاشة)</option>
                <option value="4">4. ⚡ مضاعفة الإطارات إلى 60FPS MP4 (عبر FFmpeg MCI)</option>
                <option value="5">5. 🎬 4K Ultra HD (2160p MP4)</option>
                <option value="6">6. 🎬 2K Quad HD (1440p MP4)</option>
                <option value="7">7. 🎬 Full HD (1080p MP4)</option>
                <option value="8">8. 🎬 HD (720p MP4)</option>
                <option value="9">9. 🎬 SD (480p / 360p MP4)</option>
                <option value="10">10. 🎵 صوت فقط MP3 (أعلى جودة 320kbps)</option>
            </select>

            <button id="downloadBtn" class="btn" onclick="startDownload()">⬇️ بدء التحميل لجوالك الآن</button>

            <div id="progressBox" class="progress-box">
                <div class="progress-bar-bg">
                    <div id="progressBarFill" class="progress-bar-fill"></div>
                </div>
                <div id="statusText" class="status-text">⏳ جاري معالجة التحميل...</div>
            </div>

            <a id="downloadFileBtn" class="download-link-btn" href="#" download>🎉 اضغط هنا لتنزيل الملف في جوالك مباشرة</a>
        </div>
    </div>

    <script>
        async function pasteClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    document.getElementById('videoUrl').value = text;
                    fetchPreview();
                }
            } catch (err) {
                alert('يرجى لصق الرابط يدويًا داخل الخانة.');
            }
        }

        document.getElementById('videoUrl').addEventListener('input', fetchPreview);

        async function fetchPreview() {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url || url.length < 12) return;

            const box = document.getElementById('previewBox');
            box.style.display = 'flex';
            document.getElementById('previewTitle').innerText = '🔍 جاري جلب المعلومات...';
            document.getElementById('previewMeta').innerText = 'يرجى الانتظار...';

            try {
                const res = await fetch('/api/preview?url=' + encodeURIComponent(url));
                const data = await res.json();
                if (data.success) {
                    document.getElementById('previewTitle').innerText = data.title;
                    document.getElementById('previewMeta').innerText = '👤 القناة: ' + data.uploader + ' | ⏱️ المدة: ' + data.duration;
                    if (data.thumbnail) {
                        document.getElementById('previewThumb').src = data.thumbnail;
                    }
                }
            } catch (e) {}
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
            btn.innerText = '⏳ جاري المعالجة والتحميل...';
            progressBox.style.display = 'flex';
            document.getElementById('progressBarFill').style.width = '30%';
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
                    fileBtn.innerText = '🎉 اضغط هنا لتنزيل فيديو الـ MP4 مباشرة في جوالك';
                    fileBtn.style.display = 'block';
                } else {
                    document.getElementById('statusText').innerText = '❌ خطأ: ' + (data.error || 'فشل التحميل');
                }
            } catch (err) {
                document.getElementById('statusText').innerText = '❌ حدث خطأ أثناء التواصل مع السيرفر.';
            } finally {
                btn.disabled = false;
                btn.innerText = '⬇️ بدء التحميل لجوالك الآن';
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
