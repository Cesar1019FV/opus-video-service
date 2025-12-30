import os
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx, TextClip
from src.core.effects import apply_effect_to_clip

def make_vertical_split_video(
    top_video_path: str,
    bottom_video_path: str,
    output_path: str,
    loop_gameplay: bool = True,
    fps: int = 30,
    effect_type: str = None
):
    """
    Creates a split-screen video:
    - Top: Main content
    - Bottom: Gameplay/Background
    """
    print(f"🎬 Creating Split Screen Video...")
    print(f"   Top: {os.path.basename(top_video_path)}")
    print(f"   Bottom: {os.path.basename(bottom_video_path)}")
    if effect_type: print(f"   ✨ Effect: {effect_type}")

    FINAL_W, FINAL_H = 1080, 1920
    HALF_H = FINAL_H // 2

    # ---------------- Load clips ----------------
    top = VideoFileClip(top_video_path)
    bottom = VideoFileClip(bottom_video_path)

    # ---------------- TOP CLIP ----------------
    # Resize width to match final width
    top_resized = top.resize(width=FINAL_W)

    # If it's taller than half, crop center. If shorter, resize height? 
    # Usually better to resize to width, then crop height if needed.
    # If resizing to width makes height < HALF_H, we have black bars or we stretch. 
    # Let's assume we crop to fill or resize to fill.
    
    # Resize logic: Ensure it fills the half box
    if top_resized.h < HALF_H:
         # Too short, resize by height instead
         top_resized = top.resize(height=HALF_H)
         # Then crop width
         if top_resized.w > FINAL_W:
             top_resized = top_resized.crop(x_center=top_resized.w/2, width=FINAL_W)
    else:
         # Good width, maybe too tall, crop center
         top_resized = top_resized.crop(y_center=top_resized.h/2, height=HALF_H)

    top_resized = top_resized.set_position((0, 0))

    # ---------------- BOTTOM CLIP ----------------
    bottom_resized = bottom.resize(width=FINAL_W)
    
    if bottom_resized.h < HALF_H:
        bottom_resized = bottom.resize(height=HALF_H)
        if bottom_resized.w > FINAL_W:
            bottom_resized = bottom_resized.crop(x_center=bottom_resized.w/2, width=FINAL_W)
    else:
        bottom_resized = bottom_resized.crop(y_center=bottom_resized.h/2, height=HALF_H)

    # Loop gameplay ONLY if requested
    target_duration = top.duration
    
    if loop_gameplay and bottom_resized.duration < target_duration:
        bottom_resized = vfx.loop(bottom_resized, duration=target_duration)
    
    # Cut bottom to match top duration exactly
    bottom_resized = bottom_resized.subclip(0, target_duration)
    bottom_resized = bottom_resized.set_position((0, HALF_H))

    # Apply Effect (ONLY TO TOP CLIP)
    layers = [bottom_resized, top_resized] # Order: Bottom first (background-ish), Top second
    
    if effect_type:
        # Note: Slide effect needs "center" or logic adjustment if we use (0,0).
        # Our effects use "center" alignment assumption for slide, or resize logic.
        # But top_resized is at (0,0).
        # If Slide In: We need to set final pos to (0,0) manually? 
        # apply_effect_to_clip handles set_position logic for Slide.
        # For Zoom/Flash it uses resize which is safe.
        
        # We need to be careful: top_resized was set_position((0,0)). 
        # If we apply slide, it overwrites set_position.
        
        # Pass extra layers list for Flash
        top_resized = apply_effect_to_clip(
            top_resized, 
            effect_type, 
            size=(FINAL_W, HALF_H), # Effect applies to top half size
            final_y_pos=0,          # Final Y is 0
            extra_layer_list=layers
        )
        
        # Re-ensure position if effect didn't set it (Zoom/Flash don't set pos)
        if effect_type in ['1', '2']: 
             top_resized = top_resized.set_position((0,0))
             
    # ---------------- COMPOSE ----------------
    final = CompositeVideoClip(
        layers,
        size=(FINAL_W, FINAL_H)
    )
    final = final.set_duration(target_duration).set_fps(fps)

    # Keep ONLY top audio
    if top.audio:
        final = final.set_audio(top.audio)

    # ---------------- EXPORT ----------------
    # Use preset fast for speed, threads for perf
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        threads=4,
        preset='fast',
        verbose=False,
        logger=None # We will handle logging in worker or just let moviepy print bars
    )
    
    # Cleanup (MoviePy sometimes locks files)
    top.close()
    bottom.close()
    # final.close() # Composite doesn't always have close, depending on version

