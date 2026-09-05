import os
import sys
import subprocess
import shutil
import time
import io
import contextlib

# Ensure UTF-8 output in Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import yt_dlp safely
try:
    import yt_dlp
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"])
        import yt_dlp
    except Exception:
        yt_dlp = None

# Colors for Terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Enable ANSI colors in Windows CMD
if sys.platform == "win32":
    os.system("")

@contextlib.contextmanager
def silence_output():
    """Silence stdout and stderr temporarily to suppress noisy yt-dlp error logs during retries"""
    old_err, old_out = sys.stderr, sys.stdout
    sys.stderr = io.StringIO()
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = old_err
        sys.stdout = old_out

def find_binaries():
    """Find local or system ffmpeg and aria2c paths"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check FFmpeg
    ffmpeg_exe = os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe")
    ffmpeg_dir_local = os.path.join(base_dir, "ffmpeg", "bin")
    
    if os.path.exists(ffmpeg_exe):
        ffmpeg_bin_dir = ffmpeg_dir_local
        ffmpeg_exe_path = ffmpeg_exe
    elif shutil.which("ffmpeg"):
        ffmpeg_exe_path = shutil.which("ffmpeg")
        ffmpeg_bin_dir = os.path.dirname(ffmpeg_exe_path)
    else:
        ffmpeg_bin_dir = None
        ffmpeg_exe_path = None

    # Check aria2c
    aria2_local = os.path.join(base_dir, "aria2c", "aria2c.exe")
    if os.path.exists(aria2_local):
        aria2_path = aria2_local
    elif shutil.which("aria2c"):
        aria2_path = shutil.which("aria2c")
    else:
        aria2_path = None

    # Check for local cookies.txt file
    local_cookies = os.path.join(base_dir, "cookies.txt")
    cookies_file = local_cookies if os.path.exists(local_cookies) else None

    return ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file

def detect_best_gpu_encoder(ffmpeg_exe_path):
    """Detect available GPU Hardware Acceleration encoder (NVENC > AMF > QSV > CPU)"""
    if not ffmpeg_exe_path:
        return "libx264", "CPU (Standard Software)"

    encoders_to_test = [
        ("h264_nvenc", "⚡ NVIDIA NVENC GPU Acceleration"),
        ("h264_amf", "⚡ AMD AMF GPU Acceleration"),
        ("h264_qsv", "⚡ Intel QuickSync GPU Acceleration"),
    ]

    for encoder, label in encoders_to_test:
        cmd = [
            ffmpeg_exe_path,
            "-f", "lavfi",
            "-i", "color=c=black:s=256x256:d=0.1",
            "-c:v", encoder,
            "-f", "null",
            "-"
        ]
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            if p.returncode == 0:
                return encoder, label
        except Exception:
            continue

    return "libx264", "CPU (Standard Software)"

def get_platform_folder(url):
    """Smart platform organization folder detector"""
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'YouTube'
    elif 'tiktok.com' in url_lower:
        return 'TikTok'
    elif 'instagram.com' in url_lower:
        return 'Instagram'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'Twitter'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'Facebook'
    elif 'twitch.tv' in url_lower:
        return 'Twitch'
    else:
        return 'Other'

def print_banner(ffmpeg_exe_path, aria2_path, cookies_file, gpu_label):
    """Print clean banner with status"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("==========================================================================")
    print("      🚀 UltraStream 8K Pro / ألترا ستريم 8K برو - أداة التحميل الذكية      ")
    print("==========================================================================")
    print(f"{Colors.ENDC}")
    print(f"{Colors.YELLOW}Supports: YouTube, TikTok, Instagram, Twitter/X, Facebook, Twitch, etc.{Colors.ENDC}\n")

    if ffmpeg_exe_path:
        print(f"{Colors.GREEN}✓ FFmpeg Processor: ENABLED (Auto-merging MP4, 8K Upscaling & 60FPS Interpolation){Colors.ENDC}")
        print(f"{Colors.GREEN}🎮 Hardware Acceleration: {gpu_label}{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️ FFmpeg not found (Fallback mode enabled){Colors.ENDC}")

    if aria2_path:
        print(f"{Colors.GREEN}🚀 Aria2 Accelerator: ENABLED (16 Parallel Thread Speed){Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}ℹ️ Aria2 Accelerator: Not found (Using standard downloader){Colors.ENDC}")

    if cookies_file:
        print(f"{Colors.GREEN}🔑 Local Cookies File: ACTIVE (cookies.txt loaded){Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}ℹ️ Cookies: Smart Silent Mode (Auto-authenticates if video requires login){Colors.ENDC}")

    print(f"{Colors.CYAN}📁 Format Output: Videos saved as .MP4 | Audio saved as .MP3{Colors.ENDC}")
    print(f"{Colors.CYAN}📁 Smart Organization: Files sorted automatically into Downloads/[Platform]{Colors.ENDC}")
    print("-" * 74)

