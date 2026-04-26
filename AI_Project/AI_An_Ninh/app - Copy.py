from __future__ import annotations

import os
import sys
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
    import torch
except Exception:
    torch = None

try:
    import winsound

    HAVE_WINSOUND = True
except Exception:
    HAVE_WINSOUND = False


# =========================================================
# CONFIG
# =========================================================
USE_CUDA = bool(torch is not None and torch.cuda.is_available())
if USE_CUDA and torch is not None:
    try:
        torch.backends.cudnn.benchmark = True
    except Exception:
        pass
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass

POSE_MODEL_CANDIDATES_GPU = (
    "yolo26s-pose.pt",
    "yolo11s-pose.pt",
    "yolov8s-pose.pt",
    "yolo26n-pose.pt",
    "yolo11n-pose.pt",
    "yolov8n-pose.pt",
)
POSE_MODEL_CANDIDATES_CPU = (
    "yolo26n-pose.pt",
    "yolo11n-pose.pt",
    "yolov8n-pose.pt",
    "yolo26s-pose.pt",
    "yolo11s-pose.pt",
    "yolov8s-pose.pt",
)

MODEL_PATH = "yolov8s-pose.pt" if USE_CUDA else "yolov8n-pose.pt"
CONF_THRES = 0.23 if USE_CUDA else 0.20
IOU_THRES = 0.45
IMG_SIZE = 960 if USE_CUDA else 832
POSE_MIN_IMG_SIZE = 768 if USE_CUDA else 576
POSE_MAX_DET = 120 if USE_CUDA else 96
POSE_TRACKER = "bytetrack.yaml"
POSE_DEVICE = 0 if USE_CUDA else "cpu"

# Startup: when launching app.py, prompt for a video file and auto-start.
AUTO_PROMPT_VIDEO_ON_START = True

# Fire/Smoke detection (keep original logic from app_tham_hoa.py).
ENABLE_FIRE_SMOKE_DETECTION = True
FS_MODEL_PATH = "best_nano_111.pt"
FS_MODEL_CANDIDATES = (
    FS_MODEL_PATH,
    "fire_smoke.pt",
)
FS_INFER_SIZE = 768 if USE_CUDA else 704
FS_MIN_IMG_SIZE = 640
FS_CANDIDATE_CONF = 0.30
FS_STRONG_CANDIDATE_CONF = 0.40

# HARD FILTERS
FS_HARD_MOTION_MIN = 0.010

# FIRE
FS_FIRE_COLOR_MIN = 0.30
FS_FIRE_MIN_AREA_RATIO = 0.0018
FS_SMALL_FIRE_MIN_AREA = 0.00018
FS_FIRE_FLICKER_MIN = 0.16
FS_FIRE_INTENSITY_RANGE_MIN = 0.11
FS_FIRE_MIN_STREAK = 3
FS_FIRE_MIN_MOTION = 0.007
FS_FIRE_MIN_MOTION_VAR = 0.00012
FS_FIRE_SCORE_CONFIRM = 96.0
FS_FIRE_SCORE_RELEASE = 82.0
FS_FIRE_RELEASE_PATIENCE = 10
FS_FIRE_INSTANT_CONF = 0.44
FS_FIRE_INSTANT_SCORE = 78.0
FS_FIRE_INSTANT_STREAK = 2
FS_FIRE_INSTANT_RELAXED_CONF = 0.36
FS_FIRE_INSTANT_RELAXED_SCORE = 120.0
FS_FIRE_ULTRA_FAST_CONF = 0.33
FS_FIRE_ULTRA_FAST_SCORE = 126.0
FS_FIRE_PRIORITY_FAST_CONF = 0.31
FS_FIRE_PRIORITY_FAST_SCORE = 120.0
FS_FIRE_SHORT_HISTORY_CONF = 0.33
FS_FIRE_SHORT_HISTORY_SCORE = 128.0
FS_FIRE_RESUME_CONF = 0.32
FS_FIRE_RESUME_SCORE = 118.0
FS_FIRE_RESUME_TTL = 36
FS_FIRE_RESUME_DIST = 0.20

# SMOKE
FS_SMOKE_COLOR_MIN = 0.18
FS_SMOKE_TEXTURE_MIN = 0.055
FS_SMOKE_BLUR_MIN = 0.055
FS_SMOKE_MIN_AREA_RATIO = 0.0010
FS_SMOKE_MIN_STREAK = 3
FS_SMOKE_MIN_MOTION = 0.0032
FS_SMOKE_MIN_MOTION_VAR = 0.00004
FS_SMOKE_MIN_DRIFT = 0.0032
FS_SMOKE_SCORE_CONFIRM = 82.0
FS_SMOKE_SCORE_RELEASE = 68.0
FS_SMOKE_RELEASE_PATIENCE = 9
FS_SMOKE_INSTANT_CONF = 0.40
FS_SMOKE_INSTANT_SCORE = 92.0
FS_SMOKE_INSTANT_AREA_RATIO = 0.020
FS_SMOKE_ULTRA_FAST_CONF = 0.30
FS_SMOKE_ULTRA_FAST_SCORE = 85.0
FS_SMOKE_THIN_FAST_CONF = 0.28
FS_SMOKE_THIN_FAST_SCORE = 78.0

# TRACK CONFIRMATION / HYSTERESIS
FS_IOU_MATCH = 0.40
FS_TRACK_MAX_MISSES = 10
FS_ALERT_COOLDOWN = 48

# Sticker/decoration heuristics
FS_STICKER_HUE_STD_MAX = 0.05
FS_STICKER_SAT_STD_MAX = 0.05
FS_STICKER_VAL_STD_MAX = 0.08
FS_STICKER_TEXTURE_MAX = 0.18
FS_STICKER_FILL_RATIO_MIN = 0.55
FS_STICKER_CONTOUR_FILL_MIN = 0.55
FS_STICKER_EDGE_MIN = 0.58
FS_STICKER_CONF_MAX = 0.65

# SHAPE STABILITY & REFLECTION FILTERING
FS_SHAPE_STABILITY_THRESHOLD = 0.08
FS_EDGE_SHARPNESS_THRESHOLD = 0.60
FS_ASPECT_RATIO_CHANGE_MIN = 0.006
FS_ASPECT_RATIO_CHANGE_MAX = 0.12
FS_CENTROID_CONSISTENCY_MIN = 0.04
FS_SHAPE_HISTORY_LEN = 6
FS_NO_DEFORMATION_REJECT_STREAK = 3
FS_SHAPE_DEFORMATION_MIN = 0.002
FS_MATCH_SCORE_MIN = 0.46
FS_MATCH_CENTER_DIST = 0.085
FS_MATCH_AREA_RATIO_MIN = 0.22
FS_SCENE_CUT_DIFF = 0.22
FS_SCENE_CUT_CORR = 0.72

# Snapshot throttling for fire/smoke alerts.
FS_SNAPSHOT_COOLDOWN_SEC = 6.0

# Fall detection: require a horizontal bbox to start fall detection.
FALL_HORIZONTAL_ASPECT_MIN = 1.15
FALL_EDGE_MARGIN_X = 0.055
FALL_EDGE_MARGIN_Y = 0.045
FALL_EDGE_GRACE_FRAMES = 8
FALL_PARTIAL_SUPPRESS_SEC = 0.45
FALL_ENTRY_HORIZONTAL_RATIO = 1.35
FALL_FLOOR_MIN_POINTS = 5
FALL_FLOOR_X_SPAN_MIN = 0.55
FALL_FLOOR_Y_SPAN_MAX = 0.48
FALL_FLOOR_LOWEST_MIN = 0.70
FALL_HEAD_LOW_MIN = 0.66
FALL_HIP_LOW_MIN = 0.76
FALL_BODY_STACK_MAX = 0.22
FALL_ASPECT_TREND_MIN = 0.020
FALL_ENTRY_GROWTH_MIN = 1.08
FALL_RELAXED_SHOULDER_LOW_MIN = 0.60
FALL_RELAXED_HIP_LOW_MIN = 0.72
FALL_RELAXED_STACK_MAX = 0.30
FALL_MEMORY_SEC = 1.35
FALL_MEMORY_IOU_MIN = 0.16
FALL_MEMORY_CENTER_DIST = 0.52
FALL_MEMORY_BOTTOM_GAP = 0.24
FALL_MEMORY_SCORE_MIN = 0.42
FALL_MEMORY_MAXLEN = 18

# mÃ´ hÃ¬nh nháº­n diá»‡n vÅ© khÃ­ (custom YOLO) - OPTIMIZED for real-world lighting & small objects
# lá»c ngÆ°á»i / track
MIN_PERSON_AREA = 420
SMALL_PERSON_AREA = 1800
MEDIUM_PERSON_AREA = 5200
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

# cáº£nh bÃ¡o náº¿u sau tÃ© khÃ´ng cÃ³ chuyá»ƒn Ä‘á»™ng rÃµ trong X giÃ¢y
ALERT_AFTER_LIE_SEC = 30.0

# history smoothing
ANGLE_HISTORY = 5
SPEED_HISTORY = 5
HEIGHT_HISTORY = 5
ANKLE_HISTORY = 5
GAIT_HISTORY = 14
POSE_REL_HISTORY = 10

# temporal decision smoothing (giáº£m giáº­t nhÃ£n)
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
BULLY_HISTORY = 8
BULLY_INTERACT_RANGE = 0.94
BULLY_HEAD_GRAB_DIST = 0.19
BULLY_POINT_FACE_DIST = 0.24
BULLY_POINT_ALIGN_MIN = 0.66
BULLY_POINT_ELBOW_MIN = 152.0
BULLY_MIN_STRENGTH = 0.068
BULLY_CONTACT_STRENGTH_MIN = 0.045
BULLY_PERSIST_MIN = 0.50
BULLY_RELEASE_PERSIST_MIN = 0.36
BULLY_STICKY_SEC = 1.20
BULLY_ROLE_MARGIN = 0.035
BULLY_MIN_HEIGHT_RATIO = 0.62
BULLY_MAX_BOTTOM_GAP = 0.22
BULLY_MAX_CENTER_X_GAP = 0.74
BULLY_MIN_ARM_REACH = 0.16
BULLY_MIN_X_OVERLAP = 0.24
BULLY_MIN_Y_OVERLAP = 0.34
BULLY_NEAREST_CANDIDATES = 3
BULLY_MIN_SEEN_FRAMES = 4
BULLY_SENSITIVE_DIST = 0.16
BULLY_STANDING_ONLY = True
BULLY_POINT_WARN_MIN_STRENGTH = 0.044
BULLY_POINT_PERSIST_MIN = 0.54
BULLY_TARGET_STABLE_RATIO = 0.38
BULLY_FAST_WINDOW = 2
BULLY_FAST_RECENT_MIN = 0.74
BULLY_FAST_PEAK_MIN = 0.86
BULLY_FAST_TARGET_STABLE_RATIO = 0.80
BULLY_WARN_FAST_RECENT_MIN = 0.76
BULLY_WARN_FAST_PEAK_MIN = 0.84
BULLY_WARN_FAST_TARGET_STABLE_RATIO = 0.78
BULLY_CLOSE_CENTER_DIST = 0.62
BULLY_PULL_CONTACT_DIST = 0.22
BULLY_PULL_ELBOW_MAX = 148.0
BULLY_PUSH_AWAY_MIN = 0.005
BULLY_PULL_TOWARD_MIN = 0.004

# Push/shove (count as bullying)
PUSH_CONTACT_DIST = 0.26
PUSH_WRIST_SPEED_MIN = 0.033
PUSH_RECOIL_MIN = 0.008

# pairwise combat cues for crowded scenes
COMBAT_HISTORY = 8
COMBAT_INTERACT_RANGE = 0.78
COMBAT_MIN_HEIGHT_RATIO = 0.58
COMBAT_MAX_BOTTOM_GAP = 0.22
COMBAT_MIN_X_OVERLAP = 0.20
COMBAT_CONTACT_DIST = 0.19
COMBAT_TARGET_RECOIL_MIN = 0.016
COMBAT_MIN_STRENGTH = 0.090
COMBAT_PERSIST_MIN = 0.48
COMBAT_RELEASE_PERSIST_MIN = 0.34
COMBAT_FAST_WINDOW = 2
COMBAT_FAST_RECENT_MIN = 0.76
COMBAT_FAST_PEAK_MIN = 0.90
COMBAT_FAST_TARGET_STABLE_RATIO = 0.80
COMBAT_STICKY_SEC = 1.10

ACTIONS = (
    "Äá»¨NG",
    "ÄI Bá»˜",
    "CHáº Y",
    "NGá»’I",
    "TÃ‰",
    "CHIáº¾N Äáº¤U",
    "DI CHUYá»‚N CHIáº¾N Äáº¤U",
    "Äáº¤M",
    "ÄÃ",
    "Ã”M Váº¬T",
)

(
    ACTION_STAND,
    ACTION_WALK,
    ACTION_RUN,
    ACTION_SIT,
    ACTION_FALL,
    ACTION_FIGHT,
    ACTION_MOVE_FIGHT,
    ACTION_PUNCH,
    ACTION_KICK,
    ACTION_HOLD,
) = ACTIONS

SAVE_ALERT_FRAME = True
ALERT_DIR = "alerts"

SHOW_ID_BG = True
ENABLE_FRAME_ENHANCEMENT = True
DISPLAY_MAX_WIDTH = 1180
DISPLAY_MAX_HEIGHT = 720

# náº¿u muá»‘n chá»‰ hiá»ƒn thá»‹ ngÆ°á»i lá»›n nháº¥t thÃ¬ Ä‘á»•i True
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


@lru_cache(maxsize=1024)
def normalize_ui_text(text):
    if text is None:
        return ""

    repaired = "".join(ch for ch in str(text) if ch >= " " or ch in "\n\r\t")
    if not repaired:
        return repaired

    mojibake_markers = ("Ã", "Â", "Ä", "Å", "Æ", "áº", "á»", "â€")
    for _ in range(3):
        if not any(marker in repaired for marker in mojibake_markers):
            break
        for source_encoding in ("cp1252", "latin1"):
            try:
                candidate = repaired.encode(source_encoding).decode("utf-8")
            except Exception:
                continue
            if candidate != repaired:
                repaired = candidate
                break
        else:
            break

    return repaired


def bgr_to_rgb(color):
    b, g, r = color
    return (r, g, b)


@lru_cache(maxsize=32)
def action_key(label: str):
    normalized = normalize_ui_text(label).strip()
    for action_name in ACTIONS:
        if normalize_ui_text(action_name).strip() == normalized:
            return action_name
    return label


def adjust_action_score(score_map: dict, label: str, delta: float):
    key = action_key(label)
    if key in score_map:
        score_map[key] = float(score_map.get(key, 0.0)) + float(delta)
        return key

    normalized = normalize_ui_text(label).strip()
    for action_name in list(score_map.keys()):
        if normalize_ui_text(action_name).strip() == normalized:
            score_map[action_name] = float(score_map.get(action_name, 0.0)) + float(delta)
            return action_name

    score_map[key] = float(score_map.get(key, 0.0)) + float(delta)
    return key


def pick_first_existing(candidates):
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def adaptive_infer_size(frame_or_shape, max_size: int, min_size: int = 576, stride: int = 32):
    if hasattr(frame_or_shape, "shape"):
        h, w = frame_or_shape.shape[:2]
    else:
        h, w = frame_or_shape[:2]

    base = int(max(h, w))
    desired = max(int(min_size), min(int(max_size), base))
    desired = max(int(stride), int(np.ceil(desired / float(stride))) * int(stride))
    return int(min(int(max_size), desired))


@lru_cache(maxsize=24)
def gamma_lut(gamma_value: float):
    gamma_value = max(0.10, float(gamma_value))
    inv_gamma = 1.0 / gamma_value
    return np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)], dtype=np.uint8)


@lru_cache(maxsize=16)
def clahe_filter(clip_limit: float, tile_x: int, tile_y: int):
    return cv2.createCLAHE(
        clipLimit=float(clip_limit),
        tileGridSize=(int(tile_x), int(tile_y)),
    )


