"""
Split Screen Video Editor
Creates vertical split-screen format (top + bottom).
Logic ported from src/core/editor.py
"""
import os
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx
from src.features.effects.implementations import apply_effect_to_clip

def make_vertical_split_video(
    top_video_path: str,
    bottom_video_path: str,
    output_path: str,
    loop_gameplay: bool = True, # Restored argument
    fps: int = 30,
    effect_type: str = None
):
    """
    Create vertical split-screen video.
    
    Args:
        top_video_path: Path to top video
        bottom_video_path: Path to bottom (gameplay) video  
        output_path: Output path
        loop_gameplay: Whether to loop the bottom video if it's shorter
        fps: Output FPS
        effect_type: Optional entry effect
    """
    print(f"🎬 Creating Split Screen Video...")
    
    FINAL_W, FINAL_H = 1080, 1920
    HALF_H = FINAL_H // 2
    
    # ---------------- Load clips ----------------
    top = VideoFileClip(top_video_path)
    bottom = VideoFileClip(bottom_video_path)
    
    # ---------------- TOP CLIP (Resize & Crop) ----------------
    # Robust logic: Resize to width, then crop height, or resize height then crop width
    
    # 1. Resize width to match
    top_resized = top.resize(width=FINAL_W)
    
    # 2. Check if it fills the height
    if top_resized.h < HALF_H:
         # Too short, resize by height instead to fill
         top_resized = top.resize(height=HALF_H)
         # Then crop width to fit
         if top_resized.w > FINAL_W:
             top_resized = top_resized.crop(x_center=top_resized.w/2, width=FINAL_W)
    else:
         # Good width, too tall, crop center height
         top_resized = top_resized.crop(y_center=top_resized.h/2, height=HALF_H)

    top_resized = top_resized.set_position((0, 0))

    # ---------------- BOTTOM CLIP (Resize, Crop, Loop) ----------------
    bottom_resized = bottom.resize(width=FINAL_W)
    
    if bottom_resized.h < HALF_H:
        bottom_resized = bottom.resize(height=HALF_H)
        if bottom_resized.w > FINAL_W:
            bottom_resized = bottom_resized.crop(x_center=bottom_resized.w/2, width=FINAL_W)
    else:
        bottom_resized = bottom_resized.crop(y_center=bottom_resized.h/2, height=HALF_H)

    # LOOP LOGIC
    target_duration = top.duration
    
    if loop_gameplay and bottom_resized.duration < target_duration:
        bottom_resized = vfx.loop(bottom_resized, duration=target_duration)
    
    # Cut to match
    bottom_resized = bottom_resized.subclip(0, target_duration)
    bottom_resized = bottom_resized.set_position((0, HALF_H))

    # ---------------- EFFECT APPLICATION ----------------
    layers = [bottom_resized, top_resized] # Bottom first
    
    if effect_type:
        # Use our robust apply_effect_to_clip which handles extra layers (flash)
        # and positioning for slides
        
        # Note: top_resized is at (0,0). For slide, final_y_pos is 0.
        top_resized = apply_effect_to_clip(
            top_resized, 
            effect_type, 
            size=(FINAL_W, HALF_H), 
            final_y_pos=0,
            extra_layer_list=layers
        )
        
        # Re-ensure position for effects that don't set it (Zoom/Flash)
        if effect_type in ['1', '2']: 
             top_resized = top_resized.set_position((0,0))
             
    # Update logic in case effect returned a new clip object but layers list was updated in place
    # Start fresh helper list for composite
    # layers already contains [bottom, top] (plus flash if added)
    # But we need to make sure 'top_resized' (which might be modified) is the one in the list
    
    # Re-build layers list to be safe
    final_layers = [bottom_resized, top_resized]
    
    # If flash was added to 'layers' passed to function, extract it
    # This is a bit tricky with list mutation.
    # The 'layers' list passed to apply_effect was mutated if flash was added.
    # So 'layers' now has [bottom, top, flash].
    # But 'top' in that list is the OLD top. We need the NEW top_resized.
    
    # Better approach:
    # 1. Create list [bottom]
    # 2. Apply effect (passing that list) -> adds flash if needed
    # 3. Add modified top to that list
    
    composite_layers = [bottom_resized]
    top_resized = apply_effect_to_clip(
        top_resized,
        effect_type,
        size=(FINAL_W, HALF_H),
        final_y_pos=0,
        extra_layer_list=composite_layers 
    )
    if effect_type in ['1', '2']:
        top_resized = top_resized.set_position((0,0))
        
    composite_layers.append(top_resized)

    # ---------------- COMPOSE ----------------
    final = CompositeVideoClip(
        composite_layers,
        size=(FINAL_W, FINAL_H)
    )
    final = final.set_duration(target_duration).set_fps(fps)

    # Audio from top
    if top.audio:
        final = final.set_audio(top.audio)
        
    # ---------------- EXPORT ----------------
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        threads=4, # Use threads for speed
        preset='fast',
        verbose=False,
        logger=None 
    )
    
    # Cleanup
    top.close()
    bottom.close()
    # final.close()
