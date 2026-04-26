import os
import time
from collections import deque

import cv2
import numpy as np
from ultralytics import YOLO
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# =========================================================
# CONFIG
# =========================================================
MODEL_PATH = "best_nano_111.pt"  # model bạn đang dùng
INFER_SIZE = 768                  # 640 nhanh hơn, 768 cân bằng, 960 chậm hơn
# Rất thận trọng: nâng ngưỡng model và các ngưỡng kiểm tra để giảm false positives tối đa.
# Chú: có thể làm cảnh báo chậm hơn nhưng bền vững hơn trong thực tế.
CANDIDATE_CONF = 0.60             # conservative: only accept higher-confidence detections

# GIỚI HẠN HIỂN THỊ VIDEO ĐỂ KHÔNG CHE CONTROLS
MAX_DISPLAY_W = 820
MAX_DISPLAY_H = 430

# HARD FILTERS (nới lỏng so với bản cứng)
HARD_MOTION_MIN = 0.020

# FIRE: slightly relaxed compared to the very-conservative mode
FIRE_COLOR_MIN = 0.30

# SMOKE: make more sensitive to thin/faint smoke
SMOKE_COLOR_MIN = 0.24
SMOKE_TEXTURE_MIN = 0.08
SMOKE_BLUR_MIN = 0.08

# Fire area & small-fire policy (conservative)
FIRE_MIN_AREA_RATIO = 0.0025
SMALL_FIRE_MIN_AREA = 0.0003

# Fire flicker / intensity gates (conservative)
FIRE_FLICKER_MIN = 0.20       # require stronger flicker to confirm fire
FIRE_INTENSITY_RANGE_MIN = 0.15  # require notable intensity swing for flashing fire

# Smoke conservatively: require larger region/persistence to avoid false alarms
SMOKE_MIN_AREA_RATIO = 0.0025

# TRACK CONFIRMATION / HYSTERESIS (kept conservative overall)
IOU_MATCH = 0.40
TRACK_MAX_MISSES = 10
ALERT_COOLDOWN = 48

FIRE_MIN_STREAK = 6
SMOKE_MIN_STREAK = 5

FIRE_MIN_MOTION = 0.012
SMOKE_MIN_MOTION = 0.006

FIRE_MIN_MOTION_VAR = 0.00020
SMOKE_MIN_MOTION_VAR = 0.00008

SMOKE_MIN_DRIFT = 0.006

FIRE_SCORE_CONFIRM = 160.0
SMOKE_SCORE_CONFIRM = 110.0
FIRE_SCORE_RELEASE = 130.0
SMOKE_SCORE_RELEASE = 95.0

FIRE_RELEASE_PATIENCE = 12
SMOKE_RELEASE_PATIENCE = 10

# Sticker/decoration heuristics (conservative)
STICKER_HUE_STD_MAX = 0.05
STICKER_SAT_STD_MAX = 0.05
STICKER_VAL_STD_MAX = 0.08
STICKER_TEXTURE_MAX = 0.18
STICKER_FILL_RATIO_MIN = 0.55
STICKER_CONTOUR_FILL_MIN = 0.55
STICKER_EDGE_MIN = 0.58
STICKER_CONF_MAX = 0.65

# =========================================================
# SHAPE STABILITY & REFLECTION FILTERING (NEW)
# =========================================================
SHAPE_STABILITY_THRESHOLD = 0.08          # below = rigid fixed object, above = deforming (fire/smoke)
EDGE_SHARPNESS_THRESHOLD = 0.60           # above = sharp reflection/sticker, below = fuzzy fire/smoke
ASPECT_RATIO_CHANGE_MIN = 0.006           # minimum aspect ratio variance to prove deformation
ASPECT_RATIO_CHANGE_MAX = 0.12            # maximum to avoid noise
CENTROID_CONSISTENCY_MIN = 0.04           # minimum centroid drift for tracking coherence
SHAPE_HISTORY_LEN = 6                     # frames to track shape changes (200ms at 30fps)

# Strict gates for fixed object rejection
NO_DEFORMATION_REJECT_STREAK = 3          # reject a bit earlier on fully rigid shapes
SHAPE_DEFORMATION_MIN = 0.002            # raise minimum deformation required to consider non-rigid

SAVE_ALERT_SNAPSHOTS = True
ALERT_DIR = "alerts"
os.makedirs(ALERT_DIR, exist_ok=True)

# =========================================================
# PIL RESAMPLE BACKWARD-COMPAT
# =========================================================
try:
    PIL_RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    PIL_RESAMPLE = Image.LANCZOS

# =========================================================
# UTILS
# =========================================================


def roi_flicker_score(intensity_hist):
    """
    Đo độ dao động ánh sáng theo thời gian
    """
    if len(intensity_hist) < 4:
        return 0.0

    arr = np.array(intensity_hist)
    mean = np.mean(arr)
    std = np.std(arr)

    # loại vùng quá tối (noise)
    if mean < 0.08:
        return 0.0

    # loại dao động quá nhỏ (LED ổn định)
    if std < 0.01:
        return 0.0

    return float(clamp(std / (mean + 1e-6), 0.0, 1.0))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def box_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union = area1 + area2 - inter + 1e-6
    return inter / union

def box_centroid(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)

def roi_motion(prev_gray, cur_gray, box):
    if prev_gray is None:
        return 0.0

    h, w = cur_gray.shape[:2]
    x1 = int(clamp(box[0], 0, w - 1))
    y1 = int(clamp(box[1], 0, h - 1))
    x2 = int(clamp(box[2], 0, w - 1))
    y2 = int(clamp(box[3], 0, h - 1))

    if x2 <= x1 or y2 <= y1:
        return 0.0

    roi_prev = prev_gray[y1:y2, x1:x2]
    roi_cur = cur_gray[y1:y2, x1:x2]
    if roi_prev.size == 0 or roi_cur.size == 0:
        return 0.0

    diff = cv2.absdiff(roi_cur, roi_prev)

    mean_diff = float(np.mean(diff) / 255.0)
    active_ratio = float(np.mean(diff > 18))

    # motion rõ = vừa có cường độ thay đổi vừa có vùng thay đổi
    return float(0.6 * mean_diff + 0.4 * active_ratio)