def make_blur_background_vertical_video(
    input_video_path: str,
    output_path: str,
    title_text: str,
    blur_radius: int = 35,
    main_width_ratio: float = 0.9,
    title_duration: float = None,
    fps: int = 30,
    effect_type: str = None
):
    """
    Creates a 9:16 (1080x1920) video with:
    - blurred background from the same source video
    - centered 16:9 foreground video
    - title text on top
    """
    print(f"🎬 Creating Blur Background Video...")
    print(f"   Input: {os.path.basename(input_video_path)}")
    print(f"   Title: {title_text}")
    if effect_type: print(f"   ✨ Effect: {effect_type}")

    from moviepy.editor import TextClip
    # Note: gaussian_blur might need to be imported from moviepy.video.fx.all
    # or we can use a custom simpler blur if moviepy's is tricky on some setups.
    # moviepy 1.0.3 standard approach:
    from moviepy.video.fx.all import gaussian_blur

    FINAL_W, FINAL_H = 1080, 1920

    # ---------------- Load source clip ----------------
    clip = VideoFileClip(input_video_path)

    # =================================================
    # BACKGROUND (blurred)
    # =================================================
    # Resize to occupy height
    bg = clip.resize(height=FINAL_H)

    # Crop center width if too wide, or resize if too narrow?
    # Usually clip.resize(height=1920) makes width > 1080 for HD landscape videos.
    # So we crop x center.
    if bg.w > FINAL_W:
        bg = bg.crop(x_center=bg.w / 2, width=FINAL_W)
    else:
        bg = bg.resize(width=FINAL_W)

    # Apply blur - sigma in 1.0.3
    # Note: moviepy's gaussian_blur uses skimage or PIL. 
    # Calling fx(gaussian_blur, sigma)
    bg = bg.fx(gaussian_blur, sigma=blur_radius)
    bg = bg.set_position((0, 0)).without_audio()

    # =================================================
    # FOREGROUND (main video)
    # =================================================
    main_width = int(FINAL_W * main_width_ratio)
    main = clip.resize(width=main_width)
    main = main.set_position(("center", "center"))

    # =================================================
    # TITLE (REQUIRED)
    # =================================================
    # WARNING: TextClip requires ImageMagick installed and configured.
    # On Windows, user might need to point IMAGEMAGICK_BINARY in config.
    try:
        title = TextClip(
            txt=title_text,
            font="Arial", # Safe font
            fontsize=80,
            color="white",
            stroke_color="black",
            stroke_width=4,
            method="caption",
            size=(FINAL_W - 120, None),
            align="center"
        )

        title = title.set_position(("center", 180)) # Slightly lower than top edge

        if title_duration is not None:
             title = title.set_duration(title_duration)
        else:
             title = title.set_duration(clip.duration)
             
    except Exception as e:
        print(f"⚠️ TextClip Error (ImageMagick missing?): {e}")
        print("   Skipping Title...")
        title = None

    # =================================================
    # COMPOSITION
    # =================================================
    layers = [bg]
    
    if effect_type:
        # Main clip is centered. Size is (main_width, approx_height).
        # We need to know its height for accurate slide? Or just trust "center".
        # apply_effect_to_clip with slide relies on "center" and y pos.
        # Main is center, center. Y pos is centered.
        
        main = apply_effect_to_clip(
            main, 
            effect_type, 
            size=(main.w, main.h), 
            final_y_pos=int(FINAL_H/2 - main.h/2), # Approx centered Y? 
            extra_layer_list=layers # Flash adds to layers
        )
        if effect_type in ['1','2']:
             main = main.set_position(("center", "center"))
             
    layers.append(main)
    if title: layers.append(title)
    
    final = CompositeVideoClip(
        layers,
        size=(FINAL_W, FINAL_H)
    )
    final = final.set_duration(clip.duration).set_fps(fps)

    # Keep ONLY original audio
    if clip.audio:
        final = final.set_audio(clip.audio)

    # =================================================
    # EXPORT
    # =================================================
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset="fast", # medium is slow
        threads=4,
        verbose=False,
        logger=None
    )
    
    clip.close()
    bg.close()
    main.close()
    if title: title.close()
