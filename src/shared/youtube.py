"""
YouTube Download Utilities
Handles video downloading from YouTube using yt-dlp.
Extracted from src/utils/video.py for centralization.
"""
import os
import re
import time
import yt_dlp
import sys
from pathlib import Path
from typing import Tuple, Optional

from src.translations.manager import get_translator
t = get_translator().t
from .exceptions import YouTubeDownloadError, InvalidURLError


class QuietLogger:
    """silence yt-dlp warnings"""
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:100]


def download_youtube_video(url: str, output_dir: str = ".") -> Tuple[str, str]:
    """
    Download video from YouTube URL with Rich progress bar.
    """
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn, 
        DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
    )

    if not url or not url.strip():
        raise InvalidURLError("Empty URL provided")
    
    print(t("yt_downloading", url=url))
    
    # Handle Cookies
    cookies_path = 'cookies.txt'
    cookies_env = os.environ.get("YOUTUBE_COOKIES")
    if cookies_env:
        print(t("cookies_found", platform="YouTube"))
        try:
            with open(cookies_path, 'w') as f:
                f.write(cookies_env)
        except Exception as e:
            print(t("cookies_fail", error=e))
            cookies_path = None
    elif not os.path.exists(cookies_path):
        cookies_path = None
    else:
        print(t("cookies_manual"))

    # Get video info first
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'cookiefile': cookies_path,
        'logger': QuietLogger() # Silence warnings during extraction too
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'youtube_video')
            sanitized_title = sanitize_filename(video_title)
    except Exception as e:
        # If we can't get title, use timestamp
        # print(f"⚠️ Could not extract video title: {e}") # Keep quiet for user
        sanitized_title = f"video_{int(time.time())}"

    output_template = os.path.join(output_dir, f'{sanitized_title}.%(ext)s')
    
    # Rich Progress Context
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    task_id = progress.add_task("Downloading...", filename=sanitized_title, start=False)

    def progress_hook_rich(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total:
                progress.start_task(task_id)
                progress.update(task_id, total=total, completed=downloaded)
                
        elif d['status'] == 'finished':
            progress.update(task_id, completed=d.get('total_bytes'), description="Processing...")

    # Download options
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noprogress': True, # Disable default progress
        'overwrites': True,
        'cookiefile': cookies_path,
        'retries': 3,
        'continuedl': True,
        'noplaylist': True,
        'progress_hooks': [progress_hook_rich],
        'logger': QuietLogger(), # Inject custom logger to suppress warnings
    }
    
    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
    except Exception as e:
        raise YouTubeDownloadError(f"Failed to download video: {str(e)}", url=url)
    
    downloaded_file = os.path.join(output_dir, f'{sanitized_title}.mp4')
    
    # Fallback to find file if name slightly differs
    if not os.path.exists(downloaded_file):
        for f in os.listdir(output_dir):
            if f.startswith(sanitized_title) and f.endswith('.mp4'):
                downloaded_file = os.path.join(output_dir, f)
                break
    
    if not os.path.exists(downloaded_file):
        raise YouTubeDownloadError(f"Download completed but file not found.", url=url)
                
    return downloaded_file, sanitized_title
