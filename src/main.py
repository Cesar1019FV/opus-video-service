import argparse
import sys
import os
import json
import subprocess
import time
from tqdm import tqdm
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text

# Initialize Console
console = Console()

# Core Modules
from src.core.scenes import detect_scenes, analyze_scenes_strategy
from src.core.transcriber import transcribe_video
from src.core.analyzer import get_viral_clips
from src.core.cropper import SmoothedCameraman, SpeakerTracker, detect_face_candidates, detect_person_yolo, create_general_frame, ASPECT_RATIO

# Utils
from src.utils.video import get_video_resolution, download_youtube_video
from src.utils.subtitles import generate_srt, burn_subtitles

load_dotenv()

def process_single_clip(input_video, output_path, start_time, end_time, fps, original_width, original_height, horizontal_mode=False):
    """
    Cuts a segment.
    If horizontal_mode=True: Fast cut with re-encoding (to ensure frame accuracy) or stream copy if precise enough.
    If horizontal_mode=False: Applies Face Tracking & Vertical Crop.
    """
    
    # 1. Horizontal Mode (Fast Cut, preserve Aspect Ratio)
    if horizontal_mode:
        # We use re-encoding to ensure exact frame cuts. 
        command = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', input_video,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac',
            output_path
        ]
        # print(f"✂️ Cutting Horizontal Clip: {start_time}-{end_time}")
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return

    # 2. Vertical Mode (9:16 Crop with AI Tracking)
    # 1. Detect Scenes for this clip range? 
    # Actually, we should probably treat the clip as a video.
    # But cutting first prevents analyzing the whole video again.
    # However, logic in OpenShorts analyzed the *cut* clip or the *whole* video?
    # OpenShorts: process_video_to_vertical took the CLIP as input (temp_video_output).
    
    # So we need to cut it first.
    base_name = os.path.splitext(output_path)[0]
    temp_cut = f"{base_name}_raw_cut.mp4"
    
    cut_cmd = [
        'ffmpeg', '-y', 
        '-ss', str(start_time), 
        '-to', str(end_time), 
        '-i', input_video,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', 
        '-c:a', 'aac', 
        temp_cut
    ]
    subprocess.run(cut_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    if not os.path.exists(temp_cut):
        print("❌ Failed to cut video segment.")
        return False


    # Now process this cut segment
    # Detect scenes inside this small clip
    scenes, clip_fps = detect_scenes(temp_cut)
    
    if not scenes:
        # One scene
        from scenedetect import FrameTimecode
        cap = subprocess.VideoCapture(temp_cut) # Wait, cv2
        import cv2
        cap = cv2.VideoCapture(temp_cut)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        clip_fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        scenes = [(FrameTimecode(0, clip_fps), FrameTimecode(total_frames, clip_fps))]

    # Analyze Strategy
    strategies = analyze_scenes_strategy(temp_cut, scenes, detect_face_candidates)
    
    # Process
    # Setup Output
    OUTPUT_HEIGHT = original_height # Preserving resolution of source? 
    # Usually we want vertical 1080x1920 or similar.
    # If source is 1920x1080, output height 1080? No, usually we want 1920 height?
    # OpenShorts used: OUTPUT_HEIGHT = original_height. 
    # If input 1920x1080 (HD), output 608x1080.
    # If input 4k (3840x2160), output 1216x2160.
    
    # OpenShorts logic:
    # OUTPUT_HEIGHT = original_height
    # OUTPUT_WIDTH = int(OUTPUT_HEIGHT * ASPECT_RATIO)
    
    # Let's get resolution of the CUT clip
    cut_w, cut_h = get_video_resolution(temp_cut)
    
    OUTPUT_HEIGHT = cut_h
    OUTPUT_WIDTH = int(OUTPUT_HEIGHT * ASPECT_RATIO)
    if OUTPUT_WIDTH % 2 != 0: OUTPUT_WIDTH += 1
    
    temp_processed = f"{base_name}_processed.mp4"
    
    # Initialize Tracker
    cameraman = SmoothedCameraman(OUTPUT_WIDTH, OUTPUT_HEIGHT, cut_w, cut_h)
    speaker_tracker = SpeakerTracker()
    
    # FFmpeg Pipe
    import cv2
    command = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{OUTPUT_WIDTH}x{OUTPUT_HEIGHT}', '-pix_fmt', 'bgr24',
        '-r', str(clip_fps), '-i', '-', '-c:v', 'libx264',
        '-preset', 'fast', '-crf', '23', '-an', temp_processed
    ]
    ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    cap = cv2.VideoCapture(temp_cut)
    frame_number = 0
    current_scene_index = 0
    scene_boundaries = [(s.get_frames(), e.get_frames()) for s, e in scenes]
    
    # Scene processing with Progress Bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task(f"✂️  Cropping & Retiming...", total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # update scene
            if current_scene_index < len(scene_boundaries):
                start_f, end_f = scene_boundaries[current_scene_index]
                if frame_number >= end_f and current_scene_index < len(scene_boundaries) - 1:
                    current_scene_index += 1
            
            strategy = strategies[current_scene_index] if current_scene_index < len(strategies) else 'TRACK'
            
            if strategy == 'GENERAL':
                output_frame = create_general_frame(frame, OUTPUT_WIDTH, OUTPUT_HEIGHT)
                cameraman.current_center_x = cut_w / 2
                cameraman.target_center_x = cut_w / 2
            else:
                # TRACK
                if frame_number % 2 == 0:
                    candidates = detect_face_candidates(frame)
                    target_box = speaker_tracker.get_target(candidates, frame_number, cut_w)
                    if target_box:
                        cameraman.update_target(target_box)
                    else:
                        p_box = detect_person_yolo(frame)
                        if p_box: cameraman.update_target(p_box)
                
                is_scene_start = (frame_number == scene_boundaries[current_scene_index][0])
                x1, y1, x2, y2 = cameraman.get_crop_box(force_snap=is_scene_start)
                
                if y2 > y1 and x2 > x1:
                    cropped = frame[y1:y2, x1:x2]
                    output_frame = cv2.resize(cropped, (OUTPUT_WIDTH, OUTPUT_HEIGHT))
                else:
                     output_frame = cv2.resize(frame, (OUTPUT_WIDTH, OUTPUT_HEIGHT))
                     
            ffmpeg_process.stdin.write(output_frame.tobytes())
            frame_number += 1
            progress.update(task_id, advance=1)
        
    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()
    cap.release()
    
    # Merge Audio from cut segment
    # Extract audio from cut segment
    temp_audio = f"{base_name}_audio.aac"
    subprocess.run(['ffmpeg', '-y', '-i', temp_cut, '-vn', '-acodec', 'copy', temp_audio], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # Merge
    if os.path.exists(temp_audio):
         merge = ['ffmpeg', '-y', '-i', temp_processed, '-i', temp_audio, '-c:v', 'copy', '-c:a', 'copy', output_path]
    else:
         merge = ['ffmpeg', '-y', '-i', temp_processed, '-c:v', 'copy', output_path]
         
    subprocess.run(merge, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # Cleanup
    for f in [temp_cut, temp_processed, temp_audio]:
        if os.path.exists(f): os.remove(f)
        
    return True

def run_pipeline(input_path=None, url=None, output_dir="output", use_subs=False, skip_analysis=False, alignment="bottom", keep_horizontal=False):
    """
    Main logic pipeline extracted for reusability.
    """
    if not input_path and not url:
        console.print("[bold red]❌ Must provide input path or url[/]")
        return

    os.makedirs(output_dir, exist_ok=True)
    output_dir = os.path.abspath(output_dir)
    
    # 1. Acquire Video
    if url:
        video_path, title = download_youtube_video(url, output_dir)
    else:
        video_path = os.path.abspath(input_path)
        title = os.path.splitext(os.path.basename(video_path))[0]
        
    if not os.path.exists(video_path):
        console.print(f"[bold red]❌ File not found: {video_path}[/]")
        return
        
    console.print(f"[bold cyan]🎬 Processing: {title}[/]")
    console.print(f"[dim]Format: {'Horizontal (Original)' if keep_horizontal else 'Vertical (9:16 AI Crop)'}[/]")
    if use_subs:
        console.print(f"[dim]Subtitle Alignment: {alignment}[/]")
    
    # 2. Transcribe & Analyze
    if skip_analysis:
        console.print("[yellow]⏩ Skipping analysis. Processing full video.[/]")
        output_file = os.path.join(output_dir, f"{title}_{'full' if keep_horizontal else 'vertical'}.mp4")
        w, h = get_video_resolution(video_path)
        
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frames / fps
        cap.release()
        
        process_single_clip(video_path, output_file, 0, duration, fps, w, h, horizontal_mode=keep_horizontal)
        if use_subs:
             console.print("[red]⚠️ Cannot burn subtitles without transcription (mocking empty subs not implemented).[/]")
             
    else:
        # Transcribe
        with console.status("[bold green]🎙️  Transcribing video...[/]", spinner="dots"):
            transcript = transcribe_video(video_path)
        
        # Calculate duration
        w, h = get_video_resolution(video_path)
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frames / fps
        cap.release()

        # Gemini
        with console.status("[bold blue]🧠  Analyzing viral clips with Gemini...[/]", spinner="earth"):
            clips_data = get_viral_clips(transcript, duration)
        
        if not clips_data or 'shorts' not in clips_data:
            console.print("[bold red]❌ No viral clips found.[/]")
            return
            
        # Save Metadata
        meta_path = os.path.join(output_dir, f"{title}_metadata.json")
        clips_data['transcript'] = transcript
        with open(meta_path, 'w') as f:
            json.dump(clips_data, f, indent=2)
            
        console.print(f"[bold green]🔥 Found {len(clips_data['shorts'])} clips.[/]")
        
        for i, clip in enumerate(clips_data['shorts']):
            console.print(Panel(f"[bold]Clip {i+1}:[/] {clip.get('video_title_for_youtube_short', 'Untitled')}\n[dim]Timestamp: {clip['start']}s - {clip['end']}s[/]", border_style="cyan"))
            
            clip_name = f"{title}_clip_{i+1}.mp4"
            final_path = os.path.join(output_dir, clip_name)
            
            process_single_clip(video_path, final_path, clip['start'], clip['end'], fps, w, h, horizontal_mode=keep_horizontal)
            
            if use_subs:
                with console.status(f"[bold yellow]📝 Burning subtitles for Clip {i+1}...[/]", spinner="aesthetic"):
                    srt_path = os.path.join(output_dir, f"{title}_clip_{i+1}.srt")
                    has_words = generate_srt(transcript, clip['start'], clip['end'], srt_path)
                    
                    if has_words:
                        subbed_path = os.path.join(output_dir, f"{title}_clip_{i+1}_subbed.mp4")
                        burn_subtitles(final_path, srt_path, subbed_path, alignment=alignment)
                        console.print(f"   [green]✅ Subtitled version ready: {os.path.basename(subbed_path)}[/]")

    console.print("\n[bold green]✅ All tasks completed![/]")

def run_subtitles_only(input_path, output_dir="output", alignment="bottom", specific_output_path=None):
    """
    Workflow: Transcribe -> Generate SRT -> Burn Subtitles (No Cuts, No Crop)
    """
    if not input_path or not os.path.exists(input_path):
        console.print("[bold red]❌ Input file not found[/]")
        return
    
    input_video = os.path.abspath(input_path)
    base_name = os.path.splitext(os.path.basename(input_video))[0]
    
    if specific_output_path:
        subbed_path = specific_output_path
        output_dir = os.path.dirname(subbed_path) # Ensure dir exists
    else:
        os.makedirs(output_dir, exist_ok=True)
        subbed_path = os.path.join(output_dir, f"{base_name}_subbed.mp4")

    os.makedirs(output_dir, exist_ok=True)
    
    console.print(f"[bold cyan]🎬 Processing Subtitles Only: {base_name}[/]")
    console.print(f"[dim]Alignment: {alignment}[/]")

    # 1. Transcribe
    with console.status("[bold green]🎙️  Transcribing video...[/]", spinner="dots"):
        transcript = transcribe_video(input_video)
        
    # 2. Generate SRT (Full video)
    srt_path = os.path.join(output_dir, f"{base_name}.srt")
    
    # Calculate duration needed for SRT generation? 
    # generate_srt expects clip_start/end. For full video: 0 to infinite.
    # We need video duration.
    import cv2
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frames / fps
    cap.release()
    
    with console.status("[bold yellow]📝 Generating SRT...[/]", spinner="aesthetic"):
        generate_srt(transcript, 0, duration, srt_path)
        
    # 3. Burn
    # subbed_path defined at start
    
    with console.status(f"[bold red]🔥 Burning subtitles ({alignment})...[/]", spinner="fire"):
        try:
            burn_subtitles(input_video, srt_path, subbed_path, alignment=alignment)
            console.print(f"[bold green]✅ Success! Saved to: {subbed_path}[/]")
        except Exception as e:
             console.print(f"[bold red]❌ Failed to burn subtitles: {e}[/]")

def main():
    parser = argparse.ArgumentParser(description="Opus Video Service - Viral Clips CLI")
    parser.add_argument('-i', '--input', help="Input video file path")
    parser.add_argument('-u', '--url', help="YouTube URL")
    parser.add_argument('-o', '--output', default="output", help="Output directory")
    parser.add_argument('--subs', action='store_true', help="Burn subtitles")
    parser.add_argument('--skip-analysis', action='store_true', help="Skip Gemini and process whole video")
    parser.add_argument('--subs-only', action='store_true', help="Only burn subtitles (no crop/cut)")
    parser.add_argument('--align', default="bottom", choices=['top', 'middle', 'bottom'], help="Subtitle alignment")
    
    args = parser.parse_args()
    
    if args.subs_only:
        if not args.input:
             print("❌ --subs-only requires -i (local file)")
             sys.exit(1)
        run_subtitles_only(args.input, args.output, args.align)
        return
    
    if not args.input and not args.url:
        print("❌ Must provide -i or -u")
        sys.exit(1)
    
    run_pipeline(
        input_path=args.input,
        url=args.url,
        output_dir=args.output,
        use_subs=args.subs,
        skip_analysis=args.skip_analysis
    )
