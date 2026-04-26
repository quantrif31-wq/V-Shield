from __future__ import annotations

import io
import json
import mimetypes
import os
import re
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urlparse, urlunparse

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

try:
    from PIL import Image, ImageDraw  # type: ignore
except Exception:
    Image = None
    ImageDraw = None

try:
    from ultralytics import YOLO  # type: ignore
except Exception:
    YOLO = None


ALERT_FILE_PATTERN = re.compile(
    r"^(?P<ts>\d{8}_\d{6})_id(?P<track>-?\d+)_(?P<label>.+)\.(?P<ext>jpg|jpeg|png)$",
    re.IGNORECASE,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def ensure_alert_dir(base_dir: Path) -> Path:
    configured = os.getenv("SECURITY_AI_ALERTS_DIR", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = (base_dir / configured).resolve()
    else:
        path = (base_dir / "alerts").resolve()

    path.mkdir(parents=True, exist_ok=True)
    return path


def infer_source_type(source: str) -> str:
    text = str(source or "").strip()
    if not text:
        return "unknown"
    if text.isdigit():
        return "webcam"
    lowered = text.lower()
    if lowered.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        return "rtsp" if lowered.startswith("rtsp://") else "stream"
    if Path(text).suffix:
        return "file"
    return "stream"


def normalize_rtsp_source(source: str) -> str:
    text = str(source or "").strip()
    if not text.lower().startswith("rtsp://"):
        return text

    try:
        parsed = urlparse(text)
    except Exception:
        return text

    path = (parsed.path or "").lower()
    if "/cam/realmonitor" not in path:
        return text

    try:
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
    except Exception:
        query_items = []

    query_map: dict[str, str] = {}
    for key, value in query_items:
        if key:
            query_map[key.lower()] = value

    # IMOU/Dahua realmonitor usually requires channel/subtype.
    if not str(query_map.get("channel", "")).strip():
        query_map["channel"] = "1"
    if not str(query_map.get("subtype", "")).strip():
        query_map["subtype"] = "0"

    normalized_query = urlencode(sorted(query_map.items()))
    rebuilt = parsed._replace(query=normalized_query)
    return urlunparse(rebuilt)


def create_placeholder_jpeg(title: str, subtitle: str = "", width: int = 1280, height: int = 720) -> bytes:
    if Image is None:
        return b""

    img = Image.new("RGB", (width, height), color=(17, 27, 40))
    draw = ImageDraw.Draw(img)
    draw.rectangle((24, 24, width - 24, height - 24), outline=(74, 118, 158), width=2)
    draw.text((48, 52), "V-Shield Security AI", fill=(236, 242, 250))
    if title:
        draw.text((48, 102), title, fill=(236, 242, 250))
    if subtitle:
        draw.text((48, 138), subtitle, fill=(190, 208, 228))
    draw.text((48, height - 54), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(154, 177, 206))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def encode_jpeg(frame: Any) -> bytes:
    if cv2 is None:
        return create_placeholder_jpeg("OpenCV is not available in current Python env.")

    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
    if not ok:
        return create_placeholder_jpeg("Cannot encode JPEG frame.")
    return encoded.tobytes()


def open_capture(source: Any, source_type: str) -> Any:
    if cv2 is None:
        return None

    if source_type == "webcam":
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(source, backend)
    elif source_type == "rtsp":
        # Prefer TCP to keep IMOU streams stable on Windows/LAN.
        if not os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000|max_delay;500000"
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)

    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    try:
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 7000)
    except Exception:
        pass
    try:
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 7000)
    except Exception:
        pass
    return cap


@dataclass
class RuntimeState:
    running: bool = False
    camera_enabled: bool = False
    camera_connected: bool = False
    source: str = ""
    source_type: str = "unknown"
    loop_video: bool = False
    message: str = "AI service is ready."
    error: str = ""
    started_at: float = 0.0
    last_update: str = field(default_factory=utc_now_iso)
    fps: float = 0.0
    person_count: int = 0
    abnormal_count: int = 0
    danger_count: int = 0
    actions: dict[str, int] = field(default_factory=dict)
    people: list[dict[str, Any]] = field(default_factory=list)
    current_frame_idx: int = 0
    total_frames: int = 0
    elapsed_seconds: float = 0.0
    duration_seconds: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    last_frame_jpeg: bytes = b""


