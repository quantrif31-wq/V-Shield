from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from collections import deque
from functools import lru_cache
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk
from ultralytics import YOLO

try:
    import winsound

    HAVE_WINSOUND = True
except Exception:
    HAVE_WINSOUND = False


# =========================================================
# CONFIG
# =========================================================
MODEL_PATH = "yolov8s-pose.pt"
CONF_THRES = 0.35
IOU_THRES = 0.45
IMG_SIZE = 640

# mô hình nhận diện vũ khí (custom YOLO) - OPTIMIZED for real-world lighting & small objects
WEAPON_MODEL_PATH = "yolov8s-weapon.pt"
WEAPON_MODEL_CANDIDATES = (
    WEAPON_MODEL_PATH,
    "weapon.pt",
    "weapons.pt",
    "best_weapon.pt",
    "best.pt",
)
WEAPON_CONF_THRES = 0.35
WEAPON_IOU_THRES = 0.40
WEAPON_IMG_SIZE = 640
WEAPON_MAX_DET = 32
WEAPON_INFER_EVERY_N = 2
WEAPON_STICKY_SEC = 1.50
WEAPON_PERSON_IOU_MIN = 0.05
WEAPON_ASSOC_MAX_DIST = 0.90
WEAPON_MIN_SCORE = 0.50
WEAPON_HAND_DIST_MAX = 0.20
WEAPON_HAND_SCORE_BONUS = 0.50
WEAPON_AUTO_ASSUME_MAX_CLASSES = 10
WEAPON_CLASS_KEYWORDS = (
    "weapon",
    "gun",
    "pistol",
    "rifle",
    "knife",
    "dagger",
    "sword",
    "machete",
    "bat",
    "blade",
    "grenade",
    "bom",
    "sung",
    "dao",
)

# lọc người / track
MIN_PERSON_AREA = 1600
TRACK_TTL_SEC = 2.5

# posture thresholds
STANDING_ANGLE = 30.0
LYING_ANGLE = 58.0

# sitting thresholds
SIT_ANGLE_MIN = 15.0
SIT_ANGLE_MAX = 70.0
SIT_KNEE_MAX = 155.0
SIT_LEG_EXT_MAX = 0.90
SIT_MAX_REL_SPEED = 0.018

# motion thresholds (relative to bbox height)
RUN_REL_THRES = 0.045
WALK_REL_THRES = 0.018
SIGNIFICANT_MOTION_REL_THRES = 0.012
STILL_REL_THRES = 0.006

# cảnh báo nếu sau té không có chuyển động rõ trong X giây
ALERT_AFTER_LIE_SEC = 30.0

# history smoothing
ANGLE_HISTORY = 5
SPEED_HISTORY = 5
HEIGHT_HISTORY = 5
ANKLE_HISTORY = 5
GAIT_HISTORY = 14
POSE_REL_HISTORY = 10

# temporal decision smoothing (giảm giật nhãn)
DECISION_WINDOW = 18
MIN_FRAMES_BEFORE_DECISION = 6
ACTION_STABLE_RATIO = 0.62
ACTION_MIN_HOLD_SEC = 0.55
TRANSITION_EXTRA_FRAMES = 2

# gait / transition cues
KNEE_FLEX_WALK_MIN = 18.0
KNEE_FLEX_RUN_MIN = 28.0
GAIT_ALT_WALK_MIN = 0.28
GAIT_ALT_RUN_MIN = 0.42
SIT_HIP_KNEE_REL_MAX = 0.17
STAND_HIP_KNEE_REL_MIN = 0.19

# temporal probabilities and transition intent
PROB_EMA_ALPHA = 0.42
TRANSITION_TREND_WINDOW = 8
HIGH_CONF_SWITCH = 0.68
VERY_HIGH_CONF_SWITCH = 0.82
SIT_LOCK_SEC = 1.20
SIT_DESCENT_VSPEED_MIN = 0.0045
STAND_ASCENT_VSPEED_MIN = 0.0040
KNEE_FLEX_TREND_SIT_MIN = 0.45
KNEE_FLEX_TREND_STAND_MIN = 0.35
SIT_SHAPE_ASPECT_MIN = 0.82
SIT_SHAPE_SPEED_MAX = 0.016

# combat/action detail thresholds (OPTIMIZED for real-world conditions)
PUNCH_WRIST_SPEED_MIN = 0.055
PUNCH_WRIST_ACCEL_MIN = 0.018
PUNCH_ELBOW_EXT_SPEED_MIN = 6.8
KICK_ANKLE_SPEED_MIN = 0.062
KICK_ANKLE_ACCEL_MIN = 0.022
KICK_KNEE_EXT_SPEED_MIN = 8.2
COMBAT_GUARD_MIN = 6
COMBAT_MOTION_MIN = 0.012
HOLD_WRIST_DIST_MAX = 0.24
HOLD_WRIST_TORSO_MAX = 0.28
HOLD_WRIST_SPEED_MAX = 0.018
FIGHT_ENERGY_HISTORY = 12
HOLD_HISTORY = 14

# anti-bullying interaction cues
BULLY_HISTORY = 10
BULLY_INTERACT_RANGE = 0.94
BULLY_HEAD_GRAB_DIST = 0.19
BULLY_POINT_FACE_DIST = 0.24
BULLY_POINT_ALIGN_MIN = 0.66
BULLY_POINT_ELBOW_MIN = 152.0
BULLY_MIN_STRENGTH = 0.074
BULLY_CONTACT_STRENGTH_MIN = 0.048
BULLY_PERSIST_MIN = 0.58
BULLY_RELEASE_PERSIST_MIN = 0.42
BULLY_STICKY_SEC = 1.20
BULLY_ROLE_MARGIN = 0.035
BULLY_MIN_HEIGHT_RATIO = 0.62
BULLY_MAX_BOTTOM_GAP = 0.22
BULLY_MAX_CENTER_X_GAP = 0.74
BULLY_MIN_ARM_REACH = 0.16
BULLY_MIN_X_OVERLAP = 0.24
BULLY_MIN_Y_OVERLAP = 0.34
BULLY_NEAREST_CANDIDATES = 3
BULLY_MIN_SEEN_FRAMES = 6
BULLY_SENSITIVE_DIST = 0.16
BULLY_STANDING_ONLY = True
BULLY_POINT_WARN_MIN_STRENGTH = 0.050
BULLY_POINT_PERSIST_MIN = 0.62
BULLY_TARGET_STABLE_RATIO = 0.45

# stab cue (mapped to combat) - OPTIMIZED for knife/blade holding in hand
STAB_WRIST_SPEED_MIN = 0.038
STAB_ELBOW_EXT_SPEED_MIN = 5.2
STAB_ARM_STRAIGHT_MIN = 135.0

# pairwise combat cues for crowded scenes
COMBAT_HISTORY = 10
COMBAT_INTERACT_RANGE = 0.78
COMBAT_MIN_HEIGHT_RATIO = 0.58
COMBAT_MAX_BOTTOM_GAP = 0.22
COMBAT_MIN_X_OVERLAP = 0.20
COMBAT_CONTACT_DIST = 0.19
COMBAT_WEAPON_CONTACT_DIST = 0.24
COMBAT_TARGET_RECOIL_MIN = 0.016
COMBAT_MIN_STRENGTH = 0.095
COMBAT_PERSIST_MIN = 0.54
COMBAT_RELEASE_PERSIST_MIN = 0.40
COMBAT_STICKY_SEC = 1.10

ACTIONS = (
    "ĐỨNG",
    "ĐI BỘ",
    "CHẠY",
    "NGỒI",
    "TÉ",
    "CHIẾN ĐẤU",
    "DI CHUYỂN CHIẾN ĐẤU",
    "ĐẤM",
    "ĐÁ",
    "ÔM VẬT",
)

SAVE_ALERT_FRAME = True
ALERT_DIR = "alerts"

SHOW_ID_BG = True
ENABLE_FRAME_ENHANCEMENT = True
DISPLAY_MAX_WIDTH = 1180
DISPLAY_MAX_HEIGHT = 720

# nếu muốn chỉ hiển thị người lớn nhất thì đổi True
DRAW_ONLY_PRIMARY = False


# =========================================================
# FONT / UNICODE
# =========================================================
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


@lru_cache(maxsize=64)
def get_font(size: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def bgr_to_rgb(color):
    b, g, r = color
    return (r, g, b)


# =========================================================
# DATA CLASSES
# =========================================================
@dataclass
class PersonState:
    prev_center: tuple | None = None
    prev_angle: float | None = None
    prev_posture: str = "UNKNOWN"
    prev_height: float | None = None

    first_seen: float = 0.0
    last_seen: float = 0.0
    seen_frames: int = 0

    # fall state machine
    fall_started: float | None = None
    lying_since: float | None = None
    last_significant_motion: float | None = None
    alarmed: bool = False

    # keypoint tracking for motion
    prev_left_ankle: tuple | None = None
    prev_right_ankle: tuple | None = None
    prev_left_wrist: tuple | None = None
    prev_right_wrist: tuple | None = None
    prev_hip_y: float | None = None
    prev_left_elbow_angle: float | None = None
    prev_right_elbow_angle: float | None = None
    prev_left_knee_angle: float | None = None
    prev_right_knee_angle: float | None = None
    prev_left_wrist_speed: float = 0.0
    prev_right_wrist_speed: float = 0.0
    prev_left_ankle_speed: float = 0.0
    prev_right_ankle_speed: float = 0.0

    # smoothed metrics
    angle_hist: deque = field(default_factory=lambda: deque(maxlen=ANGLE_HISTORY))
    speed_hist: deque = field(default_factory=lambda: deque(maxlen=SPEED_HISTORY))
    height_hist: deque = field(default_factory=lambda: deque(maxlen=HEIGHT_HISTORY))
    ankle_motion_hist: deque = field(default_factory=lambda: deque(maxlen=ANKLE_HISTORY))
    knee_flex_diff_hist: deque = field(default_factory=lambda: deque(maxlen=GAIT_HISTORY))
    knee_flex_l_hist: deque = field(default_factory=lambda: deque(maxlen=GAIT_HISTORY))
    knee_flex_r_hist: deque = field(default_factory=lambda: deque(maxlen=GAIT_HISTORY))
    knee_flex_mean_hist: deque = field(default_factory=lambda: deque(maxlen=GAIT_HISTORY))
    hip_knee_rel_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    hip_vertical_speed_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    ankle_span_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    wrist_speed_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    wrist_accel_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    ankle_speed_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    ankle_accel_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    elbow_ext_speed_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    knee_ext_speed_hist: deque = field(default_factory=lambda: deque(maxlen=POSE_REL_HISTORY))
    fight_energy_hist: deque = field(default_factory=lambda: deque(maxlen=FIGHT_ENERGY_HISTORY))
    hold_pose_hist: deque = field(default_factory=lambda: deque(maxlen=HOLD_HISTORY))
    guard_pose_hist: deque = field(default_factory=lambda: deque(maxlen=FIGHT_ENERGY_HISTORY))
    bully_hist: deque = field(default_factory=lambda: deque(maxlen=BULLY_HISTORY))
    bully_warn_hist: deque = field(default_factory=lambda: deque(maxlen=BULLY_HISTORY))
    bully_target_hist: deque = field(default_factory=lambda: deque(maxlen=BULLY_HISTORY))
    bully_target_id: int | None = None
    bully_active_until: float = 0.0
    bully_warn_target_id: int | None = None
    bully_warn_active_until: float = 0.0
    combat_hist: deque = field(default_factory=lambda: deque(maxlen=COMBAT_HISTORY))
    combat_target_hist: deque = field(default_factory=lambda: deque(maxlen=COMBAT_HISTORY))
    combat_target_id: int | None = None
    combat_active_until: float = 0.0

    # temporal action decision state
    action_window: deque = field(default_factory=lambda: deque(maxlen=DECISION_WINDOW))
    committed_action: str = "UNKNOWN"
    pending_action: str | None = None
    pending_count: int = 0
    pending_since: float | None = None
    last_action_change: float = 0.0
    action_prob_ema: dict[str, float] = field(default_factory=dict)
    transition_phase: str = "NONE"
    transition_since: float | None = None


# =========================================================
# IMAGE / TEXT HELPERS
# =========================================================
def draw_unicode_texts(frame, texts):
    """
    Draw multiple Unicode texts on a BGR frame using PIL.
    texts = [{"text": str, "x": int, "y": int, "color": (B,G,R), "size": int, "bg": bool}]
    """
    if not texts:
        return frame

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil_img)

    for item in texts:
        text = item.get("text", "")
        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        color = bgr_to_rgb(item.get("color", (255, 255, 255)))
        size = int(item.get("size", 24))
        bg = bool(item.get("bg", False))
        padding = int(item.get("padding", 4))

        font = get_font(size)
        try:
            bbox = draw.textbbox((x, y), text, font=font)
            if bg:
                draw.rectangle(
                    [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                    fill=(0, 0, 0),
                )
        except Exception:
            if bg:
                draw.rectangle((x - padding, y - padding, x + 240, y + 44), fill=(0, 0, 0))

        draw.text((x, y), text, font=font, fill=color)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_box(frame, x1, y1, x2, y2, color, thickness=3):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)


def preprocess_low_light(frame):
    """Advanced gamma + CLAHE + contrast enhancement for aggressive low-light conditions."""
    if not ENABLE_FRAME_ENHANCEMENT:
        return frame

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    v_mean = float(np.mean(hsv[:, :, 2]))

    # Always process if dim; aggressive for very dark
    if v_mean > 120:
        return frame

    # Adaptive gamma based on brightness level
    if v_mean < 40:
        gamma = 2.8
        clahe_clip = 3.8
        clahe_tile = (6, 6)
    elif v_mean < 60:
        gamma = 2.2
        clahe_clip = 3.2
        clahe_tile = (7, 7)
    elif v_mean < 85:
        gamma = 1.7
        clahe_clip = 2.6
        clahe_tile = (8, 8)
    else:
        gamma = 1.35
        clahe_clip = 2.0
        clahe_tile = (10, 10)

    # Apply gamma correction
    inv_gamma = 1.0 / gamma
    lut = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)], dtype=np.uint8)
    boosted = cv2.LUT(frame, lut)

    # Convert to LAB for better luminance processing
    lab = cv2.cvtColor(boosted, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE with adaptive parameters
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tile)
    l2 = clahe.apply(l)
    
    # Boost contrast further in very dark conditions
    if v_mean < 50:
        l2 = cv2.convertScaleAbs(l2 - 128) + 128
        alpha = np.clip((100 - v_mean) / 60.0, 1.0, 1.8)
        l2 = cv2.convertScaleAbs((l2.astype(np.float32) - 128) * alpha + 128).astype(np.uint8)
    
    merged = cv2.merge((l2, a, b))
    out = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # Noise reduction for very dark frames
    if v_mean < 55:
        out = cv2.bilateralFilter(out, 5, 40, 40)

    return out


def save_snapshot(frame, track_id, label):
    os.makedirs(ALERT_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(ALERT_DIR, f"{ts}_id{track_id}_{label}.jpg")
    cv2.imwrite(path, frame)
    return path


# =========================================================
# POSE HELPERS
# =========================================================
def point_from_kp(kp_xy, kp_cf, idx, min_conf=0.25):
    if kp_xy is None or idx < 0 or idx >= len(kp_xy):
        return None

    p = kp_xy[idx]
    x, y = float(p[0]), float(p[1])
    if x <= 0 or y <= 0:
        return None

    if kp_cf is not None and idx < len(kp_cf):
        if float(kp_cf[idx]) < min_conf:
            return None

    return np.array([x, y], dtype=np.float32)


def count_valid_points(kp_xy, kp_cf, indices, min_conf=0.25):
    if kp_xy is None:
        return 0
    cnt = 0
    for idx in indices:
        if point_from_kp(kp_xy, kp_cf, idx, min_conf=min_conf) is not None:
            cnt += 1
    return cnt


def angle_3pts(a, b, c):
    """Angle ABC in degrees."""
    if a is None or b is None or c is None:
        return None
    ba = a - b
    bc = c - b
    n1 = np.linalg.norm(ba)
    n2 = np.linalg.norm(bc)
    if n1 < 1e-6 or n2 < 1e-6:
        return None
    cosang = float(np.dot(ba, bc) / (n1 * n2))
    cosang = max(-1.0, min(1.0, cosang))
    return float(np.degrees(np.arccos(cosang)))


def torso_angle_and_center(kp_xy, kp_cf):
    ls = point_from_kp(kp_xy, kp_cf, 5)
    rs = point_from_kp(kp_xy, kp_cf, 6)
    lh = point_from_kp(kp_xy, kp_cf, 11)
    rh = point_from_kp(kp_xy, kp_cf, 12)

    shoulders = [p for p in [ls, rs] if p is not None]
    hips = [p for p in [lh, rh] if p is not None]

    if len(shoulders) == 0 or len(hips) == 0:
        return None, None, None, None

    shoulder_mid = np.mean(np.stack(shoulders), axis=0)
    hip_mid = np.mean(np.stack(hips), axis=0)

    sx, sy = float(shoulder_mid[0]), float(shoulder_mid[1])
    hx, hy = float(hip_mid[0]), float(hip_mid[1])

    dx = sx - hx
    dy = sy - hy

    angle = float(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))
    center = ((sx + hx) / 2.0, (sy + hy) / 2.0)
    return angle, center, shoulder_mid, hip_mid


