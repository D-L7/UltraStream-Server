import os
import sys
import socket
import time
import tempfile
import threading
import subprocess
import mimetypes
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file, make_response

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
            font-size: 14.5px;
            font-weight: 800;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .step-number {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            color: #FFFFFF;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 900;
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.4);
            flex-shrink: 0;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .input-container {
            display: flex;
            flex-direction: row;
            gap: 10px;
            width: 100%;
            align-items: center;
        }

        .input-inner {
            flex: 1;
            position: relative;
            display: flex;
            align-items: center;
            background: rgba(8, 10, 16, 0.9);
            border: 1.5px solid rgba(255, 255, 255, 0.16);
            border-radius: 18px;
            padding: 0 14px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
        }

        .input-inner:focus-within {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.35), inset 0 2px 4px rgba(0,0,0,0.5);
            background: rgba(12, 15, 26, 0.95);
        }

        .input-link-icon {
            font-size: 18px;
            color: var(--accent-cyan);
            margin-left: 8px;
            flex-shrink: 0;
            opacity: 0.85;
        }

        .input-inner input[type="text"] {
            width: 100%;
            background: transparent;
            border: none;
            padding: 14px 6px;
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 600;
            outline: none;
            direction: ltr;
            text-align: left;
        }

        .input-inner input[type="text"]::placeholder {
            color: rgba(255, 255, 255, 0.35);
            direction: rtl;
            text-align: right;
            font-weight: 400;
        }

        .clear-btn {
            display: none;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #FFF;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            font-size: 11px;
            cursor: pointer;
            align-items: center;
            justify-content: center;
            margin-right: 4px;
            transition: all 0.2s;
            flex-shrink: 0;
        }

        .clear-btn:hover {
            background: rgba(255, 50, 50, 0.5);
        }

        .input-actions {
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }

        .action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 13px 18px;
            border-radius: 14px;
            font-size: 13px;
            font-weight: 800;
            cursor: pointer;
            border: none;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
            white-space: nowrap;
        }

        .paste-action {
            background: linear-gradient(135deg, rgba(157, 0, 255, 0.25), rgba(157, 0, 255, 0.55));
            border: 1px solid var(--accent-purple);
            color: #FFFFFF;
            box-shadow: 0 4px 15px rgba(157, 0, 255, 0.3);
        }

        .paste-action:hover {
            transform: translateY(-2px);
            background: linear-gradient(135deg, rgba(157, 0, 255, 0.4), rgba(157, 0, 255, 0.8));
            box-shadow: 0 6px 20px rgba(157, 0, 255, 0.5);
        }

        .analyze-action {
            background: linear-gradient(135deg, #00F0FF 0%, #00A3FF 100%);
            color: #06070B;
            font-weight: 900;
            box-shadow: 0 4px 16px rgba(0, 240, 255, 0.4);
        }

        .analyze-action:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 22px rgba(0, 240, 255, 0.6);
            filter: brightness(1.1);
        }

        .action-btn:active {
            transform: scale(0.96);
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
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 12px;
        }

        .quality-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 14px 10px 12px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            user-select: none;
            overflow: hidden;
        }

        .quality-card:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.08);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 240, 255, 0.2);
        }

        .quality-card.selected {
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(157, 0, 255, 0.25));
            border: 2px solid var(--accent-cyan);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.45);
            transform: translateY(-3px);
        }

        .card-badge {
            position: absolute;
            top: 6px;
            right: 6px;
            background: rgba(0, 240, 255, 0.15);
            color: var(--accent-cyan);
            border: 1px solid rgba(0, 240, 255, 0.3);
            font-size: 9.5px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 8px;
            letter-spacing: 0.3px;
        }

        .quality-card.selected .card-badge {
            background: var(--accent-cyan);
            color: #000;
        }

        .icon-wrap {
            font-size: 22px;
            margin-bottom: 6px;
            margin-top: 4px;
            transition: transform 0.25s;
        }

        .quality-card:hover .icon-wrap {
            transform: scale(1.15);
        }

        .quality-card .label {
            font-size: 12.5px;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.2;
        }

        .quality-card .sub {
            font-size: 10.5px;
            color: var(--text-muted);
            margin-top: 3px;
        }

        .quality-card.audio {
            border-color: rgba(0, 255, 136, 0.3);
        }

        .quality-card.audio .card-badge {
            background: rgba(0, 255, 136, 0.15);
            color: var(--accent-green);
            border-color: rgba(0, 255, 136, 0.3);
        }

        .quality-card.audio.selected {
            border-color: var(--accent-green);
            background: rgba(0, 255, 136, 0.18);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.45);
        }

        .quality-card.audio.selected .card-badge {
            background: var(--accent-green);
            color: #000;
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

        @media (max-width: 520px) {
            body { padding: 12px 10px; }
            .header h1 { font-size: 23px; }
            .logo-img { width: 68px; height: 68px; }
            .card { padding: 18px 14px; }
            .input-container { flex-direction: column; gap: 10px; }
            .input-inner { width: 100%; }
            .input-actions { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
            .action-btn { width: 100%; padding: 12px; }
            .btn-action { font-size: 15px; padding: 15px; }
            .qualities-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        }

        /* Navigation Tabs */
        .nav-tabs {
            display: flex;
            width: 100%;
            max-width: 620px;
            background: rgba(15, 17, 28, 0.85);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 6px;
            gap: 6px;
            margin-bottom: 5px;
            backdrop-filter: blur(16px);
        }

        .nav-tab-btn {
            flex: 1;
            padding: 12px 10px;
            background: transparent;
            border: none;
            border-radius: 14px;
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .nav-tab-btn.active {
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.25) 0%, rgba(157, 0, 255, 0.3) 100%);
            border: 1px solid rgba(0, 240, 255, 0.4);
            color: var(--text-main);
            box-shadow: 0 4px 16px rgba(0, 240, 255, 0.2);
        }

        /* Media Library Container */
        .search-filter-box {
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 16px;
            backdrop-filter: blur(16px);
        }

        .library-search-input {
            width: 100%;
            background: rgba(5, 7, 12, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 12px 16px;
            color: #FFF;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        .library-search-input:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.2);
        }

        .tag-filter-list {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 4px;
            scrollbar-width: none;
        }
        .tag-filter-list::-webkit-scrollbar { display: none; }

        .tag-btn {
            padding: 6px 14px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
        }

        .tag-btn.active {
            background: var(--accent-cyan);
            color: #000;
            border-color: var(--accent-cyan);
            font-weight: 700;
        }

        .media-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 14px;
            width: 100%;
        }

        .media-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            backdrop-filter: blur(16px);
            transition: transform 0.2s ease, border-color 0.2s ease;
            position: relative;
            overflow: hidden;
        }

        .media-card:hover {
            transform: translateY(-2px);
            border-color: rgba(0, 240, 255, 0.4);
        }

        .media-card-header {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .media-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.2) 0%, rgba(157, 0, 255, 0.2) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }

        .media-info {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex: 1;
        }

        .media-title {
            font-size: 13px;
            font-weight: 700;
            color: #FFF;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .media-meta {
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 2px;
            flex-wrap: wrap;
        }

        .media-badge {
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: bold;
            background: rgba(0, 240, 255, 0.15);
            color: var(--accent-cyan);
        }

        .media-actions {
            display: flex;
            gap: 8px;
            margin-top: 4px;
        }

        .media-btn {
            flex: 1;
            padding: 8px;
            border-radius: 10px;
            border: none;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            transition: opacity 0.2s ease;
            text-decoration: none;
        }

        .media-btn-play {
            background: linear-gradient(135deg, #00F0FF 0%, #7000FF 100%);
            color: #FFF;
        }
        .media-btn-download {
            background: rgba(0, 255, 136, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .media-btn-delete {
            background: rgba(255, 0, 85, 0.15);
            color: #FF0055;
            border: 1px solid rgba(255, 0, 85, 0.3);
            max-width: 38px;
        }

        /* Streaming Modal Player */
        .player-modal-overlay {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(3, 4, 8, 0.92);
            backdrop-filter: blur(20px);
            z-index: 99999;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .player-modal-card {
            width: 100%;
            max-width: 720px;
            background: rgba(15, 17, 28, 0.95);
            border: 1px solid rgba(0, 240, 255, 0.4);
            border-radius: 24px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 50px rgba(0, 240, 255, 0.25);
            animation: modalPop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        @keyframes modalPop {
            from { opacity: 0; transform: scale(0.92); }
            to { opacity: 1; transform: scale(1); }
        }

        .player-modal-header {
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
        }

        .player-modal-title {
            font-size: 15px;
            font-weight: 700;
            color: #FFF;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 80%;
        }

        .close-modal-btn {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #FFF;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .player-media-wrapper {
            width: 100%;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 240px;
            max-height: 460px;
        }

        .player-media-wrapper video, .player-media-wrapper audio {
            width: 100%;
            max-height: 460px;
            outline: none;
        }

        /* Features & Copyright Section */
        .features-section {
            width: 100%;
            max-width: 620px;
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .section-title {
            font-size: 15px;
            font-weight: 800;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }

        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            backdrop-filter: blur(16px);
        }

        .feature-icon {
            font-size: 24px;
            margin-bottom: 2px;
        }

        .feature-heading {
            font-size: 13px;
            font-weight: 700;
            color: #FFF;
        }

        .feature-desc {
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.4;
        }

        .copyright-footer {
            width: 100%;
            max-width: 620px;
            text-align: center;
            padding: 20px 10px 10px;
            border-top: 1px solid var(--border-color);
            margin-top: 20px;
            color: var(--text-muted);
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            align-items: center;
        }

        .copyright-brand {
            font-size: 13px;
            font-weight: 800;
            color: var(--text-main);
            background: linear-gradient(135deg, #00F0FF 0%, #9D00FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
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

        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button id="downloaderTabBtn" class="nav-tab-btn active" onclick="switchTab('downloader')">
                <span>⚡ التحميل المباشر</span>
            </button>
            <button id="libraryTabBtn" class="nav-tab-btn" onclick="switchTab('library')">
                <span>📁 مكتبة المحتوى</span>
            </button>
        </div>

        <!-- Downloader Tab Content -->
        <div id="downloaderTab" style="width: 100%; display: flex; flex-direction: column; align-items: center; gap: 20px;">
            <!-- Form Card -->
            <div class="card">
                <!-- Step 1: Link Input -->
                <div class="form-group">
                    <div class="step-title">
                        <span class="step-number">1</span>
                        <span>أدخل رابط الفيديو المراد تحويله وتنزيله:</span>
                    </div>
                    <div class="input-container">
                        <div class="input-inner">
                            <span class="input-link-icon">🔗</span>
                            <input type="text" id="videoUrl" placeholder="ضع رابط الفيديو هنا (YouTube, TikTok...)" required autocomplete="off" oninput="handleUrlInput()" onpaste="setTimeout(handleUrlInput, 50)" onchange="handleUrlInput()">
                            <button class="clear-btn" id="clearBtn" type="button" onclick="clearInput()" title="مسح الرابط">✖</button>
                        </div>
                        <div class="input-actions">
                            <button class="action-btn paste-action" type="button" onclick="pasteClipboard()">
                                <span>📋</span>
                                <span>لصق</span>
                            </button>
                            <button class="action-btn analyze-action" type="button" onclick="handleUrlInput(true)">
                                <span>🔍</span>
                                <span>تحليل</span>
                            </button>
                        </div>
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
                        <div class="step-title">
                            <span class="step-number">2</span>
                            <span>اختر الجودة المطلوبة للتحميل المباشر:</span>
                        </div>
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

        <!-- Media Library Tab Content -->
        <div id="libraryTab" style="display: none; width: 100%; max-width: 620px; flex-direction: column; gap: 14px;">
            <div class="search-filter-box">
                <input type="text" id="librarySearchInput" class="library-search-input" placeholder="🔍 ابحث في المحفوظات باسم الفيديو أو المقطع..." oninput="filterLibrary()">
                <div class="tag-filter-list">
                    <button class="tag-btn active" onclick="setLibraryTag('all', this)">الكل 🌐</button>
                    <button class="tag-btn" onclick="setLibraryTag('video', this)">فيديو 🎬</button>
                    <button class="tag-btn" onclick="setLibraryTag('audio', this)">صوت MP3 🎵</button>
                    <button class="tag-btn" onclick="setLibraryTag('YouTube', this)">YouTube 🔴</button>
                    <button class="tag-btn" onclick="setLibraryTag('TikTok', this)">TikTok 🎵</button>
                    <button class="tag-btn" onclick="setLibraryTag('Instagram', this)">Instagram 📸</button>
                    <button class="tag-btn" onclick="setLibraryTag('Twitter-X', this)">Twitter / X 🐦</button>
                    <button class="tag-btn" onclick="setLibraryTag('Facebook', this)">Facebook 💙</button>
                </div>
            </div>

            <div id="libraryGrid" class="media-grid">
                <!-- Dynamically loaded media cards -->
            </div>
            
            <div id="libraryEmpty" style="display: none; text-align: center; padding: 40px 20px; color: var(--text-muted); font-weight: 600;">
                📁 لا توجد عناصر سابقة في المكتبة حتى الآن.
            </div>
        </div>

        <!-- Features Showcase Section -->
        <div class="features-section">
            <div class="section-title">
                <span>🌟 مميزات محرك UltraStream 8K Pro</span>
            </div>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <div class="feature-heading">تسريع Aria2 الفائق</div>
                    <div class="feature-desc">تحميل متعدد الخيوط بـ 16 اتصال متزامن لأعلى سرعة استجابة.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎮</div>
                    <div class="feature-heading">معالجة كرت الشاشة (GPU)</div>
                    <div class="feature-desc">تسريع هاردوير عبر NVENC و AMF و QSV لتنقية ورفع الجودة.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💎</div>
                    <div class="feature-heading">دقة فائقة تصل لـ 8K</div>
                    <div class="feature-desc">دعم استخراج أعتى الجودات 8K/4K/1080p وصوتيات 320kbps.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📱</div>
                    <div class="feature-heading">دعم PWA وجميع الشاشات</div>
                    <div class="feature-desc">تطبيق ويب تقدمي يعمل بسلاسة على الجوال والكمبيوتر والتابلت.</div>
                </div>
            </div>
        </div>

        <!-- Copyright Footer -->
        <div class="copyright-footer">
            <div class="copyright-brand">UltraStream 8K Pro Engine v2.5</div>
            <div>© 2026 جميع الحقوق محفوظة. تم تطوير النظام بقمة المعايير لسرعة واستقرار التحميل.</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px;">تطوير السيرفر والواجهة المتقدمة بنظام المعالجة الفورية المباشرة.</div>
        </div>
    </div>

    <!-- In-App Stream Player Modal -->
    <div id="playerModal" class="player-modal-overlay">
        <div class="player-modal-card">
            <div class="player-modal-header">
                <div id="playerModalTitle" class="player-modal-title">مشغل المحتوى المدمج</div>
                <button class="close-modal-btn" onclick="closeStreamPlayer()">✖</button>
            </div>
            <div class="player-media-wrapper">
                <video id="playerVideo" controls style="display: none;"></video>
                <audio id="playerAudio" controls style="display: none; width: 90%;"></audio>
            </div>
            <div style="padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; background: rgba(5, 7, 12, 0.8);">
                <div id="playerModalMeta" style="font-size: 12px; color: var(--text-muted);">UltraStream Web Streamer</div>
                <a id="playerDownloadBtn" class="media-btn media-btn-download" href="#" download style="padding: 8px 16px; border-radius: 12px;">⬇️ تحميل الملف</a>
            </div>
        </div>
    </div>

    <script>
        // Default Quality Presets
        const DEFAULT_QUALITIES = [
            { val: '1', label: 'أعلى جودة تلقائياً', sub: 'Auto 8K / 4K MP4', icon: '🌟', badge: 'تلقائي', default: true },
            { val: '2', label: '8K Ultra HD', sub: '4320p MP4', icon: '💎', badge: '8K' },
            { val: '3', label: '4K Ultra HD', sub: '2160p MP4', icon: '🎬', badge: '4K' },
            { val: '4', label: '2K Quad HD', sub: '1440p MP4', icon: '🎥', badge: '2K' },
            { val: '5', label: '1080p Full HD', sub: '1080p MP4', icon: '📺', badge: '1080p' },
            { val: '6', label: '720p HD', sub: '720p MP4', icon: '📱', badge: '720p' },
            { val: '7', label: 'صوت MP3 فقط', sub: '320kbps نقاء عالي', icon: '🎵', badge: 'MP3', isAudio: true },
            { val: '8', label: 'رفع إجباري لـ 8K', sub: 'GPU Upscale', icon: '🚀', badge: 'تسريع' },
            { val: '9', label: '60 FPS مضاعفة', sub: 'FFmpeg MCI', icon: '⚡', badge: 'سلاسة' }
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
                alert(`لتثبيت التطبيق على الجوال:
- في الآيفون (Safari): اضغط زر المشاركة 📤 ثم اختر "إضافة إلى الشاشة الرئيسية ➕".
- في الأندرويد (Chrome): اضغط على القائمة 💬 ثم اختر "تثبيت التطبيق".`);
            }
        }

        function clearInput() {
            const input = document.getElementById('videoUrl');
            const box = document.getElementById('previewBox');
            const clearBtn = document.getElementById('clearBtn');
            if (input) input.value = '';
            if (box) box.style.display = 'none';
            if (clearBtn) clearBtn.style.display = 'none';
            currentFetchedUrl = '';
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
                    handleUrlInput(true);
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
                    ${q.badge ? `<div class="card-badge">${q.badge}</div>` : ''}
                    <div class="icon-wrap">${q.icon || '🎬'}</div>
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

        async function handleUrlInput(force = false) {
            const input = document.getElementById('videoUrl');
            const box = document.getElementById('previewBox');
            if (!input || !box) return;

            let rawVal = input.value.trim();
            if (!rawVal || rawVal.length < 4) {
                box.style.display = 'none';
                currentFetchedUrl = '';
                return;
            }

            let url = normalizeUrl(rawVal);
            if (!force && url === currentFetchedUrl) return;

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

        // Media Library & Navigation Logic
        let cachedLibraryItems = [];
        let activeTagFilter = 'all';

        function switchTab(tabName) {
            const downloaderTab = document.getElementById('downloaderTab');
            const libraryTab = document.getElementById('libraryTab');
            const downloaderBtn = document.getElementById('downloaderTabBtn');
            const libraryBtn = document.getElementById('libraryTabBtn');

            if (tabName === 'library') {
                downloaderTab.style.display = 'none';
                libraryTab.style.display = 'flex';
                downloaderBtn.classList.remove('active');
                libraryBtn.classList.add('active');
                fetchLibraryItems();
            } else {
                libraryTab.style.display = 'none';
                downloaderTab.style.display = 'flex';
                libraryBtn.classList.remove('active');
                downloaderBtn.classList.add('active');
            }
        }

        async function fetchLibraryItems() {
            const grid = document.getElementById('libraryGrid');
            const emptyState = document.getElementById('libraryEmpty');
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 20px; color: var(--accent-cyan);">⏳ جاري تحميل المحفوظات...</div>';
            emptyState.style.display = 'none';

            try {
                const res = await fetch('/api/library');
                const data = await res.json();
                if (data.success) {
                    cachedLibraryItems = data.items || [];
                    renderLibraryGrid();
                } else {
                    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #FF0055;">❌ فشل جلب مكتبة المحتوى.</div>';
                }
            } catch (err) {
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #FF0055;">❌ حدث خطأ في الاتصال بالشبكة.</div>';
            }
        }

        function setLibraryTag(tag, btnElem) {
            activeTagFilter = tag;
            document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
            if (btnElem) btnElem.classList.add('active');
            renderLibraryGrid();
        }

        function filterLibrary() {
            renderLibraryGrid();
        }

        function renderLibraryGrid() {
            const grid = document.getElementById('libraryGrid');
            const emptyState = document.getElementById('libraryEmpty');
            const searchVal = (document.getElementById('librarySearchInput').value || '').toLowerCase().trim();

            let items = cachedLibraryItems.filter(item => {
                const matchesSearch = !searchVal || item.filename.toLowerCase().includes(searchVal) || item.platform.toLowerCase().includes(searchVal);
                let matchesTag = true;

                if (activeTagFilter === 'video') matchesTag = !item.is_audio;
                else if (activeTagFilter === 'audio') matchesTag = item.is_audio;
                else if (activeTagFilter !== 'all') matchesTag = item.platform.toLowerCase() === activeTagFilter.toLowerCase();

                return matchesSearch && matchesTag;
            });

            if (items.length === 0) {
                grid.innerHTML = '';
                emptyState.style.display = 'block';
                return;
            }

            emptyState.style.display = 'none';
            grid.innerHTML = items.map(item => {
                const icon = item.is_audio ? '🎵' : (item.ext === '.mkv' ? '🎥' : '🎬');
                let platformBadge = '🌐عام';
                if (item.platform.toLowerCase().includes('youtube')) platformBadge = '🔴 YouTube';
                else if (item.platform.toLowerCase().includes('tiktok')) platformBadge = '🎵 TikTok';
                else if (item.platform.toLowerCase().includes('instagram')) platformBadge = '📸 Instagram';
                else if (item.platform.toLowerCase().includes('twitter')) platformBadge = '🐦 Twitter/X';
                else if (item.platform.toLowerCase().includes('facebook')) platformBadge = '💙 Facebook';

                return `
                    <div class="media-card">
                        <div class="media-card-header">
                            <div class="media-icon">${icon}</div>
                            <div class="media-info">
                                <div class="media-title" title="${item.filename}">${item.filename}</div>
                                <div class="media-meta">
                                    <span class="media-badge">${platformBadge}</span>
                                    <span>📦 ${item.size}</span>
                                    <span>📅 ${item.date}</span>
                                </div>
                            </div>
                        </div>
                        <div class="media-actions">
                            <button class="media-btn media-btn-play" onclick="openStreamPlayer('${item.stream_url}', '${encodeURIComponent(item.filename)}', '${platformBadge}', ${item.is_audio})">
                                <span>▶️ تشغيل</span>
                            </button>
                            <a class="media-btn media-btn-download" href="${item.file_url}" download="${item.filename}">
                                <span>⬇️ حفظ</span>
                            </a>
                            <button class="media-btn media-btn-delete" onclick="deleteLibraryItem('${encodeURIComponent(item.platform)}', '${encodeURIComponent(item.filename)}')" title="حذف الملف">
                                🗑️
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function openStreamPlayer(streamUrl, filenameEnc, platformBadge, isAudio) {
            const filename = decodeURIComponent(filenameEnc);
            const modal = document.getElementById('playerModal');
            const titleEl = document.getElementById('playerModalTitle');
            const metaEl = document.getElementById('playerModalMeta');
            const videoEl = document.getElementById('playerVideo');
            const audioEl = document.getElementById('playerAudio');
            const downloadBtn = document.getElementById('playerDownloadBtn');

            titleEl.innerText = filename;
            metaEl.innerText = `${platformBadge} | UltraStream Web Streamer`;
            downloadBtn.href = streamUrl.replace('/stream_file/', '/download_file/');
            downloadBtn.setAttribute('download', filename);

            if (isAudio) {
                videoEl.pause();
                videoEl.style.display = 'none';
                audioEl.src = streamUrl;
                audioEl.style.display = 'block';
                audioEl.play().catch(() => {});
            } else {
                audioEl.pause();
                audioEl.style.display = 'none';
                videoEl.src = streamUrl;
                videoEl.style.display = 'block';
                videoEl.play().catch(() => {});
            }

            modal.style.display = 'flex';
        }

        function closeStreamPlayer() {
            const modal = document.getElementById('playerModal');
            const videoEl = document.getElementById('playerVideo');
            const audioEl = document.getElementById('playerAudio');

            videoEl.pause();
            videoEl.src = '';
            audioEl.pause();
            audioEl.src = '';
            modal.style.display = 'none';
        }

        async function deleteLibraryItem(platformEnc, filenameEnc) {
            const platform = decodeURIComponent(platformEnc);
            const filename = decodeURIComponent(filenameEnc);

            if (!confirm(`هل أنت تأكد من رغبتك في حذف الملف:\n"${filename}"؟`)) {
                return;
            }

            try {
                const res = await fetch('/api/library/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ platform: platform, filename: filename })
                });

                const data = await res.json();
                if (data.success) {
                    fetchLibraryItems();
                } else {
                    alert('فشل حذف الملف: ' + (data.error || 'خطأ غير معروف'));
                }
            } catch (err) {
                alert('حدث خطأ أثناء الاتصال بالسيرفر لحذف الملف.');
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
    resp = make_response(render_template_string(MOBILE_HTML))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


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
                {'val': '1', 'label': 'أعلى جودة تلقائياً', 'sub': 'Auto 8K / 4K MP4', 'icon': '🌟', 'badge': 'تلقائي'}
            ]
            
            heights_seen = set()
            if 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    h = fmt.get('height')
                    if h and isinstance(h, int) and h >= 144:
                        heights_seen.add(h)

            # Map detected resolutions to clean high-quality choices (720p and above)
            if 4320 in heights_seen or any(h >= 3000 for h in heights_seen):
                formats_list.append({'val': '2', 'label': '8K Ultra HD', 'sub': '4320p MP4', 'icon': '💎', 'badge': '8K'})
            if any(2000 <= h < 3000 for h in heights_seen) or 2160 in heights_seen:
                formats_list.append({'val': '3', 'label': '4K Ultra HD', 'sub': '2160p MP4', 'icon': '🎬', 'badge': '4K'})
            if any(1300 <= h < 2000 for h in heights_seen) or 1440 in heights_seen:
                formats_list.append({'val': '4', 'label': '2K Quad HD', 'sub': '1440p MP4', 'icon': '🎥', 'badge': '2K'})
            if any(900 <= h < 1300 for h in heights_seen) or 1080 in heights_seen:
                formats_list.append({'val': '5', 'label': '1080p Full HD', 'sub': '1080p MP4', 'icon': '📺', 'badge': '1080p'})
            if any(600 <= h < 900 for h in heights_seen) or 720 in heights_seen:
                formats_list.append({'val': '6', 'label': '720p HD', 'sub': '720p MP4', 'icon': '📱', 'badge': '720p'})

            # Fallback standard list if format heights were not enumerated
            if len(formats_list) <= 1:
                formats_list = [
                    {'val': '1', 'label': 'أعلى جودة تلقائياً', 'sub': 'Auto 8K / 4K MP4', 'icon': '🌟', 'badge': 'تلقائي'},
                    {'val': '2', 'label': '8K Ultra HD', 'sub': '4320p MP4', 'icon': '💎', 'badge': '8K'},
                    {'val': '3', 'label': '4K Ultra HD', 'sub': '2160p MP4', 'icon': '🎬', 'badge': '4K'},
                    {'val': '4', 'label': '2K Quad HD', 'sub': '1440p MP4', 'icon': '🎥', 'badge': '2K'},
                    {'val': '5', 'label': '1080p Full HD', 'sub': '1080p MP4', 'icon': '📺', 'badge': '1080p'},
                    {'val': '6', 'label': '720p HD', 'sub': '720p MP4', 'icon': '📱', 'badge': '720p'}
                ]

            formats_list.append({'val': '7', 'label': 'صوت MP3 فقط', 'sub': '320kbps نقاء عالي', 'icon': '🎵', 'badge': 'MP3', 'isAudio': True})
            formats_list.append({'val': '8', 'label': 'رفع إجباري لـ 8K', 'sub': 'GPU Upscale', 'icon': '🚀', 'badge': 'تسريع'})
            formats_list.append({'val': '9', 'label': '60 FPS مضاعفة', 'sub': 'FFmpeg MCI', 'icon': '⚡', 'badge': 'سلاسة'})

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


@app.route('/stream_file/<platform>/<filename>')
def stream_file(platform, filename):
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
        mime_type = mimetypes.guess_type(filepath)[0] or 'video/mp4'

    response = send_file(
        filepath,
        mimetype=mime_type,
        as_attachment=False
    )
    encoded_filename = quote(filename)
    response.headers["Content-Type"] = mime_type
    response.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{encoded_filename}"
    return response


@app.route('/api/library', methods=['GET'])
def api_library():
    downloads_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
    items = []

    if os.path.exists(downloads_root):
        for root, dirs, files in os.walk(downloads_root):
            for file in files:
                if file.startswith('temp_'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, downloads_root)
                parts = rel_path.split(os.sep)
                
                platform = parts[0] if len(parts) > 1 else 'General'
                ext = os.path.splitext(file)[1].lower()
                if ext not in ['.mp4', '.mp3', '.mkv', '.webm', '.m4a', '.flv', '.avi']:
                    continue

                stat = os.stat(filepath)
                size_mb = f"{stat.st_size / (1024 * 1024):.1f} MB" if stat.st_size >= 1024*1024 else f"{stat.st_size / 1024:.0f} KB"
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                is_audio = (ext == '.mp3' or ext == '.m4a')
                
                items.append({
                    'filename': file,
                    'platform': platform,
                    'size': size_mb,
                    'size_bytes': stat.st_size,
                    'date': mod_time,
                    'mtime': stat.st_mtime,
                    'is_audio': is_audio,
                    'ext': ext,
                    'file_url': f"/download_file/{quote(platform)}/{quote(file)}",
                    'stream_url': f"/stream_file/{quote(platform)}/{quote(file)}"
                })

    # Sort newest first
    items.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify({'success': True, 'items': items})


@app.route('/api/library/delete', methods=['POST'])
def api_library_delete():
    data = request.get_json() or {}
    platform = data.get('platform', '')
    filename = data.get('filename', '')

    if not platform or not filename:
        return jsonify({'success': False, 'error': 'Invalid request parameters'})

    downloads_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
    filepath = os.path.join(downloads_root, platform, filename)

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'File not found'})


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
