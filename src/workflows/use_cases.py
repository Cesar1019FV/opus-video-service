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
    single_word: bool = False,
    style_name: str = "default"
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
        single_word=single_word,
        style_name=style_name
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
    effect_type: Optional[str] = None,
    style_name: str = "default"
):
    """
    Create vertical video with blurred background.
    
    Args:
        input_path: Source video
        output_path: Output path
        title: Title text
        effect_type: Optional entry effect
        style_name: Subtitle style to apply to title
    """
    from src.features.editing.blur_background import make_blur_background_vertical_video
    from rich.console import Console
    import os
    import time
    
    console = Console()
    
    # Step 1: Create Blur Background with FFmpeg
    console.print("[bold cyan]🎬 Creating blur background (Step 1/2)...[/]")
    
    # If we have an effect, we need a temp file for the first step
    final_output = output_path
    if effect_type:
        timestamp = int(time.time())
        process_path = output_path.replace('.mp4', f'_base_{timestamp}.mp4')
    else:
        process_path = final_output

    try:
        make_blur_background_vertical_video(
            input_path,
            process_path,
            title,
            effect_type=None, # Blur editor doesn't handle hooks internally anymore
            style_name=style_name
        )
        
        # Step 2: Apply Hook Effect if needed
        if effect_type:
            console.print(f"[bold cyan]✨ Applying hook effect '{effect_type}' (Step 2/2)...[/]")
            add_hook_effect_to_video(process_path, final_output, effect_type)
            
            # Clean up temp base file
            if os.path.exists(process_path) and process_path != final_output:
                try:
                    os.remove(process_path)
                except:
                    pass
        
        console.print(f"[bold green]✅ Complete: {final_output}[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error in workflow: {e}[/]")
        if effect_type and 'process_path' in locals() and os.path.exists(process_path):
             # If step 2 failed, maybe keep step 1 as a backup or clean up
             pass
        raise e


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


def add_hook_effect_to_video(
    input_path: str,
    output_path: str,
    effect_type: str
):
    """
    Apply a hook effect to a video.
    
    Args:
        input_path: Source video
        output_path: Output path
        effect_type: '1'=zoom, '2'=flash, '3'=slide
    """
    from moviepy.editor import VideoFileClip, CompositeVideoClip
    from src.features.effects.implementations import apply_effect_to_clip
    from rich.console import Console
    
    console = Console()
    console.print(f"[bold cyan]🎬 Applying hook effect ({effect_type})...[/]")
    
    clip = VideoFileClip(input_path)
    
    # We use a list for layers because some effects (like flash) add overlay layers
    layers = []
    
    # Calculate final_y for slide effect (centered)
    final_y = 0 # Default for non-vertical might be different, but we'll stick to center if possible
    
    # Apply effect
    modified_main = apply_effect_to_clip(
        clip, 
        effect_type, 
        size=(clip.w, clip.h),
        final_y_pos=0,
        extra_layer_list=layers
    )
    
    # If it's zoom/flash, we usually want it centered if it's not a slide
    if effect_type == '1':
         modified_main = modified_main.set_position("center")
    
    layers.append(modified_main)
    
    final = CompositeVideoClip(layers, size=(clip.w, clip.h))
    final = final.set_duration(clip.duration).set_audio(clip.audio)
    
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=clip.fps,
        logger=None
    )
    
    clip.close()
    final.close()
    
    console.print(f"[bold green]✅ Complete: {output_path}[/]")