def posture_from_features(angle, bbox_aspect):
    if angle <= STANDING_ANGLE and bbox_aspect < 1.05:
        return "NORMAL"
    if angle >= LYING_ANGLE or bbox_aspect >= 1.15:
        return "LYING"
    return "TRANSITION"


def signed_alternation_ratio(values, min_abs=6.0):
    """Estimate left-right gait alternation from sign changes of a signal."""
    if values is None or len(values) < 4:
        return 0.0

    prev_sign = 0
    sign_changes = 0
    valid_steps = 0
    for v in values:
        if abs(v) < min_abs:
            continue
        sign = 1 if v > 0 else -1
        if prev_sign != 0:
            valid_steps += 1
            if sign != prev_sign:
                sign_changes += 1
        prev_sign = sign

    if valid_steps <= 0:
        return 0.0
    return float(sign_changes / valid_steps)


def robust_slope(values):
    """Linear trend slope per frame for short temporal windows."""
    if values is None or len(values) < 4:
        return 0.0
    arr = np.asarray(values, dtype=np.float32)
    x = np.arange(len(arr), dtype=np.float32)
    x_centered = x - float(np.mean(x))
    denom = float(np.sum(x_centered * x_centered))
    if denom <= 1e-8:
        return 0.0
    y_centered = arr - float(np.mean(arr))
    return float(np.sum(x_centered * y_centered) / denom)


def oscillation_strength(values):
    if values is None or len(values) < 5:
        return 0.0
    arr = np.asarray(values, dtype=np.float32)
    diffs = np.diff(arr)
    if len(diffs) == 0:
        return 0.0
    return float(np.std(diffs))


def ratio_true(values):
    if values is None or len(values) == 0:
        return 0.0
    arr = np.asarray(values, dtype=np.float32)
    return float(np.mean(arr))


def overlap_ratio_1d(a1, a2, b1, b2):
    a1, a2 = float(min(a1, a2)), float(max(a1, a2))
    b1, b2 = float(min(b1, b2)), float(max(b1, b2))
    inter = max(0.0, min(a2, b2) - max(a1, b1))
    if inter <= 0.0:
        return 0.0
    base = min(max(1e-6, a2 - a1), max(1e-6, b2 - b1))
    return float(inter / base)


def point_in_expanded_box(point_xy, box, expand_px: float = 0.0):
    if point_xy is None or box is None:
        return False
    x, y = float(point_xy[0]), float(point_xy[1])
    x1, y1, x2, y2 = [float(v) for v in box]
    return (x1 - expand_px) <= x <= (x2 + expand_px) and (y1 - expand_px) <= y <= (y2 + expand_px)


def bbox_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = [float(v) for v in box_a]
    bx1, by1, bx2, by2 = [float(v) for v in box_b]
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, (ax2 - ax1)) * max(0.0, (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1)) * max(0.0, (by2 - by1))
    union = area_a + area_b - inter
    if union <= 1e-6:
        return 0.0
    return float(inter / union)


def dominant_id_ratio(values):
    """Return dominant positive track id and its ratio in a short history window."""
    if values is None or len(values) == 0:
        return None, 0.0
    counts: dict[int, int] = {}
    valid = 0
    for v in values:
        iv = int(v)
        if iv < 0:
            continue
        counts[iv] = counts.get(iv, 0) + 1
        valid += 1
    if valid == 0 or not counts:
        return None, 0.0
    best_id, best_count = max(counts.items(), key=lambda kv: kv[1])
    return int(best_id), float(best_count / valid)


# =========================================================
# ADVANCED SKELETON-BASED ANALYSIS (Không dựa vào YOLO)
# =========================================================
def analyze_bone_structure(keypoints_dict: dict):
    """
    Analyze bone proportions and structure from skeleton keypoints.
    Returns normalized limb ratios for posture classification.
    """
    try:
        # Limb lengths (spine, arms, legs)
        head = keypoints_dict.get("head")
        neck = keypoints_dict.get("neck")
        lshoulder = keypoints_dict.get("left_shoulder")
        rshoulder = keypoints_dict.get("right_shoulder")
        lhip = keypoints_dict.get("left_hip")
        rhip = keypoints_dict.get("right_hip")
        lelbow = keypoints_dict.get("left_elbow")
        relbow = keypoints_dict.get("right_elbow")
        lwrist = keypoints_dict.get("left_wrist")
        rwrist = keypoints_dict.get("right_wrist")
        lknee = keypoints_dict.get("left_knee")
        rknee = keypoints_dict.get("right_knee")
        lankle = keypoints_dict.get("left_ankle")
        rankle = keypoints_dict.get("right_ankle")
        
        structure = {}
        
        # Torso length (neck to mid-hip)
        if neck is not None and lhip is not None and rhip is not None:
            mid_hip = np.array([(lhip[0] + rhip[0]) * 0.5, (lhip[1] + rhip[1]) * 0.5], dtype=np.float32)
            torso_len = float(np.linalg.norm(np.array(neck, dtype=np.float32) - mid_hip))
            structure["torso_length"] = torso_len
        
        # Arm lengths (left and right)
        if lshoulder is not None and lwrist is not None:
            left_arm_len = float(np.linalg.norm(np.array(lshoulder, dtype=np.float32) - np.array(lwrist, dtype=np.float32)))
            structure["left_arm_length"] = left_arm_len
        
        if rshoulder is not None and rwrist is not None:
            right_arm_len = float(np.linalg.norm(np.array(rshoulder, dtype=np.float32) - np.array(rwrist, dtype=np.float32)))
            structure["right_arm_length"] = right_arm_len
        
        # Leg lengths (left and right)
        if lhip is not None and lankle is not None:
            left_leg_len = float(np.linalg.norm(np.array(lhip, dtype=np.float32) - np.array(lankle, dtype=np.float32)))
            structure["left_leg_length"] = left_leg_len
        
        if rhip is not None and rankle is not None:
            right_leg_len = float(np.linalg.norm(np.array(rhip, dtype=np.float32) - np.array(rankle, dtype=np.float32)))
            structure["right_leg_length"] = right_leg_len
        
        # Arm-to-torso ratio (short arm = holding object)
        if "left_arm_length" in structure and "torso_length" in structure:
            structure["left_arm_to_torso"] = structure["left_arm_length"] / max(1.0, structure["torso_length"])
        if "right_arm_length" in structure and "torso_length" in structure:
            structure["right_arm_to_torso"] = structure["right_arm_length"] / max(1.0, structure["torso_length"])
        
        # Leg symmetry (ratio of longest to shortest leg)
        if "left_leg_length" in structure and "right_leg_length" in structure:
            leg_len_ratio = max(structure["left_leg_length"], structure["right_leg_length"]) / max(1.0, min(structure["left_leg_length"], structure["right_leg_length"]))
            structure["leg_symmetry"] = leg_len_ratio
        
        return structure
    except Exception:
        return {}


def analyze_joint_geometry(keypoints_dict: dict, height: float = 1.0):
    """
    Advanced joint angle and spatial geometry analysis for posture classification.
    Focus on multi-angle signatures to distinguish poses.
    """
    try:
        geometry = {}
        
        # Left arm angles
        lshoulder = keypoints_dict.get("left_shoulder")
        lelbow = keypoints_dict.get("left_elbow")
        lwrist = keypoints_dict.get("left_wrist")
        if lshoulder is not None and lelbow is not None and lwrist is not None:
            ls = np.array(lshoulder, dtype=np.float32)
            le = np.array(lelbow, dtype=np.float32)
            lw = np.array(lwrist, dtype=np.float32)
            v1 = ls - le
            v2 = lw - le
            cos_angle = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6))
            left_elbow_angle = float(np.arccos(np.clip(cos_angle, -1, 1)) * 180.0 / np.pi)
            geometry["left_elbow_angle"] = left_elbow_angle
            
            # Left wrist height relative to shoulder
            geometry["left_wrist_shoulder_dy"] = float((lw[1] - ls[1]) / height)
        
        # Right arm angles
        rshoulder = keypoints_dict.get("right_shoulder")
        relbow = keypoints_dict.get("right_elbow")
        rwrist = keypoints_dict.get("right_wrist")
        if rshoulder is not None and relbow is not None and rwrist is not None:
            rs = np.array(rshoulder, dtype=np.float32)
            re = np.array(relbow, dtype=np.float32)
            rw = np.array(rwrist, dtype=np.float32)
            v1 = rs - re
            v2 = rw - re
            cos_angle = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6))
            right_elbow_angle = float(np.arccos(np.clip(cos_angle, -1, 1)) * 180.0 / np.pi)
            geometry["right_elbow_angle"] = right_elbow_angle
            
            # Right wrist height relative to shoulder
            geometry["right_wrist_shoulder_dy"] = float((rw[1] - rs[1]) / height)
        
        # Shoulder-to-hip angle (spine tilt)
        lshoulder = keypoints_dict.get("left_shoulder")
        rshoulder = keypoints_dict.get("right_shoulder")
        lhip = keypoints_dict.get("left_hip")
        rhip = keypoints_dict.get("right_hip")
        if all([lshoulder, rshoulder, lhip, rhip]):
            shoulder_mid = np.array([(lshoulder[0] + rshoulder[0]) * 0.5, (lshoulder[1] + rshoulder[1]) * 0.5], dtype=np.float32)
            hip_mid = np.array([(lhip[0] + rhip[0]) * 0.5, (lhip[1] + rhip[1]) * 0.5], dtype=np.float32)
            spine_vec = hip_mid - shoulder_mid
            geometry["spine_tilt_angle"] = float(np.arctan2(spine_vec[0], spine_vec[1]) * 180.0 / np.pi)
            geometry["spine_length"] = float(np.linalg.norm(spine_vec))
        
        # Arm asymmetry (holding pose detection)
        if "left_elbow_angle" in geometry and "right_elbow_angle" in geometry:
            asymmetry = float(abs(geometry["left_elbow_angle"] - geometry["right_elbow_angle"]))
            geometry["arm_asymmetry"] = asymmetry
            geometry["asymmetric_arm_pose"] = asymmetry > 35.0
        
        # Wrist height asymmetry (weapon holding signature)
        if "left_wrist_shoulder_dy" in geometry and "right_wrist_shoulder_dy" in geometry:
            wrist_dy_diff = float(abs(geometry["left_wrist_shoulder_dy"] - geometry["right_wrist_shoulder_dy"]))
            geometry["wrist_height_asymmetry"] = wrist_dy_diff
            geometry["asymmetric_wrist_height"] = wrist_dy_diff > 0.18
        
        return geometry
    except Exception:
        return {}


def detect_holding_pose(keypoints_dict: dict, height: float):
    """
    Detect if person is holding object based on arm geometry.
    Returns confidence score for holding vs. relaxed arms.
    """
    try:
        geometry = analyze_joint_geometry(keypoints_dict, height)
        
        holding_score = 0.0
        
        # Asymmetric arm angles suggest holding something
        if geometry.get("asymmetric_arm_pose", False):
            holding_score += 0.35
        
        # Asymmetric wrist heights suggest holding
        if geometry.get("asymmetric_wrist_height", False):
            holding_score += 0.30
        
        # One arm elevated, one lowered
        if "left_wrist_shoulder_dy" in geometry and "right_wrist_shoulder_dy" in geometry:
            left_dy = geometry["left_wrist_shoulder_dy"]
            right_dy = geometry["right_wrist_shoulder_dy"]
            if (left_dy < -0.12 and right_dy > 0.08) or (right_dy < -0.12 and left_dy > 0.08):
                holding_score += 0.20
        
        # Bent elbows (holding something typically means bent arms)
        left_elbow = geometry.get("left_elbow_angle", 180.0)
        right_elbow = geometry.get("right_elbow_angle", 180.0)
        bent_count = 0
        if 60.0 <= left_elbow <= 145.0:
            bent_count += 1
        if 60.0 <= right_elbow <= 145.0:
            bent_count += 1
        if bent_count >= 1:
            holding_score += 0.15
        
        return min(1.0, holding_score)
    except Exception:
        return 0.0


def analyze_spatial_context(person_bbox: tuple, nearby_people: list, scene_height: float):
    """
    Analyze spatial context to detect crowding and improve multi-person disambiguation.
    Returns crowd density and relative position among neighbors.
    """
    try:
        x1, y1, x2, y2 = person_bbox
        p_center = np.array([(x1 + x2) * 0.5, (y1 + y2) * 0.5], dtype=np.float32)
        p_h = max(1.0, y2 - y1)
        
        context = {}
        distances = []
        
        for other in nearby_people:
            ox1, oy1, ox2, oy2 = other
            if (ox1, oy1, ox2, oy2) == person_bbox:
                continue
            o_center = np.array([(ox1 + ox2) * 0.5, (oy1 + oy2) * 0.5], dtype=np.float32)
            dist = float(np.linalg.norm(p_center - o_center) / p_h)
            distances.append(dist)
        
        if distances:
            context["min_neighbor_dist"] = float(min(distances))
            context["avg_neighbor_dist"] = float(np.mean(distances))
            context["crowding_level"] = float(np.clip(1.0 - min(distances) / 2.0, 0.0, 1.0))
        else:
            context["min_neighbor_dist"] = 99.0
            context["avg_neighbor_dist"] = 99.0
            context["crowding_level"] = 0.0
        
        return context
    except Exception:
        return {}


def distinguish_weapon_vs_posture(
    keypoints_dict: dict,
    bone_structure: dict,
    geometry: dict,
    spatial_context: dict,
    height: float,
    weapon_detected: bool
) -> tuple[str, float]:
    """
    Advanced algorithm to distinguish weapon-holding from normal postures.
    Returns (classification, confidence) where classification is 'WEAPON', 'HOLDING_OBJECT', or 'NO_WEAPON'
    """
    try:
        confidence = 0.0
        classification = "NO_WEAPON"
        
        # If YOLO detected nothing, likely no weapon
        if not weapon_detected:
            # But check for holding pose indicators
            holding_conf = detect_holding_pose(keypoints_dict, height)
            if holding_conf > 0.55:
                return ("HOLDING_OBJECT", holding_conf)
            return ("NO_WEAPON", 0.0)
        
        # Weapon detected by YOLO - but verify with skeleton geometry
        # Key insight: weapon holding has specific geometric signatures:
        # 1. Asymmetric arms (one bent, one extended)
        # 2. One wrist low, one wrist high
        # 3. Hand distance suggests holding something
        
        arm_asymmetry = geometry.get("arm_asymmetry", 0.0)
        wrist_asym = geometry.get("wrist_height_asymmetry", 0.0)
        asymmetric_pose = geometry.get("asymmetric_arm_pose", False)
        asymmetric_wrist = geometry.get("asymmetric_wrist_height", False)
        
        leg_symmetry = bone_structure.get("leg_symmetry", 1.0)
        crowding = spatial_context.get("crowding_level", 0.0)
        
        # Crowding can cause false weapon detection - discount slightly
        crowding_penalty = 0.0 if crowding < 0.3 else (crowding * 0.15)
        
        # High arm asymmetry + asymmetric wrists = likely weapon
        if asymmetric_pose and asymmetric_wrist and arm_asymmetry > 40.0 and wrist_asym > 0.22:
            confidence += 0.55 - crowding_penalty
            classification = "WEAPON"
        
        # Check elbow angles for weapon-typical signatures
        left_elbow = geometry.get("left_elbow_angle", 180.0)
        right_elbow = geometry.get("right_elbow_angle", 180.0)
        
        # Typical weapon hold: one arm extended (>140°), other bent (<100°)
        if (left_elbow > 140.0 and 50.0 < right_elbow < 100.0) or \
           (right_elbow > 140.0 and 50.0 < left_elbow < 100.0):
            confidence += 0.35 - crowding_penalty
            if confidence >= 0.50:
                classification = "WEAPON"
        
        # Very asymmetric arms but in crowded scene - likely false positive
        if crowding > 0.5 and arm_asymmetry > 50.0 and not asymmetric_wrist:
            confidence *= 0.4  # Strong discount for crowded scenes
            if confidence < 0.40:
                classification = "HOLDING_OBJECT"
        
        confidence = max(0.0, min(1.0, confidence))
        
        return (classification, confidence)
    except Exception:
        return ("NO_WEAPON", 0.0)


def punch_kick_thresholds(motion_score: float):
    """Adaptive thresholds for punch/kick detection based on motion speed."""
    if motion_score >= 0.080:
        # Fast/running combat
        return {
            "punch_wrist": PUNCH_WRIST_SPEED_MIN * 0.90,
            "punch_accel": PUNCH_WRIST_ACCEL_MIN * 0.88,
            "kick_ankle": KICK_ANKLE_SPEED_MIN * 0.92,
            "kick_accel": KICK_ANKLE_ACCEL_MIN * 0.90,
        }
    elif motion_score >= 0.040:
        # Normal combat motion
        return {
            "punch_wrist": PUNCH_WRIST_SPEED_MIN,
            "punch_accel": PUNCH_WRIST_ACCEL_MIN,
            "kick_ankle": KICK_ANKLE_SPEED_MIN,
            "kick_accel": KICK_ANKLE_ACCEL_MIN,
        }
    else:
        # Slow/limited motion - lower thresholds
        return {
            "punch_wrist": PUNCH_WRIST_SPEED_MIN * 0.92,
            "punch_accel": PUNCH_WRIST_ACCEL_MIN * 0.85,
            "kick_ankle": KICK_ANKLE_SPEED_MIN * 0.88,
            "kick_accel": KICK_ANKLE_ACCEL_MIN * 0.82,
        }


