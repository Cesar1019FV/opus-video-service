"""
Cropping Service - Main orchestrator
Smart video cropping with face/person tracking.
Consolidates logic from separate cropping modules.
"""
import cv2
import os
from pathlib import Path
from tqdm import tqdm

from .tracking import SmoothedCameraman, SpeakerTracker
from .detectors import detect_face_candidates, detect_person_yolo
from .scene_strategy import create_general_frame
from .scenes import detect_scenes, analyze_scenes_strategy

class CroppingService:
    """
    Service for intelligent video cropping.
    Orchestrates detection, tracking, and rendering of vertical videos.
    """
    
    def crop_video_to_vertical(
        self,
        input_path: str,
        output_path: str,
        start_time: float = 0.0,
        end_time: float = None
    ):
        """
        Crop video to vertical format with smart tracking.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            start_time: Start time in seconds
            end_time: End time in seconds (None for full duration)
        """
        print(f"✂️  Smart Cropping: {os.path.basename(input_path)}")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {input_path}")
            
        # Video Properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate frame range
        start_frame = int(start_time * fps)
        if end_time:
            end_frame = int(end_time * fps)
        else:
            end_frame = total_frames
            
        duration_frames = end_frame - start_frame
        
        # Initialize Output
        target_height = 1920
        target_width = 1080
        
        # Initialize Trackers
        cameraman = SmoothedCameraman(target_width, target_height, width, height)
        speaker_tracker = SpeakerTracker(stabilization_frames=int(fps/2)) # 0.5s stabilization
        
        # Initialize Writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
        
        # Seek to start
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Main Loop
        pbar = tqdm(total=duration_frames, desc="   Processing Frames", unit="fr")
        
        current_frame_idx = start_frame
        
        try:
            while current_frame_idx < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 1. Detection
                # Try faces first (more precise)
                candidates = detect_face_candidates(frame)
                target_box = None
                
                if candidates:
                     target_box = speaker_tracker.get_target(candidates, current_frame_idx, width)
                
                # Fallback to YOLO person detection if no faces found
                if not target_box:
                    target_box = detect_person_yolo(frame)
                    
                # 2. Update Cameraman
                cameraman.update_target(target_box)
                
                # 3. Get Crop Coordinates
                x1, y1, x2, y2 = cameraman.get_crop_box()
                
                # 4. Crop & Resize
                crop = frame[y1:y2, x1:x2]
                
                if crop.size == 0:
                    # Safety fallback
                    resized_crop = cv2.resize(frame, (target_width, target_height))
                else:
                    resized_crop = cv2.resize(crop, (target_width, target_height))
                
                # Write
                out.write(resized_crop)
                
                current_frame_idx += 1
                pbar.update(1)
                
        except Exception as e:
            print(f"❌ Error during cropping: {e}")
            raise
        finally:
            pbar.close()
            cap.release()
            out.release()
            
        print(f"✅ Cropped video saved to: {output_path}")
        return True

# Backward compatibility (since pipeline calls this function directly)
def process_viral_clip_with_smart_crop(input_path, start, end, output_path):
    """
    Wrapper function to match legacy signature expected by pipeline.
    """
    service = CroppingService()
    service.crop_video_to_vertical(input_path, output_path, start, end)
