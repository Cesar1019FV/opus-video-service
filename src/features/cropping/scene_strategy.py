import cv2

def create_general_frame(frame, output_width, output_height):
    """
    Creates a general frame composition with a blurred background
    and centered foreground.
    """
    orig_h, orig_w = frame.shape[:2]
    
    # 1. Background
    bg_scale = output_height / orig_h
    bg_w = int(orig_w * bg_scale)
    bg_resized = cv2.resize(frame, (bg_w, output_height))
    
    start_x = (bg_w - output_width) // 2
    if start_x < 0: start_x = 0
    background = bg_resized[:, start_x:start_x+output_width]
    if background.shape[1] != output_width:
        background = cv2.resize(background, (output_width, output_height))
        
    background = cv2.GaussianBlur(background, (51, 51), 0)
    
    # 2. Foreground
    scale = output_width / orig_w
    fg_h = int(orig_h * scale)
    foreground = cv2.resize(frame, (output_width, fg_h))
    
    # 3. Overlay
    y_offset = (output_height - fg_h) // 2
    final_frame = background.copy()
    
    # Handle edge cases where resize might result in slightly different dimensions
    # essentially just strict bounds checking
    fg_h_end = y_offset + fg_h
    if fg_h_end > output_height:
        fg_h_end = output_height
        foreground = foreground[:(fg_h_end-y_offset), :]
        
    final_frame[y_offset:fg_h_end, :] = foreground
    
    return final_frame
