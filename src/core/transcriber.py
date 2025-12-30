from faster_whisper import WhisperModel

def transcribe_video(video_path, model_size="base", device="cpu", compute_type="int8"):
    """
    Transcribes a video using Faster-Whisper.
    Returns a dictionary with full text, segments, and language info.
    """
    # print(f"🎙️  Transcribing video with Faster-Whisper ({model_size} on {device})...")
    
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    segments, info = model.transcribe(video_path, word_timestamps=True)
    
    # print(f"   Detected language '{info.language}' with probability {info.language_probability:.2f}")
    
    # Convert to standard format
    transcript_segments = []
    full_text = ""
    
    for segment in segments:
        seg_dict = {
            'text': segment.text,
            'start': segment.start,
            'end': segment.end,
            'words': []
        }
        
        if segment.words:
            for word in segment.words:
                seg_dict['words'].append({
                    'word': word.word,
                    'start': word.start,
                    'end': word.end,
                    'probability': word.probability
                })
        
        transcript_segments.append(seg_dict)
        full_text += segment.text + " "
        
    return {
        'text': full_text.strip(),
        'segments': transcript_segments,
        'language': info.language
    }
