import os
import sys
import threading
import time
import subprocess
import urllib.request
import io
import winsound
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

# Import downloader core functions
import downloader

# Configure CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Comprehensive Dual Language Translation Dictionary
TRANSLATIONS = {
    'ar': {
        'app_title': "ألترا ستريم 8K برو - UltraStream 8K Pro",
        'title': "🚀 UltraStream 8K Pro | ألترا ستريم 8K برو",
        'subtitle': "تحميل الفيديوهات حتي جودة 8K مع معالجة 60FPS والتسريع بكرت الشاشة",
        'gpu_active': "🎮 تسريع كرت الشاشة: {gpu}",
        'aria_active': "🚀 تسريع Aria2 (16 اتصال): مفعّل",
        'aria_inactive': "ℹ️ تسريع Aria2: غير مفعّل",
        'sort_active': "📁 التنظيم الذكي: Downloads/[اسم المنصة]",
        'url_label': "رابط الفيديو (يوتيوب، تيك توك، انستقرام، تويتر، فيسبوك، الخ):",
        'url_placeholder': "الصق رابط الفيديو هنا...",
        'paste': "📋 لصق",
        'clear': "❌ مسح",
        'quality_label': "اختر الجودة ونمط المعالجة المطلوب:",
        'start_download': "⬇️ بدء التحميل الآن",
        'downloading': "⏳ جاري التحميل والمعالجة...",
        'ready': "جاهز للتحميل.",
        'open_folder': "📂 فتح مجلد التحميلات",
        'lang_btn': "🇬🇧 English",
        'completed': "✅ اكتمل التحميل بنجاح!",
        'failed': "❌ فشل التحميل.",
        'warning_url': "يرجى إدخال رابط فيديو صحيح أولاً!",
        'preview_loading': "🔍 جاري جلب معاينة الفيديو والصورة المصغرة...",
        'preview_ready': "✅ تم جلب معاينة الفيديو بنجاح",
        'clipboard_switch': "⚡ رصد الحافظة التلقائي",
        'link_detected': "⚡ تم رصد رابط جديد من الحافظة!",
        'notif_title': "🚀 UltraStream 8K Pro | ألترا ستريم 8K برو",
        'notif_completed': "✅ اكتمل تحميل الفيديو بنجاح وحُفظ في مجلد Downloads!",
        'qualities': [
            "1. 🌟 أعلى جودة فائقة تلقائياً (تصل إلى 8K/4K MP4)",
            "2. 🎬 8K Ultra HD الأصلي (4320p MP4)",
            "3. 🚀 رفع إجباري إلى 8K (7680x4320 عبر HEVC NVENC / CPU)",
            "4. ⚡ مضاعفة الإطارات إلى 60FPS (عبر FFmpeg MCI)",
            "5. 🎬 4K Ultra HD (2160p MP4)",
            "6. 🎬 2K Quad HD (1440p MP4)",
            "7. 🎬 Full HD (1080p MP4)",
            "8. 🎬 HD (720p MP4)",
            "9. 🎬 SD (480p / 360p MP4)",
            "10. 🎵 صوت فقط MP3 (أعلى جودة صوتية 320kbps)",
        ]
    },
    'en': {
        'app_title': "UltraStream 8K Pro - Video Downloader",
        'title': "🚀 UltraStream 8K Pro | Video Downloader",
        'subtitle': "Download videos up to 8K, 60FPS Frame Interpolation & GPU Acceleration",
        'gpu_active': "🎮 GPU Acceleration: {gpu}",
        'aria_active': "🚀 Aria2 16-Threads: Active",
        'aria_inactive': "ℹ️ Aria2: Inactive",
        'sort_active': "📁 Auto-Sorting: Downloads/[Platform]",
        'url_label': "Video URL (YouTube, TikTok, Instagram, Twitter/X, Facebook, etc.):",
        'url_placeholder': "Paste your video link here...",
        'paste': "📋 Paste",
        'clear': "❌ Clear",
        'quality_label': "Select Quality & Processing Mode:",
        'start_download': "⬇️ START DOWNLOAD NOW",
        'downloading': "⏳ DOWNLOADING...",
        'ready': "Ready for download.",
        'open_folder': "📂 Open Downloads Folder",
        'lang_btn': "🇸🇦 العربية",
        'completed': "✅ Download Completed Successfully!",
        'failed': "❌ Download Failed.",
        'warning_url': "Please enter a valid video URL first!",
        'preview_loading': "🔍 Fetching thumbnail & video preview...",
        'preview_ready': "✅ Preview loaded successfully",
        'clipboard_switch': "⚡ Auto-Clipboard Monitor",
        'link_detected': "⚡ New video link detected from Clipboard!",
        'notif_title': "🚀 UltraStream 8K Pro",
        'notif_completed': "✅ Download completed! File saved in Downloads folder.",
        'qualities': [
            "1. 🌟 Best Quality Available (Auto 8K / 4K MP4)",
            "2. 🎬 8K Ultra HD Native (4320p MP4)",
            "3. 🚀 Forced Upscale Video to 8K (7680x4320 via HEVC NVENC / CPU)",
            "4. ⚡ Frame Interpolation to 60FPS (via FFmpeg MCI)",
            "5. 🎬 4K Ultra HD (2160p MP4)",
            "6. 🎬 2K Quad HD (1440p MP4)",
            "7. 🎬 Full HD (1080p MP4)",
            "8. 🎬 HD (720p MP4)",
            "9. 🎬 SD (480p / 360p MP4)",
            "10. 🎵 Audio Only MP3 (Highest Quality 320kbps)",
        ]
    }
}

