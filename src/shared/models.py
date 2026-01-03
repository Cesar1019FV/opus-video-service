"""
Domain Models for Opus Video Service
Centralized location for all business domain objects.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path


# ============================================================================
# Video-related Models
# ============================================================================

@dataclass
class VideoInfo:
    """Represents video file metadata"""
    path: Path
    width: int
    height: int
    fps: float
    duration: float  # in seconds
    has_audio: bool = True
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.width / self.height
    
    @property
    def is_vertical(self) -> bool:
        """Check if video is vertical (9:16 or similar)"""
        return self.height > self.width
    
    @property
    def is_horizontal(self) -> bool:
        """Check if video is horizontal (16:9 or similar)"""
        return self.width > self.height


@dataclass
class TimeRange:
    """Represents a time range in a video"""
    start: float  # seconds
    end: float    # seconds
    
    @property
    def duration(self) -> float:
        """Calculate duration of the range"""
        return self.end - self.start
    
    def contains(self, timestamp: float) -> bool:
        """Check if a timestamp falls within this range"""
        return self.start <= timestamp <= self.end
    
    def overlaps(self, other: 'TimeRange') -> bool:
        """Check if this range overlaps with another"""
        return not (self.end < other.start or self.start > other.end)


@dataclass
class ViralClip:
    """Represents a detected viral clip segment"""
    time_range: TimeRange
    title: str
    descriptions: Dict[str, str]  # platform -> description mapping
    confidence: Optional[float] = None
    
    @property
    def start(self) -> float:
        return self.time_range.start
    
    @property
    def end(self) -> float:
        return self.time_range.end
    
    @property
    def duration(self) -> float:
        return self.time_range.duration


# ============================================================================
# Transcript-related Models
# ============================================================================

@dataclass
class Word:
    """Represents a single transcribed word"""
    text: str
    start: float
    end: float
    probability: float = 1.0
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class TranscriptSegment:
    """Represents a segment of transcription"""
    text: str
    start: float
    end: float
    words: List[Word]
    
    @property
    def duration(self) -> float:
        return self.end - self.start
    
    @property
    def word_count(self) -> int:
        return len(self.words)


@dataclass
class Transcript:
    """Complete transcript with metadata"""
    text: str
    segments: List[TranscriptSegment]
    language: str
    
    @property
    def total_words(self) -> int:
        """Count total words across all segments"""
        return sum(len(seg.words) for seg in self.segments)
    
    @property
    def duration(self) -> float:
        """Get total duration from segments"""
        if not self.segments:
            return 0.0
        return max(seg.end for seg in self.segments)
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for compatibility with existing code"""
        return {
            'text': self.text,
            'segments': [
                {
                    'text': seg.text,
                    'start': seg.start,
                    'end': seg.end,
                    'words': [
                        {
                            'word': word.text,
                            'start': word.start,
                            'end': word.end,
                            'probability': word.probability
                        }
                        for word in seg.words
                    ]
                }
                for seg in self.segments
            ],
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transcript':
        """Create Transcript from dictionary (for compatibility)"""
        segments = []
        for seg_data in data.get('segments', []):
            words = [
                Word(
                    text=w['word'],
                    start=w['start'],
                    end=w['end'],
                    probability=w.get('probability', 1.0)
                )
                for w in seg_data.get('words', [])
            ]
            segments.append(
                TranscriptSegment(
                    text=seg_data['text'],
                    start=seg_data['start'],
                    end=seg_data['end'],
                    words=words
                )
            )
        
        return cls(
            text=data['text'],
            segments=segments,
            language=data['language']
        )


# ============================================================================
# Subtitle Models
# ============================================================================

@dataclass
class SubtitleBlock:
    """Represents a subtitle block for SRT generation"""
    index: int
    start: float
    end: float
    text: str
    
    def to_srt_format(self) -> str:
        """Convert to SRT format string"""
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        return f"{self.index}\n{format_time(self.start)} --> {format_time(self.end)}\n{self.text}\n\n"


# ============================================================================
# Scene Analysis Models
# ============================================================================

@dataclass
class SceneInfo:
    """Represents a detected scene"""
    start_frame: int
    end_frame: int
    fps: float
    strategy: str = 'TRACK'  # 'TRACK' or 'GENERAL'
    
    @property
    def start_time(self) -> float:
        return self.start_frame / self.fps
    
    @property
    def end_time(self) -> float:
        return self.end_frame / self.fps
    
    @property
    def duration(self) -> float:
        return (self.end_frame - self.start_frame) / self.fps
    
    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame


# ============================================================================
# Configuration Models
# ============================================================================

@dataclass
class ProcessingConfig:
    """Configuration for video processing pipeline"""
    # Transcription
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    
    # Output
    output_width: int = 1080
    output_height: int = 1920
    output_fps: int = 30
    
    # Video encoding
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "fast"
    crf: int = 23
    
    # Subtitle settings
    subtitle_fontsize: int = 16
    subtitle_alignment: str = "bottom"  # 'top', 'middle', 'bottom'
    
    # AI Analysis
    gemini_model: str = "gemini-2.5-flash"
    
    # Paths
    input_dir: str = "assets/input"
    output_dir: str = "assets/output"
    media_dir: str = "assets/media"
    music_dir: str = "assets/music"
