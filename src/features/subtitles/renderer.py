import subprocess
import os

class SubtitleRenderer:
    """
    Renders subtitles to SRT and burns them into video.
    """

    def generate_srt_from_transcript(self, transcript, clip_start, clip_end, output_path, max_chars=20, max_duration=2.0, single_word=False):
        """
        Generates SRT file from transcript within the time range[clip_start, clip_end].
        Args:
            single_word: If True, each word is a separate subtitle block (dynamic style).
        """
        words = []
        # 1. Extract and flatten words within range
        for segment in transcript.get('segments', []):
            for word_info in segment.get('words', []):
                if word_info['end'] > clip_start and word_info['start'] < clip_end:
                    words.append(word_info)
        
        if not words:
            # Create an empty file to avoid errors downstream if no speech
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("")
            return False

        srt_content = ""
        index = 1
        
        # SINGLE WORD MODE (Dynamic)
        if single_word:
            for word in words:
                start = max(0, word['start'] - clip_start)
                end = max(0, word['end'] - clip_start)
                
                # Minimum duration for readability? 
                # Ideally word-level is fast, but 0.1s might be too fast?
                # Let's stick to exact timestamps for "dynamic" feel.
                
                text = word['word'].strip()
                srt_content += self._format_srt_block(index, start, end, text)
                index += 1
                
        # STANDARD PHRASE MODE
        else:
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
                        srt_content += self._format_srt_block(index, block_start, block_end, text)
                        index += 1
                        
                        current_block = [word]
                        block_start = start
                    else:
                        current_block.append(word)
            
            if current_block:
                block_end = current_block[-1]['end'] - clip_start
                text = " ".join([w['word'] for w in current_block]).strip()
                srt_content += self._format_srt_block(index, block_start, block_end, text)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return True

    def _format_srt_block(self, index, start, end, text):
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
        return f"{index}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n"

    def burn_subtitles_to_video(self, video_path, srt_path, output_path, alignment="bottom", fontsize=16):
        """
        Burns subtitles into the video using FFmpeg.
        """
        final_fontsize = int(fontsize * 0.5) 
        if final_fontsize < 8: final_fontsize = 8

        ass_alignment = 2 # Default Bottom
        if str(alignment).lower() == 'top': ass_alignment = 6
        if str(alignment).lower() == 'middle': ass_alignment = 10

        try:
            # Cross-platform safe path for ffmpeg filter
            safe_srt_path = str(srt_path).replace('\\', '/').replace(':', '\\:')
        except:
            safe_srt_path = str(srt_path)

        # Ensure srt path exists
        if not os.path.exists(str(srt_path)):
            # If no subtitles, just copy video
            cmd_copy = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-c', 'copy',
                str(output_path)
            ]
            subprocess.run(cmd_copy, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True

        style_string = f"Alignment={ass_alignment},Fontname=Verdana,Fontsize={final_fontsize},PrimaryColour=&H00FFFFFF,OutlineColour=&H60000000,BackColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=25,Bold=1"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vf', f"subtitles='{safe_srt_path}':force_style='{style_string}'",
            '-c:a', 'copy',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr.decode()}")

        return True
