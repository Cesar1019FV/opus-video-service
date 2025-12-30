import subprocess

def generate_srt(transcript, clip_start, clip_end, output_path, max_chars=20, max_duration=2.0):
    words = []
    # 1. Extract and flatten words within range
    for segment in transcript.get('segments', []):
        for word_info in segment.get('words', []):
            if word_info['end'] > clip_start and word_info['start'] < clip_end:
                words.append(word_info)
    
    if not words:
        return False

    srt_content = ""
    index = 1
    
    current_block = []
    block_start = None
    
    for i, word in enumerate(words):
        start = max(0, word['start'] - clip_start)
        end = max(0, word['end'] - clip_start)
        
        if not current_block:
            current_block.append(word)
            block_start = start
        else:
            current_text_len = sum(len(w['word']) + 1 for w in current_block)
            duration = end - block_start
            
            if current_text_len + len(word['word']) > max_chars or duration > max_duration:
                block_end = current_block[-1]['end'] - clip_start
                
                text = " ".join([w['word'] for w in current_block]).strip()
                srt_content += format_srt_block(index, block_start, block_end, text)
                index += 1
                
                current_block = [word]
                block_start = start
            else:
                current_block.append(word)
    
    if current_block:
        block_end = current_block[-1]['end'] - clip_start
        text = " ".join([w['word'] for w in current_block]).strip()
        srt_content += format_srt_block(index, block_start, block_end, text)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
        
    return True

def format_srt_block(index, start, end, text):
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
    return f"{index}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n"

def burn_subtitles(video_path, srt_path, output_path, alignment=2, fontsize=16):
    final_fontsize = int(fontsize * 0.5) 
    if final_fontsize < 8: final_fontsize = 8

    ass_alignment = 2 # Default Bottom
    if str(alignment).lower() == 'top': ass_alignment = 6
    if str(alignment).lower() == 'middle': ass_alignment = 10

    try:
        safe_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
    except:
        safe_srt_path = srt_path

    style_string = f"Alignment={ass_alignment},Fontname=Verdana,Fontsize={final_fontsize},PrimaryColour=&H00FFFFFF,OutlineColour=&H60000000,BackColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=25,Bold=1"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', f"subtitles='{safe_srt_path}':force_style='{style_string}'",
        '-c:a', 'copy',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        output_path
    ]
    
    # print(f"🎬 Burning subtitles: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        # print(f"❌ FFmpeg Subtitle Error: {result.stderr.decode()}")
        raise Exception(f"FFmpeg failed: {result.stderr.decode()}")

    return True