def get_format_option(choice):
    """Map user quality choice to yt-dlp format selector"""
    formats = {
        "1": ("Best Quality Available (Auto 8K / 4K MP4 with FFmpeg)", "bestvideo+bestaudio/best"),
        "2": ("8K Ultra HD Native (4320p MP4)", "bestvideo[height<=4320]+bestaudio/best[height<=4320]/best"),
        "3": ("🚀 Forced Upscale Video to 8K MP4 (7680x4320 via HEVC NVENC / CPU)", "forced_8k_upscale"),
        "4": ("⚡ Frame Interpolation to 60FPS MP4 (minterpolate mi_mode=mci via GPU/CPU)", "forced_60fps_interpolation"),
        "5": ("4K Ultra HD (2160p MP4)", "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best"),
        "6": ("2K Quad HD (1440p MP4)", "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best"),
        "7": ("Full HD (1080p MP4)", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"),
        "8": ("HD (720p MP4)", "bestvideo[height<=720]+bestaudio/best[height<=720]/best"),
        "9": ("SD (480p / 360p MP4)", "bestvideo[height<=480]+bestaudio/best[height<=480]/best"),
        "10": ("Audio Only MP3 (320kbps Highest Quality)", "bestaudio/best"),
        "11": ("Manual Format Code Selection", "custom")
    }
    return formats.get(choice, formats["1"])

def list_available_formats(url, ydl_opts_base):
    """List available formats for the given URL"""
    print(f"\n{Colors.CYAN}🔍 Analyzing video link and formats...{Colors.ENDC}")
    opts = ydl_opts_base.copy()
    opts['quiet'] = True
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            print("\n" + "-"*80)
            print(f"{'Format ID':<12} | {'Ext':<8} | {'Resolution':<18} | {'Bitrate':<12} | {'Description'}")
            print("-" * 80)
            for fmt in formats:
                fmt_id = fmt.get('format_id', 'N/A')
                ext = fmt.get('ext', 'N/A')
                res = fmt.get('resolution', f"{fmt.get('width', '')}x{fmt.get('height', '')}")
                if res == 'x' or not res:
                    res = fmt.get('format_note', 'audio only' if fmt.get('vcodec') == 'none' else 'N/A')
                tbr = f"{fmt.get('tbr', 0):.1f}k" if fmt.get('tbr') else 'N/A'
                note = fmt.get('format_note', '')
                vcodec = fmt.get('vcodec', '')
                acodec = fmt.get('acodec', '')
                desc = f"v:{vcodec} | a:{acodec} ({note})"
                print(f"{fmt_id:<12} | {ext:<8} | {res:<18} | {tbr:<12} | {desc[:30]}")
            print("-" * 80)
            custom_code = input(f"\n{Colors.YELLOW}Enter format code or combination (e.g., 137+140): {Colors.ENDC}").strip()
            return custom_code if custom_code else "bestvideo+bestaudio/best"
    except Exception as e:
        print(f"{Colors.RED}[!] Could not list formats: {e}{Colors.ENDC}")
        return "bestvideo+bestaudio/best"

def progress_hook(d, callback=None):
    """Callback for download progress with optional GUI progress update"""
    if d['status'] == 'downloading':
        percent_str = d.get('_percent_str', '').strip()
        speed_str = d.get('_speed_str', '').strip()
        eta_str = d.get('_eta_str', '').strip()
        downloaded_str = d.get('_downloaded_bytes_str', '').strip()
        total_str = d.get('_total_bytes_str', d.get('_total_bytes_estimate_str', '')).strip()

        msg = f"\r{Colors.GREEN}⬇️ Downloading: {percent_str} | Size: {downloaded_str}/{total_str} | Speed: {speed_str} | ETA: {eta_str}{Colors.ENDC}".ljust(95)
        sys.stdout.write(msg)
        sys.stdout.flush()

        if callback:
            try:
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 1))
                prog = downloaded_bytes / total_bytes if total_bytes else 0
                callback(prog, f"{percent_str} | {downloaded_str}/{total_str} | {speed_str} | ETA: {eta_str}")
            except Exception:
                pass
    elif d['status'] == 'finished':
        print(f"\n{Colors.GREEN}✅ Download finished! Processing file...{Colors.ENDC}")
        if callback:
            callback(1.0, "✅ Download finished! Processing file...")

