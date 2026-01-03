"""
Configuration Management
Centralized configuration for the application.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AppConfig:
    """Main application configuration"""
    
    # API Keys
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    
    # Directories
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    input_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    media_dir: Path = field(init=False)
    music_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    
    # Transcription settings
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu, cuda
    whisper_compute_type: str = "int8"
    
    # Video output settings
    output_width: int = 1080
    output_height: int = 1920
    output_fps: int = 30
    
    # Encoding settings
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "fast"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    crf: int = 23  # 0-51, lower = better quality, 18-28 is good range
    
    # Subtitle settings
    subtitle_fontsize: int = 16
    subtitle_max_chars: int = 20
    subtitle_max_duration: float = 2.0
    
    # AI settings
    gemini_model: str = "gemini-2.5-flash"
    
    # Cropping settings
    aspect_ratio: float = 9 / 16  # For vertical videos
    
    def __post_init__(self):
        """Initialize directory paths"""
        self.assets_dir = self.project_root / "assets"
        self.input_dir = self.assets_dir / "input"
        self.output_dir = self.assets_dir / "output"
        self.media_dir = self.assets_dir / "media"
        self.music_dir = self.assets_dir / "music"
        self.models_dir = self.project_root / "src" / "models"
        
        # Create directories if they don't exist
        for dir_path in [self.input_dir, self.output_dir, self.media_dir, self.music_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        from .exceptions import MissingAPIKeyError, ConfigurationError
        
        # Check for required API keys (only if using AI features)
        # We don't enforce this at startup to allow non-AI features to work
        
        # Validate paths
        if not self.project_root.exists():
            raise ConfigurationError(f"Project root does not exist: {self.project_root}")
        
        # Validate numeric settings
        if self.output_fps <= 0:
            raise ConfigurationError(f"Invalid FPS: {self.output_fps}")
        
        if not (0 <= self.crf <= 51):
            raise ConfigurationError(f"CRF must be between 0 and 51, got: {self.crf}")
        
        return True
    
    @property
    def has_gemini_key(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(self.gemini_api_key and self.gemini_api_key.strip())


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get or create the global configuration instance.
    
    Returns:
        AppConfig instance
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None