def stab_thresholds(motion_score: float):
    """Adaptive thresholds for stab detection based on motion speed."""
    if motion_score >= 0.080:
        return {
            "wrist": STAB_WRIST_SPEED_MIN * 0.88,
            "elbow": STAB_ELBOW_EXT_SPEED_MIN * 0.90,
            "arm_straight": STAB_ARM_STRAIGHT_MIN + 8.0,
        }
    elif motion_score >= 0.040:
        return {
            "wrist": STAB_WRIST_SPEED_MIN,
            "elbow": STAB_ELBOW_EXT_SPEED_MIN,
            "arm_straight": STAB_ARM_STRAIGHT_MIN,
        }
    else:
        # Slow motion - much higher thresholds to avoid false positives
        return {
            "wrist": STAB_WRIST_SPEED_MIN * 1.15,
            "elbow": STAB_ELBOW_EXT_SPEED_MIN * 1.10,
            "arm_straight": STAB_ARM_STRAIGHT_MIN + 5.0,
        }


def softmax_scores(scores: dict[str, float], temperature: float = 1.35):
    keys = list(scores.keys())
    vals = np.asarray([float(scores[k]) for k in keys], dtype=np.float32)
    t = max(0.6, float(temperature))
    vals = vals / t
    vals = vals - float(np.max(vals))
    exp_vals = np.exp(vals)
    s = float(np.sum(exp_vals))
    if s <= 1e-8:
        p = np.ones_like(exp_vals) / max(1, len(exp_vals))
    else:
        p = exp_vals / s
    return {k: float(v) for k, v in zip(keys, p)}


# =========================================================
# SOURCE / CAPTURE
# =========================================================
def open_capture(source, source_type):
    if source_type == "webcam":
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(source, backend)
        return cap
    if source_type == "rtsp":
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        return cap
    return cv2.VideoCapture(source)


