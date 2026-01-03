"""
Subtitles Service
High-level subtitle operations.
"""
from pathlib import Path
from .renderer import SubtitleRenderer


class SubtitlesService:
    """Service for subtitle generation and burning"""
    
    def __init__(self):
        self.renderer = SubtitleRenderer()
    
    def create_and_burn_subtitles(
        self,
        transcript_dict: dict,
        video_path: str | Path,
        output_path: str | Path,
        clip_start: float = 0,
        clip_end: float = None,
        alignment: str = "bottom",
        fontsize: int = 16,
        srt_path: str | Path = None,
        single_word: bool = False
    ) -> bool:
        """
        Create SRT and burn into video in one step.
        
        Args:
            transcript_dict: Transcript dictionary
            video_path: Source video
            output_path: Output video with subtitles
            clip_start: Start offset
            clip_end: End offset (None = full video)
            alignment: Position
            fontsize: Font size
            srt_path: Optional SRT save path (default= temp file)
            single_word: If True, generate one word per subtitle block
            
        Returns:
            True if successful
        """
        if clip_end is None:
            from src.shared.ffmpeg import get_video_info
            info = get_video_info(str(video_path))
            clip_end = info.duration
        
        # Generate SRT
        if srt_path is None:
            srt_path = Path(output_path).with_suffix('.srt')
        
        self.renderer.generate_srt_from_transcript(
            transcript_dict, clip_start, clip_end, srt_path, single_word=single_word
        )
        
        # Burn to video
        self.renderer.burn_subtitles_to_video(
            video_path, srt_path, output_path, alignment, fontsize
        )
        
        return True