def person_pose_profile(box_w: int, box_h: int):
    area = max(1, int(box_w)) * max(1, int(box_h))
    if area <= SMALL_PERSON_AREA or box_h <= 120:
        return {
            "kp_min_conf": 0.08,
            "min_valid_all": 3,
            "min_valid_upper": 1,
            "fallback_box_conf": 0.28,
        }
    if area <= MEDIUM_PERSON_AREA or box_h <= 185:
        return {
            "kp_min_conf": 0.11,
            "min_valid_all": 4,
            "min_valid_upper": 2,
            "fallback_box_conf": 0.26,
        }
    return {
        "kp_min_conf": 0.15,
        "min_valid_all": 5,
        "min_valid_upper": 2,
        "fallback_box_conf": 0.24,
    }


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
    edge_guard_until: float = 0.0
    last_full_body_time: float = 0.0

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
    center_hist: deque = field(default_factory=lambda: deque(maxlen=6))
    bbox_hist: deque = field(default_factory=lambda: deque(maxlen=6))
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

    Optional:
    - align: "left" (default) or "right"
    - margin: int (used for right alignment, default 18)
    """
    if not texts:
        return frame

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil_img)
    frame_w = int(pil_img.size[0])

    for item in texts:
        text = normalize_ui_text(item.get("text", ""))
        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        color = bgr_to_rgb(item.get("color", (255, 255, 255)))
        size = int(item.get("size", 24))
        bg = bool(item.get("bg", False))
        padding = int(item.get("padding", 4))
        align = str(item.get("align", "left")).strip().lower()
        margin = int(item.get("margin", 18))

        font = get_font(size)
        try:
            # Right alignment: compute text width first then shift x.
            if align == "right":
                bbox0 = draw.textbbox((0, y), text, font=font)
                text_w = int(bbox0[2] - bbox0[0])
                x = max(0, frame_w - margin - text_w)

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

    boosted = cv2.LUT(frame, gamma_lut(gamma))

    # Convert to LAB for better luminance processing
    lab = cv2.cvtColor(boosted, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    l2 = clahe_filter(clahe_clip, clahe_tile[0], clahe_tile[1]).apply(l)
    
    # Boost contrast further in very dark conditions
    if v_mean < 50:
        alpha = np.clip((100 - v_mean) / 60.0, 1.0, 1.8)
        l2 = cv2.convertScaleAbs((l2.astype(np.float32) - 128.0) * alpha + 128.0)
    
    merged = cv2.merge((l2, a, b))
    out = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # Noise reduction for very dark frames
    if v_mean < 55:
        out = cv2.bilateralFilter(out, 5, 40, 40)

    return out


def save_snapshot(frame, track_id, label):
    os.makedirs(ALERT_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_label = normalize_ui_text(label).strip().replace(" ", "_").replace("/", "-")
    safe_label = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in safe_label)
    safe_label = safe_label.strip("_") or "ALERT"
    path = os.path.join(ALERT_DIR, f"{ts}_id{track_id}_{safe_label}.jpg")
    cv2.imwrite(path, frame)
    return path


# === FIRE_SMOKE_ORIGINAL_BEGIN ===
# =========================================================
# FIRE/SMOKE ORIGINAL ENGINE (copied from app_tham_hoa.py)
# =========================================================

def _build_fire_smoke_engine_class():
    # Bind original constants (names kept for original logic).
    MODEL_PATH = FS_MODEL_PATH
    INFER_SIZE = FS_INFER_SIZE
    CANDIDATE_CONF = FS_CANDIDATE_CONF
    STRONG_CANDIDATE_CONF = FS_STRONG_CANDIDATE_CONF
    HARD_MOTION_MIN = FS_HARD_MOTION_MIN
    FIRE_COLOR_MIN = FS_FIRE_COLOR_MIN
    SMOKE_COLOR_MIN = FS_SMOKE_COLOR_MIN
    SMOKE_TEXTURE_MIN = FS_SMOKE_TEXTURE_MIN
    SMOKE_BLUR_MIN = FS_SMOKE_BLUR_MIN
    FIRE_MIN_AREA_RATIO = FS_FIRE_MIN_AREA_RATIO
    SMALL_FIRE_MIN_AREA = FS_SMALL_FIRE_MIN_AREA
    FIRE_FLICKER_MIN = FS_FIRE_FLICKER_MIN
    FIRE_INTENSITY_RANGE_MIN = FS_FIRE_INTENSITY_RANGE_MIN
    SMOKE_MIN_AREA_RATIO = FS_SMOKE_MIN_AREA_RATIO
    IOU_MATCH = FS_IOU_MATCH
    TRACK_MAX_MISSES = FS_TRACK_MAX_MISSES
    ALERT_COOLDOWN = FS_ALERT_COOLDOWN
    FIRE_MIN_STREAK = FS_FIRE_MIN_STREAK
    SMOKE_MIN_STREAK = FS_SMOKE_MIN_STREAK
    FIRE_MIN_MOTION = FS_FIRE_MIN_MOTION
    SMOKE_MIN_MOTION = FS_SMOKE_MIN_MOTION
    FIRE_MIN_MOTION_VAR = FS_FIRE_MIN_MOTION_VAR
    SMOKE_MIN_MOTION_VAR = FS_SMOKE_MIN_MOTION_VAR
    SMOKE_MIN_DRIFT = FS_SMOKE_MIN_DRIFT
    FIRE_SCORE_CONFIRM = FS_FIRE_SCORE_CONFIRM
    SMOKE_SCORE_CONFIRM = FS_SMOKE_SCORE_CONFIRM
    FIRE_SCORE_RELEASE = FS_FIRE_SCORE_RELEASE
    SMOKE_SCORE_RELEASE = FS_SMOKE_SCORE_RELEASE
    FIRE_RELEASE_PATIENCE = FS_FIRE_RELEASE_PATIENCE
    SMOKE_RELEASE_PATIENCE = FS_SMOKE_RELEASE_PATIENCE
    FIRE_INSTANT_CONF = FS_FIRE_INSTANT_CONF
    FIRE_INSTANT_SCORE = FS_FIRE_INSTANT_SCORE
    FIRE_INSTANT_STREAK = FS_FIRE_INSTANT_STREAK
    FIRE_INSTANT_RELAXED_CONF = FS_FIRE_INSTANT_RELAXED_CONF
    FIRE_INSTANT_RELAXED_SCORE = FS_FIRE_INSTANT_RELAXED_SCORE
    FIRE_ULTRA_FAST_CONF = FS_FIRE_ULTRA_FAST_CONF
    FIRE_ULTRA_FAST_SCORE = FS_FIRE_ULTRA_FAST_SCORE
    FIRE_PRIORITY_FAST_CONF = FS_FIRE_PRIORITY_FAST_CONF
    FIRE_PRIORITY_FAST_SCORE = FS_FIRE_PRIORITY_FAST_SCORE
    FIRE_SHORT_HISTORY_CONF = FS_FIRE_SHORT_HISTORY_CONF
    FIRE_SHORT_HISTORY_SCORE = FS_FIRE_SHORT_HISTORY_SCORE
    FIRE_RESUME_CONF = FS_FIRE_RESUME_CONF
    FIRE_RESUME_SCORE = FS_FIRE_RESUME_SCORE
    FIRE_RESUME_TTL = FS_FIRE_RESUME_TTL
    FIRE_RESUME_DIST = FS_FIRE_RESUME_DIST
    SMOKE_INSTANT_CONF = FS_SMOKE_INSTANT_CONF
    SMOKE_INSTANT_SCORE = FS_SMOKE_INSTANT_SCORE
    SMOKE_INSTANT_AREA_RATIO = FS_SMOKE_INSTANT_AREA_RATIO
    SMOKE_ULTRA_FAST_CONF = FS_SMOKE_ULTRA_FAST_CONF
    SMOKE_ULTRA_FAST_SCORE = FS_SMOKE_ULTRA_FAST_SCORE
    SMOKE_THIN_FAST_CONF = FS_SMOKE_THIN_FAST_CONF
    SMOKE_THIN_FAST_SCORE = FS_SMOKE_THIN_FAST_SCORE
    STICKER_HUE_STD_MAX = FS_STICKER_HUE_STD_MAX
    STICKER_SAT_STD_MAX = FS_STICKER_SAT_STD_MAX
    STICKER_VAL_STD_MAX = FS_STICKER_VAL_STD_MAX
    STICKER_TEXTURE_MAX = FS_STICKER_TEXTURE_MAX
    STICKER_FILL_RATIO_MIN = FS_STICKER_FILL_RATIO_MIN
    STICKER_CONTOUR_FILL_MIN = FS_STICKER_CONTOUR_FILL_MIN
    STICKER_EDGE_MIN = FS_STICKER_EDGE_MIN
    STICKER_CONF_MAX = FS_STICKER_CONF_MAX
    SHAPE_STABILITY_THRESHOLD = FS_SHAPE_STABILITY_THRESHOLD
    EDGE_SHARPNESS_THRESHOLD = FS_EDGE_SHARPNESS_THRESHOLD
    ASPECT_RATIO_CHANGE_MIN = FS_ASPECT_RATIO_CHANGE_MIN
    ASPECT_RATIO_CHANGE_MAX = FS_ASPECT_RATIO_CHANGE_MAX
    CENTROID_CONSISTENCY_MIN = FS_CENTROID_CONSISTENCY_MIN
    SHAPE_HISTORY_LEN = FS_SHAPE_HISTORY_LEN
    NO_DEFORMATION_REJECT_STREAK = FS_NO_DEFORMATION_REJECT_STREAK
    SHAPE_DEFORMATION_MIN = FS_SHAPE_DEFORMATION_MIN
    MATCH_SCORE_MIN = FS_MATCH_SCORE_MIN
    MATCH_CENTER_DIST = FS_MATCH_CENTER_DIST
    MATCH_AREA_RATIO_MIN = FS_MATCH_AREA_RATIO_MIN
    SCENE_CUT_DIFF = FS_SCENE_CUT_DIFF
    SCENE_CUT_CORR = FS_SCENE_CUT_CORR

    # Original utilities + tracking (verbatim).
    def roi_flicker_score(intensity_hist):
        """
        Äo Ä‘á»™ dao Ä‘á»™ng Ã¡nh sÃ¡ng theo thá»i gian
        """
        if len(intensity_hist) < 4:
            return 0.0
    
        arr = np.array(intensity_hist)
        mean = np.mean(arr)
        std = np.std(arr)
    
        # loáº¡i vÃ¹ng quÃ¡ tá»‘i (noise)
        if mean < 0.08:
            return 0.0
    
        # loáº¡i dao Ä‘á»™ng quÃ¡ nhá» (LED á»•n Ä‘á»‹nh)
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
    
        # motion rÃµ = vá»«a cÃ³ cÆ°á»ng Ä‘á»™ thay Ä‘á»•i vá»«a cÃ³ vÃ¹ng thay Ä‘á»•i
        return float(0.6 * mean_diff + 0.4 * active_ratio)
    
    def roi_texture_score(roi_gray):
        """
        Texture cao = nhiá»u cáº¡nh/chi tiáº¿t.
        KhÃ³i thÆ°á»ng má»m/loang, tÆ°á»ng pháº³ng thÆ°á»ng tháº¥p nhÆ°ng thiáº¿u motion.
        """
        if roi_gray is None or roi_gray.size == 0:
            return 0.0
        std = float(np.std(roi_gray) / 255.0)
        return float(clamp(std * 2.5, 0.0, 1.0))
    
    def roi_blur_score(roi_gray):
        """
        Äiá»ƒm má»: cÃ ng cao cÃ ng blur / soft.
        Smoke thÆ°á»ng lÃ m vÃ¹ng áº£nh má»m, nhÆ°ng khÃ´ng dÃ¹ng má»™t mÃ¬nh.
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
        Lá»­a: mÃ u nÃ³ng, Ä‘á»/cam, bÃ£o hÃ²a cao, sÃ¡ng hÆ¡n ná»n.
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
        KhÃ³i: thÆ°á»ng lÃ  xÃ¡m/tráº¯ng/xanh xÃ¡m, Ä‘á»™ bÃ£o hÃ²a tháº¥p.
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
        Resize áº£nh Ä‘á»ƒ náº±m gá»n trong khung max_w x max_h, giá»¯ Ä‘Ãºng tá»‰ lá»‡.
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
                    conf * 112.0 +
                    motion * 290.0 +
                    color_score * 82.0 +
                    texture_score * 15.0 +
                    blur_score * 10.0
                )
            elif self.cls_name == "smoke":
                return (
                    conf * 98.0 +
                    motion * 210.0 +
                    texture_score * 62.0 +
                    blur_score * 78.0 +
                    color_score * 22.0
                )
            return conf * 100.0 + motion * 200.0 + texture_score * 30.0

        def should_instant_confirm(self):
            color = self.color_avg()
            motion = self.motion_avg()
            shape_score = self.shape_stability_score()
            edge_score = self.boundary_consistency_score()
            if self.cls_name == "fire":
                flicker = roi_flicker_score(self.intensity_hist)
                blur = self.blur_avg()
                tex = self.texture_avg()
                dynamic_ready = (
                    flicker >= FIRE_FLICKER_MIN * 0.70 or
                    motion >= FIRE_MIN_MOTION * 0.80 or
                    shape_score >= SHAPE_DEFORMATION_MIN * 2.4
                )
                rigid_object = (
                    self.streak >= FIRE_INSTANT_STREAK and
                    shape_score < SHAPE_DEFORMATION_MIN and
                    edge_score > EDGE_SHARPNESS_THRESHOLD
                )
                relaxed_small_fire = (
                    self.streak >= FIRE_INSTANT_STREAK and
                    self.conf >= FIRE_INSTANT_RELAXED_CONF and
                    self.score >= FIRE_INSTANT_RELAXED_SCORE and
                    self.area_ratio >= max(SMALL_FIRE_MIN_AREA * 4.0, FIRE_MIN_AREA_RATIO * 0.60) and
                    color >= FIRE_COLOR_MIN * 1.25 and
                    motion >= FIRE_MIN_MOTION * 3.5 and
                    self.texture_avg() >= 0.10 and
                    edge_score <= EDGE_SHARPNESS_THRESHOLD * 0.92
                )
                priority_small_fire = (
                    self.streak >= 1 and
                    self.conf >= FIRE_PRIORITY_FAST_CONF and
                    self.score >= FIRE_PRIORITY_FAST_SCORE and
                    self.area_ratio >= max(SMALL_FIRE_MIN_AREA * 4.5, FIRE_MIN_AREA_RATIO * 0.70) and
                    color >= FIRE_COLOR_MIN * 1.22 and
                    motion >= FIRE_MIN_MOTION * 4.5 and
                    tex >= 0.20 and
                    blur >= 0.14 and
                    edge_score <= EDGE_SHARPNESS_THRESHOLD * 0.96
                )
                ultra_fast_fire = (
                    self.streak >= 1 and
                    self.conf >= FIRE_ULTRA_FAST_CONF and
                    self.score >= FIRE_ULTRA_FAST_SCORE and
                    self.area_ratio >= max(SMALL_FIRE_MIN_AREA * 6.0, FIRE_MIN_AREA_RATIO * 0.78) and
                    motion >= FIRE_MIN_MOTION * 6.0 and
                    (
                        blur >= 0.14 or
                        tex >= 0.30
                    ) and
                    color >= FIRE_COLOR_MIN * 1.18 and
                    edge_score <= EDGE_SHARPNESS_THRESHOLD * 0.92
                )
                conf_ready = self.conf >= FIRE_INSTANT_CONF or relaxed_small_fire or priority_small_fire
                score_ready = self.score >= FIRE_INSTANT_SCORE or relaxed_small_fire or priority_small_fire
                return (
                    (
                        ultra_fast_fire or
                        priority_small_fire or
                        (conf_ready and score_ready)
                    ) and
                    self.area_ratio >= SMALL_FIRE_MIN_AREA and
                    (
                        color >= FIRE_COLOR_MIN * 0.90 or
                        ultra_fast_fire
                    ) and
                    dynamic_ready and
                    not rigid_object
                )
            if self.cls_name == "smoke":
                blur = self.blur_avg()
                tex = self.texture_avg()
                rigid_smoke = (
                    self.streak >= 2 and
                    shape_score < SHAPE_DEFORMATION_MIN * 0.80 and
                    edge_score > EDGE_SHARPNESS_THRESHOLD * 0.90
                )
                large_diffuse_plume = self.area_ratio >= SMOKE_INSTANT_AREA_RATIO
                strong_visual = (
                    blur >= max(0.07, SMOKE_BLUR_MIN * 1.15) and
                    tex >= max(0.16, SMOKE_TEXTURE_MIN * 2.5) and
                    color >= max(0.52, SMOKE_COLOR_MIN * 2.4)
                )
                dynamic_smoke = (
                    motion >= SMOKE_MIN_MOTION * 2.0 or
                    self.score >= SMOKE_INSTANT_SCORE * 1.10
                )
                ultra_fast_smoke = (
                    self.streak >= 1 and
                    self.conf >= SMOKE_ULTRA_FAST_CONF and
                    self.score >= SMOKE_ULTRA_FAST_SCORE and
                    self.area_ratio >= max(SMOKE_INSTANT_AREA_RATIO * 2.4, 0.050) and
                    motion >= SMOKE_MIN_MOTION * 6.0 and
                    blur >= max(0.07, SMOKE_BLUR_MIN * 1.20) and
                    tex >= max(0.35, SMOKE_TEXTURE_MIN * 5.0) and
                    color >= max(0.60, SMOKE_COLOR_MIN * 3.0) and
                    edge_score <= EDGE_SHARPNESS_THRESHOLD * 0.94
                )
                thin_fast_smoke = (
                    self.streak >= 1 and
                    self.conf >= SMOKE_THIN_FAST_CONF and
                    self.score >= SMOKE_THIN_FAST_SCORE and
                    self.area_ratio >= max(SMOKE_MIN_AREA_RATIO * 3.0, 0.0065) and
                    motion >= SMOKE_MIN_MOTION * 2.6 and
                    blur >= max(0.07, SMOKE_BLUR_MIN * 1.18) and
                    tex >= max(0.12, SMOKE_TEXTURE_MIN * 2.2) and
                    color >= max(0.42, SMOKE_COLOR_MIN * 2.1) and
                    edge_score <= EDGE_SHARPNESS_THRESHOLD * 0.98
                )
                return (
                    (
                        ultra_fast_smoke or
                        thin_fast_smoke or
                        (
                            self.conf >= SMOKE_INSTANT_CONF and
                            self.score >= SMOKE_INSTANT_SCORE and
                            large_diffuse_plume and
                            strong_visual and
                            dynamic_smoke
                        )
                    ) and
                    not rigid_smoke
                )
            return False
    
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
            Lá»­a: motion chaotic, Váº­t thá»ƒ: motion á»•n Ä‘á»‹nh.
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
            mot = self.motion_avg()
            mot_var = self.motion_var()
            tex = self.texture_avg()
            blur = self.blur_avg()
            color = self.color_avg()
            disp = self.centroid_disp(frame_w, frame_h)

            if self.cls_name == "fire":
                if self.should_instant_confirm():
                    return True
                flicker = roi_flicker_score(self.intensity_hist)
                area_v = self.area_var()
                aspect_var = self.aspect_ratio_var()
                shape_score = self.shape_stability_score()
                color_var = self.color_variance()
                
                # STRICT: Reject if shape is completely rigid (tem dÃ¡n, LED, etc)
                # If tracked for 4+ frames but shape never deformed â†’ definitely not fire
                if self.streak >= NO_DEFORMATION_REJECT_STREAK:
                    if shape_score < SHAPE_DEFORMATION_MIN and aspect_var < 0.0005:
                        return False  # Rigid object tracked consistently - reject
                
                # STRICT: Reject if high color + rigid shape + no motion + sharp edges
                # Catch stickers/LEDs/colored tape aggressively (conservative mode)
                if (color > 0.35 and shape_score < 0.02 and mot < 0.006 and 
                    self.boundary_consistency_score() > EDGE_SHARPNESS_THRESHOLD):
                    return False  # Likely a sticker/colored object, not fire
                
                # NEW: Reject if color + shape both static but moving (person walking)
                # Lá»­a PHáº¢I lÃ³e sÃ¡ng (color change) hoáº·c biáº¿n dáº¡ng (shape change)
                # Náº¿u váº­t di chuyá»ƒn nhÆ°ng mÃ u sáº¯c + hÃ¬nh dáº¡ng cá»‘ Ä‘á»‹nh â†’ khÃ´ng pháº£i lá»­a
                # NHÆ¯NG náº¿u intensity cao (lá»­a Ä‘ang táº¯t dáº§n) thÃ¬ váº«n giá»¯ â†’ khÃ´ng reject
                mean_intensity = float(np.mean(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
                max_intensity = float(np.max(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
                # Reject chá»‰ náº¿u vá»«a low intensity hiá»‡n táº¡i vá»«a khÃ´ng cÃ³ lá»‹ch sá»­ intensity cao
                if (color_var < 0.0003 and shape_score < 0.015 and mot > 0.006 and 
                    mean_intensity < 0.10 and max_intensity < 0.18):  # KhÃ´ng pháº£i lá»­a táº¯t dáº§n
                    return False  # Moving object without flickering + consistently low intensity = not fire
                
                # STRICT: Reject if sharp edges + no shape change
                shape_stable = shape_score < SHAPE_STABILITY_THRESHOLD
                edge_reflection = self.boundary_consistency_score() > EDGE_SHARPNESS_THRESHOLD
                if shape_stable and edge_reflection:
                    return False  # Likely a reflection/sticker on static object
                
                # NEW: Temporal trend analysis - reject steady/linear motion without deformation
                # Lá»­a: motion chaotic/erratic. Váº­t thá»ƒ: motion á»•n Ä‘á»‹nh/tuyáº¿n tÃ­nh
                # Xu tháº¿: phÃ¢n tÃ­ch 6 frames Ä‘á»ƒ phÃ¡t hiá»‡n pattern, khÃ´ng pháº£i frame Ä‘Æ¡n láº»
                motion_consistency = self.motion_consistency()
                motion_linearity = self.motion_linearity()
                motion_trend = abs(self.motion_trend())  # Absolute to check if trending up/down
                
                # Reject if motion too steady + no shape deformation
                # ÄÃ³ lÃ  váº­t thá»ƒ di chuyá»ƒn á»•n Ä‘á»‹nh, khÃ´ng pháº£i lá»­a bÃ¹ng
                if (motion_consistency < 0.25 and  # Motion ráº¥t á»•n Ä‘á»‹nh (not chaotic)
                    motion_linearity < 0.10 and  # Following linear trajectory (not erratic)
                    shape_score < 0.02 and  # Shape khÃ´ng deforming
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
                short_history_strong_fire = (
                    len(self.intensity_hist) < 4 and
                    self.streak >= max(2, FIRE_MIN_STREAK - 1) and
                    self.conf >= FIRE_SHORT_HISTORY_CONF and
                    self.score >= FIRE_SHORT_HISTORY_SCORE and
                    self.area_ratio >= max(SMALL_FIRE_MIN_AREA * 6.0, FIRE_MIN_AREA_RATIO * 0.70) and
                    color >= FIRE_COLOR_MIN * 1.15 and
                    mot >= FIRE_MIN_MOTION * 7.0 and
                    (
                        blur >= 0.16 or
                        tex >= 0.34
                    ) and
                    self.boundary_consistency_score() <= EDGE_SHARPNESS_THRESHOLD * 0.95
                )
     
                # Strong flicker or intensity flash is mandatory for fire
                min_intensity = float(np.min(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
                max_intensity = float(np.max(self.intensity_hist)) if len(self.intensity_hist) > 0 else 0.0
                intensity_range = max_intensity - min_intensity
     
                if (not short_history_strong_fire) and flicker < FIRE_FLICKER_MIN and intensity_range < FIRE_INTENSITY_RANGE_MIN:
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
                if short_history_strong_fire:
                    return True
                if area_ok:
                    # small fire path (require slightly lower score but still dynamic evidence)
                    return (
                        self.streak >= max(3, FIRE_MIN_STREAK - 2) and
                        self.score >= (FIRE_SCORE_CONFIRM * 0.75) and
                        dynamic_ok
                    )
    
                return False
    
            if self.cls_name == "smoke":
                if self.should_instant_confirm():
                    return True
                shape_score = self.shape_stability_score()
                color_var = self.color_variance()
                
                # STRICT: Reject if shape is completely rigid after 4+ frames
                if self.streak >= NO_DEFORMATION_REJECT_STREAK:
                    if shape_score < SHAPE_DEFORMATION_MIN:
                        return False  # Rigid object - not smoke
                
                # STRICT: Reject if moving but color + shape + blur/texture all static
                # Smoke pháº£i cÃ³ thay Ä‘á»•i: deformation hoáº·c blur hoáº·c color
                # NHÆ¯NG náº¿u blur_score hoáº·c texture_score váº«n cao thÃ¬ váº«n lÃ  khÃ³i â†’ khÃ´ng reject
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
                # KhÃ³i: motion chaotic/diffuse. Váº­t thá»ƒ: motion tuyáº¿n tÃ­nh
                motion_consistency_smoke = self.motion_consistency()
                motion_linearity_smoke = self.motion_linearity()
                
                # Reject if motion too linear + no deformation (probably object, not smoke)
                if (motion_consistency_smoke < 0.22 and  # Motion ráº¥t á»•n Ä‘á»‹nh
                    motion_linearity_smoke < 0.10 and  # Perfect linear trajectory
                    shape_score < 0.015 and  # No shape change
                    mot > 0.005 and  # Has motion
                    blur < SMOKE_BLUR_MIN):  # No blur change
                    return False  # Linear motion + rigid shape + no blur = not smoke (probably object)
    
                evidence_main = (
                    mot >= SMOKE_MIN_MOTION or
                    blur >= SMOKE_BLUR_MIN or
                    tex >= SMOKE_TEXTURE_MIN or
                    color >= SMOKE_COLOR_MIN
                )

                evidence_dynamic = (
                    disp >= SMOKE_MIN_DRIFT or
                    mot_var >= SMOKE_MIN_MOTION_VAR or
                    shape_score >= SHAPE_DEFORMATION_MIN * 1.8
                )

                strong_smoke_path = (
                    self.area_ratio >= max(SMOKE_MIN_AREA_RATIO * 2.5, 0.0020) and
                    self.conf >= max(CANDIDATE_CONF, 0.30) and
                    self.score >= SMOKE_SCORE_CONFIRM * 0.92 and
                    blur >= SMOKE_BLUR_MIN * 1.05 and
                    tex >= SMOKE_TEXTURE_MIN * 1.15 and
                    color >= SMOKE_COLOR_MIN * 1.10
                )

                return (
                    (
                        self.streak >= SMOKE_MIN_STREAK and
                        self.score >= SMOKE_SCORE_CONFIRM and
                        evidence_main and
                        evidence_dynamic
                    ) or (
                        self.streak >= max(2, SMOKE_MIN_STREAK - 1) and
                        strong_smoke_path and
                        evidence_dynamic
                    )
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
            self.recent_fire_regions = deque(maxlen=8)

        def _decay_recent_fire_regions(self):
            kept = deque(maxlen=self.recent_fire_regions.maxlen)
            for item in self.recent_fire_regions:
                ttl = int(item.get("ttl", 0)) - 1
                if ttl <= 0:
                    continue
                item["ttl"] = ttl
                kept.append(item)
            self.recent_fire_regions = kept

        def _remember_fire_region(self, tr):
            box = tuple(float(v) for v in tr.box)
            for item in self.recent_fire_regions:
                if box_iou(box, item.get("box", box)) > 0.08:
                    item["box"] = box
                    item["ttl"] = FIRE_RESUME_TTL
                    return
            self.recent_fire_regions.append({"box": box, "ttl": FIRE_RESUME_TTL})

        def _near_recent_fire(self, tr, frame_diag, frame_h):
            for item in self.recent_fire_regions:
                box = item.get("box", tr.box)
                if box_iou(tr.box, box) > 0.01:
                    return True
                center_gap = np.linalg.norm(
                    np.array(box_centroid(tr.box), dtype=np.float32)
                    - np.array(box_centroid(box), dtype=np.float32)
                ) / max(frame_diag, 1e-6)
                if center_gap <= FIRE_RESUME_DIST:
                    return True
                if (
                    overlap_ratio_1d(tr.box[0], tr.box[2], box[0], box[2]) >= 0.18 and
                    float(tr.box[1]) <= float(box[1]) + frame_h * 0.05 and
                    float(tr.box[3]) >= float(box[1]) - frame_h * 0.10
                ):
                    return True
            return False
     
        def update(self, detections, frame_bgr, prev_gray, cur_gray=None):
            h, w = frame_bgr.shape[:2]
            if cur_gray is None:
                cur_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            detections = sorted(detections, key=lambda d: d["conf"], reverse=True)
            self._decay_recent_fire_regions()
    
    
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
                # Build match matrix between existing tracks and detections (same class only).
                match_mat = np.zeros((n_tr, n_det), dtype=np.float32)
                for i, tr in enumerate(self.tracks):
                    for j, det in enumerate(detections):
                        if tr.cls_name != det["cls_name"]:
                            match_mat[i, j] = 0.0
                        else:
                            iou = box_iou(tr.box, det["box"])
                            score = float(iou)
                            if score < IOU_MATCH:
                                tr_center = np.array(box_centroid(tr.box), dtype=np.float32)
                                det_center = np.array(box_centroid(det["box"]), dtype=np.float32)
                                center_dist = float(np.linalg.norm(det_center - tr_center) / (np.hypot(w, h) + 1e-6))
                                area_sim = float(
                                    min(float(tr.area_ratio), float(det["area_ratio"]))
                                    / max(float(tr.area_ratio), float(det["area_ratio"]), 1e-6)
                                )
                                if center_dist <= MATCH_CENTER_DIST and area_sim >= MATCH_AREA_RATIO_MIN:
                                    score = max(
                                        score,
                                        0.22
                                        + max(0.0, 1.0 - center_dist / max(MATCH_CENTER_DIST, 1e-6)) * 0.48
                                        + area_sim * 0.30,
                                    )
                            match_mat[i, j] = score

                matched_tr = [False] * n_tr
                matched_det = [False] * n_det

                # Greedy global matching by strongest temporal/spatial consistency.
                while True:
                    if match_mat.size == 0:
                        break
                    max_idx = int(np.argmax(match_mat))
                    i, j = np.unravel_index(max_idx, match_mat.shape)
                    max_score = float(match_mat[i, j])
                    if max_score < MATCH_SCORE_MIN:
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
                    match_mat[i, :] = -1.0
                    match_mat[:, j] = -1.0
    
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

            confirmed_fire = [tr for tr in self.tracks if tr.state == "confirmed" and tr.cls_name == "fire"]
            frame_diag = float(np.hypot(w, h) + 1e-6)
            if confirmed_fire:
                for fire_tr in confirmed_fire:
                    self._remember_fire_region(fire_tr)
            for tr in self.tracks:
                if tr.state == "confirmed" or tr.cls_name != "fire":
                    continue
                fire_resume_support = (
                    tr.streak >= 1 and
                    tr.score >= FIRE_RESUME_SCORE and
                    tr.conf >= FIRE_RESUME_CONF and
                    tr.area_ratio >= max(SMALL_FIRE_MIN_AREA * 6.0, FIRE_MIN_AREA_RATIO * 0.70) and
                    tr.motion_avg() >= FIRE_MIN_MOTION * 7.0 and
                    (
                        tr.blur_avg() >= 0.16 or
                        tr.texture_avg() >= 0.34
                    ) and
                    tr.color_avg() >= FIRE_COLOR_MIN * 1.10 and
                    tr.boundary_consistency_score() <= EDGE_SHARPNESS_THRESHOLD * 0.96
                )
                if self._near_recent_fire(tr, frame_diag, h) and fire_resume_support:
                    tr.state = "confirmed"
                    tr.release_counter = 0
            confirmed_fire = [tr for tr in self.tracks if tr.state == "confirmed" and tr.cls_name == "fire"]
            if confirmed_fire:
                for tr in self.tracks:
                    if tr.state == "confirmed" or tr.cls_name != "smoke":
                        continue
                    near_fire = any(
                        box_iou(tr.box, fire_tr.box) > 0.01
                        or np.linalg.norm(
                            np.array(box_centroid(tr.box), dtype=np.float32)
                            - np.array(box_centroid(fire_tr.box), dtype=np.float32)
                        ) / frame_diag <= 0.30
                        or (
                            overlap_ratio_1d(tr.box[0], tr.box[2], fire_tr.box[0], fire_tr.box[2]) >= 0.20
                            and float(tr.box[1]) <= float(fire_tr.box[1]) + h * 0.04
                            and float(tr.box[3]) >= float(fire_tr.box[1]) - h * 0.08
                        )
                        for fire_tr in confirmed_fire
                    )
                    smoke_support = (
                        tr.blur_avg() >= SMOKE_BLUR_MIN * 0.82
                        or tr.texture_avg() >= SMOKE_TEXTURE_MIN * 0.85
                        or tr.color_avg() >= SMOKE_COLOR_MIN * 0.95
                    )
                    smoke_fast_confirm = (
                        tr.streak >= 1
                        and tr.score >= SMOKE_SCORE_CONFIRM * 1.10
                        and tr.conf >= max(CANDIDATE_CONF, 0.38)
                        and (
                            tr.blur_avg() >= SMOKE_BLUR_MIN * 0.95
                            or tr.texture_avg() >= SMOKE_TEXTURE_MIN * 0.92
                            or tr.color_avg() >= SMOKE_COLOR_MIN * 1.02
                        )
                    )
                    if (
                        near_fire
                        and smoke_support
                        and (
                            (
                                tr.streak >= max(2, SMOKE_MIN_STREAK - 1)
                                and tr.score >= SMOKE_SCORE_CONFIRM * 0.82
                            )
                            or smoke_fast_confirm
                        )
                    ):
                        tr.state = "confirmed"
                        tr.release_counter = 0

            confirmed = []
            candidates = []
            for tr in self.tracks:
                if tr.state == "confirmed":
                    confirmed.append(tr)
                elif tr.streak >= 2 or tr.score > 35:
                    candidates.append(tr)

            confirmed.sort(
                key=lambda tr: (
                    0 if tr.cls_name == "fire" else 1,
                    -float(tr.score),
                    -float(tr.conf),
                )
            )
            candidates.sort(
                key=lambda tr: (
                    0 if tr.cls_name == "fire" else 1,
                    -float(tr.score),
                    -float(tr.conf),
                )
            )
    
            if confirmed:
                self.alert_cooldown = ALERT_COOLDOWN
            else:
                self.alert_cooldown = max(0, self.alert_cooldown - 1)
    
            alarm_active = self.alert_cooldown > 0
            return cur_gray, confirmed, candidates, alarm_active
    
    # =========================================================

    class FireSmokeEngine:
        def __init__(self):
            self.model = None
            self.model_path = None
            self.load_error = None
            if ENABLE_FIRE_SMOKE_DETECTION:
                for candidate in FS_MODEL_CANDIDATES:
                    try:
                        if not os.path.isfile(candidate):
                            continue
                        self.model = YOLO(candidate)
                        try:
                            self.model.fuse()
                        except Exception:
                            pass
                        self.model_path = candidate
                        break
                    except Exception as ex:
                        # Keep running even if one weight file is incompatible with current ultralytics/torch.
                        print(f"[WARN] Cannot load fire/smoke model '{candidate}': {ex}")
                        self.load_error = f"{candidate}: {ex}"
                        self.model = None
            if self.model is None and self.load_error is None and ENABLE_FIRE_SMOKE_DETECTION:
                self.load_error = "Không tìm thấy model khói/lửa tương thích."
            self.prev_gray = None
            self.prev_scene_small_gray = None
            self.tm = TrackManager()
            self.frame_idx = 0

        def reset(self):
            self.prev_gray = None
            self.prev_scene_small_gray = None
            self.tm = TrackManager()
            self.frame_idx = 0

        def process(self, frame_bgr):
            if self.model is None:
                status = "Khói/lửa: model chưa tải được"
                if self.load_error and "C3k2" in self.load_error:
                    status = "Khói/lửa: model không tương thích với bản Ultralytics hiện tại"
                return {"confirmed": [], "candidates": [], "alarm_active": False, "status": status}
            self.frame_idx += 1
            cur_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            small_gray = cv2.resize(cur_gray, (64, 36), interpolation=cv2.INTER_AREA)
            if self.prev_scene_small_gray is not None:
                diff_mean = float(np.mean(cv2.absdiff(self.prev_scene_small_gray, small_gray)) / 255.0)
                prev_hist = cv2.calcHist([self.prev_scene_small_gray], [0], None, [16], [0, 256])
                cur_hist = cv2.calcHist([small_gray], [0], None, [16], [0, 256])
                prev_hist = cv2.normalize(prev_hist, None).flatten()
                cur_hist = cv2.normalize(cur_hist, None).flatten()
                hist_corr = float(cv2.compareHist(prev_hist, cur_hist, cv2.HISTCMP_CORREL))
                if diff_mean >= SCENE_CUT_DIFF and hist_corr <= SCENE_CUT_CORR:
                    self.prev_gray = cur_gray
                    self.prev_scene_small_gray = small_gray
                    self.tm = TrackManager()
                    return {"confirmed": [], "candidates": [], "alarm_active": False, "status": "Äang Ä‘á»“ng bá»™ cáº£nh má»›i"}
            self.prev_scene_small_gray = small_gray
            predict_kwargs = {
                "conf": CANDIDATE_CONF,
                "imgsz": adaptive_infer_size(frame_bgr, max_size=INFER_SIZE, min_size=FS_MIN_IMG_SIZE),
                "verbose": False,
                "device": POSE_DEVICE,
                "max_det": 16,
            }
            if USE_CUDA:
                predict_kwargs["half"] = True
            results = self.model.predict(frame_bgr, **predict_kwargs)
            
            detections = []
            res = results[0]
            boxes = res.boxes.cpu() if res.boxes is not None else None
            
            if boxes is not None and len(boxes) > 0:
                h, w = frame_bgr.shape[:2]
            
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
            
                    roi_bgr = frame_bgr[yi1:yi2, xi1:xi2]
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
            
                    # HARD FILTER - reject only when evidence is weak across all channels.
                    if motion < HARD_MOTION_MIN and conf < (CANDIDATE_CONF * 0.78) and edge_sharpness > EDGE_SHARPNESS_THRESHOLD:
                        continue

                    # Low-confidence rescue path:
                    # allow thin smoke / tiny distant fire only when extra visual evidence is strong.
                    if conf < STRONG_CANDIDATE_CONF:
                        if "fire" in cls_name_raw:
                            low_conf_fire_support = (
                                conf >= CANDIDATE_CONF and
                                area_ratio >= max(SMALL_FIRE_MIN_AREA * 2.6, 0.00048) and
                                color_score >= FIRE_COLOR_MIN * 1.08 and
                                motion >= FIRE_MIN_MOTION * 1.5 and
                                (
                                    texture_score >= 0.08 or
                                    blur_score >= 0.14
                                ) and
                                edge_sharpness <= EDGE_SHARPNESS_THRESHOLD * 1.02
                            )
                            if not low_conf_fire_support:
                                continue
                        if "smoke" in cls_name_raw:
                            low_conf_smoke_support = (
                                conf >= CANDIDATE_CONF and
                                area_ratio >= max(SMOKE_MIN_AREA_RATIO * 4.0, 0.0100) and
                                smoke_color >= max(0.40, SMOKE_COLOR_MIN * 2.0) and
                                blur_score >= max(0.07, SMOKE_BLUR_MIN * 1.08) and
                                texture_score >= max(0.10, SMOKE_TEXTURE_MIN * 1.6) and
                                edge_sharpness <= EDGE_SHARPNESS_THRESHOLD * 1.04
                            )
                            if not low_conf_smoke_support:
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
                        sat = hsv_roi[:, :, 1]
                        val = hsv_roi[:, :, 2]
                        white_hot_ratio = float(np.count_nonzero((val > 235) & (sat < 72)) / (val.size + 1e-6))
                        bright_glare_ratio = float(np.count_nonzero((val > 215) & (sat < 108)) / (val.size + 1e-6))
                    except Exception:
                        hue_std = sat_std = val_std = 1.0
                        sat = None
                        val = None
                        white_hot_ratio = 0.0
                        bright_glare_ratio = 0.0
            
                    # Heuristic: mÃ u Ä‘á»u (hue_std nhá») + cáº¡nh sáº¯c + khÃ´ng chuyá»ƒn Ä‘á»™ng => ráº¥t cÃ³ thá»ƒ sticker/decoration
                    if "fire" in cls_name_raw:
                        if hue_std < STICKER_HUE_STD_MAX and edge_sharpness > STICKER_EDGE_MIN and motion < FIRE_MIN_MOTION and conf < STICKER_CONF_MAX and texture_score < STICKER_TEXTURE_MAX:
                            continue
            
                    if "smoke" in cls_name_raw:
                        if sat_std < STICKER_SAT_STD_MAX and edge_sharpness > (STICKER_EDGE_MIN + 0.05) and motion < SMOKE_MIN_MOTION and conf < STICKER_CONF_MAX and blur_score < 0.12:
                            continue
            
                    try:
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

                    top_light_glare = bool(
                        yi1 <= int(h * 0.38)
                        and (white_hot_ratio >= 0.06 or bright_glare_ratio >= 0.13)
                        and texture_score <= 0.42
                        and (approx_rect or fill_ratio >= 0.34 or edge_sharpness >= 0.18)
                    )
                    moving_low_color_hotspot = bool(
                        "fire" in cls_name_raw
                        and color_score < FIRE_COLOR_MIN * 0.72
                        and texture_score >= 0.30
                        and motion >= FIRE_MIN_MOTION * 1.05
                        and area_ratio <= FIRE_MIN_AREA_RATIO * 2.4
                        and conf < 0.70
                    )
                    static_low_color_hotspot = bool(
                        "fire" in cls_name_raw
                        and color_score < FIRE_COLOR_MIN * 0.74
                        and texture_score >= 0.28
                        and motion < 0.015
                        and area_ratio <= FIRE_MIN_AREA_RATIO * 2.2
                        and conf < 0.62
                        and approx_rect
                    )

                    # If a region is large, uniformly colored, with sharp edges and fills most of the bbox,
                    # it's very likely a printed decoration (sticker) rather than fire/smoke.
                    if "fire" in cls_name_raw:
                        if moving_low_color_hotspot or static_low_color_hotspot:
                            continue
                        if (
                            top_light_glare
                            and conf < 0.92
                            and (
                                white_hot_ratio >= 0.06
                                or bright_glare_ratio >= 0.24
                                or motion < 0.12
                                or color_score < FIRE_COLOR_MIN * 1.80
                            )
                        ):
                            continue
                        if (fill_ratio > 0.60 and edge_sharpness > 0.58 and motion < 0.005 and conf < 0.60 and texture_score < 0.20):
                            continue
                        if approx_rect and cont_fill > 0.50 and edge_sharpness > 0.60 and conf < 0.60:
                            continue
            
                    if "smoke" in cls_name_raw:
                        if (
                            top_light_glare
                            and conf < 0.84
                            and blur_score < max(0.14, SMOKE_BLUR_MIN * 1.8)
                        ):
                            continue
                        if (fill_ratio > 0.60 and edge_sharpness > 0.65 and motion < 0.005 and conf < 0.55 and blur_score < 0.10):
                            continue
                        if approx_rect and cont_fill > 0.48 and edge_sharpness > 0.68 and conf < 0.55:
                            continue
            
                    # Lá»­a: yÃªu cáº§u mÃ u nÃ³ng tÆ°Æ¡ng Ä‘á»‘i cho vÃ¹ng khÃ´ng quÃ¡ nhá»; vÃ¹ng ráº¥t nhá» Ä‘Æ°á»£c giá»¯ Ä‘á»ƒ track
                    if "fire" in cls_name_raw and color_score < FIRE_COLOR_MIN * 0.88 and conf < 0.54 and area_ratio >= SMALL_FIRE_MIN_AREA:
                        continue
            
                    # KhÃ³i: cho phÃ©p phÃ¡t hiá»‡n khÃ³i má»ng hÆ¡n (nháº¡y hÆ¡n)
                    # chá»‰ loáº¡i khi má»i tÃ­n hiá»‡u Ä‘á»u ráº¥t yáº¿u
                    if "smoke" in cls_name_raw:
                        if (
                            conf < 0.28 and
                            smoke_color < 0.10 and
                            blur_score < 0.05 and
                            texture_score < 0.04
                        ):
                            continue
            
                    # Loáº¡i bbox quÃ¡ nhá» trá»« khi model Ä‘á»§ tin cáº­y (cho phÃ©p vÃ¹ng ráº¥t nhá» náº¿u confidence >= 0.55)
                    if "fire" in cls_name_raw and area_ratio < FIRE_MIN_AREA_RATIO and conf < 0.48:
                        continue
                    if "smoke" in cls_name_raw:
                        if area_ratio < SMOKE_MIN_AREA_RATIO and conf < 0.42 and blur_score < SMOKE_BLUR_MIN and texture_score < SMOKE_TEXTURE_MIN:
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
                frame_bgr=frame_bgr,
                prev_gray=self.prev_gray,
                cur_gray=cur_gray,
            )
            
            self.prev_gray = gray.copy()
            status = "Monitoring..."
            if confirmed:
                txt = ", ".join([f"#{t.id}:{t.cls_name}" for t in confirmed[:4]])
                if any(getattr(t, "cls_name", "") == "fire" for t in confirmed):
                    status = f"FIRE ALERT - {txt}"
                elif any(getattr(t, "cls_name", "") == "smoke" for t in confirmed):
                    status = f"SMOKE ALERT - {txt}"
                else:
                    status = f"ALERT CONFIRMED - {txt}"
            elif candidates:
                txt = ", ".join([f"#{t.id}:{t.cls_name}" for t in candidates[:4]])
                status = f"Tracking priority zones - {txt}"
            return {"confirmed": confirmed, "candidates": candidates, "alarm_active": alarm_active, "status": status}

    return FireSmokeEngine

FireSmokeEngine = _build_fire_smoke_engine_class()
# === FIRE_SMOKE_ORIGINAL_END ===

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


def torso_angle_and_center(kp_xy, kp_cf, min_conf=0.25):
    ls = point_from_kp(kp_xy, kp_cf, 5, min_conf=min_conf)
    rs = point_from_kp(kp_xy, kp_cf, 6, min_conf=min_conf)
    lh = point_from_kp(kp_xy, kp_cf, 11, min_conf=min_conf)
    rh = point_from_kp(kp_xy, kp_cf, 12, min_conf=min_conf)

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


def recent_mean(values, window: int):
    if values is None or len(values) == 0 or window <= 0:
        return 0.0
    seq = list(values)[-int(window):]
    if not seq:
        return 0.0
    return float(np.mean(np.asarray(seq, dtype=np.float32)))


def recent_peak(values, window: int):
    if values is None or len(values) == 0 or window <= 0:
        return 0.0
    seq = list(values)[-int(window):]
    if not seq:
        return 0.0
    return float(np.max(np.asarray(seq, dtype=np.float32)))


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


def recent_vector(points):
    if points is None or len(points) < 2:
        return np.zeros(2, dtype=np.float32)
    p0 = np.asarray(points[-2], dtype=np.float32)
    p1 = np.asarray(points[-1], dtype=np.float32)
    return p1 - p0


def unit_vector(vec):
    arr = np.asarray(vec, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm <= 1e-6:
        return np.zeros_like(arr)
    return arr / norm


def projected_speed(vec, direction):
    dir_u = unit_vector(direction)
    if float(np.linalg.norm(dir_u)) <= 1e-6:
        return 0.0
    return float(np.dot(np.asarray(vec, dtype=np.float32), dir_u))


def bbox_edge_flags(box, frame_w: int | None, frame_h: int | None):
    if frame_w is None or frame_h is None or frame_w <= 0 or frame_h <= 0:
        return {
            "touch_left": False,
            "touch_right": False,
            "touch_top": False,
            "touch_bottom": False,
            "touch_lr": False,
            "touch_any": False,
        }

    x1, y1, x2, y2 = [float(v) for v in box]
    margin_x = max(6.0, float(frame_w) * FALL_EDGE_MARGIN_X)
    margin_y = max(6.0, float(frame_h) * FALL_EDGE_MARGIN_Y)
    touch_left = x1 <= margin_x
    touch_right = x2 >= float(frame_w) - margin_x
    touch_top = y1 <= margin_y
    touch_bottom = y2 >= float(frame_h) - margin_y
    return {
        "touch_left": bool(touch_left),
        "touch_right": bool(touch_right),
        "touch_top": bool(touch_top),
        "touch_bottom": bool(touch_bottom),
        "touch_lr": bool(touch_left or touch_right),
        "touch_any": bool(touch_left or touch_right or touch_top or touch_bottom),
    }


def fall_ground_signature(kp_xy, kp_cf, pose_min_conf: float, box, frame_h: int | None):
    x1, y1, x2, y2 = [float(v) for v in box]
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    min_conf = max(0.05, float(pose_min_conf) * 0.85)
    pts = []
    for idx in (0, 1, 2, 5, 6, 11, 12, 13, 14, 15, 16):
        pt = point_from_kp(kp_xy, kp_cf, idx, min_conf=min_conf)
        if pt is not None:
            pts.append(np.asarray(pt, dtype=np.float32))

    if not pts:
        return {
            "point_count": 0,
            "x_span_rel": 0.0,
            "y_span_rel": 1.0,
            "lowest_rel": 0.0,
            "grounded": False,
        }

    coords = np.stack(pts, axis=0)
    x_span_rel = float((float(np.max(coords[:, 0])) - float(np.min(coords[:, 0]))) / (w + 1e-6))
    y_span_rel = float((float(np.max(coords[:, 1])) - float(np.min(coords[:, 1]))) / (h + 1e-6))
    if frame_h is not None and frame_h > 0:
        lowest_rel = float(float(np.max(coords[:, 1])) / float(frame_h))
    else:
        lowest_rel = 0.0

    grounded = (
        len(pts) >= FALL_FLOOR_MIN_POINTS
        and x_span_rel >= FALL_FLOOR_X_SPAN_MIN
        and y_span_rel <= FALL_FLOOR_Y_SPAN_MAX
        and lowest_rel >= FALL_FLOOR_LOWEST_MIN
    )
    return {
        "point_count": int(len(pts)),
        "x_span_rel": float(x_span_rel),
        "y_span_rel": float(y_span_rel),
        "lowest_rel": float(lowest_rel),
        "grounded": bool(grounded),
    }


def bbox_motion_signature(box_hist, frame_w: int | None = None, frame_h: int | None = None):
    boxes = list(box_hist or [])
    if len(boxes) < 2:
        return {
            "aspect_trend": 0.0,
            "area_growth": 1.0,
            "area_var": 0.0,
        }

    areas = []
    aspects = []
    frame_area = float(max(1, int(frame_w or 0)) * max(1, int(frame_h or 0))) if frame_w and frame_h else 1.0
    for x1, y1, x2, y2 in boxes[-6:]:
        bw = max(1.0, float(x2) - float(x1))
        bh = max(1.0, float(y2) - float(y1))
        aspects.append(float(bw / (bh + 1e-6)))
        areas.append(float((bw * bh) / max(1.0, frame_area)))

    prev_area = max(1e-6, float(areas[-2]))
    return {
        "aspect_trend": float(robust_slope(aspects[-5:])),
        "area_growth": float(areas[-1] / prev_area),
        "area_var": float(np.var(np.asarray(areas[-5:], dtype=np.float32))) if len(areas) >= 3 else 0.0,
    }


def trajectory_motion_signature(center_hist, height: float = 1.0):
    pts = list(center_hist or [])
    if len(pts) < 2:
        return {
            "disp_rel": 0.0,
            "path_rel": 0.0,
            "linearity": 0.0,
        }

    arr = np.asarray(pts[-6:], dtype=np.float32)
    diffs = np.diff(arr, axis=0)
    if len(diffs) == 0:
        return {
            "disp_rel": 0.0,
            "path_rel": 0.0,
            "linearity": 0.0,
        }

    step_norms = np.linalg.norm(diffs, axis=1)
    path_len = float(np.sum(step_norms))
    disp_vec = arr[-1] - arr[0]
    disp_len = float(np.linalg.norm(disp_vec))
    safe_height = max(1.0, float(height))
    return {
        "disp_rel": float(disp_len / safe_height),
        "path_rel": float(path_len / safe_height),
        "linearity": float(disp_len / max(1e-6, path_len)),
    }


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
# ADVANCED SKELETON-BASED ANALYSIS (KhÃ´ng dá»±a vÃ o YOLO)
# =========================================================
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
        
        # Wrist height asymmetry can signal a one-sided holding pose.
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
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
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
        self.title("V-Shield AI - Giám sát an ninh")
        self.geometry("1280x860")
        self.minsize(1100, 760)

        pose_candidates = POSE_MODEL_CANDIDATES_GPU if USE_CUDA else POSE_MODEL_CANDIDATES_CPU
        self.model_path = pick_first_existing(pose_candidates) or MODEL_PATH
        self.model = YOLO(self.model_path)
        try:
            self.model.fuse()
        except Exception:
            pass
        self.frame_index = 0

        # Fire/Smoke detection (original logic).
        self.fs_engine = FireSmokeEngine()
        self.track_states: dict[int, PersonState] = {}
        self.recent_fall_events = deque(maxlen=FALL_MEMORY_MAXLEN)

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
        self.fs_last_snapshot_time = 0.0

        self.source_mode = tk.StringVar(value="camera")
        self.camera_value = tk.StringVar(value="0")
        self.video_value = tk.StringVar(value="")
        self.status_value = tk.StringVar(value="Sẵn sàng")
        self._last_status_text = "Sẵn sàng"
        self.loop_var = tk.BooleanVar(value=True)
        self.video_fps = 0.0

        # Video seek bar (only meaningful for file sources).
        self.total_frames = 0
        self.current_frame_idx = 0
        self.seek_var = tk.IntVar(value=0)
        self.seek_pending = None
        self.seek_lock = threading.Lock()
        self.user_dragging_seek = False
        self.updating_seek = False
        self.tracker_reset = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(15, self._refresh_preview)
        self.after(200, self._maybe_autostart_on_launch)

    def _maybe_autostart_on_launch(self):
        if not AUTO_PROMPT_VIDEO_ON_START:
            return
        if self.running:
            return

        # Allow: `python app.py <source>` (file path, rtsp url, or camera index).
        arg_source = None
        if len(sys.argv) >= 2:
            arg_source = sys.argv[1].strip()

        if arg_source:
            if arg_source.isdigit():
                self.source_mode.set("camera")
                self.camera_value.set(arg_source)
            elif arg_source.lower().startswith("rtsp://"):
                self.source_mode.set("camera")
                self.camera_value.set(arg_source)
            else:
                self.source_mode.set("video")
                self.video_value.set(arg_source)
            try:
                self.start()
            except Exception:
                pass
            return

        default_test_video = os.path.join(os.getcwd(), "test.mp4")
        if os.path.isfile(default_test_video):
            self.source_mode.set("video")
            self.video_value.set(default_test_video)
            try:
                self.start()
            except Exception:
                pass
            return

        # Default: prompt for video file and auto-start if user picked one.
        if not self.video_value.get().strip():
            self.choose_video()
        if self.video_value.get().strip():
            try:
                self.start()
            except Exception:
                pass

    def _set_status(self, text: str):
        normalized = normalize_ui_text(text)

        def apply_status():
            if not self.winfo_exists():
                return
            if normalized == self._last_status_text:
                return
            self.status_value.set(normalized)
            self._last_status_text = normalized

        if threading.current_thread() is threading.main_thread():
            try:
                apply_status()
            except tk.TclError:
                pass
        else:
            try:
                self.after(0, apply_status)
            except tk.TclError:
                pass

    def _timeline_now(self):
        if self.source_type == "file" and self.video_fps and self.video_fps > 1e-3:
            return float(max(0, int(self.current_frame_idx))) / float(self.video_fps)
        return time.monotonic()

    def _reset_detection_state(self):
        self.track_states = {}
        self.recent_fall_events.clear()
        self.tracker_reset = True
        self.last_alarm_beep_time = 0.0
        try:
            self.fs_engine.reset()
        except Exception:
            pass
        self.fs_last_snapshot_time = 0.0

    def _prune_recent_fall_events(self, now: float):
        while self.recent_fall_events:
            event_time = float(self.recent_fall_events[0].get("time", now))
            if now - event_time <= FALL_MEMORY_SEC * 1.35:
                break
            self.recent_fall_events.popleft()

    def _remember_recent_fall_event(
        self,
        track_id: int,
        box,
        center,
        height: float,
        now: float,
        confidence: float,
        grounded: bool = False,
    ):
        if confidence < 0.54 and not grounded:
            return

        self._prune_recent_fall_events(now)
        event = {
            "time": float(now),
            "track_id": int(track_id),
            "box": tuple(float(v) for v in box),
            "center": (float(center[0]), float(center[1])),
            "height": max(1.0, float(height)),
            "aspect": float((float(box[2]) - float(box[0])) / max(1.0, float(box[3]) - float(box[1]))),
            "confidence": float(confidence),
            "grounded": bool(grounded),
        }

        updated = False
        for idx in range(len(self.recent_fall_events) - 1, -1, -1):
            prev = self.recent_fall_events[idx]
            same_track = int(prev.get("track_id", -10**9)) == int(track_id)
            overlap = bbox_iou(event["box"], prev.get("box", event["box"]))
            if same_track or overlap >= 0.55:
                self.recent_fall_events[idx] = event
                updated = True
                break

        if not updated:
            self.recent_fall_events.append(event)

    def _match_recent_fall_event(self, track_id: int, box, center, height: float, now: float, aspect: float):
        self._prune_recent_fall_events(now)
        best_event = None
        best_score = 0.0
        safe_height = max(1.0, float(height))

        for event in self.recent_fall_events:
            age = now - float(event.get("time", now))
            if age < 0.0 or age > FALL_MEMORY_SEC:
                continue

            ev_box = event.get("box", box)
            ev_center = event.get("center", center)
            ev_height = max(1.0, float(event.get("height", safe_height)))

            overlap = bbox_iou(box, ev_box)
            center_dist = float(np.hypot(float(center[0]) - float(ev_center[0]), float(center[1]) - float(ev_center[1]))) / max(
                safe_height, ev_height
            )
            bottom_gap = abs(float(box[3]) - float(ev_box[3])) / max(safe_height, ev_height)
            aspect_gap = abs(float(aspect) - float(event.get("aspect", aspect)))

            proximity = max(0.0, 1.0 - center_dist / FALL_MEMORY_CENTER_DIST)
            bottom_score = max(0.0, 1.0 - bottom_gap / FALL_MEMORY_BOTTOM_GAP)
            aspect_score = max(0.0, 1.0 - aspect_gap / 0.80)
            grounded_bonus = 0.08 if bool(event.get("grounded", False)) else 0.0
            score = max(overlap, proximity * 0.50 + bottom_score * 0.22 + aspect_score * 0.20 + grounded_bonus)

            if overlap < FALL_MEMORY_IOU_MIN and (center_dist > FALL_MEMORY_CENTER_DIST or bottom_gap > FALL_MEMORY_BOTTOM_GAP):
                continue
            if score < FALL_MEMORY_SCORE_MIN or score <= best_score:
                continue

            best_score = score
            best_event = {
                "track_id": int(event.get("track_id", track_id)),
                "time": float(event.get("time", now)),
                "score": float(score),
                "grounded": bool(event.get("grounded", False)),
                "confidence": float(event.get("confidence", 0.0)),
            }

        return best_event

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
        ttk.Radiobutton(row1, text="Tệp video", variable=self.source_mode, value="video").pack(side="left", padx=(0, 10))

        ttk.Label(row1, text="Chỉ số camera / RTSP:").pack(side="left", padx=(20, 6))
        self.camera_entry = ttk.Entry(row1, textvariable=self.camera_value, width=42)
        self.camera_entry.pack(side="left", padx=(0, 10))

        ttk.Label(row1, text="Đường dẫn video:").pack(side="left", padx=(10, 6))
        self.video_entry = ttk.Entry(row1, textvariable=self.video_value, width=42)
        self.video_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ttk.Button(row1, text="Chọn video", command=self.choose_video).pack(side="left", padx=(0, 8))

        row2 = ttk.Frame(control)
        row2.pack(fill="x")

        ttk.Button(row2, text="Bắt đầu", command=self.start).pack(side="left", padx=(0, 8))
        ttk.Button(row2, text="Dừng", command=self.stop).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(row2, text="Lặp lại khi hết video", variable=self.loop_var).pack(side="left", padx=(10, 8))

        ttk.Label(row2, textvariable=self.status_value).pack(side="right")

        timeline_frame = ttk.LabelFrame(main, text="Thanh tua video", padding=8)
        timeline_frame.pack(fill="x", pady=(10, 0))

        seek_row = ttk.Frame(timeline_frame)
        seek_row.pack(fill="x")
        self.seek_scale = tk.Scale(
            seek_row,
            from_=0,
            to=0,
            orient="horizontal",
            showvalue=0,
            variable=self.seek_var,
            command=self._on_seek_move,
            sliderlength=20,
            bd=0,
            highlightthickness=0,
            length=620,
        )
        self.seek_scale.pack(side="left", fill="x", expand=True)
        self.seek_scale.configure(state="disabled")
        self.seek_label = ttk.Label(seek_row, text="0 / 0 | 00:00 / 00:00")
        self.seek_label.pack(side="left", padx=(10, 0))
        self.seek_scale.bind("<ButtonPress-1>", self._on_seek_press)
        self.seek_scale.bind("<ButtonRelease-1>", self._on_seek_release)

        preview_frame = ttk.LabelFrame(main, text="Khung hình camera / video", padding=8)
        preview_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill="both", expand=True)

        hint = ttk.Label(
            main,
            text="Trong cửa sổ video, nhấn ESC hoặc Q để thoát. Với video tệp, ứng dụng sẽ tự lặp nếu bật tùy chọn.",
        )
        hint.pack(fill="x", pady=(8, 0))

    def choose_video(self):
        path = filedialog.askopenfilename(
            title="Chọn video để chạy",
            filetypes=[
                ("Tệp video", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("Tất cả tệp", "*.*"),
            ],
        )
        if path:
            self.video_value.set(path)
            self.source_mode.set("video")

    def _on_seek_press(self, _event=None):
        if self.source_type != "file" or self.total_frames <= 0:
            return
        self.user_dragging_seek = True

    def _on_seek_move(self, _value):
        # Only update label; actual seeking happens on mouse release.
        if self.source_type != "file" or self.total_frames <= 0:
            return
        if self.updating_seek:
            return
        self._update_seek_label(int(self.seek_var.get()), self.total_frames)

    def _on_seek_release(self, _event=None):
        if self.source_type != "file" or self.total_frames <= 0:
            self.user_dragging_seek = False
            return
        self.user_dragging_seek = False
        target = int(self.seek_var.get())
        with self.seek_lock:
            self.seek_pending = max(0, min(target, max(0, self.total_frames - 1)))
        # Reset trackers after seeking to avoid mismatched IDs/state.
        self.tracker_reset = True

    def _update_seek_label(self, cur_frame: int, total_frames: int):
        try:
            if total_frames <= 0:
                self.seek_label.configure(text="0 / 0 | 00:00 / 00:00")
                return
            fps = float(self.video_fps) if self.video_fps and self.video_fps > 0 else 0.0
            if fps > 0:
                cur_sec = max(0.0, float(cur_frame) / fps)
                total_sec = max(0.0, float(max(0, total_frames - 1)) / fps)
                self.seek_label.configure(
                    text=f"{int(cur_frame)} / {int(total_frames - 1)} | {self._format_timecode(cur_sec)} / {self._format_timecode(total_sec)}"
                )
            else:
                self.seek_label.configure(text=f"{int(cur_frame)} / {int(total_frames - 1)}")
        except Exception:
            pass

    @staticmethod
    def _format_timecode(seconds_value: float):
        total_seconds = max(0, int(round(float(seconds_value))))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _resolve_source(self):
        mode = self.source_mode.get().strip()
        if mode == "video":
            path = self.video_value.get().strip()
            if not path:
                messagebox.showerror("Thiếu video", "Chọn một tệp video trước khi bắt đầu.")
                return None, None
            if not os.path.isfile(path):
                messagebox.showerror("Sai đường dẫn", f"Không tìm thấy tệp video:\n{path}")
                return None, None
            return path, "file"

        raw = self.camera_value.get().strip()
        if not raw:
            messagebox.showerror("Thiếu nguồn", "Nhập chỉ số camera (ví dụ 0) hoặc URL RTSP trước khi bắt đầu.")
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
        stand_key = ACTION_STAND
        walk_key = ACTION_WALK
        run_key = ACTION_RUN
        sit_key = ACTION_SIT
        fall_key = ACTION_FALL
        alert_key = action_key("B\u00c1O \u0110\u1ed8NG")
        punch_key = ACTION_PUNCH
        kick_key = ACTION_KICK
        hold_key = ACTION_HOLD
        fight_key = ACTION_FIGHT
        moving_fight_key = ACTION_MOVE_FIGHT
        locomotion = {stand_key, walk_key, run_key}

        if current_action in (punch_key, kick_key) and candidate_action not in (punch_key, kick_key):
            return 1
        if candidate_action == alert_key:
            return 1
        if candidate_action in (punch_key, kick_key):
            return 1
        if candidate_action == fall_key:
            return 2
        if candidate_action == moving_fight_key:
            return 2
        if candidate_action == fight_key:
            return 3
        if candidate_action == hold_key:
            return 4
        if candidate_action == run_key:
            return 3
        if current_action in locomotion and candidate_action in locomotion and current_action != candidate_action:
            return 3

        required = 4
        transitional = {sit_key, stand_key, walk_key}
        if current_action in transitional and candidate_action in transitional and current_action != candidate_action:
            required += TRANSITION_EXTRA_FRAMES
        if current_action == sit_key and candidate_action == walk_key:
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
        fall_key = ACTION_FALL
        alert_key = action_key("BÁO ĐỘNG")

        if raw_action == alert_key:
            st.committed_action = alert_key
            st.pending_action = None
            st.pending_count = 0
            st.pending_since = None
            st.last_action_change = now
            st.action_window.append(raw_action)
            return alert_key

        if raw_action == fall_key and confidence >= HIGH_CONF_SWITCH:
            st.committed_action = fall_key
            st.pending_action = None
            st.pending_count = 0
            st.pending_since = None
            st.last_action_change = now
            st.action_window.append(raw_action)
            return fall_key

        st.action_window.append(raw_action)

        if st.seen_frames < MIN_FRAMES_BEFORE_DECISION:
            return "ÄANG PHÃ‚N TÃCH"

        # Bá» phiáº¿u theo Ä‘oáº¡n ngáº¯n thá»i gian, Æ°u tiÃªn cÃ¡c frame gáº§n hiá»‡n táº¡i.
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

        if st.committed_action in ("UNKNOWN", "ÄANG PHÃ‚N TÃCH"):
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
        if transition_locked and st.committed_action in (ACTION_STAND, ACTION_WALK, ACTION_SIT):
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
        locomotion = {ACTION_STAND, ACTION_WALK, ACTION_RUN}
        if (
            st.committed_action in locomotion
            and voted_action in locomotion
            and st.committed_action != voted_action
        ):
            min_agree_ratio = min(
                min_agree_ratio,
                0.50 if decision_confidence >= HIGH_CONF_SWITCH else 0.54,
            )
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
        if self.running or (self.worker_thread is not None and self.worker_thread.is_alive()):
            return

        source, source_type = self._resolve_source()
        if source is None:
            return

        self.source = source
        self.source_type = source_type
        self.loop_video = bool(self.loop_var.get())
        self.frame_index = 0
        self._reset_detection_state()
        with self.seek_lock:
            self.seek_pending = None
        self.current_frame_idx = 0
        self.cap = open_capture(self.source, self.source_type)

        if not self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
            self._set_status("Không mở được nguồn")
            messagebox.showerror("Lỗi mở nguồn", f"Không mở được nguồn:\n{self.source}")
            return

        # Seek bar setup for file sources.
        if self.source_type == "file":
            try:
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            except Exception:
                self.total_frames = 0
            try:
                self.video_fps = float(self.cap.get(cv2.CAP_PROP_FPS))
            except Exception:
                self.video_fps = 0.0
            if not np.isfinite(self.video_fps) or self.video_fps <= 1e-3:
                self.video_fps = 0.0
            try:
                self.seek_scale.configure(state="normal")
                self.seek_scale.configure(to=max(0, self.total_frames - 1))
                self.updating_seek = True
                self.seek_var.set(0)
                self.updating_seek = False
                self._update_seek_label(0, self.total_frames)
            except Exception:
                pass
        else:
            self.total_frames = 0
            self.video_fps = 0.0
            try:
                self.seek_scale.configure(state="disabled")
                self.seek_scale.configure(to=0)
                self.updating_seek = True
                self.seek_var.set(0)
                self.updating_seek = False
                self._update_seek_label(0, 0)
            except Exception:
                pass

        self.stop_event.clear()
        self.running = True
        self._set_status("Đang chạy...")
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.running = False
        self._set_status("Đã dừng")
        thread = self.worker_thread
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        if thread is None or not thread.is_alive():
            self.worker_thread = None

    def on_close(self):
        self.stop()
        self.destroy()

    def _reconnect_capture(self):
        if self.stop_event.is_set():
            return
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self._reset_detection_state()
        time.sleep(0.4)
        self.cap = open_capture(self.source, self.source_type)

    def _worker_loop(self):
        while not self.stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                if self.stop_event.is_set():
                    break
                if self.source_type in ("rtsp", "webcam"):
                    self._reconnect_capture()
                    if self.cap is None or not self.cap.isOpened():
                        time.sleep(0.2)
                        continue
                else:
                    break

            # Apply pending seek (file video only).
            if self.source_type == "file":
                pending = None
                with self.seek_lock:
                    pending = self.seek_pending
                    self.seek_pending = None
                if pending is not None:
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(pending))
                    except Exception:
                        pass
                    self._reset_detection_state()
                    self.current_frame_idx = int(pending)

            grabbed, frame = self.cap.read()
            if not grabbed or frame is None:
                if self.stop_event.is_set():
                    break
                if self.source_type == "file" and self.loop_video:
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        self._reconnect_capture()
                    self._reset_detection_state()
                    self.current_frame_idx = 0
                    continue

                if self.source_type in ("rtsp", "webcam"):
                    self._reconnect_capture()
                    continue

                break

            # Update current frame index for UI seek bar.
            if self.source_type == "file":
                try:
                    self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                except Exception:
                    pass

            annotated = self._process_frame(frame)
            with self.frame_lock:
                self.latest_frame = annotated

            time.sleep(0.001)

        self.running = False
        self._set_status("Đã dừng")

    def _classify_person_fallback(
        self,
        st: PersonState,
        now: float,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        kp_xy,
        kp_cf,
        pose_min_conf: float,
        frame_w: int | None = None,
        frame_h: int | None = None,
        track_id: int = -1,
    ):
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        bbox_aspect = float(w / (h + 1e-6))
        center = (float(x1 + x2) * 0.5, float(y1 + y2) * 0.5)
        prev_center = tuple(st.prev_center) if st.prev_center is not None else None

        if prev_center is None:
            rel_speed = 0.0
        else:
            rel_speed = float(np.hypot(center[0] - prev_center[0], center[1] - prev_center[1]) / (h + 1e-6))

        if rel_speed >= SIGNIFICANT_MOTION_REL_THRES:
            st.last_significant_motion = now

        posture = "LYING" if bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN else ("TRANSITION" if bbox_aspect >= 0.96 else "NORMAL")
        lower_valid = count_valid_points(kp_xy, kp_cf, [11, 12, 13, 14, 15, 16], min_conf=max(0.05, pose_min_conf * 0.90))
        upper_valid = count_valid_points(kp_xy, kp_cf, [0, 1, 2, 5, 6, 7, 8, 9, 10], min_conf=max(0.05, pose_min_conf * 0.85))
        head_valid = count_valid_points(kp_xy, kp_cf, [0, 1, 2], min_conf=max(0.05, pose_min_conf * 0.85))
        edge_flags = bbox_edge_flags((x1, y1, x2, y2), frame_w, frame_h)
        fall_pose = fall_ground_signature(kp_xy, kp_cf, pose_min_conf, (x1, y1, x2, y2), frame_h)
        partial_body = upper_valid < 3 or (head_valid == 0 and lower_valid < 3)
        body_inside_frame = bool(not edge_flags["touch_lr"] and not edge_flags["touch_top"])
        head_point_y = float(y1 + h * 0.18)
        hip_point_y = float(y1 + h * 0.66)
        head_low_rel = float(head_point_y / max(1.0, float(frame_h or h)))
        hip_low_rel = float(hip_point_y / max(1.0, float(frame_h or h)))
        body_stack_rel = max(0.0, hip_low_rel - head_low_rel)
        grounded_relaxed = bool(
            body_inside_frame
            and lower_valid >= 3
            and upper_valid >= 2
            and fall_pose["point_count"] >= max(3, FALL_FLOOR_MIN_POINTS - 1)
            and fall_pose["x_span_rel"] >= FALL_FLOOR_X_SPAN_MIN * 0.86
            and fall_pose["lowest_rel"] >= FALL_FLOOR_LOWEST_MIN - 0.04
            and head_low_rel >= FALL_HEAD_LOW_MIN - 0.02
            and hip_low_rel >= FALL_HIP_LOW_MIN - 0.04
            and body_stack_rel <= FALL_RELAXED_STACK_MAX
            and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 0.92
        )
        grounded_lying = bool(
            body_inside_frame
            and lower_valid >= 4
            and head_valid >= 1
            and fall_pose["grounded"]
            and head_low_rel >= FALL_HEAD_LOW_MIN
            and hip_low_rel >= FALL_HIP_LOW_MIN
            and body_stack_rel <= FALL_BODY_STACK_MAX
            and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 0.92
        )
        grounded_like = bool(grounded_lying or grounded_relaxed)
        if grounded_like and posture != "LYING":
            posture = "LYING"
        edge_occluded = bool(
            edge_flags["touch_lr"]
            or edge_flags["touch_top"]
            or (edge_flags["touch_bottom"] and partial_body and not grounded_like)
        )
        entry_like_motion = False
        if prev_center is not None and edge_flags["touch_lr"]:
            dx = float(center[0] - prev_center[0])
            dy = float(center[1] - prev_center[1])
            entry_like_motion = (
                abs(dx) >= abs(dy) * FALL_ENTRY_HORIZONTAL_RATIO
                and abs(dx) / max(1.0, float(w)) >= 0.05
            )
        upright_entry_signature = bool(
            posture == "LYING"
            and not grounded_like
            and (
                entry_like_motion
                or (st.seen_frames <= FALL_EDGE_GRACE_FRAMES + 6 and (edge_flags["touch_lr"] or partial_body))
            )
            and (head_low_rel < FALL_HEAD_LOW_MIN or body_stack_rel > FALL_BODY_STACK_MAX * 1.15)
        )
        bottom_entry_like = bool(
            edge_flags["touch_bottom"]
            and not grounded_like
            and st.seen_frames <= FALL_EDGE_GRACE_FRAMES + 8
            and (partial_body or rel_speed >= WALK_REL_THRES * 0.55)
        )
        upright_shape_signature = bool(
            posture == "LYING"
            and not grounded_like
            and upper_valid >= 3
            and body_stack_rel >= FALL_RELAXED_STACK_MAX * 0.82
            and head_low_rel < FALL_HEAD_LOW_MIN + 0.12
        )
        if upright_entry_signature or bottom_entry_like:
            posture = "TRANSITION" if bbox_aspect >= 0.95 else "NORMAL"
        elif upright_shape_signature:
            posture = "TRANSITION"
        if edge_occluded and (st.seen_frames <= FALL_EDGE_GRACE_FRAMES or partial_body or entry_like_motion):
            st.edge_guard_until = max(st.edge_guard_until, now + FALL_PARTIAL_SUPPRESS_SEC)
        if bottom_entry_like:
            st.edge_guard_until = max(st.edge_guard_until, now + FALL_PARTIAL_SUPPRESS_SEC * 1.35)
        if body_inside_frame and (not partial_body or grounded_like):
            st.last_full_body_time = now
        recent_full_body = bool(
            grounded_like
            or (
                st.last_full_body_time > 0.0
                and (now - float(st.last_full_body_time)) <= max(0.25, FALL_PARTIAL_SUPPRESS_SEC * 1.10)
            )
        )
        fall_guard_active = bool(
            not grounded_like
            and (
                now <= st.edge_guard_until
                or bottom_entry_like
                or upright_shape_signature
                or (edge_occluded and (partial_body or not recent_full_body))
            )
        )
        recent_fall_event = self._match_recent_fall_event(track_id, (x1, y1, x2, y2), center, float(h), now, bbox_aspect)
        recent_fall_match = bool(
            recent_fall_event is not None
            and body_inside_frame
            and not edge_flags["touch_lr"]
            and (posture in ("LYING", "TRANSITION") or grounded_like)
        )
        if recent_fall_match and (
            grounded_like
            or (
                posture == "LYING"
                and head_low_rel >= FALL_HEAD_LOW_MIN - 0.05
                and hip_low_rel >= FALL_HIP_LOW_MIN - 0.06
                and body_stack_rel <= FALL_RELAXED_STACK_MAX
            )
        ):
            memory_started = float(recent_fall_event.get("time", now))
            st.fall_started = memory_started if st.fall_started is None else min(float(st.fall_started), memory_started)
            st.last_full_body_time = now
            fall_guard_active = False
        if posture == "LYING" and fall_guard_active and not recent_fall_match:
            posture = "TRANSITION" if rel_speed >= WALK_REL_THRES * 0.55 or entry_like_motion else "NORMAL"

        if (grounded_like or recent_fall_match) and posture == "LYING" and not fall_guard_active:
            raw_action = fall_key = ACTION_FALL
            confidence = 0.74 if grounded_like else 0.66
        elif posture == "LYING" and not fall_guard_active:
            raw_action = ACTION_FALL
            confidence = 0.56
        elif rel_speed >= RUN_REL_THRES:
            raw_action = ACTION_RUN
            confidence = 0.50
        elif rel_speed >= WALK_REL_THRES * 0.85:
            raw_action = ACTION_WALK
            confidence = 0.46
        elif st.committed_action in (ACTION_STAND, ACTION_WALK, ACTION_RUN):
            raw_action = st.committed_action
            confidence = 0.34
        else:
            raw_action = ACTION_STAND
            confidence = 0.32

        scores = {action_name: 0.0 for action_name in ACTIONS}
        stand_key = ACTION_STAND
        fall_key = ACTION_FALL
        walk_key = ACTION_WALK
        run_key = ACTION_RUN
        alert_key = action_key("BÁO ĐỘNG")
        scores[raw_action] = 1.0
        action = self._stabilize_action(
            st,
            raw_action,
            scores,
            now,
            confidence=confidence,
            transition_locked=False,
        )
        if action == fall_key or (grounded_like and posture == "LYING" and not fall_guard_active):
            self._remember_recent_fall_event(
                track_id,
                (x1, y1, x2, y2),
                center,
                float(h),
                now,
                confidence,
                grounded=grounded_like,
            )

        head_candidates = [
            point_from_kp(kp_xy, kp_cf, idx, min_conf=max(0.05, pose_min_conf * 0.85))
            for idx in (0, 1, 2)
        ]
        head_candidates = [p for p in head_candidates if p is not None]
        head_point = np.mean(np.stack(head_candidates), axis=0) if head_candidates else np.array([center[0], y1 + h * 0.18], dtype=np.float32)

        shoulders = [
            point_from_kp(kp_xy, kp_cf, idx, min_conf=max(0.06, pose_min_conf * 0.90))
            for idx in (5, 6)
        ]
        shoulders = [p for p in shoulders if p is not None]
        shoulder_mid = np.mean(np.stack(shoulders), axis=0) if shoulders else np.array([center[0], y1 + h * 0.30], dtype=np.float32)

        hips = [
            point_from_kp(kp_xy, kp_cf, idx, min_conf=max(0.06, pose_min_conf * 0.90))
            for idx in (11, 12)
        ]
        hips = [p for p in hips if p is not None]
        hip_mid = np.mean(np.stack(hips), axis=0) if hips else np.array([center[0], y1 + h * 0.66], dtype=np.float32)
        torso_mid = (shoulder_mid + hip_mid) * 0.5

        st.prev_center = center
        st.prev_height = float(h)
        st.prev_angle = 0.0 if posture == "NORMAL" else 45.0
        st.prev_posture = posture
        st.center_hist.append((float(center[0]), float(center[1])))
        st.bbox_hist.append((int(x1), int(y1), int(x2), int(y2)))
        st.speed_hist.append(rel_speed)
        st.height_hist.append(float(h))

        color_map = {
            "Äá»¨NG": (0, 255, 0),
            "ÄI Bá»˜": (0, 255, 0),
            "CHáº Y": (0, 255, 0),
            "TÃ‰": (0, 255, 255),
            "ÄANG PHÃ‚N TÃCH": (220, 220, 220),
            "UNKNOWN": (255, 255, 255),
        }

        return {
            "action": action,
            "color": color_map.get(action, (0, 255, 0)),
            "danger": False,
            "save_frame": False,
            "interaction": {
                "head": tuple(head_point.tolist()),
                "torso_mid": tuple(torso_mid.tolist()),
                "shoulder_mid": tuple(shoulder_mid.tolist()),
                "left_wrist": None,
                "right_wrist": None,
                "left_ankle": None,
                "right_ankle": None,
                "left_elbow": None,
                "right_elbow": None,
                "left_shoulder": None,
                "right_shoulder": None,
                "hip_mid": tuple(hip_mid.tolist()),
                "left_elbow_angle": None,
                "right_elbow_angle": None,
                "left_wrist_speed": 0.0,
                "right_wrist_speed": 0.0,
                "motion_score": float(rel_speed),
                "punch_detected": False,
                "kick_detected": False,
                "guard_ratio": 0.0,
                "combat_energy": 0.0,
                "combat_move": False,
                "center": center,
                "center_velocity": (
                    float(center[0] - prev_center[0]) if prev_center is not None else 0.0,
                    float(center[1] - prev_center[1]) if prev_center is not None else 0.0,
                ),
                "height": float(h),
                "posture": posture,
                "is_sitting": False,
                "lower_valid": int(lower_valid),
                "upper_valid": int(upper_valid),
                "head_valid": int(head_valid),
                "full_body_visible": bool(body_inside_frame and (not partial_body or grounded_like)),
                "edge_guard": bool(fall_guard_active),
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "keypoints_dict": {
                    "head": tuple(head_point.tolist()),
                    "neck": tuple(shoulder_mid.tolist()),
                    "left_shoulder": None,
                    "right_shoulder": None,
                    "left_elbow": None,
                    "right_elbow": None,
                    "left_wrist": None,
                    "right_wrist": None,
                    "left_hip": None,
                    "right_hip": None,
                    "left_knee": None,
                    "right_knee": None,
                    "left_ankle": None,
                    "right_ankle": None,
                },
                "guard_pose": False,
                "hold_pose": False,
            },
            "metrics": {
                "angle": 0.0 if posture == "NORMAL" else 45.0,
                "speed": float(rel_speed),
                "ankle_motion": 0.0,
                "motion_score": float(rel_speed),
                "knee": None,
                "leg_ext": None,
                "posture": posture,
                "sitting_score": 0.0,
                "height": float(h),
                "bbox_aspect": bbox_aspect,
                "hip_knee_rel": None,
                "hip_vspeed": 0.0,
                "ankle_span": None,
                "gait_alt_ratio": 0.0,
                "gait_cadence_walk": 0.0,
                "gait_cadence_run": 0.0,
                "avg_knee_flex": 0.0,
                "knee_flex_trend": 0.0,
                "hip_knee_rel_trend": 0.0,
                "knee_diff_osc": 0.0,
                "wrist_speed": 0.0,
                "wrist_accel": 0.0,
                "ankle_speed": 0.0,
                "ankle_accel": 0.0,
                "elbow_ext": 0.0,
                "knee_ext": 0.0,
                "guard_score": 0.0,
                "guard_ratio": 0.0,
                "combat_energy": 0.0,
                "combat_move": False,
                "hold_ratio": 0.0,
                "hold_persist": False,
                "punch_detected": False,
                "kick_detected": False,
                "seated_shape_hint": False,
                "sit_down_intent": False,
                "stand_up_intent": False,
                "transition_phase": st.transition_phase,
                "decision_confidence": float(confidence),
                "raw_action": raw_action,
                "edge_guard": bool(fall_guard_active),
                "full_body_visible": bool(body_inside_frame and (not partial_body or grounded_like)),
                "recent_fall_match": bool(recent_fall_match),
                "grounded_fall": bool(grounded_like),
            },
        }

    def _classify_person(
        self,
        st: PersonState,
        now: float,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        kp_xy,
        kp_cf,
        pose_min_conf: float = 0.15,
        frame_w: int | None = None,
        frame_h: int | None = None,
        track_id: int = -1,
    ):
        """
        PhÃ¢n loáº¡i hÃ nh vi theo pose + motion + state machine.
        Tráº£ vá» dict: {action, color, danger, save_frame}
        """
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        bbox_aspect = float(w / (h + 1e-6))
        prev_center = tuple(st.prev_center) if st.prev_center is not None else None

        angle, center, shoulder_mid, hip_mid = torso_angle_and_center(kp_xy, kp_cf, min_conf=pose_min_conf)
        if angle is None or center is None:
            return self._classify_person_fallback(
                st,
                now,
                x1,
                y1,
                x2,
                y2,
                kp_xy,
                kp_cf,
                pose_min_conf,
                frame_w=frame_w,
                frame_h=frame_h,
                track_id=track_id,
            )

        # current keypoints for limbs
        nose = point_from_kp(kp_xy, kp_cf, 0, min_conf=pose_min_conf)
        leye = point_from_kp(kp_xy, kp_cf, 1, min_conf=pose_min_conf)
        reye = point_from_kp(kp_xy, kp_cf, 2, min_conf=pose_min_conf)
        ls = point_from_kp(kp_xy, kp_cf, 5, min_conf=pose_min_conf)
        rs = point_from_kp(kp_xy, kp_cf, 6, min_conf=pose_min_conf)
        le = point_from_kp(kp_xy, kp_cf, 7, min_conf=pose_min_conf)
        re = point_from_kp(kp_xy, kp_cf, 8, min_conf=pose_min_conf)
        lw = point_from_kp(kp_xy, kp_cf, 9, min_conf=pose_min_conf)
        rw = point_from_kp(kp_xy, kp_cf, 10, min_conf=pose_min_conf)
        lh = point_from_kp(kp_xy, kp_cf, 11, min_conf=pose_min_conf)
        rh = point_from_kp(kp_xy, kp_cf, 12, min_conf=pose_min_conf)
        lk = point_from_kp(kp_xy, kp_cf, 13, min_conf=pose_min_conf)
        rk = point_from_kp(kp_xy, kp_cf, 14, min_conf=pose_min_conf)
        la = point_from_kp(kp_xy, kp_cf, 15, min_conf=pose_min_conf)
        ra = point_from_kp(kp_xy, kp_cf, 16, min_conf=pose_min_conf)

        lower_valid = count_valid_points(kp_xy, kp_cf, [11, 12, 13, 14, 15, 16], min_conf=max(0.08, pose_min_conf))
        upper_valid = count_valid_points(kp_xy, kp_cf, [0, 1, 2, 5, 6, 7, 8, 9, 10], min_conf=max(0.08, pose_min_conf * 0.95))
        head_valid = count_valid_points(kp_xy, kp_cf, [0, 1, 2], min_conf=max(0.08, pose_min_conf * 0.90))

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
        if prev_center is None:
            abs_speed_px = 0.0
        else:
            dx = center[0] - prev_center[0]
            dy = center[1] - prev_center[1]
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
        st.center_hist.append((float(center[0]), float(center[1])))
        st.bbox_hist.append((int(x1), int(y1), int(x2), int(y2)))
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

        box_motion = bbox_motion_signature(st.bbox_hist, frame_w=frame_w, frame_h=frame_h)
        bbox_aspect_trend = float(box_motion["aspect_trend"])
        bbox_area_growth = float(box_motion["area_growth"])
        bbox_area_var = float(box_motion["area_var"])

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
        travel_signature = trajectory_motion_signature(
            st.center_hist,
            smooth_height if smooth_height > 0.0 else float(h),
        )
        travel_disp_rel = float(travel_signature["disp_rel"])
        travel_path_rel = float(travel_signature["path_rel"])
        travel_linearity = float(travel_signature["linearity"])
        directional_walk_support = (
            posture != "LYING"
            and travel_path_rel >= WALK_REL_THRES * 1.35
            and travel_disp_rel >= WALK_REL_THRES * 1.05
            and travel_linearity >= 0.44
            and motion_score >= WALK_REL_THRES * 0.60
        )
        sustained_run_support = directional_walk_support and motion_score >= RUN_REL_THRES * 0.84
        movement_cancels_sit = directional_walk_support and motion_score >= WALK_REL_THRES * 0.65
        if movement_cancels_sit:
            seated_shape_hint = False
            sit_geometry_strong = False
            sitting_score = max(0, sitting_score - 3)

        is_sitting = (
            posture != "LYING"
            and not movement_cancels_sit
            and (
                (sitting_score >= 6 and motion_score < WALK_REL_THRES)
                or sit_geometry_strong
                or seated_shape_hint
                or (st.committed_action == "NGá»’I" and sitting_score >= 5 and motion_score < RUN_REL_THRES * 0.75)
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

        edge_flags = bbox_edge_flags((x1, y1, x2, y2), frame_w, frame_h)
        fall_pose = fall_ground_signature(kp_xy, kp_cf, pose_min_conf, (x1, y1, x2, y2), frame_h)
        partial_body = bool(upper_valid < 3 or (head_valid == 0 and lower_valid < 3))
        body_inside_frame = bool(not edge_flags["touch_lr"] and not edge_flags["touch_top"])
        shoulder_low_rel = float(shoulder_mid[1] / max(1.0, float(frame_h or h))) if shoulder_mid is not None else 0.0
        head_low_rel = float(head_point[1] / max(1.0, float(frame_h or h))) if head_point is not None else 0.0
        hip_low_rel = float(hip_mid[1] / max(1.0, float(frame_h or h))) if hip_mid is not None else 0.0
        body_stack_rel = max(0.0, hip_low_rel - head_low_rel) if head_point is not None and hip_mid is not None else 1.0
        grounded_body_low = bool(
            head_low_rel >= FALL_HEAD_LOW_MIN
            and hip_low_rel >= FALL_HIP_LOW_MIN
            and body_stack_rel <= FALL_BODY_STACK_MAX
        )
        grounded_relaxed_signature = bool(
            body_inside_frame
            and lower_valid >= 3
            and upper_valid >= 2
            and fall_pose["point_count"] >= max(3, FALL_FLOOR_MIN_POINTS - 1)
            and fall_pose["x_span_rel"] >= FALL_FLOOR_X_SPAN_MIN * 0.88
            and fall_pose["lowest_rel"] >= FALL_FLOOR_LOWEST_MIN - 0.04
            and shoulder_low_rel >= FALL_RELAXED_SHOULDER_LOW_MIN
            and hip_low_rel >= FALL_RELAXED_HIP_LOW_MIN
            and body_stack_rel <= FALL_RELAXED_STACK_MAX
            and (posture == "LYING" or bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 0.90)
        )
        grounded_lying_signature = bool(
            body_inside_frame
            and lower_valid >= 4
            and head_valid >= 1
            and fall_pose["grounded"]
            and grounded_body_low
            and (
                bbox_aspect_trend >= FALL_ASPECT_TREND_MIN
                or bbox_area_var >= 0.00012
                or bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 1.08
            )
            and (posture == "LYING" or bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 0.92)
        )
        grounded_fall_signature = bool(grounded_lying_signature or grounded_relaxed_signature)
        if grounded_fall_signature and posture != "LYING":
            posture = "LYING"
        full_body_visible = bool(
            body_inside_frame
            and head_valid >= 1
            and upper_valid >= 3
            and (lower_valid >= 3 or grounded_fall_signature)
        )
        edge_occluded = bool(
            edge_flags["touch_lr"]
            or edge_flags["touch_top"]
            or (edge_flags["touch_bottom"] and partial_body and not grounded_fall_signature)
        )
        entry_like_motion = False
        if prev_center is not None and edge_flags["touch_lr"]:
            dx = float(center[0] - prev_center[0])
            dy = float(center[1] - prev_center[1])
            entry_like_motion = (
                abs(dx) >= abs(dy) * FALL_ENTRY_HORIZONTAL_RATIO
                and abs(dx) / max(1.0, float(h)) >= WALK_REL_THRES * 0.75
            )
        upright_entry_signature = bool(
            posture == "LYING"
            and not grounded_fall_signature
            and (
                entry_like_motion
                or bbox_area_growth >= FALL_ENTRY_GROWTH_MIN
                or (st.seen_frames <= FALL_EDGE_GRACE_FRAMES + 6 and (edge_flags["touch_lr"] or partial_body))
            )
            and (
                not grounded_body_low
                or head_low_rel < FALL_HEAD_LOW_MIN
                or body_stack_rel > FALL_BODY_STACK_MAX * 1.15
                or fall_pose["y_span_rel"] > FALL_FLOOR_Y_SPAN_MAX * 1.24
            )
        )
        bottom_entry_like = bool(
            edge_flags["touch_bottom"]
            and not grounded_fall_signature
            and st.seen_frames <= FALL_EDGE_GRACE_FRAMES + 8
            and (
                partial_body
                or motion_score >= WALK_REL_THRES * 0.55
                or bbox_area_growth >= FALL_ENTRY_GROWTH_MIN * 0.94
            )
        )
        partial_lying_without_ground = bool(
            posture == "LYING"
            and not grounded_fall_signature
            and not full_body_visible
            and (
                not grounded_body_low
                or lower_valid < 4
                or head_valid == 0
            )
        )
        false_fall_pose = bool(
            posture == "LYING"
            and not grounded_fall_signature
            and not grounded_body_low
            and bbox_aspect <= FALL_HORIZONTAL_ASPECT_MIN * 1.06
            and body_stack_rel > FALL_BODY_STACK_MAX * 1.20
            and (motion_score >= WALK_REL_THRES * 0.65 or bbox_area_growth >= FALL_ENTRY_GROWTH_MIN)
        )
        upright_torso_signature = bool(
            posture == "LYING"
            and not grounded_fall_signature
            and smooth_angle <= LYING_ANGLE - 12.0
            and upper_valid >= 3
            and body_stack_rel >= FALL_RELAXED_STACK_MAX * 0.82
            and fall_pose["y_span_rel"] >= FALL_FLOOR_Y_SPAN_MAX * 0.88
        )
        travel_false_fall = bool(
            posture == "LYING"
            and not grounded_fall_signature
            and directional_walk_support
            and smooth_angle <= LYING_ANGLE - 10.0
            and body_stack_rel >= FALL_RELAXED_STACK_MAX * 0.78
        )
        if upright_entry_signature or bottom_entry_like:
            posture = "TRANSITION" if bbox_aspect >= 0.95 else "NORMAL"
        elif false_fall_pose or upright_torso_signature or travel_false_fall:
            posture = "TRANSITION"
        elif partial_lying_without_ground:
            posture = "TRANSITION"
        if edge_occluded and (st.seen_frames <= FALL_EDGE_GRACE_FRAMES or partial_body or entry_like_motion):
            st.edge_guard_until = max(st.edge_guard_until, now + FALL_PARTIAL_SUPPRESS_SEC)
        if bottom_entry_like or travel_false_fall:
            st.edge_guard_until = max(st.edge_guard_until, now + FALL_PARTIAL_SUPPRESS_SEC * 1.40)
        if full_body_visible or grounded_fall_signature:
            st.last_full_body_time = now
        recent_full_body = bool(
            grounded_fall_signature
            or (
                st.last_full_body_time > 0.0
                and (now - float(st.last_full_body_time)) <= max(0.25, FALL_PARTIAL_SUPPRESS_SEC * 1.10)
            )
        )
        fall_guard_active = bool(
            not grounded_fall_signature
            and (
                now <= st.edge_guard_until
                or bottom_entry_like
                or upright_torso_signature
                or travel_false_fall
                or (edge_occluded and (partial_body or not recent_full_body))
            )
        )
        recent_fall_event = self._match_recent_fall_event(track_id, (x1, y1, x2, y2), center, float(h), now, bbox_aspect)
        recent_fall_match = bool(
            recent_fall_event is not None
            and body_inside_frame
            and not edge_flags["touch_lr"]
            and (posture in ("LYING", "TRANSITION") or grounded_fall_signature)
        )
        if recent_fall_match and (
            grounded_fall_signature
            or (
                posture == "LYING"
                and head_low_rel >= FALL_HEAD_LOW_MIN - 0.05
                and hip_low_rel >= FALL_HIP_LOW_MIN - 0.05
                and body_stack_rel <= FALL_RELAXED_STACK_MAX
            )
        ):
            memory_started = float(recent_fall_event.get("time", now))
            st.fall_started = memory_started if st.fall_started is None else min(float(st.fall_started), memory_started)
            st.last_full_body_time = now
            fall_guard_active = False
        center_velocity = (
            float(center[0] - prev_center[0]) if prev_center is not None else 0.0,
            float(center[1] - prev_center[1]) if prev_center is not None else 0.0,
        )

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
        # Fast hand motion can support a guard/fight pose.
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
                # REQUIREMENT: bbox must be horizontal to start fall detection.
                if not fall_guard_active and (recent_full_body or grounded_fall_signature or recent_fall_match) and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN and (
                    motion_score >= WALK_REL_THRES
                    or angle_drop >= 18.0
                    or rel_height_change > 0.12
                    or grounded_fall_signature
                    or recent_fall_match
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
        if fall_guard_active and motion_score >= STILL_REL_THRES:
            st.fall_started = None
            if posture != "LYING":
                st.lying_since = None

        scores = {action_name: 0.0 for action_name in ACTIONS}
        stand_key = ACTION_STAND
        fall_key = ACTION_FALL
        walk_key = ACTION_WALK
        run_key = ACTION_RUN
        alert_key = action_key("BÁO ĐỘNG")

        if posture == "NORMAL":
            scores["Äá»¨NG"] += 3
        if smooth_angle < 25 and bbox_aspect < 1.05:
            scores["Äá»¨NG"] += 2
        if knee_angle_avg is not None and knee_angle_avg > 160:
            scores["Äá»¨NG"] += 1
        if leg_extension_avg is not None and leg_extension_avg > 0.95:
            scores["Äá»¨NG"] += 1
        if motion_score < 0.006:
            scores["Äá»¨NG"] += 2
        if smooth_hip_knee_rel is not None and smooth_hip_knee_rel >= STAND_HIP_KNEE_REL_MIN:
            scores["Äá»¨NG"] += 1
        if avg_knee_flex < 14.0:
            scores["Äá»¨NG"] += 1
        if directional_walk_support:
            scores["Äá»¨NG"] -= 1.2
        if lower_valid < 3 and bbox_aspect >= 0.95 and motion_score < SIT_MAX_REL_SPEED * 1.1:
            scores["Äá»¨NG"] -= 1.8
        if lower_valid < 2 and smooth_hip_knee_rel is None and bbox_aspect >= 0.98:
            scores["Äá»¨NG"] -= 1.3
        if stand_up_intent:
            scores["Äá»¨NG"] += 1.4
        if st.transition_phase == "TO_STAND":
            scores["Äá»¨NG"] += 0.8
        if sit_geometry_strong:
            scores["Äá»¨NG"] -= 2.6
        if seated_shape_hint:
            scores["Äá»¨NG"] -= 2.2

        if 0.012 <= motion_score < RUN_REL_THRES:
            scores["ÄI Bá»˜"] += 3
        if posture == "NORMAL" and motion_score >= WALK_REL_THRES:
            scores["ÄI Bá»˜"] += 1
        if smooth_angle < 45 and bbox_aspect < 1.3:
            scores["ÄI Bá»˜"] += 1
        if motion_score >= SIGNIFICANT_MOTION_REL_THRES:
            scores["ÄI Bá»˜"] += 1
        if gait_walk_ready:
            scores["ÄI Bá»˜"] += 3
        if directional_walk_support:
            scores["ÄI Bá»˜"] += 2.4
        if smooth_ankle_span is not None and smooth_ankle_span > 0.10:
            scores["ÄI Bá»˜"] += 1
        if gait_cadence_walk >= 0.35:
            scores["ÄI Bá»˜"] += 1.8
        if travel_linearity >= 0.56 and travel_path_rel >= WALK_REL_THRES * 1.75:
            scores["ÄI Bá»˜"] += 0.8
        if st.transition_phase == "TO_STAND" and motion_score >= WALK_REL_THRES * 0.8:
            scores["ÄI Bá»˜"] += 1.0

        if motion_score >= RUN_REL_THRES:
            scores["CHáº Y"] += 4
        if motion_score >= RUN_REL_THRES * 1.2:
            scores["CHáº Y"] += 1
        if posture == "NORMAL" and motion_score >= RUN_REL_THRES:
            scores["CHáº Y"] += 1
        if gait_run_ready:
            scores["CHáº Y"] += 2
        if sustained_run_support:
            scores["CHáº Y"] += 1.5
        if smooth_ankle_motion >= RUN_REL_THRES * 0.9:
            scores["CHáº Y"] += 1
        if gait_cadence_run >= 0.85:
            scores["CHáº Y"] += 1.8

        if is_sitting:
            scores["NGá»’I"] += 4
        if knee_angle_avg is not None and knee_angle_avg < SIT_KNEE_MAX:
            scores["NGá»’I"] += 1
        if leg_extension_avg is not None and leg_extension_avg < SIT_LEG_EXT_MAX:
            scores["NGá»’I"] += 1
        if SIT_ANGLE_MIN < smooth_angle < SIT_ANGLE_MAX:
            scores["NGá»’I"] += 1
        if 0.70 <= bbox_aspect <= 1.45:
            scores["NGá»’I"] += 1
        if motion_score < SIT_MAX_REL_SPEED:
            scores["NGá»’I"] += 1
        if smooth_hip_knee_rel is not None and smooth_hip_knee_rel < SIT_HIP_KNEE_REL_MAX:
            scores["NGá»’I"] += 2
        if avg_knee_flex >= 22.0:
            scores["NGá»’I"] += 1
        if sit_down_intent:
            scores["NGá»’I"] += 1.7
        if st.transition_phase == "TO_SIT":
            scores["NGá»’I"] += 1.0
        if hip_knee_rel_trend <= -0.0018:
            scores["NGá»’I"] += 0.7
        if sit_geometry_strong:
            scores["NGá»’I"] += 2.0
        if seated_shape_hint:
            scores["NGá»’I"] += 1.8
        if st.committed_action == "NGá»’I" and not stand_up_intent:
            scores["NGá»’I"] += 1.1
        if movement_cancels_sit:
            scores["NGá»’I"] -= 2.6

        # REQUIREMENT: only score "TÃ‰" when bbox is horizontal enough.
        if not fall_guard_active and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN:
            if posture == "LYING":
                scores["TÃ‰"] += 4
            if smooth_angle >= LYING_ANGLE:
                scores["TÃ‰"] += 2
            if bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN:
                scores["TÃ‰"] += 1
        if grounded_fall_signature:
            adjust_action_score(scores, "TÉ", 3.2)
            if fall_pose["y_span_rel"] <= FALL_FLOOR_Y_SPAN_MAX * 0.92:
                adjust_action_score(scores, "TÉ", 0.8)
            adjust_action_score(scores, "ĐỨNG", -2.4)
            adjust_action_score(scores, "ĐI BỘ", -1.9)
            adjust_action_score(scores, "CHẠY", -2.5)
        if recent_fall_match and posture in ("LYING", "TRANSITION") and not fall_guard_active:
            adjust_action_score(scores, "TÉ", 2.6 if grounded_fall_signature else 1.8)
            adjust_action_score(scores, "ĐỨNG", -1.4)
            adjust_action_score(scores, "ĐI BỘ", -1.1)
            adjust_action_score(scores, "CHẠY", -1.5)
        if st.fall_started is not None and not fall_guard_active:
            scores["TÃ‰"] += 3

        if False and fall_guard_active:
            scores["TÃƒâ€°"] -= 4.8
            if entry_like_motion:
                scores["Ã„ÂI BÃ¡Â»Ëœ"] += 1.0
                if rel_speed >= RUN_REL_THRES * 0.80:
                    scores["CHÃ¡ÂºÂ Y"] += 0.4

        if fall_guard_active:
            scores[fall_key] -= 4.8
            if entry_like_motion:
                scores[walk_key] += 1.0
                if rel_speed >= RUN_REL_THRES * 0.80:
                    scores[run_key] += 0.4

        if guard_pose:
            scores["CHIáº¾N Äáº¤U"] += 3.5  # Slightly increased
        if guard_ratio >= 0.60:  # Tightened from 0.52 - require sustained guard pose
            scores["CHIáº¾N Äáº¤U"] += 1.8
        if 18.0 <= avg_knee_flex <= 52.0:  # Tightened range from 12-58
            scores["CHIáº¾N Äáº¤U"] += 0.95
        if smooth_combat_energy >= 0.28:  # Tightened from 0.22
            scores["CHIáº¾N Äáº¤U"] += 1.3
        if punch_detected or kick_detected:
            scores["CHIáº¾N Äáº¤U"] += 1.6

        if combat_move:
            scores["DI CHUYá»‚N CHIáº¾N Äáº¤U"] += 3.2
        if guard_pose and motion_score >= WALK_REL_THRES * 0.8:
            scores["DI CHUYá»‚N CHIáº¾N Äáº¤U"] += 1.0
        if gait_walk_ready and guard_ratio < 0.45:
            scores["DI CHUYá»‚N CHIáº¾N Äáº¤U"] -= 0.8

        if punch_detected:
            scores["Äáº¤M"] += 5.2
        if max(left_wrist_speed, right_wrist_speed) >= PUNCH_WRIST_SPEED_MIN * 1.2:
            scores["Äáº¤M"] += 1.2
        if max(left_elbow_ext_speed, right_elbow_ext_speed) >= PUNCH_ELBOW_EXT_SPEED_MIN * 1.1:
            scores["Äáº¤M"] += 1.0
        if kick_detected:
            scores["ÄÃ"] += 5.4
        if max(left_ankle_speed, right_ankle_speed) >= KICK_ANKLE_SPEED_MIN * 1.18:
            scores["ÄÃ"] += 1.2
        if max(left_knee_ext_speed, right_knee_ext_speed) >= KICK_KNEE_EXT_SPEED_MIN * 1.12:
            scores["ÄÃ"] += 1.0

        if hold_persist:
            scores["Ã”M Váº¬T"] += 3.4
        if hold_pose:
            scores["Ã”M Váº¬T"] += 1.1
        if motion_score <= WALK_REL_THRES * 1.12:
            scores["Ã”M Váº¬T"] += 0.5
        if posture in ("NORMAL", "TRANSITION"):
            scores["Ã”M Váº¬T"] += 0.4
        if is_sitting or sit_geometry_strong:
            scores["Ã”M Váº¬T"] -= 2.4

        danger = False
        if (
            not fall_guard_active
            and recent_full_body
            and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN
            and (st.fall_started is not None or posture == "LYING")
            and st.last_significant_motion is not None
        ):
            no_motion_sec = now - st.last_significant_motion
            if no_motion_sec >= ALERT_AFTER_LIE_SEC and motion_score <= STILL_REL_THRES:
                danger = True

        if danger:
            raw_action = "BÃO Äá»˜NG"
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
            combat_actions = {"CHIáº¾N Äáº¤U", "DI CHUYá»‚N CHIáº¾N Äáº¤U", "Äáº¤M", "ÄÃ"}
            if committed == "NGá»’I":
                sit_locked = (now - float(st.last_action_change)) <= SIT_LOCK_SEC and not stand_up_intent
                probs["CHáº Y"] *= 0.52
                probs["ÄI Bá»˜"] *= 1.05 if stand_up_intent else (0.56 if sit_locked else 0.78)
                probs["Äá»¨NG"] *= 1.12 if stand_up_intent else (0.52 if sit_locked else 0.78)
                probs["Ã”M Váº¬T"] *= 0.48 if sit_locked else 0.62
                probs["NGá»’I"] *= 1.20 if sit_locked or seated_shape_hint else 1.05
            elif committed in ("Äá»¨NG", "ÄI Bá»˜"):
                probs["NGá»’I"] *= 1.18 if sit_down_intent else 0.72
            elif committed == "CHáº Y" and motion_score < RUN_REL_THRES * 0.78:
                probs["CHáº Y"] *= 0.74
            elif committed == "TÃ‰":
                if posture == "LYING":
                    probs["TÃ‰"] *= 1.20
                if stand_up_intent and motion_score >= WALK_REL_THRES:
                    probs["Äá»¨NG"] *= 1.08
            elif committed == "Ã”M Váº¬T":
                probs["Ã”M Váº¬T"] *= 1.18 if hold_persist else 0.78

            if committed in combat_actions:
                probs["CHIáº¾N Äáº¤U"] *= 1.08
                probs["DI CHUYá»‚N CHIáº¾N Äáº¤U"] *= 1.08 if combat_move else 0.88
                if not (punch_detected or kick_detected):
                    probs["Äáº¤M"] *= 0.76
                    probs["ÄÃ"] *= 0.76
                probs["NGá»’I"] *= 0.72
                probs["Ã”M Váº¬T"] *= 0.68
            else:
                if not (guard_pose or punch_detected or kick_detected):
                    probs["CHIáº¾N Äáº¤U"] *= 0.74
                    probs["DI CHUYá»‚N CHIáº¾N Äáº¤U"] *= 0.72
                if not punch_detected:
                    probs["Äáº¤M"] *= 0.68
                if not kick_detected:
                    probs["ÄÃ"] *= 0.68
                if not hold_persist:
                    probs["Ã”M Váº¬T"] *= 0.78

            if is_sitting or sit_geometry_strong or seated_shape_hint:
                probs["Ã”M Váº¬T"] *= 0.44
                probs["Äá»¨NG"] *= 0.64
                probs["NGá»’I"] *= 1.16
            if hold_posture_ok and hold_persist:
                probs["NGá»’I"] *= 0.76

            if st.transition_phase == "TO_SIT":
                probs["NGá»’I"] *= 1.22
                probs["CHáº Y"] *= 0.72
            elif st.transition_phase == "TO_STAND":
                probs["Äá»¨NG"] *= 1.14
                probs["ÄI Bá»˜"] *= 1.10

            if hold_persist:
                probs["Äáº¤M"] *= 0.66
                probs["ÄÃ"] *= 0.70

            if kick_detected:
                probs["Äáº¤M"] *= 0.86
            if punch_detected:
                probs["ÄÃ"] *= 0.88

            prob_sum = max(1e-8, float(sum(probs.values())))
            probs = {k: float(v / prob_sum) for k, v in probs.items()}

            sorted_probs = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
            raw_action = sorted_probs[0][0]
            decision_confidence = float(sorted_probs[0][1])
            second_prob = float(sorted_probs[1][1]) if len(sorted_probs) > 1 else 0.0
            prob_margin = decision_confidence - second_prob
            if (grounded_fall_signature or recent_fall_match) and posture == "LYING" and raw_action in (stand_key, walk_key, run_key):
                raw_action = fall_key
                decision_confidence = max(
                    decision_confidence,
                    0.74 if grounded_fall_signature else max(0.66, float(probs.get(fall_key, 0.46))),
                )
            if fall_guard_active and raw_action == fall_key:
                raw_action = walk_key if motion_score >= WALK_REL_THRES * 0.70 or entry_like_motion else stand_key
                decision_confidence = max(0.32, decision_confidence * 0.82)

            transition_locked = False
            if st.committed_action not in ("UNKNOWN", "ÄANG PHÃ‚N TÃCH", "BÃO Äá»˜NG"):
                event_override = (raw_action == "Äáº¤M" and punch_detected) or (raw_action == "ÄÃ" and kick_detected)
                if raw_action != st.committed_action and prob_margin < 0.08 and decision_confidence < HIGH_CONF_SWITCH and not event_override:
                    raw_action = st.committed_action
                    transition_locked = True

            if raw_action == "Äá»¨NG":
                if motion_score >= RUN_REL_THRES:
                    raw_action = "CHáº Y"
                elif motion_score >= WALK_REL_THRES:
                    raw_action = "ÄI Bá»˜"
                elif directional_walk_support:
                    raw_action = "CHáº Y" if sustained_run_support else "ÄI Bá»˜"
                    decision_confidence = max(decision_confidence, 0.56 if sustained_run_support else 0.52)

            if raw_action == "Äáº¤M" and not punch_detected and decision_confidence < VERY_HIGH_CONF_SWITCH:
                raw_action = "CHIáº¾N Äáº¤U" if (guard_pose or guard_ratio >= 0.60) else st.committed_action

            if raw_action == "ÄÃ" and not kick_detected and decision_confidence < VERY_HIGH_CONF_SWITCH:
                raw_action = "DI CHUYá»‚N CHIáº¾N Äáº¤U" if combat_move else st.committed_action

            if raw_action == "DI CHUYá»‚N CHIáº¾N Äáº¤U" and not combat_move and decision_confidence < HIGH_CONF_SWITCH:
                raw_action = "CHIáº¾N Äáº¤U" if (guard_pose or guard_ratio >= 0.60) else "ÄI Bá»˜"

            if raw_action == "CHIáº¾N Äáº¤U" and not guard_pose and not (punch_detected or kick_detected):
                if motion_score >= WALK_REL_THRES:
                    raw_action = "ÄI Bá»˜"
                elif motion_score < SIT_MAX_REL_SPEED and avg_knee_flex < 16.0:
                    raw_action = "Äá»¨NG"

            if raw_action == "Ã”M Váº¬T" and not hold_persist and decision_confidence < HIGH_CONF_SWITCH:
                raw_action = st.committed_action if st.committed_action not in ("UNKNOWN", "ÄANG PHÃ‚N TÃCH") else "Äá»¨NG"

            if raw_action in ("Äá»¨NG", "Ã”M Váº¬T") and is_sitting and not stand_up_intent:
                raw_action = "NGá»’I"
                transition_locked = True

            # Far/crowded seated rows often miss lower-body keypoints; keep them from bouncing to standing labels.
            if (
                raw_action in ("Äá»¨NG", "ÄI Bá»˜", "Ã”M Váº¬T")
                and lower_valid < 2
                and seated_shape_hint
                and motion_score < WALK_REL_THRES * 0.90
                and not stand_up_intent
            ):
                raw_action = "NGá»’I"
                transition_locked = True

            if (
                st.committed_action == "NGá»’I"
                and raw_action == "Äá»¨NG"
                and not stand_up_intent
                and motion_score < WALK_REL_THRES
                and seated_shape_hint
            ):
                raw_action = "NGá»’I"
                transition_locked = True

            # Transition guards for NGá»’I <-> Äá»¨NG / ÄI Bá»˜.
            if st.committed_action == "NGá»’I" and raw_action in ("Äá»¨NG", "ÄI Bá»˜"):
                if not stand_up_intent and avg_knee_flex >= 18.0:
                    raw_action = "NGá»’I"
                    transition_locked = True

            if st.committed_action in ("Äá»¨NG", "ÄI Bá»˜") and raw_action == "NGá»’I":
                if not sit_down_intent and motion_score > SIT_MAX_REL_SPEED * 0.9:
                    raw_action = st.committed_action
                    transition_locked = True

            if raw_action == "ÄI Bá»˜" and not gait_walk_ready and motion_score < RUN_REL_THRES:
                if avg_knee_flex < 12.0 and not directional_walk_support:
                    raw_action = "Äá»¨NG"

            sustain_fall = bool(
                posture == "LYING"
                and full_body_visible
                and not fall_guard_active
                and bbox_aspect >= FALL_HORIZONTAL_ASPECT_MIN * 0.96
                and (
                    grounded_fall_signature
                    or recent_fall_match
                    or st.committed_action == fall_key
                    or st.fall_started is not None
                )
            )
            if sustain_fall and raw_action != alert_key:
                raw_action = fall_key
                decision_confidence = max(
                    decision_confidence,
                    0.76 if grounded_fall_signature else (0.70 if recent_fall_match else 0.64),
                )

        action = self._stabilize_action(
            st,
            raw_action,
            scores,
            now,
            confidence=decision_confidence,
            transition_locked=transition_locked,
        )
        if action == fall_key or (posture == "LYING" and not fall_guard_active and (grounded_fall_signature or recent_fall_match)):
            self._remember_recent_fall_event(
                track_id,
                (x1, y1, x2, y2),
                center,
                float(h),
                now,
                decision_confidence,
                grounded=grounded_fall_signature,
            )

        if action == "NGá»’I" and st.transition_phase == "TO_SIT":
            st.transition_phase = "NONE"
            st.transition_since = None
        if action in ("Äá»¨NG", "ÄI Bá»˜", "CHáº Y") and st.transition_phase == "TO_STAND":
            st.transition_phase = "NONE"
            st.transition_since = None

        color_map = {
            "Äá»¨NG": (0, 255, 0),
            "ÄI Bá»˜": (0, 255, 0),
            "CHáº Y": (0, 255, 0),
            "NGá»’I": (0, 255, 0),
            "TÃ‰": (0, 255, 255),
            "CHIáº¾N Äáº¤U": (0, 170, 255),
            "DI CHUYá»‚N CHIáº¾N Äáº¤U": (0, 145, 255),
            "Äáº¤M": (0, 90, 255),
            "ÄÃ": (0, 60, 255),
            "Ã”M Váº¬T": (255, 200, 0),
            "Báº®T Náº T": (80, 40, 255),
            "BÃO Äá»˜NG": (0, 0, 255),
            "ÄANG PHÃ‚N TÃCH": (220, 220, 220),
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
                "guard_ratio": float(guard_ratio),
                "combat_energy": float(smooth_combat_energy),
                "combat_move": bool(combat_move),
                "center": (float(center[0]), float(center[1])),
                "center_velocity": center_velocity,
                "height": float(h),
                "posture": posture,
                "is_sitting": bool(is_sitting),
                "lower_valid": int(lower_valid),
                "upper_valid": int(upper_valid),
                "head_valid": int(head_valid),
                "full_body_visible": bool(full_body_visible),
                "edge_guard": bool(fall_guard_active),
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
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
                "travel_disp_rel": travel_disp_rel,
                "travel_path_rel": travel_path_rel,
                "travel_linearity": travel_linearity,
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
                "seated_shape_hint": seated_shape_hint,
                "sit_down_intent": sit_down_intent,
                "stand_up_intent": stand_up_intent,
                "transition_phase": st.transition_phase,
                "decision_confidence": decision_confidence,
                "raw_action": raw_action,
                "edge_guard": bool(fall_guard_active),
                "full_body_visible": bool(full_body_visible),
            },
        }

    def _detect_bullying_interactions(self, people_data, now: float):
        """Aggressor-only bullying detection for crowded scenes.

        Rules:
        - Báº®T Náº T: tÃºm Ä‘áº§u/tÃ³c, cháº¡m vÃ¹ng nháº¡y cáº£m, chá»‰ tháº³ng vÃ o máº·t.
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
            a_upper_valid = int(ia.get("upper_valid", 0))
            a_motion = float(ia.get("motion_score", 0.0))

            if a_center is None or a_posture == "LYING" or st.seen_frames < BULLY_MIN_SEEN_FRAMES:
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue
            if base_action in ("TÃ‰", "BÃO Äá»˜NG", "ÄANG PHÃ‚N TÃCH"):
                st.bully_hist.append(0.0)
                st.bully_warn_hist.append(0.0)
                st.bully_target_hist.append(-1)
                continue
            # CRITICAL: Skip if aggressor is sitting - bullying requires active standing/moving aggressor
            if a_is_sitting or (a_lower_valid < 1 and a_upper_valid < 3):
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
                v_upper_valid = int(iv.get("upper_valid", 0))
                if v_head is None or v_center is None or v_posture == "LYING":
                    continue
                # CRITICAL: Skip if victim sitting - bullying requires standing victim
                if BULLY_STANDING_ONLY and (v_is_sitting or (v_lower_valid < 1 and v_upper_valid < 3)):
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
                overlap_ok = x_overlap >= BULLY_MIN_X_OVERLAP or (
                    center_dist <= BULLY_CLOSE_CENTER_DIST and y_overlap >= BULLY_MIN_Y_OVERLAP * 0.82
                )
                if not overlap_ok or y_overlap < BULLY_MIN_Y_OVERLAP * 0.75:
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
                victim_motion = float(iv.get("motion_score", 0.0))
                victim_action = str(victim.get("action", ""))
                victim_guard_ratio = float(iv.get("guard_ratio", 0.0))
                victim_combat_energy = float(iv.get("combat_energy", 0.0))
                victim_combat_move = bool(iv.get("combat_move", False))
                victim_punch = bool(iv.get("punch_detected", False))
                victim_kick = bool(iv.get("kick_detected", False))
                mutual_combat = (
                    victim_punch
                    or victim_kick
                    or victim_combat_move
                    or victim_guard_ratio >= 0.48
                    or victim_combat_energy >= 0.18
                    or victim_action in ("CHIẾN ĐẤU", "DI CHUYỂN CHIẾN ĐẤU", "ĐẤM", "ĐÁ")
                )
                mutual_scale = 0.50 if mutual_combat and a_motion >= COMBAT_MOTION_MIN * 0.85 else 1.0
                pair_dir = unit_vector(v_center - np.array(a_center, dtype=np.float32))
                a_vel = recent_vector(st.center_hist) / max(1.0, pair_scale)
                v_vel = recent_vector(vst.center_hist) / max(1.0, pair_scale)
                victim_away_speed = projected_speed(v_vel, pair_dir)
                victim_toward_speed = max(0.0, -victim_away_speed)
                aggressor_forward_speed = projected_speed(a_vel, pair_dir)
                closing_speed = max(0.0, aggressor_forward_speed + victim_toward_speed)
                v_shoulder_mid = iv.get("shoulder_mid")
                shoulder_mid_np = np.array(v_shoulder_mid, dtype=np.float32) if v_shoulder_mid is not None else head_np

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
                v_ls = iv.get("left_shoulder")
                v_rs = iv.get("right_shoulder")
                left_shoulder_np = np.array(v_ls, dtype=np.float32) if v_ls is not None else None
                right_shoulder_np = np.array(v_rs, dtype=np.float32) if v_rs is not None else None

                victim_red = 0.0
                victim_warn = 0.0
                head_contact_hits = 0
                upper_contact_hits = 0
                torso_contact_hits = 0

                for wrist_np, elbow_np, shoulder_np, elbow_angle, wrist_speed in wrists:
                    if shoulder_np is None:
                        continue
                    arm_reach = float(np.linalg.norm(wrist_np - shoulder_np) / (a_h + 1e-6))
                    if arm_reach < BULLY_MIN_ARM_REACH:
                        continue

                    d_head = float(np.linalg.norm(wrist_np - head_np) / pair_scale)
                    d_torso = float(np.linalg.norm(wrist_np - torso_np) / pair_scale)
                    d_pelvis = float(np.linalg.norm(wrist_np - pelvis_np) / pair_scale)
                    d_neck = float(np.linalg.norm(wrist_np - shoulder_mid_np) / pair_scale)
                    shoulder_dists = []
                    if left_shoulder_np is not None:
                        shoulder_dists.append(float(np.linalg.norm(wrist_np - left_shoulder_np) / pair_scale))
                    if right_shoulder_np is not None:
                        shoulder_dists.append(float(np.linalg.norm(wrist_np - right_shoulder_np) / pair_scale))
                    d_shoulder = min(shoulder_dists) if shoulder_dists else d_neck
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
                        head_contact_hits += 1

                    sensitive_touch_strength = 0.0
                    if (
                        in_victim_box
                        and own_head_dist >= min(d_torso, d_pelvis) + 0.02
                        and 0.0005 <= wrist_speed <= 0.095
                        and (d_torso <= BULLY_SENSITIVE_DIST or d_pelvis <= BULLY_SENSITIVE_DIST)
                    ):
                        sensitive_touch_strength = (BULLY_SENSITIVE_DIST - min(d_torso, d_pelvis)) * 1.65 + 0.06
                        torso_contact_hits += 1

                    # Push/shove: wrist impacts torso/pelvis with higher speed + victim recoil/motion.
                    push_strength = 0.0
                    recoil_ok = victim_motion >= PUSH_RECOIL_MIN or victim_action in ("TÃ‰", "BÃO Äá»˜NG")
                    if (
                        in_victim_box
                        and d_torso <= PUSH_CONTACT_DIST
                        and wrist_speed >= PUSH_WRIST_SPEED_MIN
                        and (align >= 0.08 or arm_reach >= BULLY_MIN_ARM_REACH * 1.10)
                    ):
                        push_strength = (PUSH_CONTACT_DIST - d_torso) * 1.00 + min(0.18, max(0.0, wrist_speed - PUSH_WRIST_SPEED_MIN) * 1.7)
                        if recoil_ok:
                            push_strength += 0.05
                        if victim_away_speed >= BULLY_PUSH_AWAY_MIN:
                            push_strength += min(0.10, (victim_away_speed - BULLY_PUSH_AWAY_MIN) * 4.2)
                        if closing_speed >= BULLY_PUSH_AWAY_MIN * 0.65:
                            push_strength += 0.03

                    pull_strength = 0.0
                    elbow_value = float(elbow_angle) if elbow_angle is not None else 180.0
                    grab_dist = min(d_head, d_neck, d_shoulder)
                    if (
                        (in_victim_box or grab_dist <= BULLY_PULL_CONTACT_DIST)
                        and grab_dist <= BULLY_PULL_CONTACT_DIST
                        and own_head_dist >= grab_dist + 0.02
                        and 0.004 <= wrist_speed <= 0.095
                        and elbow_value <= BULLY_PULL_ELBOW_MAX
                    ):
                        pull_strength = (BULLY_PULL_CONTACT_DIST - grab_dist) * 1.55 + max(0.0, BULLY_PULL_ELBOW_MAX - elbow_value) * 0.0018
                        if victim_toward_speed >= BULLY_PULL_TOWARD_MIN:
                            pull_strength += min(0.12, (victim_toward_speed - BULLY_PULL_TOWARD_MIN) * 5.0)
                        if closing_speed >= BULLY_PULL_TOWARD_MIN * 1.10:
                            pull_strength += min(0.08, closing_speed * 3.0)
                        if d_head <= BULLY_HEAD_GRAB_DIST * 1.15:
                            pull_strength += 0.04
                            head_contact_hits += 1
                        upper_contact_hits += 1

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
                        if mutual_combat:
                            point_strength *= 0.38

                    red_strength = max(head_grab_strength, sensitive_touch_strength, push_strength, pull_strength)
                    if red_strength > 0.0:
                        depth_score = max(0.0, 1.0 - bottom_gap / max(BULLY_MAX_BOTTOM_GAP, 1e-6))
                        scale_score = min(1.0, height_ratio / max(BULLY_MIN_HEIGHT_RATIO, 1e-6))
                        overlap_score = min(1.0, x_overlap / max(BULLY_MIN_X_OVERLAP, 1e-6))
                        near_score = max(0.0, 1.0 - center_dist / max(BULLY_INTERACT_RANGE, 1e-6))
                        red_strength *= 0.48 + 0.20 * depth_score + 0.16 * scale_score + 0.08 * overlap_score + 0.08 * near_score
                        red_strength *= mutual_scale

                    if red_strength > victim_red:
                        victim_red = red_strength
                    if point_strength > victim_warn:
                        victim_warn = point_strength

                if not mutual_combat and center_dist <= BULLY_CLOSE_CENTER_DIST:
                    if head_contact_hits >= 2:
                        victim_red = max(victim_red, BULLY_CONTACT_STRENGTH_MIN + 0.035)
                    elif head_contact_hits >= 1 and upper_contact_hits >= 1:
                        victim_red = max(victim_red, BULLY_CONTACT_STRENGTH_MIN + 0.022)
                    if torso_contact_hits >= 2 and victim_away_speed >= BULLY_PUSH_AWAY_MIN * 0.75:
                        victim_red = max(victim_red, BULLY_CONTACT_STRENGTH_MIN + 0.018)

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
            bully_recent = recent_mean(st.bully_hist, BULLY_FAST_WINDOW)
            bully_peak = recent_peak(st.bully_hist, BULLY_FAST_WINDOW)
            warn_recent = recent_mean(st.bully_warn_hist, BULLY_FAST_WINDOW)
            warn_peak = recent_peak(st.bully_warn_hist, BULLY_FAST_WINDOW)
            stable_target_id, stable_target_ratio = dominant_id_ratio(st.bully_target_hist)

            red_active = (
                best_red_target is not None
                and stable_target_id == best_red_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_red_strength >= BULLY_MIN_STRENGTH
                and bully_ratio >= BULLY_PERSIST_MIN
            )
            fast_red_active = (
                best_red_target is not None
                and stable_target_id == best_red_target
                and stable_target_ratio >= BULLY_FAST_TARGET_STABLE_RATIO
                and bully_recent >= BULLY_FAST_RECENT_MIN
                and bully_peak >= BULLY_FAST_PEAK_MIN
                and best_red_strength >= BULLY_CONTACT_STRENGTH_MIN * 0.80
            )
            red_active = red_active or fast_red_active
            warn_active = (
                not red_active
                and best_warn_target is not None
                and stable_target_id == best_warn_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_warn_strength >= BULLY_POINT_WARN_MIN_STRENGTH
                and warn_ratio >= BULLY_POINT_PERSIST_MIN
            )
            fast_warn_active = (
                not red_active
                and best_warn_target is not None
                and stable_target_id == best_warn_target
                and stable_target_ratio >= BULLY_WARN_FAST_TARGET_STABLE_RATIO
                and warn_recent >= BULLY_WARN_FAST_RECENT_MIN
                and warn_peak >= BULLY_WARN_FAST_PEAK_MIN
                and best_warn_strength >= BULLY_POINT_WARN_MIN_STRENGTH * 0.82
            )
            warn_active = warn_active or fast_warn_active

            if red_active:
                st.bully_target_id = int(best_red_target)
                st.bully_active_until = now + BULLY_STICKY_SEC
                candidate_map[a_id] = {
                    "score": float(best_red_strength + bully_ratio * 0.03),
                    "target_id": int(best_red_target),
                    "label": "Báº®T Náº T",
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
                    "label": "Báº®T Náº T",
                }
                continue

            st.bully_target_id = None

            if warn_active:
                st.bully_warn_target_id = int(best_warn_target)
                st.bully_warn_active_until = now + max(0.5, BULLY_STICKY_SEC * 0.75)
                candidate_map[a_id] = {
                    "score": float(best_warn_strength + warn_ratio * 0.02),
                    "target_id": int(best_warn_target),
                    "label": "Báº®T Náº T",
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
                    "label": "Báº®T Náº T",
                }
                continue

            st.bully_warn_target_id = None

        detection_map = {}
        suppressed = set()
        claimed_target = {}
        ordered = sorted(
            candidate_map.items(),
            key=lambda kv: (1 if kv[1].get("label") == "Báº®T Náº T" else 0, kv[1]["score"]),
            reverse=True,
        )

        for a_id, data in ordered:
            if a_id in suppressed:
                continue
            t_id = int(data["target_id"])
            label = data.get("label", "Báº®T Náº T")
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
                "score": float(data["score"]),
            }
            claimed_target[t_id] = {"aggressor_id": a_id, "score": float(data["score"])}

        return detection_map

    def _detect_combat_interactions(self, people_data, now: float):
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
            strike_detected = punch_detected or kick_detected
            guard_ratio = float(ia.get("guard_ratio", 0.0))
            combat_energy = float(ia.get("combat_energy", 0.0))
            combat_move = bool(ia.get("combat_move", False))
            a_motion = float(ia.get("motion_score", 0.0))

            lw = ia.get("left_wrist")
            rw = ia.get("right_wrist")
            le = ia.get("left_elbow")
            re = ia.get("right_elbow")
            ls = ia.get("left_shoulder")
            rs = ia.get("right_shoulder")
            la = ia.get("left_ankle")
            ra = ia.get("right_ankle")
            left_wrist_speed = float(ia.get("left_wrist_speed", 0.0))
            right_wrist_speed = float(ia.get("right_wrist_speed", 0.0))
            wrist_entries = []
            striking_points = []
            if lw is not None:
                striking_points.append(np.array(lw, dtype=np.float32))
                wrist_entries.append(
                    (
                        np.array(lw, dtype=np.float32),
                        np.array(le, dtype=np.float32) if le is not None else None,
                        np.array(ls, dtype=np.float32) if ls is not None else None,
                        left_wrist_speed,
                    )
                )
            if rw is not None:
                striking_points.append(np.array(rw, dtype=np.float32))
                wrist_entries.append(
                    (
                        np.array(rw, dtype=np.float32),
                        np.array(re, dtype=np.float32) if re is not None else None,
                        np.array(rs, dtype=np.float32) if rs is not None else None,
                        right_wrist_speed,
                    )
                )
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
                victim_guard_ratio = float(iv.get("guard_ratio", 0.0))
                victim_combat_move = bool(iv.get("combat_move", False))
                victim_punch = bool(iv.get("punch_detected", False))
                victim_kick = bool(iv.get("kick_detected", False))
                
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

                recoil = float(iv.get("motion_score", 0.0)) >= COMBAT_TARGET_RECOIL_MIN or victim.get("action") in ("TÃ‰", "BÃO Äá»˜NG")
                contact_limit = COMBAT_CONTACT_DIST
                contact_ok = min_contact_dist <= contact_limit
                wrist_contact_strength = 0.0
                close_wrist_hits = 0
                for wrist_np, elbow_np, shoulder_np, wrist_speed in wrist_entries:
                    d_head = float(np.linalg.norm(wrist_np - v_head_np) / pair_scale)
                    d_torso = float(np.linalg.norm(wrist_np - v_torso_np) / pair_scale)
                    d_hip = float(np.linalg.norm(wrist_np - v_hip_np) / pair_scale)
                    target_dist = min(d_head, d_torso, d_hip)
                    if target_dist > contact_limit * 1.10 or wrist_speed < PUNCH_WRIST_SPEED_MIN * 0.72:
                        continue

                    arm_reach = 0.0
                    if shoulder_np is not None:
                        arm_reach = float(np.linalg.norm(wrist_np - shoulder_np) / (a_h + 1e-6))

                    align = 0.0
                    if elbow_np is not None:
                        arm_vec = wrist_np - elbow_np
                        target_np = v_head_np if d_head <= d_torso else v_torso_np
                        tgt_vec = target_np - elbow_np
                        n_arm = float(np.linalg.norm(arm_vec))
                        n_tgt = float(np.linalg.norm(tgt_vec))
                        if n_arm > 1e-6 and n_tgt > 1e-6:
                            align = float(np.dot(arm_vec, tgt_vec) / (n_arm * n_tgt))

                    if align < 0.14 and arm_reach < BULLY_MIN_ARM_REACH * 1.05:
                        continue

                    hit_strength = (contact_limit * 1.10 - target_dist) * 0.88
                    hit_strength += min(0.12, max(0.0, wrist_speed - PUNCH_WRIST_SPEED_MIN * 0.72) * 1.9)
                    if d_head <= contact_limit * 0.92:
                        hit_strength += 0.03
                    if recoil:
                        hit_strength += 0.03
                    if victim_guard_ratio >= 0.40 or victim_combat_move or victim_punch or victim_kick:
                        hit_strength += 0.015
                    wrist_contact_strength = max(wrist_contact_strength, hit_strength)
                    close_wrist_hits += 1

                strength = 0.0
                if strike_detected and contact_ok:
                    strength += 0.095 + max(0.0, (contact_limit - min_contact_dist)) * 0.70
                if kick_detected and contact_ok:
                    strength += 0.048
                if punch_detected and contact_ok:
                    strength += 0.043
                if wrist_contact_strength > 0.0:
                    strength += 0.060 + wrist_contact_strength
                if close_wrist_hits >= 2 and center_dist <= COMBAT_INTERACT_RANGE * 0.66:
                    strength += 0.026
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
            combat_recent = recent_mean(st.combat_hist, COMBAT_FAST_WINDOW)
            combat_peak = recent_peak(st.combat_hist, COMBAT_FAST_WINDOW)
            stable_target_id, stable_target_ratio = dominant_id_ratio(st.combat_target_hist)
            red_active = (
                best_target is not None
                and stable_target_id == best_target
                and stable_target_ratio >= BULLY_TARGET_STABLE_RATIO
                and best_strength >= COMBAT_MIN_STRENGTH
                and combat_ratio >= COMBAT_PERSIST_MIN
            )
            fast_red_active = (
                best_target is not None
                and stable_target_id == best_target
                and stable_target_ratio >= COMBAT_FAST_TARGET_STABLE_RATIO
                and combat_recent >= COMBAT_FAST_RECENT_MIN
                and combat_peak >= COMBAT_FAST_PEAK_MIN
                and best_strength >= COMBAT_MIN_STRENGTH * 0.62
            )
            red_active = red_active or fast_red_active
            if red_active:
                st.combat_target_id = int(best_target)
                st.combat_active_until = now + COMBAT_STICKY_SEC
                candidate_map[a_id] = {
                    "score": float(best_strength + combat_ratio * 0.03),
                    "target_id": int(best_target),
                    "label": "CHIáº¾N Äáº¤U",
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
                    "label": "CHIáº¾N Äáº¤U",
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
            detection_map[a_id] = {
                "label": "CHIáº¾N Äáº¤U",
                "target_id": t_id,
                "score": float(data["score"]),
            }
            claimed_target[t_id] = {"aggressor_id": a_id, "score": float(data["score"])}

        return detection_map

    def _process_frame(self, frame):
        now = self._timeline_now()
        self.frame_index += 1
        display = frame.copy()
        infer_frame = preprocess_low_light(frame)

        fs_out = None
        hazard_priority_active = False
        if ENABLE_FIRE_SMOKE_DETECTION:
            try:
                fs_out = self.fs_engine.process(frame)
            except Exception:
                fs_out = None
        if fs_out is not None:
            confirmed_hazard = list(fs_out.get("confirmed") or [])
            candidate_hazard = list(fs_out.get("candidates") or [])
            hazard_priority_active = bool(confirmed_hazard)
            if not hazard_priority_active:
                for tr in candidate_hazard[:4]:
                    cls_name = str(getattr(tr, "cls_name", "")).lower()
                    score = float(getattr(tr, "score", 0.0))
                    conf = float(getattr(tr, "conf", 0.0))
                    if cls_name == "fire" and conf >= FS_FIRE_PRIORITY_FAST_CONF and score >= FS_FIRE_PRIORITY_FAST_SCORE * 0.92:
                        hazard_priority_active = True
                        break
                    if cls_name == "smoke" and conf >= FS_SMOKE_THIN_FAST_CONF and score >= FS_SMOKE_THIN_FAST_SCORE * 0.96:
                        hazard_priority_active = True
                        break

        persist_flag = not bool(self.tracker_reset)
        track_kwargs = {
            "persist": persist_flag,
            "conf": CONF_THRES,
            "iou": IOU_THRES,
            "imgsz": adaptive_infer_size(infer_frame, max_size=IMG_SIZE, min_size=POSE_MIN_IMG_SIZE),
            "verbose": False,
            "tracker": POSE_TRACKER,
            "max_det": POSE_MAX_DET,
            "classes": [0],
            "device": POSE_DEVICE,
        }
        if USE_CUDA:
            track_kwargs["half"] = True
        results = self.model.track(infer_frame, **track_kwargs)[0]
        if self.tracker_reset:
            self.tracker_reset = False

        stale_ids = []
        for tid, st in self.track_states.items():
            if now - st.last_seen > TRACK_TTL_SEC:
                stale_ids.append(tid)
        for tid in stale_ids:
            del self.track_states[tid]

        draw_items = []
        person_count = 0
        detected_people = []

        boxes_obj = results.boxes.cpu() if results.boxes is not None else None
        keypoints_obj = results.keypoints.cpu() if results.keypoints is not None else None

        if boxes_obj is not None and len(boxes_obj) > 0:
            boxes = boxes_obj.xyxy.numpy()
            box_confs = boxes_obj.conf.numpy() if boxes_obj.conf is not None else np.ones(len(boxes), dtype=np.float32)
            if boxes_obj.cls is not None:
                clss = boxes_obj.cls.numpy().astype(int)
            else:
                clss = np.zeros(len(boxes), dtype=int)
            ids = boxes_obj.id.numpy().astype(int) if boxes_obj.id is not None else None

            kps_xy = None
            kps_cf = None
            if keypoints_obj is not None:
                kps_xy = keypoints_obj.xy.numpy()
                if keypoints_obj.conf is not None:
                    kps_cf = keypoints_obj.conf.numpy()

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
                box_conf = float(box_confs[i]) if i < len(box_confs) else 0.0
                kp_xy = kps_xy[i] if kps_xy is not None and i < len(kps_xy) else None
                kp_cf = kps_cf[i] if kps_cf is not None and i < len(kps_cf) else None

                pose_profile = person_pose_profile(w, h)
                kp_min_conf = float(pose_profile["kp_min_conf"])
                valid_all = count_valid_points(kp_xy, kp_cf, list(range(17)), min_conf=kp_min_conf)
                valid_upper = count_valid_points(kp_xy, kp_cf, [5, 6, 11, 12], min_conf=kp_min_conf)
                partial_ok = box_conf >= float(pose_profile["fallback_box_conf"])
                if valid_all < int(pose_profile["min_valid_all"]) or valid_upper < int(pose_profile["min_valid_upper"]):
                    if not partial_ok:
                        continue
                if kp_xy is None and not partial_ok:
                    continue

                if track_id not in self.track_states:
                    self.track_states[track_id] = PersonState(first_seen=now, last_significant_motion=now)

                st = self.track_states[track_id]
                st.last_seen = now
                st.seen_frames += 1

                cls_result = self._classify_person(
                    st,
                    now,
                    x1,
                    y1,
                    x2,
                    y2,
                    kp_xy,
                    kp_cf,
                    pose_min_conf=kp_min_conf,
                    frame_w=frame.shape[1],
                    frame_h=frame.shape[0],
                    track_id=track_id,
                )
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

        bullying_map = self._detect_bullying_interactions(detected_people, now)
        combat_map = self._detect_combat_interactions(detected_people, now)
        combat_actions = {"CHIáº¾N Äáº¤U", "DI CHUYá»‚N CHIáº¾N Äáº¤U", "Äáº¤M", "ÄÃ"}
        alert_key = action_key("BÁO ĐỘNG")
        fall_key = action_key("TÉ")
        fight_label = normalize_ui_text("CHIẾN ĐẤU")
        bully_label = normalize_ui_text("BẮT NẠT")
        normal_label = normalize_ui_text("BÌNH THƯỜNG")

        def preferred_interaction(track_id, base_action, is_sitting):
            if is_sitting or base_action in (alert_key, fall_key):
                return None

            combat_data = combat_map.get(track_id)
            bully_data = bullying_map.get(track_id)
            if combat_data is None and bully_data is None:
                return None

            bully_target_id = None
            bully_score = 0.0
            if bully_data is not None:
                try:
                    bully_target_id = int(bully_data.get("target_id"))
                except Exception:
                    bully_target_id = None
                bully_score = float(bully_data.get("score", 0.0))

            combat_target_id = None
            combat_score = 0.0
            combat_reciprocal = False
            if combat_data is not None:
                try:
                    combat_target_id = int(combat_data.get("target_id"))
                except Exception:
                    combat_target_id = None
                combat_score = float(combat_data.get("score", 0.0))
                if combat_target_id is not None:
                    reverse = combat_map.get(combat_target_id)
                    if reverse is not None:
                        try:
                            combat_reciprocal = int(reverse.get("target_id", -1)) == int(track_id)
                        except Exception:
                            combat_reciprocal = False

            if bully_data is not None:
                same_target = combat_target_id is not None and bully_target_id == combat_target_id
                if (
                    combat_data is None
                    or not combat_reciprocal
                    or (same_target and bully_score >= combat_score * 0.96)
                ):
                    return {
                        "label": normalize_ui_text(str(bully_data.get("label", bully_label))),
                        "target_id": bully_target_id,
                        "kind": "bully",
                    }

            if combat_data is not None:
                return {
                    "label": fight_label,
                    "target_id": combat_target_id,
                    "kind": "combat",
                }
            return None
        
        # QUY Táº®C Há»† THá»NG: Kiá»ƒm soÃ¡t sá»‘ lÆ°á»£ng ngÆ°á»i
        # Náº¿u quÃ¡ Ä‘Ã´ng ngÆ°á»i: chá»‰ váº½ nhá»¯ng ngÆ°á»i cÃ³ hÃ nh vi báº¥t thÆ°á»ng Ä‘á»ƒ tráº¡nh rá»‘i khung hÃ¬nh.
        # Khi sá»‘ ngÆ°á»i vá»«a pháº£i: váº«n váº½ táº¥t cáº£ Ä‘á»ƒ giá»¯ kháº£ nÄƒng quan sÃ¡t tá»« xa.
        total_people = len(detected_people)
        draw_all_people = total_people <= 8 and not hazard_priority_active

        # People counter overlay (always show).
        draw_items.append(
            {
                "text": f"SỐ NGƯỜI: {total_people}",
                "x": 18,
                "y": 18,
                "color": (255, 255, 255),
                "size": 22,
                "bg": True,
            }
        )
        
        # QUY Táº®C Há»† THá»NG: XÃ¡c Ä‘á»‹nh hÃ nh vi cuá»‘i cÃ¹ng (Æ°u tiÃªn: TÃ‰ > CHIáº¾N Äáº¤U > Báº®T Náº T)
        # Quy táº¯c: TÃ‰ luÃ´n Ä‘Æ°á»£c phÃ©p | CHIáº¾N Äáº¤U vÃ  Báº®T Náº T chá»‰ khi KHÃ”NG ngá»“i
        person_final_actions = {}
        for item in detected_people:
            track_id = item["track_id"]
            action = item["action"]
            interaction = item.get("interaction", {})
            is_sitting = bool(interaction.get("is_sitting", False))
            interaction_choice = preferred_interaction(track_id, action, is_sitting)
            
            # Æ¯u tiÃªn 1: BÃO Äá»˜NG (Fall detection)
            if action == alert_key:
                final_action = alert_key
            # Æ¯u tiÃªn 2: TÃ‰ (luÃ´n Ä‘Æ°á»£c phÃ©p, ká»ƒ cáº£ Ä‘ang ngá»“i)
            elif action == fall_key:
                final_action = fall_key
            elif interaction_choice is not None:
                final_action = interaction_choice["label"]
            elif action in combat_actions and not is_sitting:
                final_action = fight_label
            else:
                final_action = normal_label
            
            person_final_actions[track_id] = final_action
        
        # Váº½ bounding box vÃ  label dá»±a trÃªn sá»‘ lÆ°á»£ng ngÆ°á»i
        for item in detected_people:
            track_id = item["track_id"]
            action = item["action"]
            color = item["color"]
            label_suffix = ""
            final_action = person_final_actions[track_id]
            interaction_choice = preferred_interaction(track_id, action, bool(item.get("interaction", {}).get("is_sitting", False)))
            
            # QUY Táº®C: Náº¿u Ä‘Ã´ng ngÆ°á»i (>5) vÃ  hÃ nh vi bÃ¬nh thÆ°á»ng, Bá»Ž QUA khÃ´ng váº½
            if (hazard_priority_active or not draw_all_people) and final_action == normal_label:
                continue
            
            # Láº¥y confidence score
            metrics = item.get("metrics", {})
            decision_confidence = float(metrics.get("decision_confidence", 0.0))
            confidence_str = f" ({decision_confidence:.2f})" if decision_confidence > 0 else ""
            
            # QUY Táº®C Há»† THá»NG: XÃ¡c Ä‘á»‹nh hÃ nh Ä‘á»™ng vÃ  mÃ u sáº¯c (cÃ³ thá»ƒ kÃ¨m VÅ¨ KHÃ)
            is_sitting = bool(item.get("interaction", {}).get("is_sitting", False))
            
            if action == alert_key:
                color = (0, 0, 255)
            elif action == fall_key:
                color = (0, 255, 255)
            elif interaction_choice is not None:
                target_id = interaction_choice.get("target_id")
                action = interaction_choice.get("label", bully_label if interaction_choice.get("kind") == "bully" else fight_label)
                if target_id is not None:
                    label_suffix = f" -> ID {target_id}"
                color = (0, 0, 255)
            elif action in combat_actions and not is_sitting:
                action = fight_label
                color = (0, 0, 255)
            else:
                action = normal_label
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

        # Draw fire/smoke detections (original logic; status on top-right to avoid overlap).
        if ENABLE_FIRE_SMOKE_DETECTION and fs_out is not None:
            confirmed = list(fs_out.get("confirmed") or [])
            candidates = list(fs_out.get("candidates") or [])
            status = str(fs_out.get("status") or "")

            fire_n = sum(1 for t in confirmed if getattr(t, "cls_name", "") == "fire")
            smoke_n = sum(1 for t in confirmed if getattr(t, "cls_name", "") == "smoke")
            cand_n = len(candidates)

            draw_items.append(
                {
                    "text": f"KHÓI/LỬA: LỬA={fire_n}  KHÓI={smoke_n}  (ứng viên={cand_n})",
                    "x": 0,
                    "y": 18,
                    "align": "right",
                    "margin": 18,
                    "color": (255, 255, 255),
                    "size": 22,
                    "bg": True,
                }
            )
            if status:
                draw_items.append(
                    {
                        "text": status,
                        "x": 0,
                        "y": 48,
                        "align": "right",
                        "margin": 18,
                        "color": (255, 255, 255),
                        "size": 20,
                        "bg": True,
                    }
                )

            for t in candidates[:8]:
                box = getattr(t, "box", None) or [0, 0, 0, 0]
                x1, y1, x2, y2 = [int(v) for v in box]
                cls_name = str(getattr(t, "cls_name", "")).upper()
                tid = int(getattr(t, "id", -1))
                conf = float(getattr(t, "conf", 0.0))
                color = (0, 255, 255)
                draw_box(display, x1, y1, x2, y2, color, thickness=2)
                draw_items.append(
                    {
                        "text": f"NGHI VẤN {cls_name} #{tid} ({conf:.2f})",
                        "x": x1,
                        "y": max(25, y1 - 28),
                        "color": color,
                        "size": 22,
                        "bg": SHOW_ID_BG,
                    }
                )

            for t in confirmed[:8]:
                box = getattr(t, "box", None) or [0, 0, 0, 0]
                x1, y1, x2, y2 = [int(v) for v in box]
                cls_raw = str(getattr(t, "cls_name", "")).lower()
                cls_name = cls_raw.upper()
                tid = int(getattr(t, "id", -1))
                conf = float(getattr(t, "conf", 0.0))
                color = (0, 0, 255) if cls_raw == "fire" else (0, 165, 255)
                draw_box(display, x1, y1, x2, y2, color, thickness=3)
                draw_items.append(
                    {
                        "text": f"{cls_name} #{tid} ({conf:.2f})",
                        "x": x1,
                        "y": max(25, y1 - 28),
                        "color": color,
                        "size": 24,
                        "bg": SHOW_ID_BG,
                    }
                )

            # Snapshot only when confirmed (cooldown).
            if SAVE_ALERT_FRAME and confirmed and now - float(getattr(self, "fs_last_snapshot_time", 0.0)) >= FS_SNAPSHOT_COOLDOWN_SEC:
                self.fs_last_snapshot_time = now
                try:
                    path = save_snapshot(display, 0, "KHOI_LUA")
                    print(f"[ALERT] FIRE/SMOKE saved: {path}")
                except Exception:
                    pass

        if total_people == 0:
            draw_items.append(
                {
                    "text": "KHÔNG CÓ NGƯỜI",
                    "x": 18,
                    "y": 52,
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

                # Update seek bar for file videos.
                if self.source_type == "file" and self.total_frames > 0 and not self.user_dragging_seek:
                    try:
                        idx = int(self.current_frame_idx)
                        idx = max(0, min(idx, max(0, self.total_frames - 1)))
                        self.updating_seek = True
                        self.seek_var.set(idx)
                        self.updating_seek = False
                        self._update_seek_label(idx, self.total_frames)
                    except Exception:
                        self.updating_seek = False
        finally:
            self.after(15, self._refresh_preview)


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app = FallAlarmApp()
    app.mainloop()
 