def send_windows_notification(title, message):
    """Play Windows completion sound chime & trigger Toast Notification"""
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    try:
        ps_cmd = f'''
        [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = "{title}"
        $notification.BalloonTipText = "{message}"
        $notification.Visible = $True
        $notification.ShowBalloonTip(4000)
        '''
        subprocess.Popen(["powershell", "-Command", ps_cmd], creationflags=0x08000000)
    except Exception:
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Current language state ('ar' or 'en')
        self.lang = 'ar'
        self.last_clipboard_url = ""
        self.current_preview_url = ""

        # Detect paths and GPU
        self.ffmpeg_bin_dir, self.ffmpeg_exe_path, self.aria2_path, self.cookies_file = downloader.find_binaries()
        self.gpu_encoder, self.gpu_label = downloader.detect_best_gpu_encoder(self.ffmpeg_exe_path)

        # Window Config
        self.title(TRANSLATIONS[self.lang]['app_title'])
        self.geometry("860x780")
        self.minsize(800, 680)

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        # 1. Header Title, Language Switcher & Clipboard Toggle
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=TRANSLATIONS[self.lang]['title'],
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00ADB5"
        )
        self.title_label.pack(side="left", anchor="w")

        self.btn_lang = ctk.CTkButton(
            self.header_frame,
            text=TRANSLATIONS[self.lang]['lang_btn'],
            width=100,
            height=32,
            fg_color="#393E46",
            hover_color="#222831",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_language
        )
        self.btn_lang.pack(side="right", anchor="e", padx=(10, 0))

        self.clipboard_switch_var = tk.BooleanVar(value=True)
        self.clipboard_switch = ctk.CTkSwitch(
            self.header_frame,
            text=TRANSLATIONS[self.lang]['clipboard_switch'],
            variable=self.clipboard_switch_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            progress_color="#00ADB5"
        )
        self.clipboard_switch.pack(side="right", anchor="e")

        self.subtitle_label = ctk.CTkLabel(
            self,
            text=TRANSLATIONS[self.lang]['subtitle'],
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        # 2. Status Badges Frame
        self.badges_frame = ctk.CTkFrame(self, fg_color="#1E1E2A", corner_radius=10)
        self.badges_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        gpu_text = TRANSLATIONS[self.lang]['gpu_active'].format(gpu=self.gpu_label)
        self.gpu_badge = ctk.CTkLabel(self.badges_frame, text=gpu_text, text_color="#00FFCC", font=ctk.CTkFont(size=11, weight="bold"))
        self.gpu_badge.pack(side="left", padx=12, pady=6)

        aria_text = TRANSLATIONS[self.lang]['aria_active'] if self.aria2_path else TRANSLATIONS[self.lang]['aria_inactive']
        self.aria_badge = ctk.CTkLabel(self.badges_frame, text=aria_text, text_color="#39A7FF", font=ctk.CTkFont(size=11, weight="bold"))
        self.aria_badge.pack(side="left", padx=12, pady=6)

        sort_text = TRANSLATIONS[self.lang]['sort_active']
        self.sort_badge = ctk.CTkLabel(self.badges_frame, text=sort_text, text_color="#FFB84C", font=ctk.CTkFont(size=11, weight="bold"))
        self.sort_badge.pack(side="left", padx=12, pady=6)

        # 3. URL Entry Section
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.url_label = ctk.CTkLabel(self.url_frame, text=TRANSLATIONS[self.lang]['url_label'], font=ctk.CTkFont(size=13, weight="bold"))
        self.url_label.pack(anchor="w", pady=(0, 4))

        self.url_input_frame = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        self.url_input_frame.pack(fill="x")

        self.url_entry = ctk.CTkEntry(self.url_input_frame, placeholder_text=TRANSLATIONS[self.lang]['url_placeholder'], height=40, font=ctk.CTkFont(size=13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<KeyRelease>", self.on_url_key_release)

        self.btn_paste = ctk.CTkButton(self.url_input_frame, text=TRANSLATIONS[self.lang]['paste'], width=85, height=40, command=self.paste_url, fg_color="#393E46", hover_color="#222831")
        self.btn_paste.pack(side="left", padx=(0, 5))

        self.btn_clear = ctk.CTkButton(self.url_input_frame, text=TRANSLATIONS[self.lang]['clear'], width=75, height=40, command=self.clear_url, fg_color="#393E46", hover_color="#222831")
        self.btn_clear.pack(side="left")

        # 4. Live Thumbnail & Video Metadata Preview Frame
        self.preview_frame = ctk.CTkFrame(self, fg_color="#181824", corner_radius=10, height=110)
        self.preview_frame.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        self.preview_frame.pack_propagate(False)

        # Left: Thumbnail Image Label
        self.thumb_label = ctk.CTkLabel(self.preview_frame, text="🎬", width=140, height=90, fg_color="#10101A", corner_radius=8, font=ctk.CTkFont(size=28))
        self.thumb_label.pack(side="left", padx=10, pady=10)

        # Right: Video Info (Title, Channel, Duration)
        self.preview_info_box = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self.preview_info_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.preview_title_label = ctk.CTkLabel(
            self.preview_info_box,
            text="[Paste a video link to load thumbnail & details]",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00ADB5",
            anchor="w",
            justify="left"
        )
        self.preview_title_label.pack(anchor="w", fill="x")

        self.preview_details_label = ctk.CTkLabel(
            self.preview_info_box,
            text="👤 Channel: -- | ⏱️ Duration: -- | 📌 Resolution: Auto",
            font=ctk.CTkFont(size=11),
            text_color="#AAAAAA",
            anchor="w",
            justify="left"
        )
        self.preview_details_label.pack(anchor="w", fill="x", pady=(5, 0))

        # 5. Options Section (Quality Dropdown)
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.quality_label = ctk.CTkLabel(self.options_frame, text=TRANSLATIONS[self.lang]['quality_label'], font=ctk.CTkFont(size=13, weight="bold"))
        self.quality_label.pack(anchor="w", pady=(0, 4))

        self.quality_dropdown = ctk.CTkOptionMenu(self.options_frame, values=TRANSLATIONS[self.lang]['qualities'], height=36, font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12))
        self.quality_dropdown.pack(fill="x")
        self.quality_dropdown.set(TRANSLATIONS[self.lang]['qualities'][0])

        # 6. Download Button
        self.btn_download = ctk.CTkButton(
            self,
            text=TRANSLATIONS[self.lang]['start_download'],
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            fg_color="#00ADB5",
            hover_color="#008B92",
            command=self.start_download_thread
        )
        self.btn_download.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # 7. Progress and Terminal Console Box
        self.console_frame = ctk.CTkFrame(self, fg_color="#181824", corner_radius=10)
        self.console_frame.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(2, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.console_frame, height=12, progress_color="#00ADB5")
        self.progress_bar.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.console_frame, text=TRANSLATIONS[self.lang]['ready'], font=ctk.CTkFont(size=12, weight="bold"), text_color="#00FFCC")
        self.status_label.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="w")

        self.textbox = ctk.CTkTextbox(self.console_frame, font=ctk.CTkFont(family="Consolas", size=11), text_color="#DDDDDD", fg_color="#10101A")
        self.textbox.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="nsew")

        # 8. Bottom Bar (Folder Button)
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=8, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.btn_open_folder = ctk.CTkButton(self.bottom_frame, text=TRANSLATIONS[self.lang]['open_folder'], width=220, height=34, fg_color="#393E46", hover_color="#222831", command=self.open_downloads_folder)
        self.btn_open_folder.pack(side="right")

        # Start background Clipboard Monitoring thread
        threading.Thread(target=self.clipboard_monitor_loop, daemon=True).start()

    def toggle_language(self):
        """Toggle between Arabic (ar) and English (en) instantly"""
        self.lang = 'en' if self.lang == 'ar' else 'ar'
        t = TRANSLATIONS[self.lang]

        self.title(t['app_title'])
        self.title_label.configure(text=t['title'])
        self.subtitle_label.configure(text=t['subtitle'])
        self.btn_lang.configure(text=t['lang_btn'])
        self.clipboard_switch.configure(text=t['clipboard_switch'])

        gpu_text = t['gpu_active'].format(gpu=self.gpu_label)
        self.gpu_badge.configure(text=gpu_text)
        aria_text = t['aria_active'] if self.aria2_path else t['aria_inactive']
        self.aria_badge.configure(text=aria_text)
        self.sort_badge.configure(text=t['sort_active'])

        self.url_label.configure(text=t['url_label'])
        self.url_entry.configure(placeholder_text=t['url_placeholder'])
        self.btn_paste.configure(text=t['paste'])
        self.btn_clear.configure(text=t['clear'])

        self.quality_label.configure(text=t['quality_label'])
        current_idx = 0
        try:
            current_val = self.quality_dropdown.get()
            current_idx = int(current_val.split(".")[0]) - 1
        except Exception:
            pass
        
        self.quality_dropdown.configure(values=t['qualities'])
        if 0 <= current_idx < len(t['qualities']):
            self.quality_dropdown.set(t['qualities'][current_idx])

        self.btn_download.configure(text=t['start_download'])
        self.status_label.configure(text=t['ready'])
        self.btn_open_folder.configure(text=t['open_folder'])

    def on_url_key_release(self, event=None):
        url = self.url_entry.get().strip()
        if url and url != self.current_preview_url and len(url) > 12:
            self.current_preview_url = url
            threading.Thread(target=self.fetch_preview, args=(url,), daemon=True).start()

    def paste_url(self):
        try:
            clipboard_text = self.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_text.strip())
            self.on_url_key_release()
        except Exception:
            pass

    def clear_url(self):
        self.url_entry.delete(0, tk.END)
        self.current_preview_url = ""
        self.preview_title_label.configure(text="[Paste a video link to load thumbnail & details]")
        self.preview_details_label.configure(text="👤 Channel: -- | ⏱️ Duration: -- | 📌 Resolution: Auto")
        self.thumb_label.configure(image="", text="🎬")

    def fetch_preview(self, url):
        """Fetch video thumbnail image and metadata asynchronously"""
        t = TRANSLATIONS[self.lang]
        self.after(0, lambda: self.preview_title_label.configure(text=t['preview_loading']))

        try:
            opts = {'quiet': True, 'nocheckcertificate': True}
            if self.cookies_file:
                opts['cookiefile'] = self.cookies_file

            import yt_dlp
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video Title')
                uploader = info.get('uploader', 'Unknown Channel')
                duration = info.get('duration_string', 'N/A')
                thumbnail_url = info.get('thumbnail', None)

                def update_preview_ui():
                    self.preview_title_label.configure(text=title[:70] + ("..." if len(title) > 70 else ""))
                    self.preview_details_label.configure(text=f"👤 Channel: {uploader} | ⏱️ Duration: {duration}")

                self.after(0, update_preview_ui)

                if thumbnail_url:
                    try:
                        req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            img_bytes = resp.read()
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 75))
                        self.after(0, lambda: self.thumb_label.configure(image=ctk_img, text=""))
                    except Exception:
                        pass
        except Exception:
            pass

    def clipboard_monitor_loop(self):
        """Background thread monitoring clipboard for new video URLs"""
        while True:
            try:
                if self.clipboard_switch_var.get():
                    clip = self.clipboard_get().strip()
                    if clip and clip != self.last_clipboard_url:
                        clip_lower = clip.lower()
                        valid_domains = ['youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com', 'twitter.com', 'x.com', 'facebook.com', 'fb.watch', 'twitch.tv']
                        if any(domain in clip_lower for domain in valid_domains):
                            self.last_clipboard_url = clip
                            def update_clip():
                                self.url_entry.delete(0, tk.END)
                                self.url_entry.insert(0, clip)
                                t = TRANSLATIONS[self.lang]
                                self.status_label.configure(text=t['link_detected'])
                                self.on_url_key_release()
                            self.after(0, update_clip)
            except Exception:
                pass
            time.sleep(1.2)

    def log(self, text):
        self.textbox.insert(tk.END, text + "\n")
        self.textbox.see(tk.END)

    def open_downloads_folder(self):
        downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        if sys.platform == 'win32':
            os.startfile(downloads_dir)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', downloads_dir])
        else:
            subprocess.Popen(['xdg-open', downloads_dir])

    def gui_progress_callback(self, prog_val, status_msg):
        def update_ui():
            if isinstance(prog_val, (int, float)):
                self.progress_bar.set(min(max(prog_val, 0.0), 1.0))
            self.status_label.configure(text=status_msg)
            self.log(status_msg)
        self.after(0, update_ui)

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        t = TRANSLATIONS[self.lang]
        if not url:
            messagebox.showwarning("Warning", t['warning_url'])
            return

        selected_quality_text = self.quality_dropdown.get()
        quality_choice = selected_quality_text.split(".")[0].strip()

        self.btn_download.configure(state="disabled", text=t['downloading'])
        self.progress_bar.set(0.05)
        self.status_label.configure(text=t['downloading'])

        threading.Thread(target=self.run_download, args=(url, quality_choice), daemon=True).start()

    def run_download(self, url, quality_choice):
        t = TRANSLATIONS[self.lang]
        self.log(f"\n[+] Link: {url}")
        self.log(f"[+] Option: {quality_choice}")

        try:
            downloader.download_video(
                url,
                quality_choice,
                self.ffmpeg_bin_dir,
                self.ffmpeg_exe_path,
                self.aria2_path,
                self.cookies_file,
                self.gpu_encoder,
                gui_callback=self.gui_progress_callback
            )
            self.log(f"[{t['completed']}]")
            self.after(0, lambda: self.status_label.configure(text=t['completed']))
            self.after(0, lambda: self.progress_bar.set(1.0))
            
            # Send Windows System Sound & Toast Notification
            send_windows_notification(t['notif_title'], t['notif_completed'])
        except Exception as e:
            self.log(f"[❌] {t['failed']}: {e}")
            self.after(0, lambda: self.status_label.configure(text=t['failed']))
        finally:
            self.after(0, lambda: self.btn_download.configure(state="normal", text=t['start_download']))

if __name__ == "__main__":
    app = App()
    app.mainloop()
