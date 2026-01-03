import cv2
import os
import numpy as np
from ultralytics import YOLO
from src.shared.config import get_config

# Lazy-loaded models
_yolo_model = None
_face_net = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        # Load YOLO model (using standard path or from models dir if customization needed)
        # Using standard 'yolov8n.pt' which usually downloads or looks in current dir
        # For robustness we could put it in models_dir, but for now we follow original logic
        # which just passed 'yolov8n.pt'
        _yolo_model = YOLO('yolov8n.pt')
    return _yolo_model

def get_face_net():
    global _face_net
    if _face_net is None:
        config = get_config()
        # Use config.models_dir which is src/models
        # Files are: deploy.prototxt and res10_300x300_ssd_iter_140000.caffemodel
        proto_path = config.models_dir / "deploy.prototxt"
        model_path = config.models_dir / "res10_300x300_ssd_iter_140000.caffemodel"
        
        try:
             _face_net = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))
        except Exception as e:
            print(f"⚠️ Warning: Could not load OpenCV DNN face detector: {e}")
            print(f"Make sure {proto_path} and {model_path} exist.")
            _face_net = None
    return _face_net

def detect_face_candidates(frame):
    face_net = get_face_net()
    if face_net is None:
        return []
        
    height, width = frame.shape[:2]

    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0)
    )

    face_net.setInput(blob)
    detections = face_net.forward()

    candidates = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence < 0.5:
            continue

        box = detections[0, 0, i, 3:7]
        x1 = int(box[0] * width)
        y1 = int(box[1] * height)
        x2 = int(box[2] * width)
        y2 = int(box[3] * height)

        w = x2 - x1
        h = y2 - y1

        if w <= 0 or h <= 0:
            continue

        candidates.append({
            'box': [x1, y1, w, h],
            'score': w * h
        })

    return candidates

def detect_person_yolo(frame):
    model = get_yolo_model()
    results = model(frame, verbose=False, classes=[0]) 
    
    if not results:
        return None
        
    best_box = None
    max_area = 0
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = [int(i) for i in box.xyxy[0]]
            w = x2 - x1
            h = y2 - y1
            area = w * h
            
            if area > max_area:
                max_area = area
                face_h = int(h * 0.4)
                best_box = [x1, y1, w, face_h]
                
    return best_box
