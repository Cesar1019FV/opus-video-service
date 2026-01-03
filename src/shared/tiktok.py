"""
TikTok Download Utilities
Handles video downloading from TikTok using yt-dlp.
Extends functionality similar to youtube.py for consistent user experience.
"""
import os
import re
import time
import yt_dlp
from pathlib import Path
from typing import Tuple
from .exceptions import TikTokDownloadError, InvalidURLError


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


def download_tiktok_video(url: str, output_dir: str = ".") -> Tuple[str, str]:
    """
    Download video from TikTok URL with Rich progress bar.
    
    Args:
        url: TikTok video URL
        output_dir: Directory to save the downloaded video
        
    Returns:
        Tuple of (downloaded_file_path, video_title)
        
    Raises:
        InvalidURLError: If URL is invalid
        TikTokDownloadError: If download fails
    """
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn, 
        DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
    )

    if not url or not url.strip():
        raise InvalidURLError("Empty URL provided")
    
    print(f"📥 Downloading video from TikTok: {url}")
    
    # Handle Cookies (TikTok often needs them more than YouTube)
    cookies_path = 'cookies.txt'
    cookies_env = os.environ.get("TIKTOK_COOKIES") or os.environ.get("YOUTUBE_COOKIES")
    if cookies_env:
        print("🍪 Found COOKIES env var, using it.")
        try:
            with open(cookies_path, 'w') as f:
                f.write(cookies_env)
        except Exception as e:
            print(f"⚠️ Failed to write cookies file: {e}")
            cookies_path = None
    elif not os.path.exists(cookies_path):
        cookies_path = None

    # Get video info first
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'cookiefile': cookies_path,
        'logger': QuietLogger() 
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'tiktok_video')
            sanitized_title = sanitize_filename(video_title)
    except Exception as e:
        # Fallback if title extraction fails
        sanitized_title = f"tiktok_{int(time.time())}"

    output_template = os.path.join(output_dir, f'{sanitized_title}.%(ext)s')
    
    # Rich Progress Context
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold magenta]{task.fields[filename]}", justify="right"), # Magenta for TikTok
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
        'format': 'best', # TikTok usually single file
        'outtmpl': output_template,
        'quiet': True,
        'noprogress': True, 
        'overwrites': True,
        'cookiefile': cookies_path,
        'retries': 3,
        'progress_hooks': [progress_hook_rich],
        'logger': QuietLogger(),
    }
    
    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
    except Exception as e:
        raise TikTokDownloadError(f"Failed to download TikTok video: {str(e)}", url=url)
    
    # Determine final filename (might be mp4 or unpredictable)
    # TikTok downloads usually result in .mp4
    downloaded_file = os.path.join(output_dir, f'{sanitized_title}.mp4')
    
    # Fallback search
    if not os.path.exists(downloaded_file):
        for f in os.listdir(output_dir):
            if f.startswith(sanitized_title):
                downloaded_file = os.path.join(output_dir, f)
                break
    
    if not os.path.exists(downloaded_file):
        raise TikTokDownloadError(f"Download completed but file not found.", url=url)
                
    return downloaded_file, sanitized_title
