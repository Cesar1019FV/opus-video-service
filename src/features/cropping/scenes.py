import cv2
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from tqdm import tqdm

def detect_scenes(video_path):
    """
    Detects scenes in a video using PySceneDetect.
    Returns a list of (start_time, end_time) tuples and the FPS.
    """
    try:
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        
        # Improve performance by downscaling
        video_manager.set_downscale_factor()
        
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        fps = video_manager.get_framerate()
        
    except Exception as e:
        print(f"⚠️ Scene detection failed: {e}")
        return [], 30.0
        
    finally:
        if 'video_manager' in locals():
            video_manager.release()
    
    return scene_list, fps

def analyze_scenes_strategy(video_path, scenes, face_detection_fn):
    """
    Analyzes each scene to determine if it should be TRACK (Single person) or GENERAL (Group/Wide).
    face_detection_fn: Function that accepts a frame and returns list of candidates.
    
    Args:
        video_path: Path to video
        scenes: List of (start_time, end_time) from detect_scenes
        face_detection_fn: Callable(frame) -> list of dicts (candidates)
        
    Returns:
        List of strategy strings ('TRACK' or 'GENERAL')
    """
    
    cap = cv2.VideoCapture(str(video_path))
    strategies = []
    
    if not cap.isOpened():
        return ['TRACK'] * len(scenes)
        
    try:
        for start, end in tqdm(scenes, desc="   Analyzing Scenes"):
            # Sample 3 frames (start, middle, end)
            start_frame = start.get_frames()
            end_frame = end.get_frames()
            
            frames_to_check = [
                start_frame + 5,
                int((start_frame + end_frame) / 2),
                end_frame - 5
            ]
            
            face_counts = []
            for f_idx in frames_to_check:
                cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
                ret, frame = cap.read()
                if not ret: continue
                
                # Detect faces using the passed function/dependency
                candidates = face_detection_fn(frame)
                face_counts.append(len(candidates))
                
            # Decision Logic
            if not face_counts:
                avg_faces = 0
            else:
                avg_faces = sum(face_counts) / len(face_counts)
                
            # Strategy:
            # 0 faces -> GENERAL (Landscape/B-roll)
            # 1 face -> TRACK
            # > 1.2 faces -> GENERAL (Group)
            
            if avg_faces > 1.2 or avg_faces < 0.5:
                strategies.append('GENERAL')
            else:
                strategies.append('TRACK')
                
    except Exception as e:
        print(f"⚠️ Error analyzing scenes: {e}")
        # Fallback to TRACK for remaining scenes if we have partial failure
        current_len = len(strategies)
        remaining = len(scenes) - current_len
        strategies.extend(['TRACK'] * remaining)
    
    finally:
        cap.release()
        
    return strategies
