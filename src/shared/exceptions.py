"""
Custom Exception Hierarchy for Opus Video Service
Provides specific exceptions for different error scenarios.
"""


class OpusVideoError(Exception):
    """Base exception for all Opus Video Service errors"""
    pass


# ============================================================================
# Video Processing Errors
# ============================================================================

class VideoProcessingError(OpusVideoError):
    """Base class for video processing errors"""
    pass


class VideoNotFoundError(VideoProcessingError):
    """Raised when a video file cannot be found"""
    pass


class VideoCorruptedError(VideoProcessingError):
    """Raised when a video file is corrupted or unreadable"""
    pass


class FFmpegError(VideoProcessingError):
    """Raised when FFmpeg command fails"""
    def __init__(self, message: str, command: str = None, stderr: str = None):
        super().__init__(message)
        self.command = command
        self.stderr = stderr


# ============================================================================
# Transcription Errors
# ============================================================================

class TranscriptionError(OpusVideoError):
    """Base class for transcription errors"""
    pass


class WhisperModelError(TranscriptionError):
    """Raised when Whisper model fails to load or process"""
    pass


class NoAudioError(TranscriptionError):
    """Raised when video has no audio track"""
    pass


# ============================================================================
# AI Analysis Errors
# ============================================================================

class AIAnalysisError(OpusVideoError):
    """Base class for AI analysis errors"""
    pass


class GeminiAPIError(AIAnalysisError):
    """Raised when Gemini API call fails"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class NoViralClipsFoundError(AIAnalysisError):
    """Raised when no viral clips are detected"""
    pass


class InvalidPromptResponseError(AIAnalysisError):
    """Raised when AI returns invalid or unparseable response"""
    pass


# ============================================================================
# Detection Errors
# ============================================================================

class DetectionError(OpusVideoError):
    """Base class for object/face detection errors"""
    pass


class FaceDetectionError(DetectionError):
    """Raised when face detection fails"""
    pass


class PersonDetectionError(DetectionError):
    """Raised when person detection fails"""
    pass


class ModelLoadError(DetectionError):
    """Raised when detection model fails to load"""
    pass


# ============================================================================
# Download Errors
# ============================================================================

class DownloadError(OpusVideoError):
    """Base class for download errors"""
    pass


class YouTubeDownloadError(DownloadError):
    """Raised when YouTube download fails"""
    def __init__(self, message: str, url: str = None):
        super().__init__(message)
        self.url = url


class TikTokDownloadError(DownloadError):
    """Raised when TikTok download fails"""
    def __init__(self, message: str, url: str = None):
        super().__init__(message)
        self.url = url


class InvalidURLError(DownloadError):
    """Raised when provided URL is invalid"""
    pass


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(OpusVideoError):
    """Raised when configuration is invalid or missing"""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is not found"""
    def __init__(self, key_name: str):
        super().__init__(f"Missing required API key: {key_name}")
        self.key_name = key_name


# ============================================================================
# File System Errors
# ============================================================================

class FileSystemError(OpusVideoError):
    """Base class for file system errors"""
    pass


class OutputDirectoryError(FileSystemError):
    """Raised when output directory cannot be created or accessed"""
    pass


class InsufficientDiskSpaceError(FileSystemError):
    """Raised when there's not enough disk space"""
    pass
