import os
import tempfile
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment, silence

def extract_audio_from_video(input_path):
    """
    Extracts the audio from a video and saves it as a temporary WAV file.
    """
    video = VideoFileClip(input_path)
    audio = video.audio
    temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio_name = temp_audio_file.name
    temp_audio_file.close() # Close the file so moviepy can write to it
    
    audio.write_audiofile(temp_audio_name, logger=None)
    video.close()
    
    return temp_audio_name

def determine_silence_threshold(audio_segment, silence_duration=1500):
    """
    Analyzes the audio segment to determine a suitable silence threshold in dBFS.
    """
    chunk_length = silence_duration // 10  # shorter chunks for analysis
    loudness = [audio_segment[i:i+chunk_length].dBFS for i in range(0, len(audio_segment), chunk_length)]

    # Filter out -inf values which can occur with absolute silence
    loudness = [l for l in loudness if l != float('-inf')]
    
    if not loudness:
        return -50 # Default threshold if no loudness data

    hist, bin_edges = np.histogram(loudness, bins=100)

    peak_loudness_index = np.argmax(hist)
    silence_threshold = bin_edges[peak_loudness_index]
    
    silence_threshold -= 5  

    return silence_threshold

def get_silence_threshold(input_path):
    """
    High-level function to extract audio and determine the optimal silence threshold.
    """
    temp_audio_file = extract_audio_from_video(input_path)
    
    audio_segment = AudioSegment.from_wav(temp_audio_file)
    
    silence_threshold = determine_silence_threshold(audio_segment)    
    
    # Cleanup
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)
        
    return int(silence_threshold - 8) # tweak the level as per original recommendation

def remove_silences_from_video(input_path, output_path, silence_threshold=None, silence_duration=1500, padding=500):
    """
    Removes silent parts from a video based on an automatically or manually determined threshold.
    """
    if silence_threshold is None:
        silence_threshold = get_silence_threshold(input_path)
        
    video = VideoFileClip(input_path)
    audio = video.audio
    
    # Create temp file for audio analysis
    temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio_name = temp_audio_file.name
    temp_audio_file.close()
    
    audio.write_audiofile(temp_audio_name, logger=None)
    
    audio_segment = AudioSegment.from_wav(temp_audio_name)
    
    # Detect silent ranges
    silent_ranges = silence.detect_silence(audio_segment, min_silence_len=silence_duration, silence_thresh=silence_threshold)
    
    # Add padding to silences (wait, original logic was padding silences, let me re-read)
    # The original logic: silent_ranges = [(max(0, start-padding), min(len(audio_segment), end+padding)) for start, end in silent_ranges]
    # This actually increases the "silent" area, effectively cutting more? 
    # Usually you want to keep some air around speech. 
    # Let's stick to the blog logic for now.
    
    padded_silent_ranges = [(max(0, start - padding), min(len(audio_segment), end + padding)) for start, end in silent_ranges]
    
    # Convert silent ranges to sound ranges
    sound_ranges = []
    last_end = 0
    for start, end in padded_silent_ranges:
        if last_end < start:
            sound_ranges.append((last_end, start))
        last_end = end
        
    if last_end < len(audio_segment):
        sound_ranges.append((last_end, len(audio_segment)))
    
    # Extract clips
    clips = []
    for start, end in sound_ranges:
        start_time = start / 1000.0
        end_time = end / 1000.0
        # Sanity check for clip duration
        if end_time > start_time:
            clips.append(video.subclip(start_time, end_time))
    
    if not clips:
        # Fallback if everything was considered silent (unlikely but possible with bad threshold)
        video.close()
        os.remove(temp_audio_name)
        raise ValueError("Could not find any non-silent parts in the video with the given threshold.")

    # Concatenate and write
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(
        output_path, 
        codec='libx264', 
        audio_codec='aac', 
        preset='slow', 
        ffmpeg_params=['-crf', '18'], 
        audio_bitrate='192k',
        logger=None # Suppress moviepy logs
    )
    
    # Cleanup
    video.close()
    final_clip.close()
    for clip in clips:
        clip.close()
    
    if os.path.exists(temp_audio_name):
        os.remove(temp_audio_name)
