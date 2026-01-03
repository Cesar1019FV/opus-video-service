from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def add_background_music_overlay(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.3,
    loop_music: bool = True
):
    """
    Adds background music overlay to a video while preserving original audio.
    """
    try:
        # Load video with original audio
        video = VideoFileClip(video_path)
        
        # Check if video has audio
        if video.audio is None:
            # No original audio, just set music as audio
            music = AudioFileClip(music_path).volumex(music_volume)
            
            # Loop music if shorter than video AND enabled
            if loop_music and music.duration < video.duration:
                music = music.audio_loop(duration=video.duration)
            
            if loop_music:
                music = music.set_duration(video.duration)
            else:
                music = music.set_duration(min(music.duration, video.duration))

            final = video.set_audio(music)
        else:
            # Load and adjust music volume
            music = AudioFileClip(music_path).volumex(music_volume)
            
            # Loop music if shorter than video AND enabled
            if loop_music and music.duration < video.duration:
                music = music.audio_loop(duration=video.duration)
            
            if loop_music:
                music = music.set_duration(video.duration)
            else:
                music = music.set_duration(min(music.duration, video.duration))
            
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
        
    except Exception as e:
        print(f"Error adding background music: {e}")
        return False