class SecurityAnalyzer:
    def __init__(self, base_dir: Path, alerts_dir: Path) -> None:
        self.base_dir = base_dir
        self.alerts_dir = alerts_dir
        self.person_model = None
        self.hazard_model = None
        self.last_alert_at = 0.0
        self.alert_cooldown_seconds = 6.0
        self._load_models()

    def _load_model(self, candidates: list[Path], preferred_env: str) -> Any:
        if YOLO is None:
            return None

        env_value = os.getenv(preferred_env, "").strip()
        if env_value:
            env_path = Path(env_value)
            if not env_path.is_absolute():
                env_path = (self.base_dir / env_path).resolve()
            candidates = [env_path] + candidates

        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                return YOLO(str(candidate))
            except Exception:
                continue

        return None

    def _load_models(self) -> None:
        person_candidates = [
            self.base_dir / "yolov8n.pt",
            self.base_dir / "yolov8s-pose.pt",
        ]
        hazard_candidates = [
            self.base_dir / "best_nano_111.pt",
            self.base_dir / "best.pt",
        ]

        self.person_model = self._load_model(person_candidates, "SECURITY_AI_PERSON_MODEL")
        self.hazard_model = self._load_model(hazard_candidates, "SECURITY_AI_HAZARD_MODEL")

    @staticmethod
    def _safe_names_map(model: Any, result: Any) -> dict[int, str]:
        names = {}
        try:
            names = getattr(result, "names", None) or getattr(model, "names", None) or {}
            if isinstance(names, dict):
                return {int(k): str(v) for k, v in names.items()}
            if isinstance(names, list):
                return {index: str(value) for index, value in enumerate(names)}
        except Exception:
            pass
        return {}

    def _save_alert_if_needed(self, frame: Any, label: str, track_id: int = 0) -> None:
        now = time.time()
        if now - self.last_alert_at < self.alert_cooldown_seconds:
            return
        self.last_alert_at = now

        safe_label = re.sub(r"[^A-Za-z0-9_]+", "_", label).strip("_").upper() or "ALERT"
        file_name = f"{datetime.now():%Y%m%d_%H%M%S}_id{track_id}_{safe_label}.jpg"
        path = self.alerts_dir / file_name
        try:
            if cv2 is not None:
                cv2.imwrite(str(path), frame)
        except Exception:
            pass

    def analyze(self, frame: Any) -> tuple[Any, dict[str, Any]]:
        if cv2 is None:
            return frame, {
                "person_count": 0,
                "abnormal_count": 0,
                "danger_count": 0,
                "actions": {},
                "people": [],
            }

        annotated = frame.copy()
        people: list[dict[str, Any]] = []
        actions: dict[str, int] = {}
        danger_count = 0

        if self.person_model is not None:
            try:
                result = self.person_model.predict(
                    source=annotated,
                    imgsz=640,
                    conf=0.35,
                    classes=[0],
                    verbose=False,
                )[0]
                boxes = getattr(result, "boxes", None)
                if boxes is not None:
                    for index, box in enumerate(boxes, start=1):
                        xyxy = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = [int(value) for value in xyxy]
                        confidence = float(box.conf[0]) if box.conf is not None else 0.0

                        cv2.rectangle(annotated, (x1, y1), (x2, y2), (33, 204, 114), 2)
                        cv2.putText(
                            annotated,
                            f"ID {index} | BINH_THUONG ({confidence:.2f})",
                            (x1, max(24, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.58,
                            (33, 204, 114),
                            2,
                            cv2.LINE_AA,
                        )
                        people.append(
                            {
                                "track_id": index,
                                "action": "BINH_THUONG",
                                "final_action": "BINH_THUONG",
                                "confidence": round(confidence, 3),
                            }
                        )
            except Exception:
                pass

        if people:
            actions["BINH_THUONG"] = len(people)

        if self.hazard_model is not None:
            try:
                result = self.hazard_model.predict(
                    source=annotated,
                    imgsz=768,
                    conf=0.32,
                    verbose=False,
                )[0]
                boxes = getattr(result, "boxes", None)
                names_map = self._safe_names_map(self.hazard_model, result)
                if boxes is not None:
                    for box in boxes:
                        cls_index = int(box.cls[0]) if box.cls is not None else -1
                        label = names_map.get(cls_index, str(cls_index)).strip().upper()
                        lower_label = label.lower()
                        if not any(token in lower_label for token in ("fire", "smoke", "khoi", "lua")):
                            continue

                        danger_count += 1
                        xyxy = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = [int(value) for value in xyxy]
                        confidence = float(box.conf[0]) if box.conf is not None else 0.0
                        color = (0, 0, 255) if "fire" in lower_label or "lua" in lower_label else (0, 165, 255)
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
                        cv2.putText(
                            annotated,
                            f"{label} ({confidence:.2f})",
                            (x1, max(26, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.62,
                            color,
                            2,
                            cv2.LINE_AA,
                        )

                if danger_count > 0:
                    actions["KHOI_LUA"] = danger_count
                    self._save_alert_if_needed(annotated, "KHOI_LUA", track_id=0)
            except Exception:
                pass

        return annotated, {
            "person_count": len(people),
            "abnormal_count": danger_count,
            "danger_count": danger_count,
            "actions": actions,
            "people": people,
        }


class SecurityAiService:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.alerts_dir = ensure_alert_dir(base_dir)
        self.lock = threading.RLock()
        self.state = RuntimeState(last_frame_jpeg=create_placeholder_jpeg("Camera is not running."))
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.pending_seek_frame: int | None = None
        self.analyzer = SecurityAnalyzer(base_dir, self.alerts_dir)

    def _snapshot(self) -> dict[str, Any]:
        state = self.state
        uptime = max(0.0, time.time() - state.started_at) if state.started_at else 0.0
        stream_url = "/api/camera/frame" if state.camera_enabled else ""
        return {
            "success": True,
            "running": state.running,
            "camera_enabled": state.camera_enabled,
            "camera_connected": state.camera_connected,
            "source": state.source,
            "ip": state.source,
            "source_type": state.source_type,
            "message": state.message,
            "error": state.error,
            "last_update": state.last_update,
            "started_at": datetime.fromtimestamp(state.started_at, tz=timezone.utc).isoformat() if state.started_at else None,
            "uptime_seconds": round(uptime, 3),
            "fps": round(state.fps, 3),
            "person_count": state.person_count,
            "abnormal_count": state.abnormal_count,
            "danger_count": state.danger_count,
            "actions": state.actions,
            "people": state.people,
            "current_frame_idx": state.current_frame_idx,
            "total_frames": state.total_frames,
            "elapsed_seconds": round(state.elapsed_seconds, 3),
            "duration_seconds": round(state.duration_seconds, 3),
            "frame_width": state.frame_width,
            "frame_height": state.frame_height,
            "stream_url": stream_url,
        }

    def get_status(self) -> dict[str, Any]:
        with self.lock:
            return self._snapshot()

    def get_result(self) -> dict[str, Any]:
        with self.lock:
            return self._snapshot()

    def get_frame(self) -> bytes:
        with self.lock:
            frame = self.state.last_frame_jpeg
            if frame:
                return frame
            return create_placeholder_jpeg("No frame available.")

    def start(self, source: str, loop_video: bool, restart_if_running: bool) -> tuple[bool, str]:
        source = str(source or "").strip()
        if not source:
            return False, "Nguon camera rong. Hay truyen chi so webcam (vi du: 0) hoac RTSP URL."

        with self.lock:
            if self.worker_thread and self.worker_thread.is_alive():
                if not restart_if_running:
                    return True, "AI is already running."
                self._stop_locked("Restarting AI service.")

            self.stop_event = threading.Event()
            startup_event = threading.Event()
            startup_state: dict[str, Any] = {"ok": False, "error": "Timeout while starting camera source."}

            self.state = RuntimeState(
                running=False,
                camera_enabled=False,
                camera_connected=False,
                source=source,
                source_type=infer_source_type(source),
                loop_video=loop_video,
                message="Starting AI worker...",
                error="",
                started_at=time.time(),
                last_update=utc_now_iso(),
                last_frame_jpeg=create_placeholder_jpeg("Starting camera source...", source),
            )
            self.pending_seek_frame = None

            thread = threading.Thread(
                target=self._worker,
                args=(source, loop_video, startup_event, startup_state, self.stop_event),
                daemon=True,
                name="security-ai-worker",
            )
            self.worker_thread = thread
            thread.start()

        if not startup_event.wait(timeout=12.0):
            self.stop("Startup timeout.")
            return False, "Khong the khoi dong camera source trong thoi gian cho phep."

        if not startup_state.get("ok", False):
            self.stop(startup_state.get("error") or "Cannot open source.")
            return False, str(startup_state.get("error") or "Cannot open source.")

        return True, "Da bat AI an ninh."

    def _stop_locked(self, message: str) -> None:
        stop_event = self.stop_event
        worker = self.worker_thread
        stop_event.set()
        if worker and worker.is_alive():
            worker.join(timeout=4.0)
        self.worker_thread = None
        self.state.running = False
        self.state.camera_enabled = False
        self.state.camera_connected = False
        self.state.source = ""
        self.state.source_type = "unknown"
        self.state.fps = 0.0
        self.state.message = message
        self.state.error = ""
        self.state.last_update = utc_now_iso()
        self.state.people = []
        self.state.actions = {}
        self.state.person_count = 0
        self.state.abnormal_count = 0
        self.state.danger_count = 0
        self.state.current_frame_idx = 0
        self.state.total_frames = 0
        self.state.elapsed_seconds = 0.0
        self.state.duration_seconds = 0.0
        self.pending_seek_frame = None

    def stop(self, message: str = "Da dung AI an ninh.") -> None:
        with self.lock:
            self._stop_locked(message)

    def reset(self) -> None:
        with self.lock:
            self.state.people = []
            self.state.actions = {}
            self.state.person_count = 0
            self.state.abnormal_count = 0
            self.state.danger_count = 0
            self.state.current_frame_idx = 0
            self.state.elapsed_seconds = 0.0
            self.state.message = "Da reset trang thai AI an ninh."
            self.state.error = ""
            self.state.last_update = utc_now_iso()
            self.pending_seek_frame = None

    def request_seek(self, frame_index: int) -> tuple[bool, int, str, int]:
        try:
            requested = int(frame_index)
        except Exception:
            return False, 400, "Frame index khong hop le.", 0

        with self.lock:
            if not self.state.running or not self.state.camera_enabled:
                return False, 409, "AI an ninh chua chay.", 0

            if self.state.source_type != "file":
                return False, 409, "Chi ho tro tua voi tep video.", 0

            max_frame_index = max(0, int(self.state.total_frames) - 1)
            if max_frame_index <= 0:
                return False, 409, "Video khong co du lieu frame de tua.", 0

            clamped = max(0, min(requested, max_frame_index))
            self.pending_seek_frame = clamped
            self.state.message = f"Dang tua den frame {clamped}..."
            self.state.error = ""
            self.state.last_update = utc_now_iso()
            return True, 200, "Da ghi nhan lenh tua video.", clamped

    def _resolve_capture_source(self, source: str) -> tuple[Any, str]:
        stripped = str(source or "").strip()
        source_type = infer_source_type(stripped)
        if source_type == "webcam":
            try:
                return int(stripped), source_type
            except Exception:
                return 0, source_type
        if source_type == "rtsp":
            return normalize_rtsp_source(stripped), source_type
        return stripped, source_type

    def _worker(
        self,
        source: str,
        loop_video: bool,
        startup_event: threading.Event,
        startup_state: dict[str, Any],
        stop_event: threading.Event,
    ) -> None:
        try:
            if cv2 is None:
                with self.lock:
                    self.state.running = True
                    self.state.camera_enabled = True
                    self.state.camera_connected = True
                    self.state.message = "OpenCV khong co san. Dang chay che do placeholder."
                    self.state.last_update = utc_now_iso()
                startup_state["ok"] = True
                startup_event.set()

                frame_times: deque[float] = deque(maxlen=30)
                while not stop_event.is_set():
                    now = time.time()
                    frame_times.append(now)
                    fps = 0.0
                    if len(frame_times) >= 2:
                        span = frame_times[-1] - frame_times[0]
                        if span > 0:
                            fps = (len(frame_times) - 1) / span

                    frame_bytes = create_placeholder_jpeg("AI is running without OpenCV.", source)
                    with self.lock:
                        self.state.last_frame_jpeg = frame_bytes
                        self.state.elapsed_seconds = max(0.0, now - self.state.started_at)
                        self.state.fps = fps
                        self.state.last_update = utc_now_iso()
                    time.sleep(0.25)

                return

            capture_source, source_type = self._resolve_capture_source(source)
            cap = open_capture(capture_source, source_type)
            if not cap.isOpened():
                startup_state["ok"] = False
                startup_state["error"] = f"Khong mo duoc nguon camera: {source}"
                startup_event.set()
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            duration_seconds = (total_frames / source_fps) if (total_frames > 0 and source_fps > 0) else 0.0

            with self.lock:
                self.state.running = True
                self.state.camera_enabled = True
                self.state.camera_connected = True
                self.state.source_type = source_type
                self.state.total_frames = max(0, total_frames)
                self.state.duration_seconds = max(0.0, duration_seconds)
                self.state.message = "Dang xu ly nguon camera."
                self.state.error = ""
                self.state.last_update = utc_now_iso()

            startup_state["ok"] = True
            startup_event.set()

            frame_times: deque[float] = deque(maxlen=30)
            while not stop_event.is_set():
                if source_type == "file":
                    pending_seek: int | None = None
                    with self.lock:
                        if self.pending_seek_frame is not None:
                            pending_seek = int(self.pending_seek_frame)
                            self.pending_seek_frame = None

                    if pending_seek is not None:
                        clamped_seek = max(0, min(pending_seek, max(0, total_frames - 1)))
                        try:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, clamped_seek)
                        except Exception:
                            pass

                ok, frame = cap.read()
                if not ok:
                    if source_type == "file" and loop_video and total_frames > 0:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    if source_type in {"rtsp", "stream", "webcam"}:
                        try:
                            cap.release()
                        except Exception:
                            pass
                        if stop_event.is_set():
                            break
                        time.sleep(0.35)
                        cap = open_capture(capture_source, source_type)
                        if cap is not None and cap.isOpened():
                            continue
                    break

                now = time.time()
                frame_times.append(now)
                fps = 0.0
                if len(frame_times) >= 2:
                    span = frame_times[-1] - frame_times[0]
                    if span > 0:
                        fps = (len(frame_times) - 1) / span

                analyzed_frame, result = self.analyzer.analyze(frame)
                current_frame_idx = int(max(0, cap.get(cv2.CAP_PROP_POS_FRAMES) - 1))
                if source_type == "file" and source_fps > 0:
                    elapsed_seconds = max(0.0, current_frame_idx / source_fps)
                else:
                    elapsed_seconds = max(0.0, now - self.state.started_at)
                height, width = analyzed_frame.shape[:2]
                frame_bytes = encode_jpeg(analyzed_frame)

                with self.lock:
                    self.state.last_frame_jpeg = frame_bytes
                    self.state.fps = fps
                    self.state.person_count = int(result.get("person_count", 0))
                    self.state.abnormal_count = int(result.get("abnormal_count", 0))
                    self.state.danger_count = int(result.get("danger_count", 0))
                    self.state.actions = dict(result.get("actions", {}))
                    self.state.people = list(result.get("people", []))[:24]
                    self.state.current_frame_idx = current_frame_idx
                    self.state.elapsed_seconds = elapsed_seconds
                    self.state.frame_width = int(width)
                    self.state.frame_height = int(height)
                    self.state.last_update = utc_now_iso()

            cap.release()

            with self.lock:
                if stop_event.is_set():
                    self.state.message = "Da dung AI an ninh."
                else:
                    self.state.message = "Nguon video da ket thuc."
                self.state.running = False
                self.state.camera_enabled = False
                self.state.camera_connected = False
                self.state.source = ""
                self.state.source_type = "unknown"
                self.state.fps = 0.0
                self.state.last_update = utc_now_iso()
                self.pending_seek_frame = None

        except Exception as exc:
            error_message = f"AI worker error: {exc}"
            traceback.print_exc()
            with self.lock:
                self.state.running = False
                self.state.camera_enabled = False
                self.state.camera_connected = False
                self.state.message = "AI worker bi loi."
                self.state.error = error_message
                self.state.last_update = utc_now_iso()
                self.state.last_frame_jpeg = create_placeholder_jpeg("AI worker crashed.", error_message[:96])
                self.pending_seek_frame = None
            startup_state["ok"] = False
            startup_state["error"] = error_message
            startup_event.set()
        finally:
            if not startup_event.is_set():
                startup_state["ok"] = False
                startup_state["error"] = "AI worker exited before startup completed."
                startup_event.set()

    def list_alerts(self, take: int) -> dict[str, Any]:
        files = []
        for item in self.alerts_dir.iterdir():
            if not item.is_file():
                continue
            ext = item.suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png"}:
                continue
            files.append(item)

        files.sort(key=lambda value: value.stat().st_mtime, reverse=True)
        limited = files[: max(1, min(take, 120))]
        items = [self._build_alert_item(path) for path in limited]
        return {"items": items, "total": len(files)}

    def _build_alert_item(self, path: Path) -> dict[str, Any]:
        default_captured_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        label = "ALERT"
        track_id: int | None = None
        captured_at = default_captured_at

        match = ALERT_FILE_PATTERN.match(path.name)
        if match:
            label = match.group("label").replace("_", " ").strip().upper() or "ALERT"
            track_text = match.group("track")
            try:
                track_id = int(track_text)
            except Exception:
                track_id = None
            ts_text = match.group("ts")
            try:
                parsed = datetime.strptime(ts_text, "%Y%m%d_%H%M%S")
                captured_at = parsed.replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                captured_at = default_captured_at

        return {
            "fileName": path.name,
            "label": label,
            "trackId": track_id,
            "capturedAt": captured_at,
            "imageUrl": f"/api/camera/alerts/{path.name}",
            "sizeBytes": path.stat().st_size,
        }

    def get_alert_bytes(self, file_name: str) -> tuple[bytes | None, str]:
        safe_name = Path(file_name).name
        path = (self.alerts_dir / safe_name).resolve()
        if not str(path).startswith(str(self.alerts_dir)):
            return None, "application/octet-stream"
        if not path.exists() or not path.is_file():
            return None, "application/octet-stream"

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return path.read_bytes(), content_type


class ApiHandler(BaseHTTPRequestHandler):
    service: SecurityAiService | None = None

    def log_message(self, format: str, *args: Any) -> None:
        message = format % args
        print(f"[HTTP] {self.address_string()} - {message}")

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        try:
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        except Exception as exc:
            fallback = {
                "success": False,
                "message": f"JSON encode error: {exc}",
            }
            body = json.dumps(fallback, ensure_ascii=False).encode("utf-8")
            status_code = 500
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status_code: int, body: bytes, content_type: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        raw = b""

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 0:
            raw = self.rfile.read(length)
        else:
            transfer_encoding = str(self.headers.get("Transfer-Encoding", "") or "").lower()
            if "chunked" in transfer_encoding:
                chunks: list[bytes] = []
                while True:
                    header_line = self.rfile.readline()
                    if not header_line:
                        break

                    header_text = header_line.strip().split(b";", 1)[0]
                    if not header_text:
                        continue

                    try:
                        chunk_size = int(header_text, 16)
                    except Exception:
                        break

                    if chunk_size <= 0:
                        # Consume trailing headers after last chunk.
                        while True:
                            trailer_line = self.rfile.readline()
                            if not trailer_line or trailer_line in {b"\r\n", b"\n"}:
                                break
                        break

                    chunk = self.rfile.read(chunk_size)
                    if chunk:
                        chunks.append(chunk)
                    # Consume CRLF after each chunk.
                    self.rfile.read(2)

                raw = b"".join(chunks)

        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
            if isinstance(value, dict):
                return value
            return {}
        except Exception:
            return {}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        try:
            service = self.service
            if service is None:
                self._send_json(500, {"success": False, "message": "Service is not initialized."})
                return

            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"

            if path == "/api/camera/status":
                self._send_json(200, service.get_status())
                return

            if path == "/api/camera/result":
                self._send_json(200, service.get_result())
                return

            if path == "/api/camera/frame":
                frame = service.get_frame()
                if not frame:
                    self._send_json(404, {"success": False, "message": "No frame available."})
                    return
                self._send_bytes(200, frame, "image/jpeg")
                return

            if path == "/api/camera/alerts":
                query = parse_qs(parsed.query)
                raw_take = (query.get("take") or ["24"])[0]
                try:
                    take = int(raw_take)
                except Exception:
                    take = 24
                self._send_json(200, service.list_alerts(take))
                return

            if path.startswith("/api/camera/alerts/"):
                file_name = unquote(path.split("/api/camera/alerts/", 1)[1])
                data, content_type = service.get_alert_bytes(file_name)
                if data is None:
                    self._send_json(404, {"success": False, "message": "Alert image not found."})
                    return
                self._send_bytes(200, data, content_type)
                return

            if path in {"/", "/health"}:
                self._send_json(200, {"success": True, "message": "Security AI API is running."})
                return

            self._send_json(404, {"success": False, "message": "Endpoint not found."})
        except Exception as exc:
            traceback.print_exc()
            try:
                self._send_json(500, {"success": False, "message": f"Unhandled GET error: {exc}"})
            except Exception:
                pass

    def do_POST(self) -> None:  # noqa: N802
        try:
            service = self.service
            if service is None:
                self._send_json(500, {"success": False, "message": "Service is not initialized."})
                return

            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"

            if path == "/api/camera/on":
                payload = self._read_json_body()
                source = payload.get("source") or payload.get("ip") or ""
                loop_video = parse_bool(payload.get("loopVideo"), default=False)
                restart_if_running = parse_bool(payload.get("restartIfRunning"), default=True)
                ok, message = service.start(str(source), loop_video=loop_video, restart_if_running=restart_if_running)
                status_payload = service.get_status()
                status_payload["success"] = ok
                status_payload["message"] = message
                if ok:
                    self._send_json(200, status_payload)
                else:
                    self._send_json(500, status_payload)
                return

            if path == "/api/camera/off":
                service.stop("Da dung AI an ninh.")
                status_payload = service.get_status()
                status_payload["success"] = True
                status_payload["message"] = "Da dung AI an ninh."
                self._send_json(200, status_payload)
                return

            if path == "/api/camera/seek":
                payload = self._read_json_body()
                raw_frame_index = payload.get("frameIndex")
                if raw_frame_index is None:
                    raw_frame_index = payload.get("frame_index")

                ok, status_code, message, frame_index = service.request_seek(raw_frame_index)
                status_payload = service.get_status()
                status_payload["success"] = ok
                status_payload["message"] = message
                status_payload["frameIndex"] = frame_index
                self._send_json(status_code, status_payload)
                return

            if path == "/api/camera/reset":
                service.reset()
                status_payload = service.get_status()
                status_payload["success"] = True
                status_payload["message"] = "Da reset trang thai AI an ninh."
                self._send_json(200, status_payload)
                return

            self._send_json(404, {"success": False, "message": "Endpoint not found."})
        except Exception as exc:
            traceback.print_exc()
            try:
                self._send_json(500, {"success": False, "message": f"Unhandled POST error: {exc}"})
            except Exception:
                pass


def run() -> None:
    base_dir = Path(__file__).resolve().parent
    host = os.getenv("SECURITY_AI_API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    raw_port = os.getenv("SECURITY_AI_API_PORT", "5003").strip() or "5003"
    try:
        port = int(raw_port)
    except Exception:
        port = 5003

    service = SecurityAiService(base_dir)
    ApiHandler.service = service

    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"[START] Security AI headless API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("[STOP] Security AI headless API shutting down.")
        service.stop("Security AI service stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
