"""
FFmpeg Wrapper Utilities
Provides high-level functions for common FFmpeg operations.
Extracted from various modules to centralize FFmpeg interactions.
"""
import subprocess
import cv2
from pathlib import Path
from typing import Tuple, Optional
from .models import VideoInfo
from .exceptions import FFmpegError, VideoNotFoundError, VideoCorruptedError


def get_video_info(video_path: str) -> VideoInfo:
    """
    Extract video metadata using OpenCV.
    
    Args:
        video_path: Path to video file
        
    Returns:
        VideoInfo object with metadata
        
    Raises:
        VideoNotFoundError: If file doesn't exist
        VideoCorruptedError: If file cannot be read
    """
    path = Path(video_path)
    if not path.exists():
        raise VideoNotFoundError(f"Video not found: {video_path}")
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise VideoCorruptedError(f"Cannot open video: {video_path}")
    
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0.0
        
        # Check if video has audio (we'll assume yes for now, can be checked with ffprobe)
        has_audio = True
        
        return VideoInfo(
            path=path,
            width=width,
            height=height,
            fps=fps,
            duration=duration,
            has_audio=has_audio
        )
    finally:
        cap.release()


def get_video_resolution(video_path: str) -> Tuple[int, int]:
    """
    Get video resolution (width, height).
    Legacy function for compatibility.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (width, height)
    """
    info = get_video_info(video_path)
    return info.width, info.height


def cut_video(input_path: str, output_path: str, start: float, end: float, re_encode: bool = True) -> None:
    """
    Cut a segment from a video.
    
    Args:
        input_path: Source video path
        output_path: Destination video path
        start: Start time in seconds
        end: End time in seconds
        re_encode: If True, re-encode for frame accuracy. If False, use stream copy (faster but less precise)
        
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    if re_encode:
        command = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-to', str(end),
            '-i', input_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac',
            output_path
        ]
    else:
        command = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-to', str(end),
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]
    
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise FFmpegError(
            f"Failed to cut video from {start}s to {end}s",
            command=' '.join(command),
            stderr=result.stderr.decode() if result.stderr else None
        )


def extract_audio(video_path: str, output_path: str, audio_codec: str = 'copy') -> None:
    """
    Extract audio track from video.
    
    Args:
        video_path: Source video path
        output_path: Destination audio path
        audio_codec: Audio codec to use ('copy' for stream copy, 'aac', 'mp3', etc.)
        
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    command = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', audio_codec,
        output_path
    ]
    
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise FFmpegError(
            f"Failed to extract audio from {video_path}",
            command=' '.join(command),
            stderr=result.stderr.decode() if result.stderr else None
        )


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    alignment: str = "bottom",
    fontsize: int = 16
) -> None:
    """
    Burn subtitles into video using FFmpeg.
    
    Args:
        video_path: Source video path
        srt_path: SRT subtitle file path
        output_path: Destination video path
        alignment: Subtitle alignment ('top', 'middle', 'bottom')
        fontsize: Font size multiplier
        
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    final_fontsize = int(fontsize * 0.5)
    if final_fontsize < 8:
        final_fontsize = 8

    # ASS alignment values
    ass_alignment = 2  # Default Bottom
    if alignment.lower() == 'top':
        ass_alignment = 6
    elif alignment.lower() == 'middle':
        ass_alignment = 10

    # Sanitize path for FFmpeg filter
    try:
        safe_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
    except:
        safe_srt_path = srt_path

    style_string = (
        f"Alignment={ass_alignment},"
        f"Fontname=Verdana,"
        f"Fontsize={final_fontsize},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H60000000,"
        f"BackColour=&H00000000,"
        f"BorderStyle=3,"
        f"Outline=1,"
        f"Shadow=0,"
        f"MarginV=25,"
        f"Bold=1"
    )
    
    command = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', f"subtitles='{safe_srt_path}':force_style='{style_string}'",
        '-c:a', 'copy',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        output_path
    ]
    
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise FFmpegError(
            f"Failed to burn subtitles into {video_path}",
            command=' '.join(command),
            stderr=result.stderr.decode() if result.stderr else None
        )


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Merge video and audio streams.
    
    Args:
        video_path: Source video path
        audio_path: Source audio path
        output_path: Destination path
        
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    command = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_path
    ]
    
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise FFmpegError(
            f"Failed to merge audio and video",
            command=' '.join(command),
            stderr=result.stderr.decode() if result.stderr else None
        )


def check_ffmpeg_available() -> bool:
    """
    Check if FFmpeg is available in PATH.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
