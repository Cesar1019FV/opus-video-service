"""
Effect Implementations
Video entry effects (zoom with slide, flash overlay, etc).
Refactored to use MoviePy's optimized methods rather than raw numpy loops for stability.
"""
from moviepy.editor import VideoClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.all import gaussian_blur
import numpy as np

# ---------------------------------------------------------
# OPTION 1 — Zoom Punch
# ---------------------------------------------------------
def zoom_punch_effect(
    clip: VideoClip, 
    duration: float = 0.2, 
    start_scale: float = 1.12
) -> VideoClip:
    """
    Zoom punch effect - starts separate from the main clip.
    """
    # Zoom animation (scale down from start_scale to 1.0)
    return clip.resize(
        lambda t: start_scale - (start_scale - 1) * min(t / duration, 1) if duration > 0 else 1
    )

# ---------------------------------------------------------
# OPTION 2 — Flash In
# ---------------------------------------------------------
def flash_punch_effect(
    clip: VideoClip, 
    size: tuple,
    flash_duration: float = 0.15,
    punch_scale: float = 1.1,
    extra_layer_list: list = None
):
    """
    Aggressive entrance with a white flash + zoom punch.
    Returns: modified_clip (and appends flash to extra_layer_list if provided)
    """
    # 1. White flash overlay
    flash = (
        ColorClip(size, color=(255, 255, 255))
        .set_duration(flash_duration)
        .set_opacity(lambda t: 1 - min(t / flash_duration, 1) if flash_duration > 0 else 0)
    )
    
    if extra_layer_list is not None:
        extra_layer_list.append(flash)

    # 2. Punch zoom on main clip
    main_mod = clip.resize(
        lambda t: punch_scale - (punch_scale - 1) * min(t / flash_duration, 1) if flash_duration > 0 else 1
    )

    return main_mod

# ---------------------------------------------------------
# OPTION 3 — Slide In from Top + Zoom
# ---------------------------------------------------------
def slide_zoom_effect(
    clip: VideoClip, 
    final_y: int, 
    duration: float = 0.25, 
    start_scale: float = 1.05
) -> VideoClip:
    """
    Slide from top with a subtle zoom.
    """
    # 1. Subtle zoom
    clip = clip.resize(
        lambda t: start_scale - (start_scale - 1) * min(t / duration, 1) if duration > 0 else 1
    )

    # 2. Vertical slide
    # Start at -Height (completely above) -> End at final_y
    def slide_pos(t):
        if t > duration:
            return ("center", final_y)
        
        progress = t / duration
        start_y = -clip.h
        current_y = start_y + (final_y - start_y) * progress
        return ("center", int(current_y))

    return clip.set_position(slide_pos)


# ---------------------------------------------------------
# HELPER — Apply Effect Logic
# ---------------------------------------------------------
def apply_effect_to_clip(
    clip: VideoClip, 
    effect_type: str, 
    size: tuple = None, 
    final_y_pos: int = 0, 
    extra_layer_list: list = None
) -> VideoClip:
    """
    Applies the selected effect to the clip.
    
    Args:
        clip: Input video clip
        effect_type: '1' (Zoom), '2' (Flash), '3' (Slide)
        size: (width, height) of the canvas/clip (required for Flash)
        final_y_pos: Target Y position for slide effect
        extra_layer_list: List to append overlay clips (like flash) to
        
    Returns:
        Modified clip
    """
    if not effect_type:
        return clip

    # Ensure size is available if needed (infer from clip if not passed)
    if size is None:
        size = (clip.w, clip.h)

    if effect_type == '1': # Zoom Punch
        # Default params from legacy
        return zoom_punch_effect(clip)
    
    elif effect_type == '2': # Flash Punch
        # Important: This modifies extra_layer_list inside
        return flash_punch_effect(clip, size, extra_layer_list=extra_layer_list)
        
    elif effect_type == '3': # Slide In
        return slide_zoom_effect(clip, final_y=final_y_pos)
        
    return clip