# =========================================================
# GUI APP
# =========================================================
class FallAlarmApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Fall Detection - GUI")
        self.geometry("1280x860")
        self.minsize(1100, 760)

        self.model = YOLO(MODEL_PATH)
        self.weapon_model = None
        self.weapon_model_path = ""
        self.weapon_model_num_classes = 0
        self.weapon_assume_all_classes = "weapon" in WEAPON_MODEL_PATH.lower()
        self.weapon_cache: list[dict] = []
        self.weapon_cache_expire: float = 0.0
        self.frame_index = 0
        for candidate in WEAPON_MODEL_CANDIDATES:
            if not os.path.isfile(candidate):
                continue
            try:
                self.weapon_model = YOLO(candidate)
                self.weapon_model_path = candidate
                names = getattr(self.weapon_model, "names", None)
                if isinstance(names, dict):
                    self.weapon_model_num_classes = len(names)
                elif isinstance(names, list):
                    self.weapon_model_num_classes = len(names)
                if self.weapon_model_num_classes and self.weapon_model_num_classes <= WEAPON_AUTO_ASSUME_MAX_CLASSES:
                    self.weapon_assume_all_classes = True
                print(f"[INFO] Loaded weapon model: {candidate}")
                break
            except Exception as ex:
                print(f"[WARN] Cannot load weapon model '{candidate}': {ex}")
        if self.weapon_model is None:
            print("[WARN] Weapon model not found, weapon detection disabled.")
        self.track_states: dict[int, PersonState] = {}

        self.running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.cap = None
        self.source_type = None
        self.source = None
        self.loop_video = True

        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.last_alarm_beep_time = 0.0

        self.source_mode = tk.StringVar(value="camera")
        self.camera_value = tk.StringVar(value="0")
        self.video_value = tk.StringVar(value="")
        self.status_value = tk.StringVar(value="Sẵn sàng")
        self.loop_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(15, self._refresh_preview)

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        control = ttk.LabelFrame(main, text="Điều khiển", padding=10)
        control.pack(fill="x")

        row1 = ttk.Frame(control)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Radiobutton(row1, text="Camera / RTSP", variable=self.source_mode, value="camera").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(row1, text="Video file", variable=self.source_mode, value="video").pack(side="left", padx=(0, 10))

        ttk.Label(row1, text="Camera index / RTSP:").pack(side="left", padx=(20, 6))
        self.camera_entry = ttk.Entry(row1, textvariable=self.camera_value, width=42)
        self.camera_entry.pack(side="left", padx=(0, 10))

        ttk.Label(row1, text="Video path:").pack(side="left", padx=(10, 6))
        self.video_entry = ttk.Entry(row1, textvariable=self.video_value, width=42)
        self.video_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ttk.Button(row1, text="Chọn video", command=self.choose_video).pack(side="left", padx=(0, 8))

        row2 = ttk.Frame(control)
        row2.pack(fill="x")

        ttk.Button(row2, text="Start", command=self.start).pack(side="left", padx=(0, 8))
        ttk.Button(row2, text="Stop", command=self.stop).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(row2, text="Lặp video khi hết", variable=self.loop_var).pack(side="left", padx=(10, 8))

        ttk.Label(row2, textvariable=self.status_value).pack(side="right")

        preview_frame = ttk.LabelFrame(main, text="Camera / Video", padding=8)
        preview_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill="both", expand=True)

        hint = ttk.Label(
            main,
            text="Phím trong cửa sổ: ESC/Q để thoát. Với video file, chương trình tự lặp nếu bật tùy chọn.",
        )
        hint.pack(fill="x", pady=(8, 0))

    def choose_video(self):
        path = filedialog.askopenfilename(
            title="Chọn video để chạy",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.video_value.set(path)
            self.source_mode.set("video")

    def _resolve_source(self):
        mode = self.source_mode.get().strip()
        if mode == "video":
            path = self.video_value.get().strip()
            if not path:
                messagebox.showerror("Thiếu video", "Chọn một file video trước khi Start.")
                return None, None
            if not os.path.isfile(path):
                messagebox.showerror("Sai đường dẫn", f"Không tìm thấy file video:\n{path}")
                return None, None
            return path, "file"

        raw = self.camera_value.get().strip()
        if not raw:
            messagebox.showerror("Thiếu nguồn", "Nhập camera index (0) hoặc RTSP URL trước khi Start.")
            return None, None

        if raw.isdigit():
            return int(raw), "webcam"
        if raw.lower().startswith("rtsp://"):
            return raw, "rtsp"
        if os.path.isfile(raw):
            return raw, "file"
        return raw, "rtsp"

    def _play_alarm_once(self):
        now = time.time()
        if now - self.last_alarm_beep_time < 1.0:
            return
        self.last_alarm_beep_time = now
        if HAVE_WINSOUND:
            try:
                winsound.Beep(1200, 180)
                winsound.Beep(1200, 180)
                winsound.Beep(1200, 180)
            except Exception:
                pass

    def _required_stable_frames(self, current_action: str, candidate_action: str):
        if current_action in ("ĐẤM", "ĐÁ") and candidate_action not in ("ĐẤM", "ĐÁ"):
            return 1
        if candidate_action == "BÁO ĐỘNG":
            return 1
        if candidate_action in ("ĐẤM", "ĐÁ"):
            return 1
        if candidate_action == "TÉ":
            return 2
        if candidate_action == "DI CHUYỂN CHIẾN ĐẤU":
            return 2
        if candidate_action == "CHIẾN ĐẤU":
            return 3
        if candidate_action == "ÔM VẬT":
            return 4
        if candidate_action == "CHẠY":
            return 3

        required = 4
        transitional = {"NGỒI", "ĐỨNG", "ĐI BỘ"}
        if current_action in transitional and candidate_action in transitional and current_action != candidate_action:
            required += TRANSITION_EXTRA_FRAMES
        if current_action == "NGỒI" and candidate_action == "ĐI BỘ":
            required += 1
        return required

    def _stabilize_action(
        self,
        st: PersonState,
        raw_action: str,
        scores: dict[str, float],
        now: float,
        confidence: float,
        transition_locked: bool,
    ):
        if raw_action == "BÁO ĐỘNG":
            st.committed_action = "BÁO ĐỘNG"
            st.pending_action = None
            st.pending_count = 0
            st.pending_since = None
            st.last_action_change = now
            st.action_window.append(raw_action)
            return "BÁO ĐỘNG"

        st.action_window.append(raw_action)

        if st.seen_frames < MIN_FRAMES_BEFORE_DECISION:
            return "ĐANG PHÂN TÍCH"

        # Bỏ phiếu theo đoạn ngắn thời gian, ưu tiên các frame gần hiện tại.
        votes: dict[str, float] = {}
        items = list(st.action_window)
        n = len(items)
        for i, label in enumerate(items):
            weight = 0.7 + (i + 1) / max(1.0, n)
            votes[label] = votes.get(label, 0.0) + weight

        voted_action = max(votes.items(), key=lambda kv: kv[1])[0]
        agree_ratio = items.count(voted_action) / max(1, len(items))

        total_score = max(1.0, float(sum(max(0.0, float(v)) for v in scores.values())))
        voted_score = float(scores.get(voted_action, 0))
        score_confidence = voted_score / total_score
        decision_confidence = max(float(confidence), score_confidence)

        if st.committed_action in ("UNKNOWN", "ĐANG PHÂN TÍCH"):
            st.committed_action = voted_action
            st.last_action_change = now
            return st.committed_action

        if voted_action == st.committed_action:
            st.pending_action = None
            st.pending_count = 0
            st.pending_since = None
            return st.committed_action

        required = self._required_stable_frames(st.committed_action, voted_action)
        if decision_confidence >= 0.50:
            required = max(2, required - 1)
        if transition_locked and st.committed_action in ("ĐỨNG", "ĐI BỘ", "NGỒI"):
            required += 1
        if decision_confidence >= HIGH_CONF_SWITCH:
            required = max(1, required - 1)
        if decision_confidence >= VERY_HIGH_CONF_SWITCH:
            required = 1

        if st.pending_action == voted_action:
            st.pending_count += 1
        else:
            st.pending_action = voted_action
            st.pending_count = 1
            st.pending_since = now

        pending_age = now - (st.pending_since if st.pending_since is not None else now)
        min_agree_ratio = 0.50 if decision_confidence >= VERY_HIGH_CONF_SWITCH else ACTION_STABLE_RATIO
        if (
            st.pending_count >= required
            and pending_age >= (0.10 if decision_confidence >= VERY_HIGH_CONF_SWITCH else ACTION_MIN_HOLD_SEC)
            and agree_ratio >= min_agree_ratio
        ):
            st.committed_action = voted_action
            st.last_action_change = now
            st.pending_action = None
            st.pending_count = 0
            st.pending_since = None

        return st.committed_action

    def start(self):
        if self.running:
            return

        source, source_type = self._resolve_source()
        if source is None:
            return

        self.source = source
        self.source_type = source_type
        self.loop_video = bool(self.loop_var.get())
        self.frame_index = 0
        self.weapon_cache = []
        self.weapon_cache_expire = 0.0
        self.cap = open_capture(self.source, self.source_type)

        if not self.cap.isOpened():
            messagebox.showerror("Lỗi mở nguồn", f"Không mở được nguồn:\n{self.source}")
            return

        self.stop_event.clear()
        self.running = True
        self.status_value.set("Đang chạy...")
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.running = False
        self.status_value.set("Đã dừng")
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass

    def on_close(self):
        self.stop()
        self.destroy()

    def _reconnect_capture(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        time.sleep(0.4)
        self.cap = open_capture(self.source, self.source_type)

    def _worker_loop(self):
        while not self.stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                if self.source_type in ("rtsp", "webcam"):
                    self._reconnect_capture()
                    if self.cap is None or not self.cap.isOpened():
                        time.sleep(0.2)
                        continue
                else:
                    break

            grabbed, frame = self.cap.read()
            if not grabbed or frame is None:
                if self.source_type == "file" and self.loop_video:
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        self._reconnect_capture()
                    continue

                if self.source_type in ("rtsp", "webcam"):
                    self._reconnect_capture()
                    continue

                break

            annotated = self._process_frame(frame)
            with self.frame_lock:
                self.latest_frame = annotated

            time.sleep(0.001)

        self.running = False
        self.status_value.set("Đã dừng")

    def _classify_person(self, st: PersonState, now: float, x1: int, y1: int, x2: int, y2: int, kp_xy, kp_cf):
        """
        Phân loại hành vi theo pose + motion + state machine.
        Trả về dict: {action, color, danger, save_frame}
        """
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        bbox_aspect = float(w / (h + 1e-6))

        angle, center, shoulder_mid, hip_mid = torso_angle_and_center(kp_xy, kp_cf)
        if angle is None or center is None:
            return None

        # current keypoints for limbs
        nose = point_from_kp(kp_xy, kp_cf, 0)
        leye = point_from_kp(kp_xy, kp_cf, 1)
        reye = point_from_kp(kp_xy, kp_cf, 2)
        ls = point_from_kp(kp_xy, kp_cf, 5)
        rs = point_from_kp(kp_xy, kp_cf, 6)
        le = point_from_kp(kp_xy, kp_cf, 7)
        re = point_from_kp(kp_xy, kp_cf, 8)
        lw = point_from_kp(kp_xy, kp_cf, 9)
        rw = point_from_kp(kp_xy, kp_cf, 10)
        lh = point_from_kp(kp_xy, kp_cf, 11)
        rh = point_from_kp(kp_xy, kp_cf, 12)
        lk = point_from_kp(kp_xy, kp_cf, 13)
        rk = point_from_kp(kp_xy, kp_cf, 14)
        la = point_from_kp(kp_xy, kp_cf, 15)
        ra = point_from_kp(kp_xy, kp_cf, 16)

        lower_valid = count_valid_points(kp_xy, kp_cf, [11, 12, 13, 14, 15, 16], min_conf=0.20)

        left_elbow_angle = angle_3pts(ls, le, lw)
        right_elbow_angle = angle_3pts(rs, re, rw)
        left_arm_flex = float(max(0.0, 180.0 - left_elbow_angle)) if left_elbow_angle is not None else 0.0
        right_arm_flex = float(max(0.0, 180.0 - right_elbow_angle)) if right_elbow_angle is not None else 0.0

        # knee angles
        left_knee_angle = angle_3pts(lh, lk, la)
        right_knee_angle = angle_3pts(rh, rk, ra)
        knee_angles = [a for a in [left_knee_angle, right_knee_angle] if a is not None]
        knee_angle_avg = float(np.mean(knee_angles)) if knee_angles else None
        left_flex = float(max(0.0, 180.0 - left_knee_angle)) if left_knee_angle is not None else None
        right_flex = float(max(0.0, 180.0 - right_knee_angle)) if right_knee_angle is not None else None

        knee_flex_diff = None
        if left_flex is not None and right_flex is not None:
            knee_flex_diff = float(left_flex - right_flex)

        left_elbow_ext_speed = 0.0
        if st.prev_left_elbow_angle is not None and left_elbow_angle is not None:
            left_elbow_ext_speed = float(left_elbow_angle - st.prev_left_elbow_angle)
        right_elbow_ext_speed = 0.0
        if st.prev_right_elbow_angle is not None and right_elbow_angle is not None:
            right_elbow_ext_speed = float(right_elbow_angle - st.prev_right_elbow_angle)

        left_knee_ext_speed = 0.0
        if st.prev_left_knee_angle is not None and left_knee_angle is not None:
            left_knee_ext_speed = float(left_knee_angle - st.prev_left_knee_angle)
        right_knee_ext_speed = 0.0
        if st.prev_right_knee_angle is not None and right_knee_angle is not None:
            right_knee_ext_speed = float(right_knee_angle - st.prev_right_knee_angle)

        # leg extension normalized by bbox height
        leg_exts = []
        if lh is not None and la is not None:
            leg_exts.append(float(np.linalg.norm(lh - la) / (h + 1e-6)))
        if rh is not None and ra is not None:
            leg_exts.append(float(np.linalg.norm(rh - ra) / (h + 1e-6)))
        leg_extension_avg = float(np.mean(leg_exts)) if leg_exts else None

        # bbox center speed
        if st.prev_center is None:
            abs_speed_px = 0.0
        else:
            dx = center[0] - st.prev_center[0]
            dy = center[1] - st.prev_center[1]
            abs_speed_px = float((dx * dx + dy * dy) ** 0.5)
        rel_speed = abs_speed_px / float(h + 1e-6)

        # ankle and wrist dynamics (normalized by bbox height)
        left_ankle_speed = 0.0
        if st.prev_left_ankle is not None and la is not None:
            left_ankle_speed = float(np.linalg.norm(la - np.array(st.prev_left_ankle, dtype=np.float32)) / max(1.0, h))
        right_ankle_speed = 0.0
        if st.prev_right_ankle is not None and ra is not None:
            right_ankle_speed = float(np.linalg.norm(ra - np.array(st.prev_right_ankle, dtype=np.float32)) / max(1.0, h))
        ankle_motion = float(left_ankle_speed + right_ankle_speed)

        left_wrist_speed = 0.0
        if st.prev_left_wrist is not None and lw is not None:
            left_wrist_speed = float(np.linalg.norm(lw - np.array(st.prev_left_wrist, dtype=np.float32)) / max(1.0, h))
        right_wrist_speed = 0.0
        if st.prev_right_wrist is not None and rw is not None:
            right_wrist_speed = float(np.linalg.norm(rw - np.array(st.prev_right_wrist, dtype=np.float32)) / max(1.0, h))

        left_wrist_accel = max(0.0, left_wrist_speed - st.prev_left_wrist_speed)
        right_wrist_accel = max(0.0, right_wrist_speed - st.prev_right_wrist_speed)
        left_ankle_accel = max(0.0, left_ankle_speed - st.prev_left_ankle_speed)
        right_ankle_accel = max(0.0, right_ankle_speed - st.prev_right_ankle_speed)

        hip_knee_rel = None
        if hip_mid is not None and lk is not None and rk is not None:
            knee_mid_y = float((lk[1] + rk[1]) * 0.5)
            hip_knee_rel = float((knee_mid_y - float(hip_mid[1])) / (h + 1e-6))

        ankle_span = None
        if la is not None and ra is not None:
            ankle_span = float(abs(float(la[0]) - float(ra[0])) / (h + 1e-6))

        hip_vertical_speed = 0.0
        if hip_mid is not None:
            hip_y = float(hip_mid[1])
            if st.prev_hip_y is not None:
                hip_vertical_speed = float((hip_y - st.prev_hip_y) / (h + 1e-6))
            st.prev_hip_y = hip_y

        # height change
        if st.prev_height is None:
            rel_height_change = 0.0
        else:
            rel_height_change = float((st.prev_height - h) / (st.prev_height + 1e-6))

        # update histories
        st.prev_center = center
        st.prev_height = float(h)
        st.angle_hist.append(angle)
        st.speed_hist.append(rel_speed)
        st.height_hist.append(float(h))
        st.ankle_motion_hist.append(ankle_motion)
        st.hip_vertical_speed_hist.append(hip_vertical_speed)
        st.wrist_speed_hist.append(float(max(left_wrist_speed, right_wrist_speed)))
        st.wrist_accel_hist.append(float(max(left_wrist_accel, right_wrist_accel)))
        st.ankle_speed_hist.append(float(max(left_ankle_speed, right_ankle_speed)))
        st.ankle_accel_hist.append(float(max(left_ankle_accel, right_ankle_accel)))
        st.elbow_ext_speed_hist.append(float(max(left_elbow_ext_speed, right_elbow_ext_speed)))
        st.knee_ext_speed_hist.append(float(max(left_knee_ext_speed, right_knee_ext_speed)))
        st.prev_left_ankle = tuple(la.tolist()) if la is not None else st.prev_left_ankle
        st.prev_right_ankle = tuple(ra.tolist()) if ra is not None else st.prev_right_ankle
        st.prev_left_wrist = tuple(lw.tolist()) if lw is not None else st.prev_left_wrist
        st.prev_right_wrist = tuple(rw.tolist()) if rw is not None else st.prev_right_wrist
        st.prev_left_wrist_speed = float(left_wrist_speed)
        st.prev_right_wrist_speed = float(right_wrist_speed)
        st.prev_left_ankle_speed = float(left_ankle_speed)
        st.prev_right_ankle_speed = float(right_ankle_speed)
        st.prev_left_elbow_angle = float(left_elbow_angle) if left_elbow_angle is not None else st.prev_left_elbow_angle
        st.prev_right_elbow_angle = float(right_elbow_angle) if right_elbow_angle is not None else st.prev_right_elbow_angle
        st.prev_left_knee_angle = float(left_knee_angle) if left_knee_angle is not None else st.prev_left_knee_angle
        st.prev_right_knee_angle = float(right_knee_angle) if right_knee_angle is not None else st.prev_right_knee_angle
        if left_flex is not None:
            st.knee_flex_l_hist.append(left_flex)
        if right_flex is not None:
            st.knee_flex_r_hist.append(right_flex)
        if left_flex is not None and right_flex is not None:
            st.knee_flex_mean_hist.append(float((left_flex + right_flex) * 0.5))
        if knee_flex_diff is not None:
            st.knee_flex_diff_hist.append(knee_flex_diff)
        if hip_knee_rel is not None:
            st.hip_knee_rel_hist.append(hip_knee_rel)
        if ankle_span is not None:
            st.ankle_span_hist.append(ankle_span)

        smooth_angle = float(np.mean(st.angle_hist))
        smooth_rel_speed = float(np.mean(st.speed_hist))
        smooth_ankle_motion = float(np.mean(st.ankle_motion_hist))
        smooth_height = float(np.mean(st.height_hist))
        smooth_hip_knee_rel = float(np.mean(st.hip_knee_rel_hist)) if st.hip_knee_rel_hist else None
        smooth_ankle_span = float(np.mean(st.ankle_span_hist)) if st.ankle_span_hist else None
        smooth_hip_vspeed = float(np.mean(st.hip_vertical_speed_hist)) if st.hip_vertical_speed_hist else 0.0
        smooth_wrist_speed = float(np.mean(st.wrist_speed_hist)) if st.wrist_speed_hist else 0.0
        smooth_wrist_accel = float(np.mean(st.wrist_accel_hist)) if st.wrist_accel_hist else 0.0
        smooth_ankle_speed = float(np.mean(st.ankle_speed_hist)) if st.ankle_speed_hist else 0.0
        smooth_ankle_accel = float(np.mean(st.ankle_accel_hist)) if st.ankle_accel_hist else 0.0
        smooth_elbow_ext = float(np.mean(st.elbow_ext_speed_hist)) if st.elbow_ext_speed_hist else 0.0
        smooth_knee_ext = float(np.mean(st.knee_ext_speed_hist)) if st.knee_ext_speed_hist else 0.0

        gait_alt_ratio = signed_alternation_ratio(list(st.knee_flex_diff_hist), min_abs=8.0)
        avg_left_flex = float(np.mean(st.knee_flex_l_hist)) if st.knee_flex_l_hist else 0.0
        avg_right_flex = float(np.mean(st.knee_flex_r_hist)) if st.knee_flex_r_hist else 0.0
        avg_knee_flex = float((avg_left_flex + avg_right_flex) * 0.5)
        knee_flex_trend = robust_slope(list(st.knee_flex_mean_hist)[-TRANSITION_TREND_WINDOW:])
        hip_knee_rel_trend = robust_slope(list(st.hip_knee_rel_hist)[-TRANSITION_TREND_WINDOW:])
        knee_diff_osc = oscillation_strength(list(st.knee_flex_diff_hist))

        motion_score = max(smooth_rel_speed, smooth_ankle_motion, smooth_wrist_speed * 0.75)

        # update motion timestamp if clear movement
        if motion_score >= SIGNIFICANT_MOTION_REL_THRES:
            st.last_significant_motion = now

        posture = posture_from_features(smooth_angle, bbox_aspect)

        # Sitting heuristic with geometric body-shape cues.
        sitting_score = 0
        if knee_angle_avg is not None and knee_angle_avg < SIT_KNEE_MAX:
            sitting_score += 2
        if leg_extension_avg is not None and leg_extension_avg < SIT_LEG_EXT_MAX:
            sitting_score += 2
        if SIT_ANGLE_MIN < smooth_angle < SIT_ANGLE_MAX:
            sitting_score += 1
        if 0.70 <= bbox_aspect <= 1.45:
            sitting_score += 1
        if motion_score < SIT_MAX_REL_SPEED:
            sitting_score += 1
        if rel_height_change > -0.10:
            sitting_score += 1
        if smooth_hip_knee_rel is not None and smooth_hip_knee_rel < SIT_HIP_KNEE_REL_MAX:
            sitting_score += 2
        if avg_knee_flex >= 25.0:
            sitting_score += 1
        if smooth_hip_vspeed > 0.004:
            sitting_score += 1
        if lower_valid < 3 and bbox_aspect >= 0.92 and motion_score < 0.014 and posture != "LYING":
            sitting_score += 2
        sit_geometry_strong = (
            smooth_hip_knee_rel is not None
            and smooth_hip_knee_rel < SIT_HIP_KNEE_REL_MAX + 0.015
            and avg_knee_flex >= 24.0
            and 0.72 <= bbox_aspect <= 1.52
        )
        if (
            not sit_geometry_strong
            and lower_valid < 3
            and bbox_aspect >= 0.98
            and motion_score <= SIT_SHAPE_SPEED_MAX
            and smooth_angle <= 45.0
        ):
            sit_geometry_strong = True
        seated_shape_hint = (
            bbox_aspect >= SIT_SHAPE_ASPECT_MIN
            and motion_score <= SIT_SHAPE_SPEED_MAX
            and smooth_angle <= 48.0
            and (
                avg_knee_flex >= 16.0
                or (smooth_hip_knee_rel is not None and smooth_hip_knee_rel <= SIT_HIP_KNEE_REL_MAX + 0.05)
            )
        )

        is_sitting = (
            posture != "LYING"
            and (
                (sitting_score >= 6 and motion_score < WALK_REL_THRES)
                or sit_geometry_strong
                or seated_shape_hint
                or (st.committed_action == "NGỒI" and sitting_score >= 5 and motion_score < RUN_REL_THRES * 0.75)
            )
        )

        # Gait phase cues: walking/running should show alternating knee flex pattern.
        gait_walk_ready = (
            gait_alt_ratio >= GAIT_ALT_WALK_MIN
            and avg_knee_flex >= KNEE_FLEX_WALK_MIN
            and posture != "LYING"
        )
        gait_run_ready = (
            gait_alt_ratio >= GAIT_ALT_RUN_MIN
            and avg_knee_flex >= KNEE_FLEX_RUN_MIN
            and posture == "NORMAL"
        )

        gait_cadence_walk = gait_alt_ratio * min(1.6, 0.8 + knee_diff_osc / 10.0)
        gait_cadence_run = gait_alt_ratio * min(2.0, motion_score / max(RUN_REL_THRES * 0.85, 1e-6))

        # Transition intent cues to avoid abrupt NGOI <-> DUNG / DI BO jumps.
        sit_down_intent = (
            smooth_hip_vspeed > SIT_DESCENT_VSPEED_MIN
            and knee_flex_trend >= KNEE_FLEX_TREND_SIT_MIN
            and avg_knee_flex >= 20.0
            and (smooth_hip_knee_rel is None or smooth_hip_knee_rel <= STAND_HIP_KNEE_REL_MIN + 0.02)
            and posture in ("NORMAL", "TRANSITION")
        )
        stand_up_intent = (
            smooth_hip_vspeed < -STAND_ASCENT_VSPEED_MIN
            and knee_flex_trend <= -KNEE_FLEX_TREND_STAND_MIN
            and smooth_hip_knee_rel is not None
            and smooth_hip_knee_rel >= STAND_HIP_KNEE_REL_MIN
            and posture in ("NORMAL", "TRANSITION")
        )

        if sit_down_intent and posture != "LYING":
            if st.transition_phase != "TO_SIT":
                st.transition_phase = "TO_SIT"
                st.transition_since = now
        elif stand_up_intent and posture != "LYING":
            if st.transition_phase != "TO_STAND":
                st.transition_phase = "TO_STAND"
                st.transition_since = now
        elif st.transition_phase != "NONE":
            phase_age = now - (st.transition_since if st.transition_since is not None else now)
            if phase_age > 1.4 or abs(smooth_hip_vspeed) < 0.0018:
                st.transition_phase = "NONE"
                st.transition_since = None

        shoulder_y = float(shoulder_mid[1]) if shoulder_mid is not None else None
        hip_y = float(hip_mid[1]) if hip_mid is not None else None
        torso_mid = None
        if shoulder_mid is not None and hip_mid is not None:
            torso_mid = (shoulder_mid + hip_mid) * 0.5

        head_candidates = [p for p in [nose, leye, reye] if p is not None]
        if head_candidates:
            head_point = np.mean(np.stack(head_candidates), axis=0)
        elif shoulder_mid is not None:
            head_point = np.array([float(shoulder_mid[0]), float(shoulder_mid[1]) - h * 0.16], dtype=np.float32)
        else:
            head_point = None

        guard_score = 0
        if posture != "LYING":
            guard_score += 1
        if smooth_ankle_span is not None and 0.08 <= smooth_ankle_span <= 0.58:  # Extended range
            guard_score += 1
        if 6.0 <= avg_knee_flex <= 58.0:  # More lenient knee flex
            guard_score += 1
        if left_arm_flex >= 15.0:  # Lower threshold
            guard_score += 1
        if right_arm_flex >= 15.0:  # Lower threshold
            guard_score += 1
        if shoulder_y is not None and lw is not None and float(lw[1]) <= shoulder_y + h * 0.20:  # Extended
            guard_score += 1
        if shoulder_y is not None and rw is not None and float(rw[1]) <= shoulder_y + h * 0.20:  # Extended
            guard_score += 1
        # Additional: if weapon detected, boost guard score
        if smooth_wrist_speed >= PUNCH_WRIST_SPEED_MIN * 0.85:
            guard_score += 1

        guard_pose = guard_score >= COMBAT_GUARD_MIN
        st.guard_pose_hist.append(1.0 if guard_pose else 0.0)
        guard_ratio = ratio_true(st.guard_pose_hist)

        punch_left = False
        punch_right = False
        if hip_y is not None:
            thresholds = punch_kick_thresholds(motion_score)
            punch_left = (
                left_wrist_speed >= thresholds["punch_wrist"]
                and left_wrist_accel >= thresholds["punch_accel"]
                and left_elbow_ext_speed >= PUNCH_ELBOW_EXT_SPEED_MIN * 0.92
                and lw is not None
                and float(lw[1]) <= hip_y + h * 0.12
            )
            punch_right = (
                right_wrist_speed >= thresholds["punch_wrist"]
                and right_wrist_accel >= thresholds["punch_accel"]
                and right_elbow_ext_speed >= PUNCH_ELBOW_EXT_SPEED_MIN * 0.92
                and rw is not None
                and float(rw[1]) <= hip_y + h * 0.12
            )
        punch_detected = (punch_left or punch_right) and posture != "LYING"

        stab_left = False
        stab_right = False
        if hip_y is not None:
            # OPTIMIZED & ADAPTIVE: More lenient thresholds for knife stabbing motions
            thresholds = stab_thresholds(motion_score)
            stab_left = (
                left_wrist_speed >= thresholds["wrist"]
                and left_elbow_ext_speed >= thresholds["elbow"]
                and left_elbow_angle is not None
                and float(left_elbow_angle) >= thresholds["arm_straight"]
                and lw is not None
                and float(lw[1]) <= hip_y + h * 0.28  # Extended range for natural holding
            )
            stab_right = (
                right_wrist_speed >= thresholds["wrist"]
                and right_elbow_ext_speed >= thresholds["elbow"]
                and right_elbow_angle is not None
                and float(right_elbow_angle) >= thresholds["arm_straight"]
                and rw is not None
                and float(rw[1]) <= hip_y + h * 0.28  # Extended range for natural holding
            )
        stab_detected = (stab_left or stab_right) and posture != "LYING"

        kick_left = False
        kick_right = False
        if hip_y is not None:
            thresholds = punch_kick_thresholds(motion_score)
            kick_left = (
                left_ankle_speed >= thresholds["kick_ankle"]
                and left_ankle_accel >= thresholds["kick_accel"]
                and left_knee_ext_speed >= KICK_KNEE_EXT_SPEED_MIN * 0.92
                and la is not None
                and float(la[1]) <= hip_y + h * 0.28
            )
            kick_right = (
                right_ankle_speed >= thresholds["kick_ankle"]
                and right_ankle_accel >= thresholds["kick_accel"]
                and right_knee_ext_speed >= KICK_KNEE_EXT_SPEED_MIN * 0.92
                and ra is not None
                and float(ra[1]) <= hip_y + h * 0.28
            )
        kick_detected = (kick_left or kick_right) and posture != "LYING"

        hold_pose = False
        hold_posture_ok = (
            posture in ("NORMAL", "TRANSITION")
            and not is_sitting
            and avg_knee_flex < 22.0
            and (smooth_hip_knee_rel is None or smooth_hip_knee_rel >= SIT_HIP_KNEE_REL_MAX + 0.02)
        )
        if lw is not None and rw is not None and torso_mid is not None and shoulder_mid is not None and hip_mid is not None:
            wrist_dist = float(np.linalg.norm(lw - rw) / (h + 1e-6))
            wrist_to_torso = float((np.linalg.norm(lw - torso_mid) + np.linalg.norm(rw - torso_mid)) * 0.5 / (h + 1e-6))
            wrist_band_ok = (
                float(shoulder_mid[1]) - h * 0.05 <= float(lw[1]) <= float(hip_mid[1]) + h * 0.22
                and float(shoulder_mid[1]) - h * 0.05 <= float(rw[1]) <= float(hip_mid[1]) + h * 0.22
            )
            hold_pose = (
                wrist_dist <= HOLD_WRIST_DIST_MAX
                and wrist_to_torso <= HOLD_WRIST_TORSO_MAX
                and wrist_band_ok
                and left_arm_flex >= 20.0
                and right_arm_flex >= 20.0
                and max(left_wrist_speed, right_wrist_speed) <= HOLD_WRIST_SPEED_MAX
                and hold_posture_ok
            )
        st.hold_pose_hist.append(1.0 if hold_pose else 0.0)
        hold_ratio = ratio_true(st.hold_pose_hist)
        hold_persist = len(st.hold_pose_hist) >= 6 and hold_ratio >= 0.70 and hold_posture_ok

        combat_energy = (
            float(max(left_wrist_speed, right_wrist_speed)) * 1.2
            + float(max(left_ankle_speed, right_ankle_speed)) * 1.1
            + float(max(left_wrist_accel, right_wrist_accel)) * 2.0
            + float(max(left_ankle_accel, right_ankle_accel)) * 1.6
            + float(max(left_elbow_ext_speed, right_elbow_ext_speed, 0.0)) * 0.025
            + float(max(left_knee_ext_speed, right_knee_ext_speed, 0.0)) * 0.020
            + (0.24 if guard_pose else 0.0)
        )
        st.fight_energy_hist.append(combat_energy)
        smooth_combat_energy = float(np.mean(st.fight_energy_hist)) if st.fight_energy_hist else 0.0
        combat_move = (
            (guard_pose or guard_ratio >= 0.55)
            and motion_score >= COMBAT_MOTION_MIN
            and motion_score < RUN_REL_THRES * 1.45
            and gait_alt_ratio < 0.62
            and posture != "LYING"
        )

        # fall candidate
        sudden_drop = False
        if st.prev_angle is not None and st.seen_frames >= 3:
            angle_drop = abs(smooth_angle - st.prev_angle)
            if st.prev_posture in ("NORMAL", "TRANSITION") and posture == "LYING":
                if (
                    motion_score >= WALK_REL_THRES
                    or angle_drop >= 18.0
                    or bbox_aspect >= 1.15
                    or rel_height_change > 0.12
                ):
                    sudden_drop = True

        if sudden_drop and st.fall_started is None:
            st.fall_started = now
            st.last_significant_motion = now

        if posture == "LYING":
            if st.lying_since is None:
                st.lying_since = now
        else:
            st.lying_since = None

        if posture == "NORMAL" and not is_sitting:
            if st.fall_started is not None and motion_score >= WALK_REL_THRES:
                st.fall_started = None
                st.alarmed = False

        scores = {action_name: 0.0 for action_name in ACTIONS}

        if posture == "NORMAL":
            scores["ĐỨNG"] += 3
        if smooth_angle < 25 and bbox_aspect < 1.05:
            scores["ĐỨNG"] += 2
        if knee_angle_avg is not None and knee_angle_avg > 160:
            scores["ĐỨNG"] += 1
        if leg_extension_avg is not None and leg_extension_avg > 0.95:
            scores["ĐỨNG"] += 1
        if motion_score < 0.006:
            scores["ĐỨNG"] += 2
        if smooth_hip_knee_rel is not None and smooth_hip_knee_rel >= STAND_HIP_KNEE_REL_MIN:
            scores["ĐỨNG"] += 1
        if avg_knee_flex < 14.0:
            scores["ĐỨNG"] += 1
        if lower_valid < 3 and bbox_aspect >= 0.95 and motion_score < SIT_MAX_REL_SPEED * 1.1:
            scores["ĐỨNG"] -= 1.8
        if lower_valid < 2 and smooth_hip_knee_rel is None and bbox_aspect >= 0.98:
            scores["ĐỨNG"] -= 1.3
        if stand_up_intent:
            scores["ĐỨNG"] += 1.4
        if st.transition_phase == "TO_STAND":
            scores["ĐỨNG"] += 0.8
        if sit_geometry_strong:
            scores["ĐỨNG"] -= 2.6
        if seated_shape_hint:
            scores["ĐỨNG"] -= 2.2

        if 0.012 <= motion_score < RUN_REL_THRES:
            scores["ĐI BỘ"] += 3
        if posture == "NORMAL" and motion_score >= WALK_REL_THRES:
            scores["ĐI BỘ"] += 1
        if smooth_angle < 45 and bbox_aspect < 1.3:
            scores["ĐI BỘ"] += 1
        if motion_score >= SIGNIFICANT_MOTION_REL_THRES:
            scores["ĐI BỘ"] += 1
        if gait_walk_ready:
            scores["ĐI BỘ"] += 3
        if smooth_ankle_span is not None and smooth_ankle_span > 0.10:
            scores["ĐI BỘ"] += 1
        if gait_cadence_walk >= 0.35:
            scores["ĐI BỘ"] += 1.8
        if st.transition_phase == "TO_STAND" and motion_score >= WALK_REL_THRES * 0.8:
            scores["ĐI BỘ"] += 1.0

        if motion_score >= RUN_REL_THRES:
            scores["CHẠY"] += 4
        if motion_score >= RUN_REL_THRES * 1.2:
            scores["CHẠY"] += 1
        if posture == "NORMAL" and motion_score >= RUN_REL_THRES:
            scores["CHẠY"] += 1
        if gait_run_ready:
            scores["CHẠY"] += 2
        if smooth_ankle_motion >= RUN_REL_THRES * 0.9:
            scores["CHẠY"] += 1
        if gait_cadence_run >= 0.85:
            scores["CHẠY"] += 1.8

        if is_sitting:
            scores["NGỒI"] += 4
        if knee_angle_avg is not None and knee_angle_avg < SIT_KNEE_MAX:
            scores["NGỒI"] += 1
        if leg_extension_avg is not None and leg_extension_avg < SIT_LEG_EXT_MAX:
            scores["NGỒI"] += 1
        if SIT_ANGLE_MIN < smooth_angle < SIT_ANGLE_MAX:
            scores["NGỒI"] += 1
        if 0.70 <= bbox_aspect <= 1.45:
            scores["NGỒI"] += 1
        if motion_score < SIT_MAX_REL_SPEED:
            scores["NGỒI"] += 1
        if smooth_hip_knee_rel is not None and smooth_hip_knee_rel < SIT_HIP_KNEE_REL_MAX:
            scores["NGỒI"] += 2
        if avg_knee_flex >= 22.0:
            scores["NGỒI"] += 1
        if sit_down_intent:
            scores["NGỒI"] += 1.7
        if st.transition_phase == "TO_SIT":
            scores["NGỒI"] += 1.0
        if hip_knee_rel_trend <= -0.0018:
            scores["NGỒI"] += 0.7
        if sit_geometry_strong:
            scores["NGỒI"] += 2.0
        if seated_shape_hint:
            scores["NGỒI"] += 1.8
        if st.committed_action == "NGỒI" and not stand_up_intent:
            scores["NGỒI"] += 1.1

        if posture == "LYING":
            scores["TÉ"] += 4
        if smooth_angle >= LYING_ANGLE:
            scores["TÉ"] += 2
        if bbox_aspect >= 1.15:
            scores["TÉ"] += 1
        if st.fall_started is not None:
            scores["TÉ"] += 3

        if guard_pose:
            scores["CHIẾN ĐẤU"] += 3.5  # Slightly increased
        if guard_ratio >= 0.60:  # Tightened from 0.52 - require sustained guard pose
            scores["CHIẾN ĐẤU"] += 1.8
        if 18.0 <= avg_knee_flex <= 52.0:  # Tightened range from 12-58
            scores["CHIẾN ĐẤU"] += 0.95
        if smooth_combat_energy >= 0.28:  # Tightened from 0.22
            scores["CHIẾN ĐẤU"] += 1.3
        if punch_detected or kick_detected or stab_detected:
            scores["CHIẾN ĐẤU"] += 1.6

        if combat_move:
            scores["DI CHUYỂN CHIẾN ĐẤU"] += 3.2
        if guard_pose and motion_score >= WALK_REL_THRES * 0.8:
            scores["DI CHUYỂN CHIẾN ĐẤU"] += 1.0
        if gait_walk_ready and guard_ratio < 0.45:
            scores["DI CHUYỂN CHIẾN ĐẤU"] -= 0.8

        if punch_detected:
            scores["ĐẤM"] += 5.2
        if max(left_wrist_speed, right_wrist_speed) >= PUNCH_WRIST_SPEED_MIN * 1.2:
            scores["ĐẤM"] += 1.2
        if max(left_elbow_ext_speed, right_elbow_ext_speed) >= PUNCH_ELBOW_EXT_SPEED_MIN * 1.1:
            scores["ĐẤM"] += 1.0
        if stab_detected:
            scores["ĐẤM"] += 3.8  # ENHANCED: Stab contributes more to punch score

        if kick_detected:
            scores["ĐÁ"] += 5.4
        if max(left_ankle_speed, right_ankle_speed) >= KICK_ANKLE_SPEED_MIN * 1.18:
            scores["ĐÁ"] += 1.2
        if max(left_knee_ext_speed, right_knee_ext_speed) >= KICK_KNEE_EXT_SPEED_MIN * 1.12:
            scores["ĐÁ"] += 1.0

        if hold_persist:
            scores["ÔM VẬT"] += 3.4
        if hold_pose:
            scores["ÔM VẬT"] += 1.1
        if motion_score <= WALK_REL_THRES * 1.12:
            scores["ÔM VẬT"] += 0.5
        if posture in ("NORMAL", "TRANSITION"):
            scores["ÔM VẬT"] += 0.4
        if is_sitting or sit_geometry_strong:
            scores["ÔM VẬT"] -= 2.4

        danger = False
        if (st.fall_started is not None or posture == "LYING") and st.last_significant_motion is not None:
            no_motion_sec = now - st.last_significant_motion
            if no_motion_sec >= ALERT_AFTER_LIE_SEC and motion_score <= STILL_REL_THRES:
                danger = True

        if danger:
            raw_action = "BÁO ĐỘNG"
            decision_confidence = 1.0
            transition_locked = False
        else:
            raw_probs = softmax_scores(scores, temperature=1.30)
            if not st.action_prob_ema:
                st.action_prob_ema = {k: float(v) for k, v in raw_probs.items()}
            else:
                for k in ACTIONS:
                    prev = float(st.action_prob_ema.get(k, 0.0))
                    cur = float(raw_probs.get(k, 0.0))
                    st.action_prob_ema[k] = prev * (1.0 - PROB_EMA_ALPHA) + cur * PROB_EMA_ALPHA

            probs = {k: float(st.action_prob_ema.get(k, 0.0)) for k in ACTIONS}
            committed = st.committed_action
            combat_actions = {"CHIẾN ĐẤU", "DI CHUYỂN CHIẾN ĐẤU", "ĐẤM", "ĐÁ"}
            if committed == "NGỒI":
                sit_locked = (now - float(st.last_action_change)) <= SIT_LOCK_SEC and not stand_up_intent
                probs["CHẠY"] *= 0.52
                probs["ĐI BỘ"] *= 1.05 if stand_up_intent else (0.56 if sit_locked else 0.78)
                probs["ĐỨNG"] *= 1.12 if stand_up_intent else (0.52 if sit_locked else 0.78)
                probs["ÔM VẬT"] *= 0.48 if sit_locked else 0.62
                probs["NGỒI"] *= 1.20 if sit_locked or seated_shape_hint else 1.05
            elif committed in ("ĐỨNG", "ĐI BỘ"):
                probs["NGỒI"] *= 1.18 if sit_down_intent else 0.72
            elif committed == "CHẠY" and motion_score < RUN_REL_THRES * 0.78:
                probs["CHẠY"] *= 0.74
            elif committed == "TÉ":
                if posture == "LYING":
                    probs["TÉ"] *= 1.20
                if stand_up_intent and motion_score >= WALK_REL_THRES:
                    probs["ĐỨNG"] *= 1.08
            elif committed == "ÔM VẬT":
                probs["ÔM VẬT"] *= 1.18 if hold_persist else 0.78

            if committed in combat_actions:
                probs["CHIẾN ĐẤU"] *= 1.08
                probs["DI CHUYỂN CHIẾN ĐẤU"] *= 1.08 if combat_move else 0.88
                if not (punch_detected or kick_detected or stab_detected):
                    probs["ĐẤM"] *= 0.76
                    probs["ĐÁ"] *= 0.76
                probs["NGỒI"] *= 0.72
                probs["ÔM VẬT"] *= 0.68
            else:
                if not (guard_pose or punch_detected or kick_detected or stab_detected):
                    probs["CHIẾN ĐẤU"] *= 0.74
                    probs["DI CHUYỂN CHIẾN ĐẤU"] *= 0.72
                if not (punch_detected or stab_detected):
                    probs["ĐẤM"] *= 0.68
                if not kick_detected:
                    probs["ĐÁ"] *= 0.68
                if not hold_persist:
                    probs["ÔM VẬT"] *= 0.78

            if is_sitting or sit_geometry_strong or seated_shape_hint:
                probs["ÔM VẬT"] *= 0.44
                probs["ĐỨNG"] *= 0.64
                probs["NGỒI"] *= 1.16
            if hold_posture_ok and hold_persist:
                probs["NGỒI"] *= 0.76

            if st.transition_phase == "TO_SIT":
                probs["NGỒI"] *= 1.22
                probs["CHẠY"] *= 0.72
            elif st.transition_phase == "TO_STAND":
                probs["ĐỨNG"] *= 1.14
                probs["ĐI BỘ"] *= 1.10

            if hold_persist:
                probs["ĐẤM"] *= 0.66
                probs["ĐÁ"] *= 0.70

            if kick_detected:
                probs["ĐẤM"] *= 0.86
            if punch_detected:
                probs["ĐÁ"] *= 0.88

            prob_sum = max(1e-8, float(sum(probs.values())))
            probs = {k: float(v / prob_sum) for k, v in probs.items()}

            sorted_probs = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
            raw_action = sorted_probs[0][0]
            decision_confidence = float(sorted_probs[0][1])
            second_prob = float(sorted_probs[1][1]) if len(sorted_probs) > 1 else 0.0
            prob_margin = decision_confidence - second_prob

            transition_locked = False
            if st.committed_action not in ("UNKNOWN", "ĐANG PHÂN TÍCH", "BÁO ĐỘNG"):
                event_override = (raw_action == "ĐẤM" and punch_detected) or (raw_action == "ĐÁ" and kick_detected)
                if raw_action != st.committed_action and prob_margin < 0.08 and decision_confidence < HIGH_CONF_SWITCH and not event_override:
                    raw_action = st.committed_action
                    transition_locked = True

            if raw_action == "ĐỨNG":
                if motion_score >= RUN_REL_THRES:
                    raw_action = "CHẠY"
                elif motion_score >= WALK_REL_THRES:
                    raw_action = "ĐI BỘ"

            if raw_action == "ĐẤM" and not (punch_detected or stab_detected) and decision_confidence < VERY_HIGH_CONF_SWITCH:
                raw_action = "CHIẾN ĐẤU" if (guard_pose or guard_ratio >= 0.60) else st.committed_action

            if raw_action == "ĐÁ" and not kick_detected and decision_confidence < VERY_HIGH_CONF_SWITCH:
                raw_action = "DI CHUYỂN CHIẾN ĐẤU" if combat_move else st.committed_action

            if raw_action == "DI CHUYỂN CHIẾN ĐẤU" and not combat_move and decision_confidence < HIGH_CONF_SWITCH:
                raw_action = "CHIẾN ĐẤU" if (guard_pose or guard_ratio >= 0.60) else "ĐI BỘ"

            if raw_action == "CHIẾN ĐẤU" and not guard_pose and not (punch_detected or kick_detected):
                if motion_score >= WALK_REL_THRES:
                    raw_action = "ĐI BỘ"
                elif motion_score < SIT_MAX_REL_SPEED and avg_knee_flex < 16.0:
                    raw_action = "ĐỨNG"

            if raw_action == "ÔM VẬT" and not hold_persist and decision_confidence < HIGH_CONF_SWITCH:
                raw_action = st.committed_action if st.committed_action not in ("UNKNOWN", "ĐANG PHÂN TÍCH") else "ĐỨNG"

            if raw_action in ("ĐỨNG", "ÔM VẬT") and is_sitting and not stand_up_intent:
                raw_action = "NGỒI"
                transition_locked = True

            # Far/crowded seated rows often miss lower-body keypoints; keep them from bouncing to standing labels.
            if (
                raw_action in ("ĐỨNG", "ĐI BỘ", "ÔM VẬT")
                and lower_valid < 2
                and seated_shape_hint
                and motion_score < WALK_REL_THRES * 0.90
                and not stand_up_intent
            ):
                raw_action = "NGỒI"
                transition_locked = True

            if (
                st.committed_action == "NGỒI"
                and raw_action == "ĐỨNG"
                and not stand_up_intent
                and motion_score < WALK_REL_THRES
                and seated_shape_hint
            ):
                raw_action = "NGỒI"
                transition_locked = True

            # Transition guards for NGỒI <-> ĐỨNG / ĐI BỘ.
            if st.committed_action == "NGỒI" and raw_action in ("ĐỨNG", "ĐI BỘ"):
                if not stand_up_intent and avg_knee_flex >= 18.0:
                    raw_action = "NGỒI"
                    transition_locked = True

            if st.committed_action in ("ĐỨNG", "ĐI BỘ") and raw_action == "NGỒI":
                if not sit_down_intent and motion_score > SIT_MAX_REL_SPEED * 0.9:
                    raw_action = st.committed_action
                    transition_locked = True

            if raw_action == "ĐI BỘ" and not gait_walk_ready and motion_score < RUN_REL_THRES:
                if avg_knee_flex < 12.0:
                    raw_action = "ĐỨNG"

        action = self._stabilize_action(
            st,
            raw_action,
            scores,
            now,
            confidence=decision_confidence,
            transition_locked=transition_locked,
        )

        if action == "NGỒI" and st.transition_phase == "TO_SIT":
            st.transition_phase = "NONE"
            st.transition_since = None
        if action in ("ĐỨNG", "ĐI BỘ", "CHẠY") and st.transition_phase == "TO_STAND":
            st.transition_phase = "NONE"
            st.transition_since = None

        color_map = {
            "ĐỨNG": (0, 255, 0),
            "ĐI BỘ": (0, 255, 0),
            "CHẠY": (0, 255, 0),
            "NGỒI": (0, 255, 0),
            "TÉ": (0, 255, 255),
            "CHIẾN ĐẤU": (0, 170, 255),
            "DI CHUYỂN CHIẾN ĐẤU": (0, 145, 255),
            "ĐẤM": (0, 90, 255),
            "ĐÁ": (0, 60, 255),
            "ÔM VẬT": (255, 200, 0),
            "BẮT NẠT": (80, 40, 255),
            "DẤU HIỆU BẮT NẠT": (0, 255, 255),
            "BÁO ĐỘNG": (0, 0, 255),
            "ĐANG PHÂN TÍCH": (220, 220, 220),
            "UNKNOWN": (255, 255, 255),
        }
        color = color_map.get(action, (255, 255, 255))

        save_frame = False
        if danger and not st.alarmed:
            st.alarmed = True
            self._play_alarm_once()
            save_frame = True

        st.prev_angle = smooth_angle
        st.prev_posture = posture

        return {
            "action": action,
            "color": color,
            "danger": danger,
            "save_frame": save_frame,
            "interaction": {
                "head": tuple(head_point.tolist()) if head_point is not None else None,
                "torso_mid": tuple(torso_mid.tolist()) if torso_mid is not None else None,
                "shoulder_mid": tuple(shoulder_mid.tolist()) if shoulder_mid is not None else None,
                "left_wrist": tuple(lw.tolist()) if lw is not None else None,
                "right_wrist": tuple(rw.tolist()) if rw is not None else None,
                "left_ankle": tuple(la.tolist()) if la is not None else None,
                "right_ankle": tuple(ra.tolist()) if ra is not None else None,
                "left_elbow": tuple(le.tolist()) if le is not None else None,
                "right_elbow": tuple(re.tolist()) if re is not None else None,
                "left_shoulder": tuple(ls.tolist()) if ls is not None else None,
                "right_shoulder": tuple(rs.tolist()) if rs is not None else None,
                "hip_mid": tuple(hip_mid.tolist()) if hip_mid is not None else None,
                "left_elbow_angle": float(left_elbow_angle) if left_elbow_angle is not None else None,
                "right_elbow_angle": float(right_elbow_angle) if right_elbow_angle is not None else None,
                "left_wrist_speed": float(left_wrist_speed),
                "right_wrist_speed": float(right_wrist_speed),
                "motion_score": float(motion_score),
                "punch_detected": bool(punch_detected),
                "kick_detected": bool(kick_detected),
                "stab_detected": bool(stab_detected),
                "guard_ratio": float(guard_ratio),
                "combat_energy": float(smooth_combat_energy),
                "combat_move": bool(combat_move),
                "center": (float(center[0]), float(center[1])),
                "height": float(h),
                "posture": posture,
                "is_sitting": bool(is_sitting),
                "lower_valid": int(lower_valid),
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                # Advanced skeleton analysis for weapon vs posture discrimination
                "keypoints_dict": {
                    "head": tuple(head_point.tolist()) if head_point is not None else None,
                    "neck": tuple(((ls[0] + rs[0]) * 0.5, (ls[1] + rs[1]) * 0.5)) if ls is not None and rs is not None else None,
                    "left_shoulder": tuple(ls.tolist()) if ls is not None else None,
                    "right_shoulder": tuple(rs.tolist()) if rs is not None else None,
                    "left_elbow": tuple(le.tolist()) if le is not None else None,
                    "right_elbow": tuple(re.tolist()) if re is not None else None,
                    "left_wrist": tuple(lw.tolist()) if lw is not None else None,
                    "right_wrist": tuple(rw.tolist()) if rw is not None else None,
                    "left_hip": tuple(lh.tolist()) if lh is not None else None,
                    "right_hip": tuple(rh.tolist()) if rh is not None else None,
                    "left_knee": tuple(lk.tolist()) if lk is not None else None,
                    "right_knee": tuple(rk.tolist()) if rk is not None else None,
                    "left_ankle": tuple(la.tolist()) if la is not None else None,
                    "right_ankle": tuple(ra.tolist()) if ra is not None else None,
                },
                "guard_pose": bool(guard_pose),
                "hold_pose": bool(hold_pose),
            },
            "metrics": {
                "angle": smooth_angle,
                "speed": smooth_rel_speed,
                "ankle_motion": smooth_ankle_motion,
                "motion_score": motion_score,
                "knee": knee_angle_avg,
                "leg_ext": leg_extension_avg,
                "posture": posture,
                "sitting_score": sitting_score,
                "height": smooth_height,
                "bbox_aspect": bbox_aspect,
                "hip_knee_rel": smooth_hip_knee_rel,
                "hip_vspeed": smooth_hip_vspeed,
                "ankle_span": smooth_ankle_span,
                "gait_alt_ratio": gait_alt_ratio,
                "gait_cadence_walk": gait_cadence_walk,
                "gait_cadence_run": gait_cadence_run,
                "avg_knee_flex": avg_knee_flex,
                "knee_flex_trend": knee_flex_trend,
                "hip_knee_rel_trend": hip_knee_rel_trend,
                "knee_diff_osc": knee_diff_osc,
                "wrist_speed": smooth_wrist_speed,
                "wrist_accel": smooth_wrist_accel,
                "ankle_speed": smooth_ankle_speed,
                "ankle_accel": smooth_ankle_accel,
                "elbow_ext": smooth_elbow_ext,
                "knee_ext": smooth_knee_ext,
                "guard_score": guard_score,
                "guard_ratio": guard_ratio,
                "combat_energy": smooth_combat_energy,
                "combat_move": combat_move,
                "hold_ratio": hold_ratio,
                "hold_persist": hold_persist,
                "punch_detected": punch_detected,
                "kick_detected": kick_detected,
                "stab_detected": stab_detected,
                "seated_shape_hint": seated_shape_hint,
                "sit_down_intent": sit_down_intent,
                "stand_up_intent": stand_up_intent,
                "transition_phase": st.transition_phase,
                "decision_confidence": decision_confidence,
                "raw_action": raw_action,
            },
        }

    def _detect_bullying_interactions(self, people_data, now: float):
        """Aggressor-only bullying detection for crowded scenes.

        Rules:
        - Red BẮT NẠT: túm đầu/tóc, chạm vùng nhạy cảm.
        - Yellow DẤU HIỆU BẮT NẠT: chỉ vào mặt.
        """
        if not people_data:
            return {}

        present_ids = {int(item.get("track_id")) for item in people_data}
        candidate_map = {}

        for aggressor in people_data:
            a_id = int(aggressor["track_id"])
            st = aggressor["state"]
            ia = aggressor.get("interaction", {})
            base_action = aggressor.get("action")
            a_center = ia.get("center")
            a_head = ia.get("head")
            a_h = max(1.0, float(ia.get("height", 1.0)))
            a_posture = ia.get("posture")
            a_box = (aggressor.get("x1", 0), aggressor.get("y1", 0), aggressor.get("x2", 0), aggressor.get("y2", 0))
            a_bottom = float(aggressor.get("y2", 0))
            a_is_sitting = bool(ia.get("is_sitting", False))
            a_lower_valid = int(ia.get("lower_valid", 0))

            if a_center is None or a_posture == "LYING" or st.seen_frames < BULLY_MIN_SEEN_FRAMES:
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue
            if base_action in ("TÉ", "BÁO ĐỘNG", "ĐANG PHÂN TÍCH"):
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue
            # CRITICAL: Skip if aggressor is sitting - bullying requires active standing/moving aggressor
            if a_is_sitting or a_lower_valid < 2:
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue

            lw = ia.get("left_wrist")
            rw = ia.get("right_wrist")
            le = ia.get("left_elbow")
            re = ia.get("right_elbow")
            ls = ia.get("left_shoulder")
            rs = ia.get("right_shoulder")
            left_elbow_angle = ia.get("left_elbow_angle")
            right_elbow_angle = ia.get("right_elbow_angle")
            left_wrist_speed = float(ia.get("left_wrist_speed", 0.0))
            right_wrist_speed = float(ia.get("right_wrist_speed", 0.0))

            wrists = []
            if lw is not None:
                wrists.append(
                    (
                        np.array(lw, dtype=np.float32),
                        np.array(le, dtype=np.float32) if le is not None else None,
                        np.array(ls, dtype=np.float32) if ls is not None else None,
                        left_elbow_angle,
                        left_wrist_speed,
                    )
                )
            if rw is not None:
                wrists.append(
                    (
                        np.array(rw, dtype=np.float32),
                        np.array(re, dtype=np.float32) if re is not None else None,
                        np.array(rs, dtype=np.float32) if rs is not None else None,
                        right_elbow_angle,
                        right_wrist_speed,
                    )
                )
            if not wrists:
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue

            prefiltered_victims = []
            for victim in people_data:
                v_id = int(victim["track_id"])
                if v_id == a_id:
                    continue

                vst = victim.get("state")
                if vst is None or vst.seen_frames < BULLY_MIN_SEEN_FRAMES:
                    continue

                iv = victim.get("interaction", {})
                v_head = iv.get("head")
                v_center = iv.get("center")
                v_h = max(1.0, float(iv.get("height", 1.0)))
                v_posture = iv.get("posture")
                v_is_sitting = bool(iv.get("is_sitting", False))
                v_lower_valid = int(iv.get("lower_valid", 0))
                if v_head is None or v_center is None or v_posture == "LYING":
                    continue
                # CRITICAL: Skip if victim sitting - bullying requires standing victim
                if BULLY_STANDING_ONLY and (v_is_sitting or v_lower_valid < 2):
                    continue
                # Additional: Even if not STANDING_ONLY mode, if both sitting close together, not bullying
                if v_is_sitting and a_is_sitting:
                    continue

                v_box = (victim.get("x1", 0), victim.get("y1", 0), victim.get("x2", 0), victim.get("y2", 0))
                v_bottom = float(victim.get("y2", 0))
                pair_scale = max(1.0, (a_h + v_h) * 0.5)
                center_delta = np.array(a_center, dtype=np.float32) - np.array(v_center, dtype=np.float32)
                center_dist = float(np.linalg.norm(center_delta) / pair_scale)
                center_x_gap = float(abs(center_delta[0]) / pair_scale)
                if center_dist > BULLY_INTERACT_RANGE or center_x_gap > BULLY_MAX_CENTER_X_GAP:
                    continue

                height_ratio = float(min(a_h, v_h) / max(a_h, v_h))
                if height_ratio < BULLY_MIN_HEIGHT_RATIO:
                    continue

                bottom_gap = float(abs(a_bottom - v_bottom) / max(a_h, v_h))
                if bottom_gap > BULLY_MAX_BOTTOM_GAP:
                    continue

                x_overlap = overlap_ratio_1d(a_box[0], a_box[2], v_box[0], v_box[2])
                y_overlap = overlap_ratio_1d(a_box[1], a_box[3], v_box[1], v_box[3])
                if x_overlap < BULLY_MIN_X_OVERLAP or y_overlap < BULLY_MIN_Y_OVERLAP:
                    continue

                prefiltered_victims.append((victim, iv, v_box, pair_scale, center_dist, bottom_gap, height_ratio, x_overlap))

            if not prefiltered_victims:
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue

            prefiltered_victims.sort(key=lambda item: item[4])
            prefiltered_victims = prefiltered_victims[: BULLY_NEAREST_CANDIDATES]

            own_head_np = np.array(a_head, dtype=np.float32) if a_head is not None else None
            best_red_strength = 0.0
            best_red_target = None
            best_warn_strength = 0.0
            best_warn_target = None

            for victim, iv, v_box, pair_scale, center_dist, bottom_gap, height_ratio, x_overlap in prefiltered_victims:
                v_id = int(victim["track_id"])
                v_center = np.array(iv.get("center"), dtype=np.float32)
                head_np = np.array(iv.get("head"), dtype=np.float32)

                v_torso = iv.get("torso_mid")
                if v_torso is not None:
                    torso_np = np.array(v_torso, dtype=np.float32)
                else:
                    v_hip = iv.get("hip_mid")
                    v_shoulder = iv.get("shoulder_mid")
                    if v_hip is not None and v_shoulder is not None:
                        torso_np = (np.array(v_hip, dtype=np.float32) + np.array(v_shoulder, dtype=np.float32)) * 0.5
                    else:
                        torso_np = v_center
                v_hip = iv.get("hip_mid")
                pelvis_np = np.array(v_hip, dtype=np.float32) if v_hip is not None else v_center

                victim_red = 0.0
                victim_warn = 0.0

                for wrist_np, elbow_np, shoulder_np, elbow_angle, wrist_speed in wrists:
                    if shoulder_np is None:
                        continue
                    arm_reach = float(np.linalg.norm(wrist_np - shoulder_np) / (a_h + 1e-6))
                    if arm_reach < BULLY_MIN_ARM_REACH:
                        continue

                    d_head = float(np.linalg.norm(wrist_np - head_np) / pair_scale)
                    d_torso = float(np.linalg.norm(wrist_np - torso_np) / pair_scale)
                    d_pelvis = float(np.linalg.norm(wrist_np - pelvis_np) / pair_scale)
                    own_head_dist = 10.0
                    if own_head_np is not None:
                        own_head_dist = float(np.linalg.norm(wrist_np - own_head_np) / pair_scale)

                    expand_px = pair_scale * 0.08
                    in_victim_box = point_in_expanded_box(wrist_np, v_box, expand_px=expand_px)

                    align = 0.0
                    if elbow_np is not None:
                        arm_vec = wrist_np - elbow_np
                        tgt_vec = head_np - elbow_np
                        n_arm = float(np.linalg.norm(arm_vec))
                        n_tgt = float(np.linalg.norm(tgt_vec))
                        if n_arm > 1e-6 and n_tgt > 1e-6:
                            align = float(np.dot(arm_vec, tgt_vec) / (n_arm * n_tgt))

                    head_grab_strength = 0.0
                    if (
                        d_head <= BULLY_HEAD_GRAB_DIST
                        and in_victim_box
                        and own_head_dist >= d_head + 0.02
                        and 0.001 <= wrist_speed <= 0.095
                        and align >= 0.10
                    ):
                        head_grab_strength = (BULLY_HEAD_GRAB_DIST - d_head) * 2.2 + max(0.0, align - 0.10) * 0.25

                    sensitive_touch_strength = 0.0
                    if (
                        in_victim_box
                        and own_head_dist >= min(d_torso, d_pelvis) + 0.02
                        and 0.0005 <= wrist_speed <= 0.095
                        and (d_torso <= BULLY_SENSITIVE_DIST or d_pelvis <= BULLY_SENSITIVE_DIST)
                    ):
                        sensitive_touch_strength = (BULLY_SENSITIVE_DIST - min(d_torso, d_pelvis)) * 1.65 + 0.06

                    point_strength = 0.0
                    if (
                        elbow_np is not None
                        and elbow_angle is not None
                        and d_head <= BULLY_POINT_FACE_DIST
                        and own_head_dist >= d_head + 0.03
                        and align >= BULLY_POINT_ALIGN_MIN
                        and float(elbow_angle) >= BULLY_POINT_ELBOW_MIN
                        and 0.0001 <= wrist_speed <= 0.070
                    ):
                        point_strength = (BULLY_POINT_FACE_DIST - d_head) * 1.55 + (align - BULLY_POINT_ALIGN_MIN) * 0.55

                    red_strength = max(head_grab_strength, sensitive_touch_strength)
                    if red_strength > 0.0:
                        depth_score = max(0.0, 1.0 - bottom_gap / max(BULLY_MAX_BOTTOM_GAP, 1e-6))
                        scale_score = min(1.0, height_ratio / max(BULLY_MIN_HEIGHT_RATIO, 1e-6))
                        overlap_score = min(1.0, x_overlap / max(BULLY_MIN_X_OVERLAP, 1e-6))
                        near_score = max(0.0, 1.0 - center_dist / max(BULLY_INTERACT_RANGE, 1e-6))
                        red_strength *= 0.48 + 0.20 * depth_score + 0.16 * scale_score + 0.08 * overlap_score + 0.08 * near_score

                    if red_strength > victim_red:
                        victim_red = red_strength
                    if point_strength > victim_warn:
                        victim_warn = point_strength

                if victim_red > best_red_strength:
                    best_red_strength = victim_red
                    best_red_target = v_id
                if victim_warn > best_warn_strength:
                    best_warn_strength = victim_warn
                    best_warn_target = v_id

            chosen_target = best_red_target if best_red_strength >= best_warn_strength * 0.85 else best_warn_target
            st.bully_target_hist.append(int(chosen_target) if chosen_target is not None else -1)
            st.bully_hist.append(min(1.0, best_red_strength / max(1e-6, BULLY_MIN_STRENGTH)))
            st.bully_warn_hist.append(min(1.0, best_warn_strength / max(1e-6, BULLY_POINT_WARN_MIN_STRENGTH)))

            bully_ratio = ratio_true(st.bully_hist)
            warn_ratio = ratio_true(st.bully_warn_hist)
            stable_target_id, stable_target_ratio = dominant_id_ratio(st.bully_target_hist)

            red_active = (
                best_red_target is not None
                and stable_target_id == best_red_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_red_strength >= BULLY_MIN_STRENGTH
                and bully_ratio >= BULLY_PERSIST_MIN
            )
            warn_active = (
                not red_active
                and best_warn_target is not None
                and stable_target_id == best_warn_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_warn_strength >= BULLY_POINT_WARN_MIN_STRENGTH
                and warn_ratio >= BULLY_POINT_PERSIST_MIN
            )

            if red_active:
                st.bully_target_id = int(best_red_target)
                st.bully_active_until = now + BULLY_STICKY_SEC
                candidate_map[a_id] = {
                    "score": float(best_red_strength + bully_ratio * 0.03),
                    "target_id": int(best_red_target),
                    "label": "BẮT NẠT",
                }
                continue

            sticky_red_ok = (
                st.bully_target_id is not None
                and st.bully_target_id in present_ids
                and now <= st.bully_active_until
                and bully_ratio >= BULLY_RELEASE_PERSIST_MIN
                and best_red_strength >= BULLY_CONTACT_STRENGTH_MIN
            )
            if sticky_red_ok:
                candidate_map[a_id] = {
                    "score": float(max(best_red_strength, BULLY_MIN_STRENGTH * bully_ratio)),
                    "target_id": int(st.bully_target_id),
                    "label": "BẮT NẠT",
                }
                continue

            st.bully_target_id = None

            if warn_active:
                st.bully_warn_target_id = int(best_warn_target)
                st.bully_warn_active_until = now + max(0.5, BULLY_STICKY_SEC * 0.75)
                candidate_map[a_id] = {
                    "score": float(best_warn_strength + warn_ratio * 0.02),
                    "target_id": int(best_warn_target),
                    "label": "DẤU HIỆU BẮT NẠT",
                }
                continue

            sticky_warn_ok = (
                st.bully_warn_target_id is not None
                and st.bully_warn_target_id in present_ids
                and now <= st.bully_warn_active_until
                and warn_ratio >= BULLY_RELEASE_PERSIST_MIN
                and best_warn_strength >= BULLY_POINT_WARN_MIN_STRENGTH * 0.65
            )
            if sticky_warn_ok:
                candidate_map[a_id] = {
                    "score": float(max(best_warn_strength, BULLY_POINT_WARN_MIN_STRENGTH * warn_ratio)),
                    "target_id": int(st.bully_warn_target_id),
                    "label": "DẤU HIỆU BẮT NẠT",
                }
                continue

            st.bully_warn_target_id = None

        detection_map = {}
        suppressed = set()
        claimed_target = {}
        ordered = sorted(
            candidate_map.items(),
            key=lambda kv: (1 if kv[1].get("label") == "BẮT NẠT" else 0, kv[1]["score"]),
            reverse=True,
        )

        for a_id, data in ordered:
            if a_id in suppressed:
                continue
            t_id = int(data["target_id"])
            label = data.get("label", "BẮT NẠT")
            if t_id not in present_ids:
                continue

            reverse = candidate_map.get(t_id)
            if reverse is not None and int(reverse.get("target_id", -1)) == a_id:
                if data["score"] >= reverse["score"] + BULLY_ROLE_MARGIN:
                    suppressed.add(t_id)
                elif reverse["score"] >= data["score"] + BULLY_ROLE_MARGIN:
                    suppressed.add(a_id)
                    continue
                else:
                    suppressed.add(a_id)
                    suppressed.add(t_id)
                    continue

            prev_owner = claimed_target.get(t_id)
            if prev_owner is not None and prev_owner["score"] >= data["score"] - BULLY_ROLE_MARGIN:
                continue

            detection_map[a_id] = {
                "label": label,
                "target_id": t_id,
            }
            claimed_target[t_id] = {"aggressor_id": a_id, "score": float(data["score"])}

        return detection_map

    def _detect_combat_interactions(self, people_data, now: float, weapon_owner_map):
        """Pairwise combat detector with impact cues (aggressor-only labeling)."""
        if not people_data:
            return {}

        present_ids = {int(item.get("track_id")) for item in people_data}
        candidate_map = {}

        for aggressor in people_data:
            a_id = int(aggressor["track_id"])
            st = aggressor["state"]
            ia = aggressor.get("interaction", {})
            a_center = ia.get("center")
            a_posture = ia.get("posture")
            a_h = max(1.0, float(ia.get("height", 1.0)))
            a_box = (aggressor.get("x1", 0), aggressor.get("y1", 0), aggressor.get("x2", 0), aggressor.get("y2", 0))
            a_bottom = float(aggressor.get("y2", 0))
            a_is_sitting = bool(ia.get("is_sitting", False))
            
            # CRITICAL: Skip if aggressor is sitting - combat requires standing/moving
            if a_center is None or a_posture == "LYING" or st.seen_frames < BULLY_MIN_SEEN_FRAMES or a_is_sitting:
                st.combat_hist.append(0.0)
                st.combat_target_hist.append(-1)
                continue

            punch_detected = bool(ia.get("punch_detected", False))
            kick_detected = bool(ia.get("kick_detected", False))
            stab_detected = bool(ia.get("stab_detected", False))
            strike_detected = punch_detected or kick_detected or stab_detected
            guard_ratio = float(ia.get("guard_ratio", 0.0))
            combat_energy = float(ia.get("combat_energy", 0.0))
            combat_move = bool(ia.get("combat_move", False))
            a_motion = float(ia.get("motion_score", 0.0))

            lw = ia.get("left_wrist")
            rw = ia.get("right_wrist")
            la = ia.get("left_ankle")
            ra = ia.get("right_ankle")
            striking_points = []
            if lw is not None:
                striking_points.append(np.array(lw, dtype=np.float32))
            if rw is not None:
                striking_points.append(np.array(rw, dtype=np.float32))
            if kick_detected and la is not None:
                striking_points.append(np.array(la, dtype=np.float32))
            if kick_detected and ra is not None:
                striking_points.append(np.array(ra, dtype=np.float32))

            if not striking_points:
                st.combat_hist.append(0.0)
                st.combat_target_hist.append(-1)
                continue

            best_strength = 0.0
            best_target = None
            for victim in people_data:
                v_id = int(victim["track_id"])
                if v_id == a_id:
                    continue

                iv = victim.get("interaction", {})
                v_center = iv.get("center")
                v_posture = iv.get("posture")
                v_h = max(1.0, float(iv.get("height", 1.0)))
                v_is_sitting = bool(iv.get("is_sitting", False))
                
                # CRITICAL: Skip if victim is sitting - sitting close together is NOT combat
                if v_center is None or v_posture == "LYING" or v_is_sitting:
                    continue

                v_box = (victim.get("x1", 0), victim.get("y1", 0), victim.get("x2", 0), victim.get("y2", 0))
                v_bottom = float(victim.get("y2", 0))
                pair_scale = max(1.0, (a_h + v_h) * 0.5)
                center_delta = np.array(a_center, dtype=np.float32) - np.array(v_center, dtype=np.float32)
                center_dist = float(np.linalg.norm(center_delta) / pair_scale)
                if center_dist > COMBAT_INTERACT_RANGE:
                    continue

                height_ratio = float(min(a_h, v_h) / max(a_h, v_h))
                if height_ratio < COMBAT_MIN_HEIGHT_RATIO:
                    continue

                bottom_gap = float(abs(a_bottom - v_bottom) / max(a_h, v_h))
                if bottom_gap > COMBAT_MAX_BOTTOM_GAP:
                    continue

                x_overlap = overlap_ratio_1d(a_box[0], a_box[2], v_box[0], v_box[2])
                if x_overlap < COMBAT_MIN_X_OVERLAP and center_dist > COMBAT_INTERACT_RANGE * 0.65:
                    continue
                
                # CRITICAL: Both people with very low motion in crowded scene = not combat
                # (they're just standing/moving together normally)
                v_motion = float(iv.get("motion_score", 0.0))
                if a_motion < WALK_REL_THRES * 0.5 and v_motion < WALK_REL_THRES * 0.5 and not strike_detected:
                    continue  # Both stationary/minimal motion + no strikes = not combat

                v_head = iv.get("head")
                v_torso = iv.get("torso_mid")
                v_hip = iv.get("hip_mid")
                if v_head is None:
                    continue
                v_head_np = np.array(v_head, dtype=np.float32)
                v_torso_np = np.array(v_torso, dtype=np.float32) if v_torso is not None else np.array(v_center, dtype=np.float32)
                v_hip_np = np.array(v_hip, dtype=np.float32) if v_hip is not None else np.array(v_center, dtype=np.float32)

                min_contact_dist = 99.0
                for p in striking_points:
                    d_head = float(np.linalg.norm(p - v_head_np) / pair_scale)
                    d_torso = float(np.linalg.norm(p - v_torso_np) / pair_scale)
                    d_hip = float(np.linalg.norm(p - v_hip_np) / pair_scale)
                    min_contact_dist = min(min_contact_dist, d_head, d_torso, d_hip)

                recoil = float(iv.get("motion_score", 0.0)) >= COMBAT_TARGET_RECOIL_MIN or victim.get("action") in ("TÉ", "BÁO ĐỘNG")
                weapon_owned = a_id in weapon_owner_map

                contact_limit = COMBAT_WEAPON_CONTACT_DIST if weapon_owned else COMBAT_CONTACT_DIST
                contact_ok = min_contact_dist <= contact_limit

                strength = 0.0
                if strike_detected and contact_ok:
                    strength += 0.095 + max(0.0, (contact_limit - min_contact_dist)) * 0.70  # Enhanced stab/strike
                if stab_detected and contact_ok:
                    strength += 0.065  # Higher reward for stab
                if kick_detected and contact_ok:
                    strength += 0.048
                if punch_detected and contact_ok:
                    strength += 0.043
                if weapon_owned and contact_ok:
                    strength += 0.080  # Significant boost for weapon holder
                if guard_ratio >= 0.60 and (strike_detected or combat_move):  # Tightened from 0.55
                    strength += 0.032  # Enhanced guard+action multiplier
                if combat_energy >= 0.28:  # Tightened from 0.25
                    strength += 0.028
                if recoil:
                    strength += 0.035  # Boost if victim shows recoil
                if a_motion >= COMBAT_MOTION_MIN * 0.95 and center_dist <= COMBAT_INTERACT_RANGE * 0.75:  # Tightened from 0.85
                    strength += 0.016

                depth_score = max(0.0, 1.0 - bottom_gap / max(COMBAT_MAX_BOTTOM_GAP, 1e-6))
                near_score = max(0.0, 1.0 - center_dist / max(COMBAT_INTERACT_RANGE, 1e-6))
                strength *= 0.62 + 0.22 * depth_score + 0.16 * near_score

                if strength > best_strength:
                    best_strength = strength
                    best_target = v_id

            st.combat_target_hist.append(int(best_target) if best_target is not None else -1)
            st.combat_hist.append(min(1.0, best_strength / max(1e-6, COMBAT_MIN_STRENGTH)))

            combat_ratio = ratio_true(st.combat_hist)
            stable_target_id, stable_target_ratio = dominant_id_ratio(st.combat_target_hist)
            red_active = (
                best_target is not None
                and stable_target_id == best_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_strength >= COMBAT_MIN_STRENGTH
                and combat_ratio >= COMBAT_PERSIST_MIN
            )
            if red_active:
                st.combat_target_id = int(best_target)
                st.combat_active_until = now + COMBAT_STICKY_SEC
                candidate_map[a_id] = {
                    "score": float(best_strength + combat_ratio * 0.03),
                    "target_id": int(best_target),
                    "label": "CHIẾN ĐẤU",
                }
                continue

            sticky_ok = (
                st.combat_target_id is not None
                and st.combat_target_id in present_ids
                and now <= st.combat_active_until
                and combat_ratio >= COMBAT_RELEASE_PERSIST_MIN
                and best_strength >= COMBAT_MIN_STRENGTH * 0.45
            )
            if sticky_ok:
                candidate_map[a_id] = {
                    "score": float(max(best_strength, COMBAT_MIN_STRENGTH * combat_ratio)),
                    "target_id": int(st.combat_target_id),
                    "label": "CHIẾN ĐẤU",
                }
                continue

            st.combat_target_id = None

        detection_map = {}
        claimed_target = {}
        for a_id, data in sorted(candidate_map.items(), key=lambda kv: kv[1]["score"], reverse=True):
            t_id = int(data["target_id"])
            if t_id not in present_ids:
                continue
            prev_owner = claimed_target.get(t_id)
            if prev_owner is not None and prev_owner["score"] >= data["score"] - BULLY_ROLE_MARGIN:
                continue
            detection_map[a_id] = {"label": "CHIẾN ĐẤU", "target_id": t_id}
            claimed_target[t_id] = {"aggressor_id": a_id, "score": float(data["score"])}

        return detection_map

    def _is_weapon_label(self, label: str):
        normalized = label.strip().lower()
        if not normalized:
            return bool(self.weapon_assume_all_classes)
        
        # Direct keyword matching with better distinction
        knife_keywords = ("knife", "dao", "dagger", "dq", "blade", "thanh kiếm", "kiếm")
        gun_keywords = ("gun", "pistol", "sung", "rifle", "shotgun", "ak")
        
        for k in knife_keywords:
            if k in normalized:
                return True
        for k in gun_keywords:
            if k in normalized:
                return True
        
        if any(k in normalized for k in WEAPON_CLASS_KEYWORDS):
            return True
        
        # Numeric class IDs - assume weapon for compact models
        if normalized.isdigit() and self.weapon_model_num_classes and self.weapon_model_num_classes <= WEAPON_AUTO_ASSUME_MAX_CLASSES:
            return True
        
        return bool(self.weapon_assume_all_classes)

    def _detect_weapons(self, frame, now: float):
        if self.weapon_model is None:
            return []

        # Reuse recent detections between sampled frames to reduce GPU/CPU load.
        if self.frame_index % max(1, WEAPON_INFER_EVERY_N) != 0 and now <= self.weapon_cache_expire:
            return list(self.weapon_cache)

        detections = []
        try:
            # OPTIMIZED: Improved inference parameters for small objects
            result = self.weapon_model.predict(
                frame,
                conf=WEAPON_CONF_THRES,
                iou=WEAPON_IOU_THRES,
                imgsz=WEAPON_IMG_SIZE,
                max_det=WEAPON_MAX_DET,
                verbose=False,
                augment=True,  # Enable augmentation to improve detection robustness
            )[0]

            names = getattr(result, "names", None)
            if isinstance(names, dict) and names:
                self.weapon_model_num_classes = len(names)
                if self.weapon_model_num_classes <= WEAPON_AUTO_ASSUME_MAX_CLASSES:
                    self.weapon_assume_all_classes = True
            elif isinstance(names, list) and names:
                self.weapon_model_num_classes = len(names)
                if self.weapon_model_num_classes <= WEAPON_AUTO_ASSUME_MAX_CLASSES:
                    self.weapon_assume_all_classes = True
            
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy() if result.boxes.conf is not None else np.ones(len(boxes), dtype=np.float32)
                clss = result.boxes.cls.cpu().numpy().astype(int) if result.boxes.cls is not None else np.zeros(len(boxes), dtype=int)

                filtered_count = 0

                for i in range(len(boxes)):
                    cls_id = int(clss[i])
                    if isinstance(names, dict):
                        cls_name = str(names.get(cls_id, cls_id))
                    elif isinstance(names, list) and 0 <= cls_id < len(names):
                        cls_name = str(names[cls_id])
                    else:
                        cls_name = str(cls_id)

                    if not self._is_weapon_label(cls_name):
                        continue
                    filtered_count += 1

                    x1, y1, x2, y2 = boxes[i].astype(int)
                    conf = float(confs[i])
                    if conf < WEAPON_CONF_THRES:
                        continue

                    detections.append(
                        {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                            "conf": conf,
                            "label": cls_name,
                        }
                    )

                # If the model looks like a compact custom weapon model, keep all classes.
                if (
                    filtered_count == 0
                    and self.weapon_model_num_classes
                    and self.weapon_model_num_classes <= WEAPON_AUTO_ASSUME_MAX_CLASSES
                ):
                    for i in range(len(boxes)):
                        x1, y1, x2, y2 = boxes[i].astype(int)
                        conf = float(confs[i])
                        if conf < WEAPON_CONF_THRES:
                            continue
                        cls_id = int(clss[i])
                        if isinstance(names, dict):
                            cls_name = str(names.get(cls_id, cls_id))
                        elif isinstance(names, list) and 0 <= cls_id < len(names):
                            cls_name = str(names[cls_id])
                        else:
                            cls_name = str(cls_id)
                        detections.append(
                            {
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2),
                                "conf": conf,
                                "label": cls_name,
                            }
                        )
        except Exception as ex:
            print(f"[WARN] Weapon inference failed: {ex}")
            detections = []

        self.weapon_cache = detections
        self.weapon_cache_expire = now + WEAPON_STICKY_SEC
        return detections

    def _associate_weapons_to_people(self, weapon_dets, people_data):
        if not weapon_dets or not people_data:
            return {}, set()

        owner_map = {}
        used_weapon_idx = set()

        for wi, wd in enumerate(weapon_dets):
            w_box = (wd["x1"], wd["y1"], wd["x2"], wd["y2"])
            w_center = np.array([(wd["x1"] + wd["x2"]) * 0.5, (wd["y1"] + wd["y2"]) * 0.5], dtype=np.float32)
            w_h = max(1.0, wd["y2"] - wd["y1"])
            w_w = max(1.0, wd["x2"] - wd["x1"])

            best_person = None
            best_score = -1.0
            best_person_data = None
            
            # Build list of nearby people for spatial context analysis
            nearby_boxes = [
                (p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0))
                for p in people_data
            ]
            
            for person in people_data:
                p_box = (person["x1"], person["y1"], person["x2"], person["y2"])
                p_h = max(1.0, float(person["y2"] - person["y1"]))
                p_w = max(1.0, float(person["x2"] - person["x1"]))
                p_iou = bbox_iou(w_box, p_box)
                p_center = np.array([(person["x1"] + person["x2"]) * 0.5, (person["y1"] + person["y2"]) * 0.5], dtype=np.float32)
                cdist = float(np.linalg.norm(w_center - p_center) / p_h)
                in_person_box = point_in_expanded_box(w_center, p_box, expand_px=p_h * 0.22)
                
                interaction = person.get("interaction", {})
                lw = interaction.get("left_wrist")
                rw = interaction.get("right_wrist")
                hand_min_dist = 99.0
                if lw is not None:
                    hand_min_dist = min(hand_min_dist, float(np.linalg.norm(w_center - np.array(lw, dtype=np.float32)) / p_h))
                if rw is not None:
                    hand_min_dist = min(hand_min_dist, float(np.linalg.norm(w_center - np.array(rw, dtype=np.float32)) / p_h))
                
                # CRITICAL: Hand must be very close to weapon (tightened from 0.38)
                hand_near = hand_min_dist <= WEAPON_HAND_DIST_MAX
                
                # CRITICAL: Require person to be in combat stance (guard pose or hold pose)
                is_in_combat_stance = bool(interaction.get("guard_pose", False)) or bool(interaction.get("hold_pose", False))
                
                # Skip if person not in combat stance AND hand not near weapon
                if not is_in_combat_stance and not hand_near:
                    continue

                # STRICT: Skip if weapon far from person AND not in person box
                if p_iou < WEAPON_PERSON_IOU_MIN and cdist > WEAPON_ASSOC_MAX_DIST and not in_person_box and not hand_near:
                    continue
                
                # ================================================================================
                # ADVANCED: SKELETON-BASED WEAPON VS POSTURE DISCRIMINATION
                # ================================================================================
                keypoints_dict = interaction.get("keypoints_dict", {})
                bone_structure = analyze_bone_structure(keypoints_dict)
                geometry = analyze_joint_geometry(keypoints_dict, p_h)
                spatial_context = analyze_spatial_context(p_box, nearby_boxes, p_h)
                
                # Determine if this person is actually holding weapon or just in a pose
                weapon_classification, skeleton_confidence = distinguish_weapon_vs_posture(
                    keypoints_dict,
                    bone_structure,
                    geometry,
                    spatial_context,
                    p_h,
                    weapon_detected=True
                )
                
                # If skeleton analysis says no weapon, heavily discount
                if weapon_classification == "NO_WEAPON":
                    continue  # Skip this person entirely
                
                # If skeleton says HOLDING_OBJECT (but not weapon), still skip
                if weapon_classification == "HOLDING_OBJECT" and skeleton_confidence > 0.55:
                    continue
                
                # Base score from spatial proximity
                score = (p_iou * 2.0) + max(0.0, 1.0 - cdist) * 1.0 + (0.30 if in_person_box else 0.0)
                
                # CRITICAL: Hand proximity is strongest indicator
                if hand_near:
                    score += WEAPON_HAND_SCORE_BONUS + max(0.0, WEAPON_HAND_DIST_MAX - hand_min_dist) * 2.0
                else:
                    # Without hand proximity, heavily discount
                    score *= 0.35
                
                # Apply skeleton confidence weighting
                score *= (0.5 + skeleton_confidence * 0.5)  # Min 0.5x, max 1.0x
                
                # Combat stance bonus (but not too high)
                if is_in_combat_stance:
                    score += 0.20
                
                # Weapon size heuristics
                weapon_aspect = w_w / (w_h + 1e-6)
                if weapon_aspect < 0.35:  # Thin object = likely knife
                    score += 0.15
                    if hand_near:
                        score += 0.10
                elif weapon_aspect > 0.60:  # Wide object = likely gun  
                    score += 0.10
                
                # Arm asymmetry boost from skeleton
                arm_asymmetry = geometry.get("arm_asymmetry", 0.0)
                if arm_asymmetry > 40.0:
                    score += 0.12  # Asymmetric arms suggest weapon
                
                # Person-weapon action context (reduced influence)
                action = person.get("action", "")
                if action in ("CHIẾN ĐẤU", "ĐẤM", "ĐÁ"):
                    score += 0.10
                
                if score > best_score:
                    best_score = score
                    best_person = person
                    best_person_data = {
                        "hand_dist": hand_min_dist,
                        "weapon_aspect": weapon_aspect,
                        "in_stance": is_in_combat_stance,
                        "skeleton_conf": skeleton_confidence,
                        "weapon_class": weapon_classification,
                    }

            # High skeleton confidence (>0.50) required to assign weapon
            if best_person is None or best_score < WEAPON_MIN_SCORE or (best_person_data and best_person_data.get("skeleton_conf", 0.0) < 0.50):
                continue

            track_id = int(best_person["track_id"])
            prev = owner_map.get(track_id)
            if prev is None or wd["conf"] > prev["conf"]:
                owner_map[track_id] = {
                    "weapon_idx": wi,
                    "conf": float(wd["conf"]),
                    "label": str(wd["label"]),
                }
            used_weapon_idx.add(wi)

        return owner_map, used_weapon_idx

    def _process_frame(self, frame):
        now = time.time()
        self.frame_index += 1
        display = frame.copy()
        infer_frame = preprocess_low_light(frame)

        results = self.model.track(
            infer_frame,
            persist=True,
            conf=CONF_THRES,
            iou=IOU_THRES,
            imgsz=IMG_SIZE,
            verbose=False,
            tracker="bytetrack.yaml",
            max_det=48,
        )[0]

        stale_ids = []
        for tid, st in self.track_states.items():
            if now - st.last_seen > TRACK_TTL_SEC:
                stale_ids.append(tid)
        for tid in stale_ids:
            del self.track_states[tid]

        draw_items = []
        person_count = 0
        detected_people = []

        if results.boxes is not None and len(results.boxes) > 0:
            boxes = results.boxes.xyxy.cpu().numpy()
            if results.boxes.cls is not None:
                clss = results.boxes.cls.cpu().numpy().astype(int)
            else:
                clss = np.zeros(len(boxes), dtype=int)
            ids = results.boxes.id.cpu().numpy().astype(int) if results.boxes.id is not None else None

            kps_xy = None
            kps_cf = None
            if results.keypoints is not None:
                kps_xy = results.keypoints.xy.cpu().numpy()
                if results.keypoints.conf is not None:
                    kps_cf = results.keypoints.conf.cpu().numpy()

            indices = list(range(len(boxes)))
            if DRAW_ONLY_PRIMARY:
                best_i = None
                best_area = -1
                for i, box in enumerate(boxes):
                    if clss[i] != 0:
                        continue
                    x1, y1, x2, y2 = box
                    area = max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))
                    if area > best_area:
                        best_area = area
                        best_i = i
                indices = [best_i] if best_i is not None else []

            for i in indices:
                if i is None:
                    continue
                if clss[i] != 0:
                    continue

                x1, y1, x2, y2 = boxes[i].astype(int)
                w = max(1, x2 - x1)
                h = max(1, y2 - y1)
                area = w * h
                if area < MIN_PERSON_AREA:
                    continue

                track_id = int(ids[i]) if ids is not None and i < len(ids) else i
                kp_xy = kps_xy[i] if kps_xy is not None and i < len(kps_xy) else None
                kp_cf = kps_cf[i] if kps_cf is not None and i < len(kps_cf) else None

                valid_all = count_valid_points(kp_xy, kp_cf, list(range(17)), min_conf=0.20)
                valid_upper = count_valid_points(kp_xy, kp_cf, [5, 6, 11, 12], min_conf=0.20)
                if valid_all < 6 or valid_upper < 3:
                    continue

                if track_id not in self.track_states:
                    self.track_states[track_id] = PersonState(first_seen=now, last_significant_motion=now)

                st = self.track_states[track_id]
                st.last_seen = now
                st.seen_frames += 1

                cls_result = self._classify_person(st, now, x1, y1, x2, y2, kp_xy, kp_cf)
                if cls_result is None:
                    continue

                action = cls_result["action"]
                color = cls_result["color"]
                danger = cls_result["danger"]
                save_frame = cls_result["save_frame"]
                interaction = cls_result.get("interaction", {})

                if danger and save_frame and SAVE_ALERT_FRAME:
                    path = save_snapshot(display, track_id, action)
                    print(f"[ALERT] ID={track_id} saved: {path}")

                detected_people.append(
                    {
                        "track_id": track_id,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "action": action,
                        "color": color,
                        "state": st,
                        "interaction": interaction,
                        "metrics": cls_result.get("metrics", {}),
                    }
                )

        # QUY TẮC HỆ THỐNG: LOẠI BỎ HOÀN TOÀN NHẬN DIỆN VŨ KHÍ
        weapon_dets = []
        weapon_owner_map = {}

        bullying_map = self._detect_bullying_interactions(detected_people, now)
        combat_map = self._detect_combat_interactions(detected_people, now, weapon_owner_map)
        combat_actions = {"CHIẾN ĐẤU", "DI CHUYỂN CHIẾN ĐẤU", "ĐẤM", "ĐÁ"}
        
        # QUY TẮC HỆ THỐNG: Kiểm soát số lượng người
        # Nếu > 5 người: CHỈ vẽ những người có hành vi bất thường (TÉ, CHIẾN ĐẤU, BẮT NẠT, BÁO ĐỘNG)
        # Nếu ≤ 5 người: Vẽ tất cả với đầy đủ lọc tư thế
        total_people = len(detected_people)
        draw_all_people = total_people <= 5
        
        # Danh sách hành vi "bất thường" (cần hiển thị khi đông người)
        # LƯU Ý: KHÔNG bao gồm VŨ KHÍ (đã bị loại bỏ)
        abnormal_behaviors = {"TÉ", "CHIẾN ĐẤU", "BẮT NẠT", "BÁO ĐỘNG", "DI CHUYỂN CHIẾN ĐẤU", "ĐẤM", "ĐÁ", "DẤU HIỆU BẮT NẠT"}
        
        # QUY TẮC HỆ THỐNG: Xác định hành vi cuối cùng (ưu tiên: TÉ > CHIẾN ĐẤU > BẮT NẠT)
        # Quy tắc: TÉ luôn được phép | CHIẾN ĐẤU và BẮT NẠT chỉ khi KHÔNG ngồi
        person_final_actions = {}
        for item in detected_people:
            track_id = item["track_id"]
            action = item["action"]
            interaction = item.get("interaction", {})
            is_sitting = bool(interaction.get("is_sitting", False))
            
            # Ưu tiên 1: BÁO ĐỘNG (Fall detection)
            if action == "BÁO ĐỘNG":
                final_action = "BÁO ĐỘNG"
            # Ưu tiên 2: TÉ (luôn được phép, kể cả đang ngồi)
            elif action == "TÉ":
                final_action = "TÉ"
            # Ưu tiên 3: CHIẾN ĐẤU (chỉ khi KHÔNG ngồi)
            elif track_id in combat_map and action not in ("BÁO ĐỘNG", "TÉ") and not is_sitting:
                final_action = "CHIẾN ĐẤU"
            # Ưu tiên 4: BẮT NẠT (chỉ khi KHÔNG ngồi)
            elif track_id in bullying_map and action != "BÁO ĐỘNG" and not is_sitting:
                final_action = bullying_map[track_id].get("label", "BẮT NẠT")
            elif action in combat_actions and not is_sitting:
                final_action = "CHIẾN ĐẤU"
            else:
                final_action = "BÌNH THƯỜNG"
            
            person_final_actions[track_id] = final_action
        
        # Vẽ bounding box và label dựa trên số lượng người
        for item in detected_people:
            track_id = item["track_id"]
            action = item["action"]
            color = item["color"]
            label_suffix = ""
            final_action = person_final_actions[track_id]
            
            # QUY TẮC: Nếu đông người (>5) và hành vi bình thường, BỎ QUA không vẽ
            if not draw_all_people and final_action == "BÌNH THƯỜNG":
                continue
            
            # Lấy confidence score
            metrics = item.get("metrics", {})
            decision_confidence = float(metrics.get("decision_confidence", 0.0))
            confidence_str = f" ({decision_confidence:.2f})" if decision_confidence > 0 else ""
            
            # QUY TẮC HỆ THỐNG: Xác định hành động và màu sắc (KHÔNG VŨ KHÍ)
            is_sitting = bool(item.get("interaction", {}).get("is_sitting", False))
            
            if action == "BÁO ĐỘNG":
                color = (0, 0, 255)
            elif action == "TÉ":
                color = (0, 255, 255)
            # Chỉ cho phép CHIẾN ĐẤU nếu KHÔNG ngồi
            elif track_id in combat_map and action not in ("BÁO ĐỘNG", "TÉ") and not is_sitting:
                target_id = combat_map[track_id].get("target_id")
                action = "CHIẾN ĐẤU"
                if target_id is not None:
                    label_suffix = f" -> ID {target_id}"
                color = (0, 0, 255)
            # Chỉ cho phép BẮT NẠT nếu KHÔNG ngồi
            elif track_id in bullying_map and action != "BÁO ĐỘNG" and not is_sitting:
                target_id = bullying_map[track_id].get("target_id")
                action = bullying_map[track_id].get("label", "BẮT NẠT")
                if target_id is not None:
                    label_suffix = f" -> ID {target_id}"
                color = (0, 255, 255) if action == "DẤU HIỆU BẮT NẠT" else (0, 0, 255)
            elif action in combat_actions and not is_sitting:
                action = "CHIẾN ĐẤU"
                color = (0, 0, 255)
            else:
                action = "BÌNH THƯỜNG"
                color = (0, 255, 0)

            draw_box(display, item["x1"], item["y1"], item["x2"], item["y2"], color, thickness=3)
            draw_items.append(
                {
                    "text": f"ID {track_id} | {action}{label_suffix}{confidence_str}",
                    "x": item["x1"],
                    "y": max(25, item["y1"] - 28),
                    "color": color,
                    "size": 24,
                    "bg": SHOW_ID_BG,
                }
            )
            person_count += 1

        # QUY TẮC HỆ THỐNG: Vũ khí đã bị loại bỏ hoàn toàn - không vẽ

        if person_count == 0:
            draw_items.append(
                {
                    "text": "KHÔNG CÓ NGƯỜI",
                    "x": 18,
                    "y": 18,
                    "color": (255, 255, 255),
                    "size": 22,
                    "bg": False,
                }
            )

        display = draw_unicode_texts(display, draw_items)
        return display

    def _refresh_preview(self):
        try:
            with self.frame_lock:
                frame = None if self.latest_frame is None else self.latest_frame.copy()

            if frame is not None:
                h, w = frame.shape[:2]
                scale = min(DISPLAY_MAX_WIDTH / max(1, w), DISPLAY_MAX_HEIGHT / max(1, h), 1.0)
                new_w = int(w * scale)
                new_h = int(h * scale)
                if new_w != w or new_h != h:
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.preview_label.configure(image=imgtk)
                self.preview_label.image = imgtk
                self.status_value.set("Đang chạy...")
        finally:
            self.after(15, self._refresh_preview)


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app = FallAlarmApp()
    app.mainloop()
 