def forced_8k_upscale_ffmpeg(temp_input_file, final_output_file, ffmpeg_exe_path, gpu_encoder, progress_callback=None):
    """Upscale video file forcefully to 7680x4320 (8K MP4) via HEVC NVENC for GPU acceleration with automatic CPU fallback"""
    print(f"\n{Colors.CYAN}⚙️ Starting forced UltraStream 8K MP4 Upscaling to 7680x4320...{Colors.ENDC}")
    print(f"{Colors.YELLOW}Note: Audio stream is preserved (-c:a copy) for maximum processing speed.{Colors.ENDC}")

    encoder_candidates = []
    if "nvenc" in gpu_encoder.lower():
        encoder_candidates = [("hevc_nvenc", ["-preset", "p1"]), ("libx264", ["-preset", "superfast"])]
    elif "amf" in gpu_encoder.lower():
        encoder_candidates = [("hevc_amf", []), ("libx264", ["-preset", "superfast"])]
    elif "qsv" in gpu_encoder.lower():
        encoder_candidates = [("hevc_qsv", []), ("libx264", ["-preset", "superfast"])]
    else:
        encoder_candidates = [("libx264", ["-preset", "superfast"])]

    for enc_name, enc_opts in encoder_candidates:
        cmd = [
            ffmpeg_exe_path,
            "-y",
            "-i", temp_input_file,
            "-vf", "scale=7680:4320:flags=bicubic",
            "-c:v", enc_name,
        ] + enc_opts + [
            "-c:a", "copy",
            final_output_file
        ]

        try:
            print(f"{Colors.BLUE}🎮 Attempting 8K Encoding with [{enc_name.upper()}]...{Colors.ENDC}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='replace')
            last_update = 0
            for line in process.stdout:
                now = time.time()
                if now - last_update >= 0.2:
                    pairs = {}
                    for token in line.replace('\r', ' ').split():
                        if '=' in token:
                            parts = token.split('=', 1)
                            if len(parts) == 2:
                                pairs[parts[0]] = parts[1]
                    if 'frame' in pairs or 'time' in pairs:
                        frame = pairs.get('frame', '0')
                        fps = pairs.get('fps', '0')
                        time_val = pairs.get('time', '00:00:00')
                        speed = pairs.get('speed', '1x')
                        status_str = f"🚀 UltraStream 8K [{enc_name.upper()}] Rendering: frame={frame} | fps={fps} | time={time_val} | speed={speed}"
                        msg = f"\r{Colors.GREEN}{status_str}{Colors.ENDC}".ljust(95)
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                        if progress_callback:
                            progress_callback(status_str)
                        last_update = now
            process.wait()
            
            if process.returncode == 0:
                print(f"\n{Colors.GREEN}✅ Forced 8K MP4 Upscale Completed Successfully with [{enc_name.upper()}]!{Colors.ENDC}")
                return True
            else:
                print(f"\n{Colors.YELLOW}⚠️ Encoder [{enc_name.upper()}] returned code {process.returncode}. Trying fallback encoder...{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.YELLOW}⚠️ Exception on [{enc_name.upper()}]: {e}. Trying fallback...{Colors.ENDC}")

    return False

def frame_interpolation_60fps_ffmpeg(temp_input_file, final_output_file, ffmpeg_exe_path, gpu_encoder, progress_callback=None):
    """Interpolate video frame rate to 60FPS MP4 using FFmpeg minterpolate filter with GPU/CPU fallback"""
    print(f"\n{Colors.CYAN}⚙️ Starting UltraStream 60FPS Frame Interpolation MP4 (minterpolate mi_mode=mci)...{Colors.ENDC}")
    print(f"{Colors.YELLOW}Note: Motion Compensated Interpolation creates smooth 60fps frames while preserving original audio (-c:a copy).{Colors.ENDC}")

    encoder_candidates = [
        (gpu_encoder, ["-preset", "p1"] if "nvenc" in gpu_encoder.lower() else []),
        ("libx264", ["-preset", "superfast"])
    ]

    for enc_name, enc_opts in encoder_candidates:
        cmd = [
            ffmpeg_exe_path,
            "-y",
            "-i", temp_input_file,
            "-vf", "minterpolate=fps=60:mi_mode=mci",
            "-c:v", enc_name,
        ] + enc_opts + [
            "-c:a", "copy",
            final_output_file
        ]

        try:
            print(f"{Colors.BLUE}🎮 Attempting 60FPS Frame Interpolation with [{enc_name.upper()}]...{Colors.ENDC}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='replace')
            last_update = 0
            for line in process.stdout:
                now = time.time()
                if now - last_update >= 0.2:
                    pairs = {}
                    for token in line.replace('\r', ' ').split():
                        if '=' in token:
                            parts = token.split('=', 1)
                            if len(parts) == 2:
                                pairs[parts[0]] = parts[1]
                    if 'frame' in pairs or 'time' in pairs:
                        frame = pairs.get('frame', '0')
                        fps = pairs.get('fps', '0')
                        time_val = pairs.get('time', '00:00:00')
                        speed = pairs.get('speed', '1x')
                        status_str = f"🚀 UltraStream 60FPS [{enc_name.upper()}] Rendering: frame={frame} | fps={fps} | time={time_val} | speed={speed}"
                        msg = f"\r{Colors.GREEN}{status_str}{Colors.ENDC}".ljust(95)
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                        if progress_callback:
                            progress_callback(status_str)
                        last_update = now
            process.wait()
            
            if process.returncode == 0:
                print(f"\n{Colors.GREEN}✅ 60FPS Frame Interpolation Completed Successfully with [{enc_name.upper()}]!{Colors.ENDC}")
                return True
            else:
                print(f"\n{Colors.YELLOW}⚠️ Encoder [{enc_name.upper()}] returned code {process.returncode}. Trying fallback encoder...{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.YELLOW}⚠️ Exception on [{enc_name.upper()}]: {e}. Trying fallback...{Colors.ENDC}")

    return False

def download_video(url, quality_choice, ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file, gpu_encoder, gui_callback=None):
    """Main download logic saving directly into Downloads/[Platform] folder as MP4 or MP3"""
    platform_name = get_platform_folder(url)
    download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads", platform_name)
    os.makedirs(download_dir, exist_ok=True)

    is_forced_8k = (quality_choice == "3")
    is_60fps_interpolation = (quality_choice == "4")
    is_audio_mp3 = (quality_choice == "10")
    requires_post_processing = is_forced_8k or is_60fps_interpolation
    
    # Configure output template
    if requires_post_processing:
        temp_filename = f"temp_{int(time.time())}.mp4"
        temp_filepath = os.path.join(download_dir, temp_filename)
        outtmpl = temp_filepath
    elif is_audio_mp3:
        outtmpl = os.path.join(download_dir, '%(title)s.%(ext)s')
    else:
        outtmpl = os.path.join(download_dir, '%(title)s [%(resolution)s].%(ext)s')

    def local_hook(d):
        progress_hook(d, callback=gui_callback)

    ydl_opts = {
        'outtmpl': outtmpl,
        'progress_hooks': [local_hook],
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    # Set local cookies.txt if exists
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file

    # Set FFmpeg location
    if ffmpeg_bin_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_bin_dir

    # Set Aria2 multi-threaded downloader if available
    if aria2_path:
        ydl_opts['external_downloader'] = aria2_path
        ydl_opts['external_downloader_args'] = {
            'aria2c': [
                '-j', '16',
                '-x', '16',
                '-s', '16',
                '-k', '1M',
                '--min-split-size=1M',
                '--disable-ipv6=true',
                '--allow-overwrite=true',
                '--auto-file-renaming=false'
            ]
        }

    # Set quality/format
    quality_label, format_spec = get_format_option(quality_choice)
    
    if is_audio_mp3:
        # MP3 audio mode (320kbps MP3)
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        ]


    elif quality_choice == "11":
        custom_format = list_available_formats(url, ydl_opts)
        ydl_opts['format'] = custom_format
        ydl_opts['merge_output_format'] = 'mp4'
    elif requires_post_processing:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    else:
        ydl_opts['format'] = format_spec
        ydl_opts['merge_output_format'] = 'mp4'

    print(f"\n{Colors.CYAN}📌 Selected Quality: {quality_label}{Colors.ENDC}")
    print(f"{Colors.YELLOW}📂 Save Folder: Downloads/{platform_name}{Colors.ENDC}")

    video_title = "Video"
    # Fetch title & info first
    try:
        print(f"{Colors.BLUE}🔍 Fetching video details...{Colors.ENDC}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Video')
            video_title = "".join(c for c in video_title if c.isalnum() or c in " -_()[]").strip()
            duration = info.get('duration_string', 'N/A')
            uploader = info.get('uploader', 'Unknown')
            print(f"{Colors.BOLD}🎬 Title: {video_title}{Colors.ENDC}")
            print(f"👤 Channel: {uploader} | ⏱️ Duration: {duration}\n")
    except Exception:
        print(f"{Colors.YELLOW}[!] Starting download directly...{Colors.ENDC}\n")

    # Helper execution wrapper
    def execute_download(current_opts):
        with yt_dlp.YoutubeDL(current_opts) as ydl:
            ydl.download([url])

    # Start Download with automatic aria2 fallback to native downloader
    try:
        try:
            execute_download(ydl_opts)
        except Exception as first_err:
            err_msg = str(first_err)
            if 'aria2c' in err_msg.lower() and 'external_downloader' in ydl_opts:
                print(f"\n{Colors.YELLOW}⚠️ Aria2 network issue detected. Falling back to native high-speed downloader...{Colors.ENDC}")
                fallback_opts = ydl_opts.copy()
                fallback_opts.pop('external_downloader', None)
                fallback_opts.pop('external_downloader_args', None)
                execute_download(fallback_opts)
            else:
                raise first_err

        if is_forced_8k:
            if not ffmpeg_exe_path:
                print(f"{Colors.RED}❌ Error: FFmpeg is required for Forced 8K Upscaling!{Colors.ENDC}")
                return
            
            final_8k_filename = f"[FORCED_8K] {video_title}.mp4"
            final_8k_filepath = os.path.join(download_dir, final_8k_filename)
            
            def render_cb(msg):
                if gui_callback:
                    gui_callback(0.85, msg)

            success = forced_8k_upscale_ffmpeg(temp_filepath, final_8k_filepath, ffmpeg_exe_path, gpu_encoder, progress_callback=render_cb)
            
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                    print(f"{Colors.CYAN}🧹 Temporary file removed: {temp_filename}{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Could not remove temp file: {e}{Colors.ENDC}")
                    
            if success:
                print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 UltraStream Forced 8K MP4 Video Created Successfully! Saved in Downloads/{platform_name}/{final_8k_filename}{Colors.ENDC}\n")

        elif is_60fps_interpolation:
            if not ffmpeg_exe_path:
                print(f"{Colors.RED}❌ Error: FFmpeg is required for 60FPS Frame Interpolation!{Colors.ENDC}")
                return
            
            final_60fps_filename = f"[60FPS_MCI] {video_title}.mp4"
            final_60fps_filepath = os.path.join(download_dir, final_60fps_filename)
            
            def render_cb(msg):
                if gui_callback:
                    gui_callback(0.85, msg)

            success = frame_interpolation_60fps_ffmpeg(temp_filepath, final_60fps_filepath, ffmpeg_exe_path, gpu_encoder, progress_callback=render_cb)
            
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                    print(f"{Colors.CYAN}🧹 Temporary file removed: {temp_filename}{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Could not remove temp file: {e}{Colors.ENDC}")
                    
            if success:
                print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 UltraStream 60FPS Interpolated MP4 Video Created Successfully! Saved in Downloads/{platform_name}/{final_60fps_filename}{Colors.ENDC}\n")

        elif is_audio_mp3:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 UltraStream MP3 Audio Downloaded Successfully! Saved in Downloads/{platform_name}/{Colors.ENDC}\n")

        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 UltraStream MP4 Video Downloaded Successfully! Saved in Downloads/{platform_name}/{Colors.ENDC}\n")
            
    except Exception as e:
        err_msg = str(e)
        if any(keyword in err_msg.lower() for keyword in ['log in', 'cookie', 'rehydration', 'age restricted', 'comfortable for some audiences']):
            print(f"\n{Colors.YELLOW}🔑 Restricted/Age-gated video detected. Retrying with Silent Browser Authentication...{Colors.ENDC}")
            fallback_browsers = ['firefox', 'chrome', 'edge', 'brave', 'opera']
            download_success = False
            for browser in fallback_browsers:
                try:
                    retry_opts = ydl_opts.copy()
                    retry_opts['cookiesfrombrowser'] = (browser,)
                    retry_opts['quiet'] = True
                    retry_opts['no_warnings'] = True
                    with silence_output():
                        execute_download(retry_opts)
                    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Download successful using '{browser.upper()}' browser cookies!{Colors.ENDC}\n")
                    download_success = True
                    break
                except Exception:
                    continue
            
            if not download_success:
                print(f"\n{Colors.RED}❌ Download error: Could not access restricted video.{Colors.ENDC}")
                print(f"{Colors.YELLOW}💡 Tip: Place a 'cookies.txt' file in the tool folder or close your browser to allow cookie access.{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.RED}❌ Download error: {err_msg}{Colors.ENDC}\n")

def main():
    ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file = find_binaries()
    gpu_encoder, gpu_label = detect_best_gpu_encoder(ffmpeg_exe_path)

    while True:
        print_banner(ffmpeg_exe_path, aria2_path, cookies_file, gpu_label)

        # Input URL
        print(f"{Colors.BOLD}Enter Video URL (YouTube, TikTok, Instagram, Twitter/X, etc.):{Colors.ENDC}")
        url = input(f"{Colors.GREEN}🔗 URL (or type 'exit' to quit): {Colors.ENDC}").strip()

        if not url:
            print(f"{Colors.RED}No URL entered! Please try again.{Colors.ENDC}")
            time.sleep(1.5)
            continue

        if url.lower() in ['exit', 'quit', 'q']:
            print(f"\n{Colors.CYAN}Thank you for using UltraStream 8K Pro! Goodbye 👋{Colors.ENDC}\n")
            break

        # Select Quality Menu
        print("\n" + "="*60)
        print(f"{Colors.BOLD}Select Download Quality:{Colors.ENDC}")
        print("="*60)
        print(" [1] 🌟 Best Quality Available (Auto 8K / 4K MP4 with FFmpeg)")
        print(" [2] 🎬 8K Ultra HD Native (4320p MP4)")
        print(f" [3] 🚀 Forced Upscale Video to 8K MP4 (7680x4320 via HEVC NVENC / CPU)")
        print(f" [4] ⚡ Frame Interpolation to 60FPS MP4 (minterpolate mi_mode=mci via GPU/CPU)")
        print(" [5] 🎬 4K Ultra HD (2160p MP4)")
        print(" [6] 🎬 2K Quad HD (1440p MP4)")
        print(" [7] 🎬 Full HD (1080p MP4)")
        print(" [8] 🎬 HD (720p MP4)")
        print(" [9] 🎬 SD (480p / 360p MP4)")
        print(" [10] 🎵 Audio Only MP3 (320kbps Highest Quality)")
        print(" [11] 📋 List All Available Formats (Manual Code)")
        print("="*60)

        choice = input(f"{Colors.YELLOW}Enter choice number [Default 1]: {Colors.ENDC}").strip()
        if not choice:
            choice = "1"

        download_video(url, choice, ffmpeg_bin_dir, ffmpeg_exe_path, aria2_path, cookies_file, gpu_encoder)

        # Ask to continue
        again = input(f"{Colors.CYAN}Do you want to download another video link? (y/n): {Colors.ENDC}").strip().lower()
        if again in ['n', 'no', 'q', 'exit']:
            print(f"\n{Colors.CYAN}Thank you for using UltraStream 8K Pro! Goodbye 👋{Colors.ENDC}\n")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program stopped by user.{Colors.ENDC}")
        sys.exit(0)
