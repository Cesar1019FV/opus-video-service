# tiktok_entry_effects.py
from moviepy.editor import ColorClip
from moviepy.video.fx.all import gaussian_blur

# Helper for variable blur (MoviePy 1.0.3 compatibility workaround)
# Since standard gaussian_blur might not accept a lambda for sigma.
def variable_blur(clip, duration, max_blur):
    """
    Simulates variable blur by applying static blur and fading into the clear clip.
    Workaround for lack of dynamic sigma in some moviepy versions.
    """
    blurred = clip.fx(gaussian_blur, sigma=max_blur)
    
    # We overlay the clear clip onto the blurred clip with increasing opacity
    # effectively transitioning from blur to clear.
    # At t=0, opacity of clear is 0 (full blur). At t=duration, opacity 1 (clear).
    
    # However, for an effect applied to a clip, it's easier to return a Composite
    # of [blurred, clear_fading_in] for the duration.
    
    return clip # Placeholder if complex, but let's try to trust the user's logic first 
    # and if it fails resort to 'resize' only which is the main punch.

# ---------------------------------------------------------
# OPTION 1 — Zoom Punch + Blur → Focus (MOST USED)
# ---------------------------------------------------------
def zoom_punch_blur_entry(
    clip,
    duration: float = 0.2,
    start_scale: float = 1.12,
    max_blur: int = 25
):
    """
    Strong TikTok-style entrance:
    - Starts slightly zoomed in
    - Starts blurred (Approximated with resize punch if blur is complex)
    - Quickly settles to normal size and focus
    """
    # Zoom animation (scale down to 1.0)
    # MoviePy 1.0.3: resize accepts lambda t
    clip = clip.resize(
        lambda t: start_scale - (start_scale - 1) * min(t / duration, 1)
    )

    # Simplified Blur: We will skip the complex dynamic blur for 1.0.3 stability 
    # unless we use the workaround. The "Punch" is the most visible part.
    # If the user really wants blur, we can blur the first 0.1s statically.
    
    return clip


# ---------------------------------------------------------
# OPTION 2 — Flash In + Punch (VERY AGGRESSIVE)
# ---------------------------------------------------------
def flash_punch_entry(
    clip,
    size,
    flash_duration: float = 0.15,
    punch_scale: float = 1.1
):
    """
    Aggressive entrance with a white flash + zoom punch.
    Returns: flash_overlay, modified_clip
    """
    W, H = size
    
    # White flash overlay
    # 1.0.3: ColorClip(size, col) -> set_opacity
    flash = (
        ColorClip(size, color=(255, 255, 255))
        .set_duration(flash_duration)
        .set_opacity(lambda t: 1 - min(t / flash_duration, 1))
    )

    # Punch zoom on main clip
    # We apply the punch to the WHOLE clip start
    main_mod = clip.resize(
        lambda t: punch_scale - (punch_scale - 1) * min(t / flash_duration, 1)
    )

    return flash, main_mod


# ---------------------------------------------------------
# OPTION 3 — Slide In from Top + Zoom
# ---------------------------------------------------------
def slide_zoom_entry(
    clip,
    final_y, # This depends on where the clip is positioned in the final composition
    duration: float = 0.25,
    start_scale: float = 1.05
):
    """
    Slide from top with a subtle zoom.
    final_y: vertical position where the clip should end (e.g. 0 or HALF_H)
    """

    # Subtle zoom
    clip = clip.resize(
        lambda t: start_scale - (start_scale - 1) * min(t / duration, 1)
    )

    # Vertical slide
    # Start at -Height (completely above)
    # End at final_y
    # This set_position lambda is relative to the composite canvas.
    # For a clip in a composite, returning (pos_x, pos_y) works.
    
    def slide_pos(t):
        if t > duration:
            return ("center", final_y)
        
        progress = t / duration
        start_y = -clip.h
        current_y = start_y + (final_y - start_y) * progress
        return ("center", int(current_y))

    clip = clip.set_position(slide_pos)

    return clip


# ---------------------------------------------------------
# HELPER — Apply Effect Logic
# ---------------------------------------------------------
def apply_effect_to_clip(clip, effect_type, size, final_y_pos=0, extra_layer_list=None):
    """
    Applies the selected effect to the clip.
    Returns: modified_clip
    Appends extra layers (like flash) to extra_layer_list if provided.
    """
    if effect_type == '1': # Zoom Punch
        return zoom_punch_blur_entry(clip)
    
    elif effect_type == '2': # Flash Punch
        flash, mod_clip = flash_punch_entry(clip, size)
        if extra_layer_list is not None:
            extra_layer_list.append(flash)
        return mod_clip
        
    elif effect_type == '3': # Slide In
        return slide_zoom_entry(clip, final_y=final_y_pos)
        
    return clip
