"""
Main Pipeline Orchestrator
High-level workflow for viral clips detection and processing.
Consolidates logic from src/main.py run_pipeline function.
"""
from pathlib import Path
from typing import Optional

# New imports
from src.shared.ffmpeg import get_video_info, get_video_resolution
from src.features.cropping.service import process_viral_clip_with_smart_crop
from src.shared.config import get_config


class ViralClipsPipeline:
    """
    Main pipeline for processing videos into viral clips.
    Orchestrates: download -> transcribe -> analyze -> crop -> subtitle
    """
    
    def __init__(self):
        # Lazy load services to avoid circular imports
        self._transcription_service = None
        self._viral_clips_service = None
        self._subtitle_renderer = None
    
    @property
    def transcription_service(self):
        if self._transcription_service is None:
            from src.features.transcription.service import TranscriptionService
            self._transcription_service = TranscriptionService()
        return self._transcription_service
    
    @property
    def viral_clips_service(self):
        if self._viral_clips_service is None:
            from src.features.viral_clips.service import ViralClipsService
            self._viral_clips_service = ViralClipsService()
        return self._viral_clips_service
    
    @property
    def subtitle_renderer(self):
        if self._subtitle_renderer is None:
            from src.features.subtitles.renderer import SubtitleRenderer
            self._subtitle_renderer = SubtitleRenderer()
        return self._subtitle_renderer
    
    def run(
        self,
        input_path: str,
        output_dir: Optional[str] = None,
        use_subs: bool = False,
        skip_analysis: bool = False,
        alignment: str = "bottom",
        single_word: bool = False
    ):
        """
        Execute the viral clips pipeline on a local video file.
        """
        from rich.console import Console
        console = Console()
        
        # Default output_dir from config if not provided
        if not output_dir or output_dir == "output":
            output_dir = str(get_config().output_dir)
        
        if not input_path:
            console.print("[bold red]❌ No input provided[/]")
            return
        
        # Step 2: Transcribe
        console.print(f"[bold cyan]🎙️  Transcribing audio...[/]")
        transcript_dict = self.transcription_service.transcribe_to_dict(input_path, verbose=True)
        console.print(f"[bold green]✅ Transcription complete[/]")
        
        # Step 3: Analyze or process whole video
        if not skip_analysis:
            console.print(f"[bold cyan]🧠 Analyzing with Gemini AI...[/]")
            from src.shared.ffmpeg import get_video_info
            video_info = get_video_info(input_path)
            
            try:
                clips = self.viral_clips_service.find_viral_clips(
                    transcript_dict,
                    video_info.duration
                )
                console.print(f"[bold green]✅ Found {len(clips)} viral moments[/]")
                
                # Process each clip
                for i, clip in enumerate(clips, 1):
                    console.print(f"\n[bold magenta]Processing Clip {i}/{len(clips)}...[/]")
                    self._process_single_clip(
                        input_path,
                        clip.start,
                        clip.end,
                        transcript_dict,
                        output_dir,
                        use_subs,
                        alignment,
                        f"clip_{i}",
                        single_word
                    )
            except Exception as e:
                console.print(f"[bold red]❌ AI Analysis failed: {e}[/]")
                console.print("[yellow]Processing entire video instead...[/]")
                skip_analysis = True
        
        if skip_analysis:
            # Process entire video
            console.print(f"[bold cyan]📹 Processing entire video...[/]")
            from src.shared.ffmpeg import get_video_info
            video_info = get_video_info(input_path)
            
            self._process_single_clip(
                input_path,
                0,
                video_info.duration,
                transcript_dict,
                output_dir,
                use_subs,
                alignment,
                "full_video",
                single_word
            )
        
        console.print(f"\n[bold green]✨ Pipeline complete![/]")
    
    def _process_single_clip(
        self,
        input_path: str,
        start: float,
        end: float,
        transcript_dict: dict,
        output_dir: str,
        use_subs: bool,
        alignment: str,
        clip_name: str,
        single_word: bool = False
    ):
        """Process a single clip: crop and optionally add subtitles"""
        from rich.console import Console
        import os
        
        console = Console()
        
        # Output paths
        cropped_path = os.path.join(output_dir, f"{clip_name}_vertical.mp4")
        
        # Crop to vertical
        console.print(f"  ✂️  Cropping to vertical format...")
        process_viral_clip_with_smart_crop(
            input_path,
            start,
            end,
            cropped_path
        )
        
        # Add subtitles if requested
        if use_subs:
            console.print(f"  📝 Adding subtitles...")
            final_path = os.path.join(output_dir, f"{clip_name}_subbed.mp4")
            srt_path = os.path.join(output_dir, f"{clip_name}.srt")
            
            self.subtitle_renderer.generate_srt_from_transcript(
                transcript_dict,
                start,
                end,
                srt_path,
                single_word=single_word
            )
            
            self.subtitle_renderer.burn_subtitles_to_video(
                cropped_path,
                srt_path,
                final_path,
                alignment
            )
            
            console.print(f"  [bold green]✅ Saved: {final_path}[/]")
        else:
            console.print(f"  [bold green]✅ Saved: {cropped_path}[/]")


# Legacy function for backward compatibility
def run_pipeline(
    input_path: str,
    output_dir: str = "output",
    use_subs: bool = False,
    skip_analysis: bool = False,
    alignment: str = "bottom",
    single_word: bool = False
):
    """Legacy function maintaining updated signature"""
    pipeline = ViralClipsPipeline()
    pipeline.run(input_path, output_dir, use_subs, skip_analysis, alignment, single_word)
