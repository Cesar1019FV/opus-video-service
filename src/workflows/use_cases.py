"""
Individual Use Cases
Standalone workflows for specific operations.
"""
from pathlib import Path
from typing import Optional


def run_subtitles_only(
    input_path: str,
    output_dir: str = "output",
    specific_output_path: Optional[str] = None,
    alignment: str = "bottom",
    single_word: bool = False
):
    """
    Add subtitles to a complete video.
    
    Args:
        input_path: Source video
        output_dir: Output directory (used if specific_output_path not provided)
        specific_output_path: Specific output path (overrides output_dir)
        alignment: Subtitle position
        single_word: Enable word-by-word subtitles
    """
    from src.features.transcription.service import TranscriptionService
    from src.features.subtitles.service import SubtitlesService
    from rich.console import Console
    import os
    
    console = Console()
    
    # Transcribe
    console.print("[bold cyan]🎙️  Transcribing...[/]")
    transcription = TranscriptionService()
    transcript_dict = transcription.transcribe_to_dict(input_path, verbose=True)
    
    # Determine output path
    # If output_dir is "output" (legacy default) or None, use config
    if output_dir == "output":
        from src.shared.config import get_config
        output_dir = str(get_config().output_dir)
        
    if specific_output_path:
        output_path = specific_output_path
    else:
        basename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{basename}_subbed.mp4")
    
    # Add subtitles
    console.print("[bold cyan]📝 Burning subtitles...[/]")
    subtitles = SubtitlesService()
    subtitles.create_and_burn_subtitles(
        transcript_dict,
        input_path,
        output_path,
        alignment=alignment,
        single_word=single_word
    )
    
    console.print(f"[bold green]✅ Complete: {output_path}[/]")


def convert_to_vertical_split(
    top_video_path: str,
    bottom_video_path: str,
    output_path: str,
    effect_type: Optional[str] = None
):
    """
    Create split-screen vertical video.
    
    Args:
        top_video_path: Top video
        bottom_video_path: Bottom video (gameplay)
        output_path: Output path
        effect_type: Optional entry effect
    """
    from src.features.editing.split_screen import make_vertical_split_video
    from rich.console import Console
    
    console = Console()
    console.print("[bold cyan]🎬 Creating split-screen...[/]")
    
    make_vertical_split_video(
        top_video_path,
        bottom_video_path,
        output_path,
        effect_type
    )
    
    console.print(f"[bold green]✅ Complete: {output_path}[/]")


def convert_to_vertical_blur(
    input_path: str,
    output_path: str,
    title: str = "",
    effect_type: Optional[str] = None
):
    """
    Create vertical video with blurred background.
    
    Args:
        input_path: Source video
        output_path: Output path
        title: Title text
        effect_type: Optional entry effect
    """
    from src.features.editing.blur_background import make_blur_background_vertical_video
    from rich.console import Console
    
    console = Console()
    console.print("[bold cyan]🎬 Creating blur background...[/]")
    
    make_blur_background_vertical_video(
        input_path,
        output_path,
        title,
        effect_type
    )
    
    console.print(f"[bold green]✅ Complete: {output_path}[/]")


def add_background_music_to_video(
    video_path: str,
    music_path: str,
    output_path: str,
    volume: float = 0.3
):
    """
    Add background music to video.
    
    Args:
        video_path: Source video
        music_path: Music file
        output_path: Output path
        volume: Music volume (0.0-1.0)
    """
    from src.features.audio.service import AudioService
    from rich.console import Console
    
    console = Console()
    console.print("[bold cyan]🎵 Adding background music...[/]")
    
    audio = AudioService()
    audio.add_background_music(video_path, music_path, output_path, volume)
    
    console.print(f"[bold green]✅ Complete: {output_path}[/]")
