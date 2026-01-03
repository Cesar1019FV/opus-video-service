"""
Shared Utilities and Domain Models
Centralized location for cross-cutting concerns.
"""

# Export commonly used items for convenience
from .models import (
    VideoInfo,
    TimeRange,
    ViralClip,
    Word,
    TranscriptSegment,
    Transcript,
    SubtitleBlock,
    SceneInfo,
    ProcessingConfig
)

from .exceptions import (
    OpusVideoError,
    VideoProcessingError,
    FFmpegError,
    TranscriptionError,
    AIAnalysisError,
    YouTubeDownloadError,
    ConfigurationError,
    MissingAPIKeyError
)

from .config import get_config, AppConfig
from .ffmpeg import get_video_info, get_video_resolution, cut_video, extract_audio, burn_subtitles
from .youtube import download_youtube_video, sanitize_filename

__all__ = [
    # Models
    'VideoInfo',
    'TimeRange',
    'ViralClip',
    'Word',
    'TranscriptSegment',
    'Transcript',
    'SubtitleBlock',
    'SceneInfo',
    'ProcessingConfig',
    # Exceptions
    'OpusVideoError',
    'VideoProcessingError',
    'FFmpegError',
    'TranscriptionError',
    'AIAnalysisError',
    'YouTubeDownloadError',
    'ConfigurationError',
    'MissingAPIKeyError',
    # Config
    'get_config',
    'AppConfig',
    # FFmpeg utils
    'get_video_info',
    'get_video_resolution',
    'cut_video',
    'extract_audio',
    'burn_subtitles',
    # YouTube utils
    'download_youtube_video',
    'sanitize_filename',
]

