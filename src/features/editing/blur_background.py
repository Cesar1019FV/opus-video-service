"""
Blur Background Vertical Editor
Creates vertical video with blurred background.
Logic ported from src/core/editor.py
"""
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import gaussian_blur
from src.features.effects.implementations import apply_effect_to_clip

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

    FINAL_W, FINAL_H = 1080, 1920

    # ---------------- Load source clip ----------------
    clip = VideoFileClip(input_video_path)

    # =================================================
    # BACKGROUND (blurred)
    # =================================================
    # Resize to occupy height
    bg = clip.resize(height=FINAL_H)

    # Crop center width
    if bg.w > FINAL_W:
        bg = bg.crop(x_center=bg.w / 2, width=FINAL_W)
    else:
        bg = bg.resize(width=FINAL_W)

    # Apply blur
    # Note: Using MoviePy's gaussian_blur (requires skimage or PIL)
    try:
        bg = bg.fx(gaussian_blur, sigma=blur_radius)
    except Exception as e:
        print(f"⚠️ Blur failed (skimage missing?), using resize fallback: {e}")
        # Fallback: Resize small then big
        bg = bg.resize(0.1).resize(width=FINAL_W)
        
    bg = bg.set_position((0, 0)).without_audio()

    # =================================================
    # FOREGROUND (main video)
    # =================================================
    main_width = int(FINAL_W * main_width_ratio)
    main = clip.resize(width=main_width)
    main = main.set_position(("center", "center"))

    # =================================================
    # TITLE
    # =================================================
    title_clip = None
    if title_text:
        try:
            # Check ImageMagick availability (conceptually)
            title_clip = TextClip(
                txt=title_text,
                font="Arial", 
                fontsize=80,
                color="white",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(FINAL_W - 120, None),
                align="center"
            )
            title_clip = title_clip.set_position(("center", 180))

            if title_duration is not None:
                 title_clip = title_clip.set_duration(title_duration)
            else:
                 title_clip = title_clip.set_duration(clip.duration)
                 
        except Exception as e:
            print(f"⚠️ TextClip Error (ImageMagick missing?): {e}")
            print("   Skipping Title...")
            title_clip = None

    # =================================================
    # COMPOSITION & EFFECTS
    # =================================================
    layers = [bg]
    
    if effect_type:
        # Main clip is centered
        # apply_effect_to_clip relies on size and y pos for slides
        # Center Y = (FINAL_H - main.h) // 2
        center_y = int((FINAL_H - main.h) / 2)
        
        main = apply_effect_to_clip(
            main, 
            effect_type, 
            size=(main.w, main.h), 
            final_y_pos=center_y,
            extra_layer_list=layers # Flash adds to layers
        )
        # Re-center for non-slide effects
        if effect_type in ['1', '2']:
             main = main.set_position(("center", "center"))
             
    layers.append(main)
    if title_clip: layers.append(title_clip)
    
    final = CompositeVideoClip(
        layers,
        size=(FINAL_W, FINAL_H)
    )
    final = final.set_duration(clip.duration).set_fps(fps)

    # Audio
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
        preset="fast",
        threads=4,
        verbose=False,
        logger=None
    )
    
    clip.close()
    bg.close()
    main.close()
    if title_clip: title_clip.close()
