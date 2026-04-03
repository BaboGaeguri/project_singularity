import cv2
import numpy as np

# 카메라 캘리브레이션 값(테스트용 기본값)
CAMERA_INTRINSICS = {
    "fx": 500,
    "fy": 500,
    "cx": 320,
    "cy": 240
}

# 카메라→로봇 변환 (기본값)
CAMERA_TO_ROBOT = {
    "tx": 0.0,
    "ty": 0.0,
    "tz": 30.0,
    "roll": 0,
    "pitch": -15,
    "yaw": 0
}

OBJECT_MAPPING = {
    "cup": "starbucks_cup",
    "bottle": "tumbler",
    "teddy bear": "doll",
    "person": "human"
}

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    yolo_model = YOLO("yolov8n.pt")
except ImportError:
    YOLO_AVAILABLE = False
    yolo_model = None


def estimate_depth_from_size(width, height, class_name):
    size_pixels = (width + height) / 2
    depth = 100 - (size_pixels / 8)
    return max(20, min(100, depth))


def pixel_to_robot_coords(x_pixel, y_pixel, depth_cm):
    fx = CAMERA_INTRINSICS["fx"]
    fy = CAMERA_INTRINSICS["fy"]
    cx = CAMERA_INTRINSICS["cx"]
    cy = CAMERA_INTRINSICS["cy"]

    x_cam = (x_pixel - cx) * depth_cm / fx
    y_cam = (y_pixel - cy) * depth_cm / fy
    z_cam = depth_cm

    pitch = np.radians(CAMERA_TO_ROBOT["pitch"])

    x_rot = x_cam
    y_rot = y_cam * np.cos(pitch) - z_cam * np.sin(pitch)
    z_rot = y_cam * np.sin(pitch) + z_cam * np.cos(pitch)

    x_robot = x_rot + CAMERA_TO_ROBOT["tx"]
    y_robot = y_rot + CAMERA_TO_ROBOT["ty"]
    z_robot = z_rot + CAMERA_TO_ROBOT["tz"]

    return x_robot, y_robot, z_robot


def perceive_environment(use_camera=True):
    """카메라 촬영 + 객체 감지"""
    if not use_camera:
        return [], None

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return [], None

    detections = []
    if YOLO_AVAILABLE and yolo_model is not None:
        results = yolo_model(frame)
        for r in results:
            for box in r.boxes:
                class_name = r.names[int(box.cls[0])]
                target_class = OBJECT_MAPPING.get(class_name, class_name)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x_center = (x1 + x2) // 2
                y_center = (y1 + y2) // 2
                width = x2 - x1
                height = y2 - y1
                depth = estimate_depth_from_size(width, height, class_name)

                detections.append({
                    "class": target_class,
                    "x_pixel": x_center,
                    "y_pixel": y_center,
                    "width": width,
                    "height": height,
                    "confidence": float(box.conf[0]),
                    "depth_cm": depth
                })

    return sorted(detections, key=lambda x: x["confidence"], reverse=True), frame
