"""
Effect Implementations
Video entry effects (zoom with slide, slide in from left, etc).
MoviePy-safe version (no lambda resize / opacity bugs).
"""

from moviepy.editor import VideoClip, ColorClip
import numpy as np
import cv2


# Valid Effects for CLI/Workflows
EFFECTS = {
    '1': 'Zoom Punch + Focus',
    '2': 'Quick Slide Left',
    '3': 'Slide In Top + Zoom'
}


# ---------------------------------------------------------
# INTERNAL — Safe animated resize via fl()
# ---------------------------------------------------------
def animated_zoom(clip: VideoClip, scale_fn):
    """
    Applies a time-based zoom using MoviePy-safe frame transformation.
    """

    def fl(gf, t):
        frame = gf(t)
        scale = scale_fn(t)

        if scale == 1:
            return frame

        h, w = frame.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)

        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Center-crop back to original size
        x1 = (new_w - w) // 2
        y1 = (new_h - h) // 2
        return resized[y1:y1 + h, x1:x1 + w]

    return clip.fl(fl)


# ---------------------------------------------------------
# OPTION 1 — Zoom Punch
# ---------------------------------------------------------
def zoom_punch_effect(
    clip: VideoClip,
    duration: float = 0.2,
    start_scale: float = 1.12
) -> VideoClip:
    """
    Zoom punch effect - MoviePy safe.
    """

    def scale_fn(t):
        if duration <= 0:
            return 1
        return start_scale - (start_scale - 1) * min(t / duration, 1)

    return animated_zoom(clip, scale_fn)


# ---------------------------------------------------------
# OPTION 2 — Quick Slide In from Left
# ---------------------------------------------------------
def slide_in_left_effect(
    clip: VideoClip,
    container_width: int = 1080, # Project standard
    final_x: int or str = "center",
    final_y: int or str = "center",
    duration: float = 0.18 # Even faster for "lightning" feel
) -> VideoClip:
    """
    Very fast slide from left to exact final position with aggressive Easing.
    """
    w = clip.w
    
    # Precise target calculation
    if final_x == "center":
        target_x = (container_width - w) // 2
    elif isinstance(final_x, (int, float)):
        target_x = final_x
    else:
        target_x = 0
            
    start_x = -w

    def pos_fn(t):
        if t >= duration:
            # Return the exact requested value to let MoviePy handle strings if necessary
            # but usually numeric is better for the lock-in
            return (target_x if final_x == "center" else final_x, final_y)
        
        # Quadratic Easing Out (aggressive)
        progress = 1 - (1 - (t / duration))**2
        progress = max(0, min(1, progress)) # Safety
        
        current_x = start_x + (target_x - start_x) * progress
        return (int(current_x), final_y)

    return clip.set_position(pos_fn)


# ---------------------------------------------------------
# OPTION 3 — Slide In from Top + Zoom
# ---------------------------------------------------------
def slide_zoom_effect(
    clip: VideoClip,
    final_y: int,
    duration: float = 0.2,
    start_scale: float = 1.05
) -> VideoClip:
    """
    Slide from top with subtle zoom (MoviePy-safe).
    """

    # --- ZOOM ---
    def scale_fn(t):
        if duration <= 0:
            return 1
        return start_scale - (start_scale - 1) * min(t / duration, 1)

    clip = animated_zoom(clip, scale_fn)

    # --- SLIDE ---
    h = clip.h

    def slide_pos(t):
        if t >= duration:
            return ("center", final_y)

        progress = t / duration
        start_y = -h
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
    Applies the selected effect safely.
    """

    if not effect_type:
        return clip

    if size is None:
        size = (clip.w, clip.h)

    if effect_type == '1':
        return zoom_punch_effect(clip, duration=0.18)

    elif effect_type == '2':
        # Quick Slide Left
        return slide_in_left_effect(
            clip,
            container_width=size[0], # Correctly use container width
            final_x="center",
            final_y=final_y_pos,
            duration=0.18
        )

    elif effect_type == '3':
        return slide_zoom_effect(
            clip,
            final_y=final_y_pos,
            duration=0.18
        )

    return clip
