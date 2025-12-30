from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def add_background_music_overlay(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.3
):
    """
    Adds background music overlay to a video while preserving original audio.
    
    Args:
        video_path: Path to input video
        music_path: Path to music file (mp3/wav/etc)
        output_path: Path for output video
        music_volume: Volume multiplier for background music (0.0-1.0), default 0.3
    """
    # Load video with original audio
    video = VideoFileClip(video_path)
    
    # Check if video has audio
    if video.audio is None:
        # No original audio, just set music as audio
        music = AudioFileClip(music_path).volumex(music_volume)
        # Loop music if shorter than video
        if music.duration < video.duration:
            music = music.audio_loop(duration=video.duration)
        final = video.set_audio(music.set_duration(video.duration))
    else:
        # Load and adjust music volume
        music = AudioFileClip(music_path).volumex(music_volume)
        
        # Loop music if it's shorter than the video
        if music.duration < video.duration:
            music = music.audio_loop(duration=video.duration)
        
        # Trim music if longer than video
        music = music.set_duration(video.duration)
        
        # Overlay music on top of original audio
        final_audio = CompositeAudioClip([
            video.audio,  # Original audio (e.g., podcast, dialogue)
            music         # Background music
        ])
        
        # Attach combined audio back to video
        final = video.set_audio(final_audio)
    
    # Export with safe codec settings
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        verbose=False,
        logger=None
    )
    
    # Clean up
    video.close()
    if final:
        final.close()
    
    return True