def roi_texture_score(roi_gray):
    """
    Texture cao = nhiều cạnh/chi tiết.
    Khói thường mềm/loang, tường phẳng thường thấp nhưng thiếu motion.
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    std = float(np.std(roi_gray) / 255.0)
    return float(clamp(std * 2.5, 0.0, 1.0))

def roi_blur_score(roi_gray):
    """
    Điểm mờ: càng cao càng blur / soft.
    Smoke thường làm vùng ảnh mềm, nhưng không dùng một mình.
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    lap_var = float(cv2.Laplacian(roi_gray, cv2.CV_64F).var())
    return float(clamp(1.0 / (1.0 + lap_var / 120.0), 0.0, 1.0))

def extract_edge_features(roi_bgr, roi_gray):
    """
    Extract edge sharpness score to distinguish reflections (sharp edges) from real fire/smoke (fuzzy edges).
    
    Returns:
        float: Edge sharpness score (0-1). High = sharp reflection, Low = fuzzy fire/smoke
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    
    h, w = roi_gray.shape[:2]
    if h < 4 or w < 4:
        return 0.0
    
    try:
        # Apply Canny edge detection
        edges = cv2.Canny(roi_gray, 50, 150)
        edge_pixels = np.count_nonzero(edges)
        total_pixels = h * w
        
        if edge_pixels == 0:
            return 0.0
        
        # Calculate edge density
        edge_density = float(edge_pixels) / float(total_pixels)
        
        # Sobel magnitude for edge strength
        sobelx = cv2.Sobel(roi_gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(roi_gray, cv2.CV_32F, 0, 1, ksize=3)
        sobel_mag = np.sqrt(sobelx**2 + sobely**2)
        
        # Edge strength: average magnitude of gradient at edge pixels
        if edge_pixels > 0:
            edge_strength = float(np.mean(sobel_mag[edges > 0])) / 255.0
        else:
            edge_strength = 0.0
        
        # Combined score: high edge density + high edge strength = sharp reflection
        # Real fire has lower edge density and weaker edges (fuzzy boundaries)
        sharpness = float(clamp(0.5 * edge_density + 0.5 * edge_strength, 0.0, 1.0))
        return sharpness
    except Exception:
        return 0.0

def fire_color_score(roi_bgr):
    """
    Lửa: màu nóng, đỏ/cam, bão hòa cao, sáng hơn nền.
    """
    if roi_bgr is None or roi_bgr.size == 0:
        return 0.0

    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    h = float(np.mean(hsv[:, :, 0]) / 179.0)
    s = float(np.mean(hsv[:, :, 1]) / 255.0)
    v = float(np.mean(hsv[:, :, 2]) / 255.0)

    warm_hue = 1.0 - clamp(abs(h - 0.07) / 0.14, 0.0, 1.0)
    score = 0.60 * warm_hue + 0.30 * s + 0.10 * v
    return float(clamp(score, 0.0, 1.0))

def smoke_color_score(roi_bgr):
    """
    Khói: thường là xám/trắng/xanh xám, độ bão hòa thấp.
    """
    if roi_bgr is None or roi_bgr.size == 0:
        return 0.0

    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = float(np.mean(hsv[:, :, 1]) / 255.0)
    v = float(np.mean(hsv[:, :, 2]) / 255.0)

    grayness = 1.0 - s
    brightness_center = 1.0 - min(abs(v - 0.72) / 0.72, 1.0)
    score = 0.75 * grayness + 0.25 * brightness_center
    return float(clamp(score, 0.0, 1.0))

def get_class_name(model, cls_id):
    try:
        names = model.names
        if isinstance(names, dict):
            return str(names.get(int(cls_id), str(int(cls_id))))
        return str(names[int(cls_id)])
    except Exception:
        return str(int(cls_id))

def fit_image_letterbox(pil_img, max_w, max_h, bg=(0, 0, 0)):
    """
    Resize ảnh để nằm gọn trong khung max_w x max_h, giữ đúng tỉ lệ.
    """
    if pil_img.width == 0 or pil_img.height == 0:
        return Image.new("RGB", (max_w, max_h), bg)

    scale = min(max_w / pil_img.width, max_h / pil_img.height)
    new_w = max(1, int(pil_img.width * scale))
    new_h = max(1, int(pil_img.height * scale))

    resized = pil_img.resize((new_w, new_h), PIL_RESAMPLE)
    canvas = Image.new("RGB", (max_w, max_h), bg)
    x = (max_w - new_w) // 2
    y = (max_h - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas

# =========================================================
# TRACKING
# =========================================================
class Track:
    def area_var(self):
        if len(self.area_hist) < 3:
            return 0.0
        return float(np.var(self.area_hist))


    def __init__(self, track_id, cls_name, box, conf, motion, color_score, texture_score, blur_score, area_ratio, intensity, edge_sharpness):
        self.id = track_id
        self.cls_name = cls_name.lower()
        self.box = list(map(float, box))
        self.conf = float(conf)

        self.motion_hist = deque([float(motion)], maxlen=SHAPE_HISTORY_LEN)
        self.color_hist = deque([float(color_score)], maxlen=SHAPE_HISTORY_LEN)
        self.texture_hist = deque([float(texture_score)], maxlen=SHAPE_HISTORY_LEN)
        self.blur_hist = deque([float(blur_score)], maxlen=SHAPE_HISTORY_LEN)
        self.centroid_hist = deque([box_centroid(self.box)], maxlen=SHAPE_HISTORY_LEN)
        self.area_hist = deque([area_ratio], maxlen=SHAPE_HISTORY_LEN)
        self.intensity_hist = deque([float(intensity)], maxlen=SHAPE_HISTORY_LEN)
        
        # NEW: Shape stability tracking
        w, h = box[2] - box[0], box[3] - box[1]
        aspect_ratio = w / (h + 1e-6)
        bbox_diagonal = np.hypot(w, h)
        
        self.aspect_ratio_hist = deque([float(aspect_ratio)], maxlen=SHAPE_HISTORY_LEN)
        self.bbox_diagonal_hist = deque([float(bbox_diagonal)], maxlen=SHAPE_HISTORY_LEN)
        self.edge_sharpness_hist = deque([float(edge_sharpness)], maxlen=SHAPE_HISTORY_LEN)

        self.area_ratio = float(area_ratio)
        self.streak = 1
        self.misses = 0
        self.score = self._frame_score(conf, motion, color_score, texture_score, blur_score)

        self.state = "candidate"   # candidate / confirmed
        self.release_counter = 0
        

    def _frame_score(self, conf, motion, color_score, texture_score, blur_score):
        if self.cls_name == "fire":
            return (
                conf * 100.0 +
                motion * 260.0 +
                color_score * 70.0 +
                texture_score * 15.0 +
                blur_score * 10.0
            )
        elif self.cls_name == "smoke":
            return (
                conf * 100.0 +
                motion * 240.0 +
                texture_score * 55.0 +
                blur_score * 65.0 +
                color_score * 15.0
            )
        return conf * 100.0 + motion * 200.0 + texture_score * 30.0

    def update(self, box, conf, motion, color_score, texture_score, blur_score, area_ratio, intensity, edge_sharpness):
        alpha = 0.35
        self.box = [
            self.box[0] * (1 - alpha) + box[0] * alpha,
            self.box[1] * (1 - alpha) + box[1] * alpha,
            self.box[2] * (1 - alpha) + box[2] * alpha,
            self.box[3] * (1 - alpha) + box[3] * alpha,
        ]

        self.conf = 0.65 * self.conf + 0.35 * conf
        self.motion_hist.append(float(motion))
        self.color_hist.append(float(color_score))
        self.texture_hist.append(float(texture_score))
        self.blur_hist.append(float(blur_score))
        self.centroid_hist.append(box_centroid(box))
        self.area_ratio = 0.7 * self.area_ratio + 0.3 * area_ratio
        self.area_hist.append(area_ratio)
        self.intensity_hist.append(float(intensity))
        
        # NEW: Update shape metrics
        w, h = box[2] - box[0], box[3] - box[1]
        aspect_ratio = w / (h + 1e-6)
        bbox_diagonal = np.hypot(w, h)
        
        self.aspect_ratio_hist.append(float(aspect_ratio))
        self.bbox_diagonal_hist.append(float(bbox_diagonal))
        self.edge_sharpness_hist.append(float(edge_sharpness))

        self.streak += 1
        self.misses = 0

        frame_score = self._frame_score(conf, motion, color_score, texture_score, blur_score)
        self.score = 0.72 * self.score + 0.28 * frame_score

    def miss(self):
        self.misses += 1
        self.streak = max(0, self.streak - 1)
        self.score *= 0.92

    def motion_avg(self):
        return float(np.mean(self.motion_hist)) if self.motion_hist else 0.0

    def motion_var(self):
        return float(np.var(self.motion_hist)) if len(self.motion_hist) >= 2 else 0.0

    def motion_trend(self):
        """
        Calculate motion trend (slope). 
        Positive = motion increasing, Negative = decreasing, ~0 = stable.
        Real fire: chaotic trend. Object: linear/stable trend.
        """
        if len(self.motion_hist) < 2:
            return 0.0
        motions = list(self.motion_hist)
        # Simple slope: (last - first) / time_steps
        slope = (motions[-1] - motions[0]) / (len(motions) - 1 + 1e-6)
        return float(slope)

    def motion_consistency(self):
        """
        Measure motion consistency (coefficient of variation).
        Low (~0.1) = very steady motion (object moving). 
        High (~0.5+) = erratic motion (fire).
        Lửa: motion chaotic, Vật thể: motion ổn định.
        """
        if len(self.motion_hist) < 2:
            return 0.0
        motions = np.array(list(self.motion_hist))
        mean_motion = float(np.mean(motions))
        if mean_motion < 0.001:
            return 0.0  # No motion, can't compute consistency
        std_motion = float(np.std(motions))
        # Coefficient of variation: std/mean (0.0 = perfectly consistent, >1.0 = very erratic)
        return std_motion / (mean_motion + 1e-6)

    def motion_linearity(self):
        """
        Detect if motion follows a linear trajectory (object) vs chaotic (fire).
        Uses simple polynomial fit - lower = more linear, higher = more chaotic.
        Object: linear trajectory. Fire: erratic movements.
        """
        if len(self.centroid_hist) < 3:
            return 0.0
        
        centroids = np.array(self.centroid_hist)
        x = centroids[:, 0]
        y = centroids[:, 1]
        
        # Fit line to x,y trajectory
        frame_idx = np.arange(len(centroids))
        try:
            # Fit x vs frame index
            coef_x = np.polyfit(frame_idx, x, 1)
            fit_x = np.polyval(coef_x, frame_idx)
            error_x = np.mean(np.abs(x - fit_x))
            
            # Fit y vs frame index  
            coef_y = np.polyfit(frame_idx, y, 1)
            fit_y = np.polyval(coef_y, frame_idx)
            error_y = np.mean(np.abs(y - fit_y))
            
            # Scale by trajectory magnitude to normalize
            trajectory_size = np.hypot(np.max(x) - np.min(x), np.max(y) - np.min(y)) + 1e-6
            linearity_error = (error_x + error_y) / trajectory_size
            # Invert: lower error = higher linearity, but return as deviation (higher = more chaotic)
            return float(min(linearity_error, 1.0))
        except:
            return 0.0

    def color_avg(self):
        return float(np.mean(self.color_hist)) if self.color_hist else 0.0

    def texture_avg(self):
        return float(np.mean(self.texture_hist)) if self.texture_hist else 0.0

    def blur_avg(self):
        return float(np.mean(self.blur_hist)) if self.blur_hist else 0.0

    def centroid_disp(self, frame_w, frame_h):
        if len(self.centroid_hist) < 2:
            return 0.0
        c0 = self.centroid_hist[0]
        c1 = self.centroid_hist[-1]
        diag = np.hypot(frame_w, frame_h) + 1e-6
        return float(np.hypot(c1[0] - c0[0], c1[1] - c0[1]) / diag)

    def aspect_ratio_var(self):
        """Variance of aspect ratio (width/height) over time. High = shape deformation."""
        if len(self.aspect_ratio_hist) < 2:
            return 0.0
        return float(np.var(self.aspect_ratio_hist))

    def shape_stability_score(self):
        """
        Combined shape stability metric: lower = rigid object, higher = deforming (fire/smoke).
        Combines normalized variances of area, aspect ratio, and bbox diagonal.
        """
        if len(self.area_hist) < 2:
            return 0.0
        
        area_var = float(np.var(self.area_hist))
        aspect_var = self.aspect_ratio_var()
        diagonal_var = float(np.var(self.bbox_diagonal_hist)) if len(self.bbox_diagonal_hist) >= 2 else 0.0
        
        # Normalize by mean to account for size differences
        area_mean = float(np.mean(self.area_hist)) + 1e-6
        aspect_mean = float(np.mean(self.aspect_ratio_hist)) + 1e-6
        diagonal_mean = float(np.mean(self.bbox_diagonal_hist)) + 1e-6
        
        area_norm = area_var / (area_mean ** 2 + 1e-6)
        aspect_norm = aspect_var / (aspect_mean ** 2 + 1e-6)
        diagonal_norm = diagonal_var / (diagonal_mean ** 2 + 1e-6)
        
        # Weighted combination: aspect ratio changes are most indicative of deformation
        score = 0.5 * clamp(aspect_norm, 0.0, 1.0) + 0.3 * clamp(area_norm, 0.0, 1.0) + 0.2 * clamp(diagonal_norm, 0.0, 1.0)
        return float(clamp(score, 0.0, 1.0))

    def boundary_consistency_score(self):
        """
        Edge sharpness consistency. High = sharp, consistent edges (reflection).
        Low = fuzzy, variable edges (real fire/smoke).
        """
        if len(self.edge_sharpness_hist) < 2:
            return 0.0
        mean_sharpness = float(np.mean(self.edge_sharpness_hist))
        return float(clamp(mean_sharpness, 0.0, 1.0))

    def color_variance(self):
        """Color score variance over time. High = flickering (fire). Low = stable color (not fire)."""
        if len(self.color_hist) < 2:
            return 0.0
        return float(np.var(self.color_hist))

    def should_confirm(self, frame_w, frame_h):
        stable_flicker = (
            np.mean(self.intensity_hist) > 0.18 and
            roi_flicker_score(self.intensity_hist) > 0.06
        )

        mot = self.motion_avg()
        mot_var = self.motion_var()
        tex = self.texture_avg()
        blur = self.blur_avg()
        color = self.color_avg()
        disp = self.centroid_disp(frame_w, frame_h)

        if self.cls_name == "fire":
            flicker = roi_flicker_score(self.intensity_hist)
            area_v = self.area_var()
            aspect_var = self.aspect_ratio_var()
            shape_score = self.shape_stability_score()
            color_var = self.color_variance()
            
            # STRICT: Reject if shape is completely rigid (tem dán, LED, etc)
            # If tracked for 4+ frames but shape never deformed → definitely not fire
            if self.streak >= NO_DEFORMATION_REJECT_STREAK:
                if shape_score < SHAPE_DEFORMATION_MIN and aspect_var < 0.0005:
                    return False  # Rigid object tracked consistently - reject
            
            # STRICT: Reject if high color + rigid shape + no motion + sharp edges
            # Catch stickers/LEDs/colored tape aggressively (conservative mode)
            if (color > 0.35 and shape_score < 0.02 and mot < 0.006 and 
                self.boundary_consistency_score() > EDGE_SHARPNESS_THRESHOLD):
                return False  # Likely a sticker/colored object, not fire
            
            # NEW: Reject if color + shape both static but moving (person walking)
            # Lửa PHẢI lóe sáng (color change) hoặc biến dạng (shape change)
            # Nếu vật di chuyển nhưng màu sắc + hình dạng cố định → không phải lửa
            # NHƯNG nếu intensity cao (lửa đang tắt dần) thì vẫn giữ → không reject
            mean_intensity = float(np.mean(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
            max_intensity = float(np.max(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
            # Reject chỉ nếu vừa low intensity hiện tại vừa không có lịch sử intensity cao
            if (color_var < 0.0003 and shape_score < 0.015 and mot > 0.006 and 
                mean_intensity < 0.10 and max_intensity < 0.18):  # Không phải lửa tắt dần
                return False  # Moving object without flickering + consistently low intensity = not fire
            
            # STRICT: Reject if sharp edges + no shape change
            shape_stable = shape_score < SHAPE_STABILITY_THRESHOLD
            edge_reflection = self.boundary_consistency_score() > EDGE_SHARPNESS_THRESHOLD
            if shape_stable and edge_reflection:
                return False  # Likely a reflection/sticker on static object
            
            # NEW: Temporal trend analysis - reject steady/linear motion without deformation
            # Lửa: motion chaotic/erratic. Vật thể: motion ổn định/tuyến tính
            # Xu thế: phân tích 6 frames để phát hiện pattern, không phải frame đơn lẻ
            motion_consistency = self.motion_consistency()
            motion_linearity = self.motion_linearity()
            motion_trend = abs(self.motion_trend())  # Absolute to check if trending up/down
            
            # Reject if motion too steady + no shape deformation
            # Đó là vật thể di chuyển ổn định, không phải lửa bùng
            if (motion_consistency < 0.25 and  # Motion rất ổn định (not chaotic)
                motion_linearity < 0.10 and  # Following linear trajectory (not erratic)
                shape_score < 0.02 and  # Shape không deforming
                mot > 0.004):  # But has some motion
                return False  # Steady motion + linear trajectory + rigid shape = not fire (probably object/person)
            
            # NEW: Enhanced dynamic proof - add aspect ratio deformation
            # Real fire morphs continuously, not just moves
            dynamic_ok = (
                (flicker > 0.08 and area_v > 0.00002) or
                (flicker > 0.14 and mot > 0.008) or
                (area_v > 0.0001 and mot > 0.008) or
                (aspect_var > ASPECT_RATIO_CHANGE_MIN and aspect_var < ASPECT_RATIO_CHANGE_MAX)
            )

            # Strong flicker or intensity flash is mandatory for fire
            min_intensity = float(np.min(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
            max_intensity = float(np.max(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
            intensity_range = max_intensity - min_intensity

            if flicker < FIRE_FLICKER_MIN and intensity_range < FIRE_INTENSITY_RANGE_MIN:
                return False

            # Area acceptance: normal-sized regions must exceed FIRE_MIN_AREA_RATIO.
            # Very small regions can still be accepted if flicker is strong and score/conf reasonable.
            area_ok = False
            if self.area_ratio >= FIRE_MIN_AREA_RATIO:
                area_ok = True
            elif self.area_ratio >= SMALL_FIRE_MIN_AREA and flicker >= FIRE_FLICKER_MIN and self.conf >= 0.55 and self.score >= (FIRE_SCORE_CONFIRM * 0.75):
                area_ok = True

            # Final decision: different persistence/score requirements for small vs normal regions
            if area_ok and self.area_ratio >= FIRE_MIN_AREA_RATIO:
                return (
                    self.streak >= FIRE_MIN_STREAK and
                    self.score >= FIRE_SCORE_CONFIRM and
                    dynamic_ok
                )
            if area_ok:
                # small fire path (require slightly lower score but still dynamic evidence)
                return (
                    self.streak >= max(3, FIRE_MIN_STREAK - 2) and
                    self.score >= (FIRE_SCORE_CONFIRM * 0.75) and
                    dynamic_ok
                )

            return False

        if self.cls_name == "smoke":
            shape_score = self.shape_stability_score()
            color_var = self.color_variance()
            
            # STRICT: Reject if shape is completely rigid after 4+ frames
            if self.streak >= NO_DEFORMATION_REJECT_STREAK:
                if shape_score < SHAPE_DEFORMATION_MIN:
                    return False  # Rigid object - not smoke
            
            # STRICT: Reject if moving but color + shape + blur/texture all static
            # Smoke phải có thay đổi: deformation hoặc blur hoặc color
            # NHƯNG nếu blur_score hoặc texture_score vẫn cao thì vẫn là khói → không reject
            blur_var = float(np.var(self.blur_hist)) if len(self.blur_hist) >= 2 else 0.0
            if (color_var < 0.0002 and shape_score < 0.012 and blur_var < 0.0002 and 
                mot > 0.006 and blur < SMOKE_BLUR_MIN and tex < SMOKE_TEXTURE_MIN):
                return False  # Moving but no smoke characteristics = not smoke
            
            # STRICT: Reject if sharp edges + no shape deformation
            shape_stable = shape_score < (SHAPE_STABILITY_THRESHOLD * 0.75)
            edge_reflection = self.boundary_consistency_score() > (EDGE_SHARPNESS_THRESHOLD + 0.05)
            if shape_stable and edge_reflection:
                return False  # Static reflection/sticker on object

            # NEW: Temporal trend analysis for smoke
            # Khói: motion chaotic/diffuse. Vật thể: motion tuyến tính
            motion_consistency_smoke = self.motion_consistency()
            motion_linearity_smoke = self.motion_linearity()
            
            # Reject if motion too linear + no deformation (probably object, not smoke)
            if (motion_consistency_smoke < 0.22 and  # Motion rất ổn định
                motion_linearity_smoke < 0.10 and  # Perfect linear trajectory
                shape_score < 0.015 and  # No shape change
                mot > 0.005 and  # Has motion
                blur < SMOKE_BLUR_MIN):  # No blur change
                return False  # Linear motion + rigid shape + no blur = not smoke (probably object)

            evidence_main = (
                mot >= SMOKE_MIN_MOTION or
                blur >= SMOKE_BLUR_MIN or
                tex >= SMOKE_TEXTURE_MIN
            )

            evidence_dynamic = (
                disp >= SMOKE_MIN_DRIFT or
                mot_var >= SMOKE_MIN_MOTION_VAR
            )

            return (
                self.streak >= SMOKE_MIN_STREAK and
                self.score >= SMOKE_SCORE_CONFIRM and
                evidence_main and
                evidence_dynamic
            )

        return False

    def should_release(self):
        if self.cls_name == "fire":
            return self.score < FIRE_SCORE_RELEASE
        if self.cls_name == "smoke":
            return self.score < SMOKE_SCORE_RELEASE
        return True

class TrackManager:
    def __init__(self):
        self.tracks = []
        self.next_id = 1
        self.alert_cooldown = 0

    def update(self, detections, frame_bgr, prev_gray):
        h, w = frame_bgr.shape[:2]
        cur_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        detections = sorted(detections, key=lambda d: d["conf"], reverse=True)


        new_tracks = []

        # 1) Global greedy IoU matching (better for simultaneous multi-targets)
        n_tr = len(self.tracks)
        n_det = len(detections)

        if n_tr == 0:
            # No existing tracks: create new tracks for all detections
            for det in detections:
                new_tracks.append(
                    Track(
                        self.next_id,
                        det["cls_name"],
                        det["box"],
                        det["conf"],
                        det["motion"],
                        det["color_score"],
                        det["texture_score"],
                        det["blur_score"],
                        det["area_ratio"],
                        det["intensity"],
                        det["edge_sharpness"]
                    )
                )
                self.next_id += 1
        else:
            # Build IoU matrix between existing tracks and detections (only same class considered)
            iou_mat = np.zeros((n_tr, n_det), dtype=np.float32)
            for i, tr in enumerate(self.tracks):
                for j, det in enumerate(detections):
                    if tr.cls_name != det["cls_name"]:
                        iou_mat[i, j] = 0.0
                    else:
                        iou_mat[i, j] = box_iou(tr.box, det["box"])

            matched_tr = [False] * n_tr
            matched_det = [False] * n_det

            # Greedy global matching by highest IoU until below threshold
            while True:
                if iou_mat.size == 0:
                    break
                max_idx = int(np.argmax(iou_mat))
                i, j = np.unravel_index(max_idx, iou_mat.shape)
                max_iou = float(iou_mat[i, j])
                if max_iou < IOU_MATCH:
                    break

                # Assign detection j to track i
                tr = self.tracks[i]
                det = detections[j]
                tr.update(
                    det["box"], det["conf"], det["motion"],
                    det["color_score"], det["texture_score"], det["blur_score"],
                    det["area_ratio"], det["intensity"], det["edge_sharpness"]
                )
                matched_tr[i] = True
                matched_det[j] = True

                # Invalidate row i and column j
                iou_mat[i, :] = -1.0
                iou_mat[:, j] = -1.0

            # Unmatched detections -> create new tracks
            for j, det in enumerate(detections):
                if not matched_det[j]:
                    new_tracks.append(
                        Track(
                            self.next_id,
                            det["cls_name"],
                            det["box"],
                            det["conf"],
                            det["motion"],
                            det["color_score"],
                            det["texture_score"],
                            det["blur_score"],
                            det["area_ratio"],
                            det["intensity"],
                            det["edge_sharpness"]
                        )
                    )
                    self.next_id += 1

            # Tracks that were not matched count as misses
            for i, tr in enumerate(self.tracks):
                if not matched_tr[i]:
                    tr.miss()

        # 3) add new tracks after matching
        self.tracks.extend(new_tracks)

        # 4) prune
        self.tracks = [t for t in self.tracks if t.misses <= TRACK_MAX_MISSES]

        # 5) state machine with hysteresis
        confirmed = []
        candidates = []

        for tr in self.tracks:
            if tr.state != "confirmed":
                if tr.should_confirm(w, h):
                    tr.state = "confirmed"
                    tr.release_counter = 0
            else:
                if tr.should_release():
                    tr.release_counter += 1
                else:
                    tr.release_counter = 0

                patience = FIRE_RELEASE_PATIENCE if tr.cls_name == "fire" else SMOKE_RELEASE_PATIENCE
                if tr.release_counter >= patience:
                    tr.state = "candidate"
                    tr.release_counter = 0

            if tr.state == "confirmed":
                confirmed.append(tr)
            elif tr.streak >= 2 or tr.score > 35:
                candidates.append(tr)

        if confirmed:
            self.alert_cooldown = ALERT_COOLDOWN
        else:
            self.alert_cooldown = max(0, self.alert_cooldown - 1)

        alarm_active = self.alert_cooldown > 0
        return cur_gray, confirmed, candidates, alarm_active

# =========================================================
# APP
# =========================================================
class FireSmokeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Fire & Smoke Detection - Temporal Guard")
        self.root.geometry(f"{MAX_DISPLAY_W + 80}x{MAX_DISPLAY_H + 250}")
        self.root.minsize(MAX_DISPLAY_W + 80, MAX_DISPLAY_H + 250)

        try:
            self.model = YOLO(MODEL_PATH)
        except Exception as e:
            messagebox.showerror("Model load error", f"Không load được model:\n{e}")
            raise

        self.cap = None
        self.total_frames = 0
        self.frame_idx = 0
        self.paused = False
        self.loop_video = True
        self.prev_gray = None
        self.last_frame_bgr = None

        self.seek_pending = None
        self.updating_slider = False

        self.tm = TrackManager()
        self.last_saved_alert_frame = -999999

        # Video container cố định, không làm các control bị đẩy xuống / khuất
        self.video_container = tk.Frame(root, bg="black", width=MAX_DISPLAY_W, height=MAX_DISPLAY_H)
        self.video_container.pack_propagate(False)
        self.video_container.pack(pady=(8, 6))

        self.panel = tk.Label(self.video_container, bg="black")
        self.panel.pack(expand=True, fill="both")

        control = tk.Frame(root)
        control.pack(pady=8)

        tk.Button(control, text="Open Video", command=self.open_video, width=12).grid(row=0, column=0, padx=5)
        tk.Button(control, text="Pause/Resume", command=self.toggle_pause, width=12).grid(row=0, column=1, padx=5)
        tk.Button(control, text="Toggle Loop", command=self.toggle_loop, width=12).grid(row=0, column=2, padx=5)
        tk.Button(control, text="Reset", command=self.reset_video, width=12).grid(row=0, column=3, padx=5)

        self.status_var = tk.StringVar(value="Monitoring...")
        self.status_label = tk.Label(root, textvariable=self.status_var, font=("Arial", 12, "bold"))
        self.status_label.pack(pady=(2, 6))

        self.slider = tk.Scale(
            root,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=MAX_DISPLAY_W + 20,
            showvalue=True,
            label="Timeline",
            command=self.on_seek
        )
        self.slider.pack(padx=10, pady=(0, 8))

        info = tk.Label(
            root,
            text="Video được giới hạn trong khung cố định. Logic dùng persistence + hysteresis để giảm nhấp nháy.",
            fg="gray"
        )
        info.pack(pady=(0, 8))

        self.root.after(15, self.update_frame)

    def open_video(self):
        path = filedialog.askopenfilename(
            title="Select video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*")]
        )
        if not path:
            return

        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            messagebox.showerror("Video error", "Không mở được video.")
            self.cap = None
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.frame_idx = 0
        self.prev_gray = None
        self.last_frame_bgr = None
        self.tm = TrackManager()
        self.paused = False
        self.seek_pending = None
        self.last_saved_alert_frame = -999999

        if self.total_frames > 0:
            self.slider.config(to=max(0, self.total_frames - 1))
            self.updating_slider = True
            self.slider.set(0)
            self.updating_slider = False

        self.status_var.set("Video loaded. Monitoring...")

    def reset_video(self):
        if self.cap is None:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.frame_idx = 0
        self.prev_gray = None
        self.last_frame_bgr = None
        self.tm = TrackManager()
        self.seek_pending = None
        self.status_var.set("Reset to beginning.")

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_loop(self):
        self.loop_video = not self.loop_video

    def on_seek(self, value):
        if self.cap is None:
            return
        if self.updating_slider:
            return
        try:
            self.seek_pending = int(float(value))
        except Exception:
            pass

    def draw_tracks(self, frame, confirmed_tracks, candidate_tracks):
        out = frame.copy()
        h, w = out.shape[:2]

        if confirmed_tracks:
            banner = "ALERT: FIRE / SMOKE CONFIRMED"
            color = (0, 0, 255)
        elif candidate_tracks:
            banner = "Monitoring: suspicious pattern detected, waiting for persistence..."
            color = (0, 255, 255)
        else:
            banner = "Monitoring: no confirmed fire/smoke"
            color = (0, 200, 0)

        cv2.rectangle(out, (0, 0), (w, 42), (20, 20, 20), -1)
        cv2.putText(out, banner, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2)

        def draw_one(tr, box_color, thick=2):
            x1, y1, x2, y2 = map(int, tr.box)
            x1 = int(clamp(x1, 0, w - 1))
            y1 = int(clamp(y1, 0, h - 1))
            x2 = int(clamp(x2, 0, w - 1))
            y2 = int(clamp(y2, 0, h - 1))

            cv2.rectangle(out, (x1, y1), (x2, y2), box_color, thick)

            label = (
                f"#{tr.id} {tr.cls_name} "
                f"c:{tr.conf:.2f} s:{tr.score:.1f} "
                f"st:{tr.streak} m:{tr.motion_avg():.3f}"
            )
            y_text = y1 - 8 if y1 > 18 else y1 + 18
            cv2.putText(out, label, (x1, y_text), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)

        for tr in candidate_tracks:
            draw_one(tr, (0, 255, 255), 2)

        for tr in confirmed_tracks:
            draw_one(tr, (0, 0, 255), 3)

        return out

    def save_alert_snapshot(self, frame_bgr, frame_idx):
        if not SAVE_ALERT_SNAPSHOTS:
            return
        if frame_idx - self.last_saved_alert_frame < 30:
            return

        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(ALERT_DIR, f"alert_{ts}_frame{frame_idx}.jpg")
        try:
            cv2.imwrite(path, frame_bgr)
            self.last_saved_alert_frame = frame_idx
        except Exception:
            pass

    def render_frame(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        fitted = fit_image_letterbox(pil_img, MAX_DISPLAY_W, MAX_DISPLAY_H, bg=(0, 0, 0))
        imgtk = ImageTk.PhotoImage(image=fitted)
        self.panel.imgtk = imgtk
        self.panel.config(image=imgtk)

    def process_current_frame(self, frame):
        results = self.model.predict(
            frame,
            conf=CANDIDATE_CONF,
            imgsz=INFER_SIZE,
            verbose=False
        )

        detections = []
        res = results[0]
        boxes = res.boxes

        if boxes is not None and len(boxes) > 0:
            h, w = frame.shape[:2]
            cur_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for b in boxes:
                conf = float(b.conf[0])
                cls_id = int(b.cls[0])
                cls_name_raw = get_class_name(self.model, cls_id).lower()

                # Only fire/smoke
                if ("fire" not in cls_name_raw) and ("smoke" not in cls_name_raw):
                    continue

                x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
                xi1 = int(clamp(x1, 0, w - 1))
                yi1 = int(clamp(y1, 0, h - 1))
                xi2 = int(clamp(x2, 0, w - 1))
                yi2 = int(clamp(y2, 0, h - 1))

                if xi2 <= xi1 or yi2 <= yi1:
                    continue

                roi_bgr = frame[yi1:yi2, xi1:xi2]
                roi_gray = cur_gray[yi1:yi2, xi1:xi2]
                intensity = float(np.mean(roi_gray) / 255.0)

                # NEW: Extract edge features for reflection detection
                edge_sharpness = extract_edge_features(roi_bgr, roi_gray)

                motion = roi_motion(self.prev_gray, cur_gray, [x1, y1, x2, y2])
                texture_score = roi_texture_score(roi_gray)
                blur_score = roi_blur_score(roi_gray)
                area_ratio = max(0.0, (x2 - x1) * (y2 - y1) / float(w * h))

                if "fire" in cls_name_raw:
                    color_score = fire_color_score(roi_bgr)
                    smoke_color = 0.0
                else:
                    smoke_color = smoke_color_score(roi_bgr)
                    color_score = smoke_color

                # HARD FILTER - reject when model is very uncertain AND no motion
                if motion < HARD_MOTION_MIN and conf < CANDIDATE_CONF:
                    continue

                # ANTI-STICKER: High color + sharp edges + no motion = likely sticker/tape
                if "fire" in cls_name_raw and color_score > FIRE_COLOR_MIN and edge_sharpness > EDGE_SHARPNESS_THRESHOLD and motion < FIRE_MIN_MOTION and conf < STICKER_CONF_MAX:
                    continue

                # NEW: Uniform-color / printed-sticker heuristic (conservative)
                try:
                    hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
                    hue_std = float(np.std(hsv_roi[:, :, 0]) / 179.0)
                    sat_std = float(np.std(hsv_roi[:, :, 1]) / 255.0)
                    val_std = float(np.std(hsv_roi[:, :, 2]) / 255.0)
                except Exception:
                    hue_std = sat_std = val_std = 1.0

                # Heuristic: màu đều (hue_std nhỏ) + cạnh sắc + không chuyển động => rất có thể sticker/decoration
                if "fire" in cls_name_raw:
                    if hue_std < STICKER_HUE_STD_MAX and edge_sharpness > STICKER_EDGE_MIN and motion < FIRE_MIN_MOTION and conf < STICKER_CONF_MAX and texture_score < STICKER_TEXTURE_MAX:
                        continue

                if "smoke" in cls_name_raw:
                    if sat_std < STICKER_SAT_STD_MAX and edge_sharpness > (STICKER_EDGE_MIN + 0.05) and motion < SMOKE_MIN_MOTION and conf < STICKER_CONF_MAX and blur_score < 0.12:
                        continue

                # SOLIDITY (fill) + contour rectangularity checks to detect printed decorations
                try:
                    sat = hsv_roi[:, :, 1]
                    val = hsv_roi[:, :, 2]
                    mask_color = (sat > 30) | (val > 80)
                    fill_ratio = float(np.count_nonzero(mask_color) / (mask_color.size + 1e-6))
                    mask_u8 = (mask_color.astype(np.uint8) * 255)
                    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    max_cont_area = 0.0
                    approx_rect = False
                    if contours:
                        cnt = max(contours, key=cv2.contourArea)
                        max_cont_area = float(cv2.contourArea(cnt))
                        peri = cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                        if 4 <= len(approx) <= 8:
                            approx_rect = True
                    cont_fill = float(max_cont_area / (mask_color.size + 1e-6))
                except Exception:
                    fill_ratio = 0.0
                    approx_rect = False
                    cont_fill = 0.0

                # If a region is large, uniformly colored, with sharp edges and fills most of the bbox,
                # it's very likely a printed decoration (sticker) rather than fire/smoke.
                if "fire" in cls_name_raw:
                    if (fill_ratio > STICKER_FILL_RATIO_MIN and edge_sharpness > 0.58 and motion < 0.006 and conf < STICKER_CONF_MAX and texture_score < STICKER_TEXTURE_MAX):
                        continue
                    if approx_rect and cont_fill > STICKER_CONTOUR_FILL_MIN and edge_sharpness > 0.60 and conf < STICKER_CONF_MAX:
                        continue

                if "smoke" in cls_name_raw:
                    if (fill_ratio > STICKER_FILL_RATIO_MIN and edge_sharpness > 0.62 and motion < 0.006 and conf < STICKER_CONF_MAX and blur_score < 0.12):
                        continue
                    if approx_rect and cont_fill > (STICKER_CONTOUR_FILL_MIN - 0.05) and edge_sharpness > 0.65 and conf < STICKER_CONF_MAX:
                        continue

                # NEW SOLIDITY / SHAPE HEURISTIC: detect printed stickers / flat decorations
                try:
                    sat = hsv_roi[:, :, 1]
                    val = hsv_roi[:, :, 2]
                    mask_color = (sat > 30) | (val > 80)
                    fill_ratio = float(np.count_nonzero(mask_color) / (mask_color.size + 1e-6))
                    mask_u8 = (mask_color.astype(np.uint8) * 255)
                    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    max_cont_area = 0.0
                    approx_rect = False
                    if contours:
                        cnt = max(contours, key=cv2.contourArea)
                        max_cont_area = float(cv2.contourArea(cnt))
                        peri = cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                        if 4 <= len(approx) <= 8:
                            approx_rect = True
                    cont_fill = float(max_cont_area / (mask_color.size + 1e-6))
                except Exception:
                    fill_ratio = 0.0
                    approx_rect = False
                    cont_fill = 0.0

                # If a region is large, uniformly colored, with sharp edges and fills most of the bbox,
                # it's very likely a printed decoration (sticker) rather than fire/smoke.
                if "fire" in cls_name_raw:
                    if (fill_ratio > 0.60 and edge_sharpness > 0.58 and motion < 0.005 and conf < 0.60 and texture_score < 0.20):
                        continue
                    if approx_rect and cont_fill > 0.50 and edge_sharpness > 0.60 and conf < 0.60:
                        continue

                if "smoke" in cls_name_raw:
                    if (fill_ratio > 0.60 and edge_sharpness > 0.65 and motion < 0.005 and conf < 0.55 and blur_score < 0.10):
                        continue
                    if approx_rect and cont_fill > 0.48 and edge_sharpness > 0.68 and conf < 0.55:
                        continue

                # Lửa: yêu cầu màu nóng tương đối cho vùng không quá nhỏ; vùng rất nhỏ được giữ để track
                if "fire" in cls_name_raw and color_score < FIRE_COLOR_MIN and conf < 0.60 and area_ratio >= SMALL_FIRE_MIN_AREA:
                    continue

                # Khói: cho phép phát hiện khói mỏng hơn (nhạy hơn)
                # chỉ loại khi mọi tín hiệu đều rất yếu
                if "smoke" in cls_name_raw:
                    if (
                        conf < 0.40 and
                        smoke_color < 0.12 and
                        blur_score < 0.09 and
                        texture_score < 0.06
                    ):
                        continue

                # Loại bbox quá nhỏ trừ khi model đủ tin cậy (cho phép vùng rất nhỏ nếu confidence >= 0.55)
                if "fire" in cls_name_raw and area_ratio < FIRE_MIN_AREA_RATIO and conf < 0.55:
                    continue
                if "smoke" in cls_name_raw:
                    if area_ratio < SMOKE_MIN_AREA_RATIO and conf < 0.60:
                        continue

                detections.append({
                    "cls_name": "fire" if "fire" in cls_name_raw else "smoke",
                    "conf": conf,
                    "box": [x1, y1, x2, y2],
                    "motion": motion,
                    "color_score": color_score,
                    "texture_score": texture_score,
                    "blur_score": blur_score,
                    "area_ratio": area_ratio,
                    "intensity": intensity,
                    "edge_sharpness": edge_sharpness
                })

        gray, confirmed, candidates, alarm_active = self.tm.update(
            detections=detections,
            frame_bgr=frame,
            prev_gray=self.prev_gray
        )

        self.prev_gray = gray.copy()
        annotated = self.draw_tracks(frame, confirmed, candidates)

        if confirmed:
            txt = ", ".join([f"#{t.id}:{t.cls_name}" for t in confirmed[:4]])
            self.status_var.set(f"ALERT CONFIRMED → {txt}")
            self.save_alert_snapshot(annotated, self.frame_idx)
        elif candidates:
            txt = ", ".join([f"#{t.id}:{t.cls_name}" for t in candidates[:4]])
            self.status_var.set(f"Suspected / tracking → {txt}")
        else:
            self.status_var.set("Monitoring...")

        return annotated

    def update_frame(self):
        if self.cap is None:
            self.root.after(15, self.update_frame)
            return

        # seek handling
        if self.seek_pending is not None:
            pos = self.seek_pending
            self.seek_pending = None
            try:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ok, frame = self.cap.read()
                if ok:
                    self.frame_idx = pos
                    self.prev_gray = None
                    self.last_frame_bgr = frame.copy()
                    self.tm = TrackManager()  # reset tracks khi tua
                    annotated = self.process_current_frame(frame)
                    self.render_frame(annotated)

                    self.updating_slider = True
                    self.slider.set(pos)
                    self.updating_slider = False
            except Exception:
                pass

            self.root.after(15, self.update_frame)
            return

        if not self.paused:
            ret, frame = self.cap.read()

            if not ret:
                if self.loop_video:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.frame_idx = 0
                    self.prev_gray = None
                    self.last_frame_bgr = None
                    self.tm = TrackManager()

                    self.updating_slider = True
                    self.slider.set(0)
                    self.updating_slider = False

                    self.root.after(15, self.update_frame)
                    return
                else:
                    self.status_var.set("Video ended.")
                    self.root.after(15, self.update_frame)
                    return

            self.frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.last_frame_bgr = frame.copy()

            annotated = self.process_current_frame(frame)
            self.render_frame(annotated)

            if self.total_frames > 0:
                self.updating_slider = True
                self.slider.set(self.frame_idx)
                self.updating_slider = False

        self.root.after(15, self.update_frame)

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FireSmokeApp(root)
    root.mainloop()