<template>
  <div class="page page-container animate-in">
    <div class="topbar">
      <div class="topbar-left">
        <div class="topbar-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div>
          <span class="panel-kicker">Gate Control</span>
          <h1 class="page-title">Điều phối thông hành</h1>
          <p class="topbar-desc">Quản lý 2 làn — QR Code + Nhận diện biển số xe</p>
        </div>
      </div>
    </div>

    <div class="lane-grid">
      <section
        v-for="lane in lanes"
        :key="lane.id"
        class="lane-card"
        :class="{ ready: isLaneReady(lane) }"
      >
        <div class="lane-head">
          <div class="lane-head-info">
            <div class="lane-icon" :class="{ active: laneAnyRunning(lane) }">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <div>
              <h2>{{ lane.name }}</h2>
              <p>{{ lane.desc }}</p>
            </div>
          </div>

          <div class="lane-final-status" :class="isLaneReady(lane) ? 'ok' : 'wait'">
            <span class="status-dot"></span>
            {{ isLaneReady(lane) ? "SẴN SÀNG XÁC NHẬN" : "ĐANG XỬ LÝ" }}
          </div>
        </div>

        <div class="lane-actions">
          <button class="btn btn-preview" :disabled="lane.loading" @click="previewLane(lane)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            {{ lane.loading ? "Đang xử lý..." : "Preview" }}
          </button>

          <button
            class="btn btn-main"
            :disabled="lane.loading || !lane.qr.cameraIp.trim() || !lane.plate.cameraIp.trim()"
            @click="readAllLane(lane)"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            {{ lane.loading ? "Đang xử lý..." : laneAnyRunning(lane) ? "Đọc lại cả 2" : "Đọc cả 2" }}
          </button>

          <button
            class="btn btn-sub"
            :disabled="lane.loading || !lane.qr.cameraIp.trim()" :style="!lane.qr.cameraIp.trim() ? { opacity: 0.4 } : {}"
            @click="retryQr(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : "Đọc lại QR" }}
          </button>

          <button
            class="btn btn-sub"
            :disabled="lane.loading || !lane.plate.cameraIp.trim()" :style="!lane.plate.cameraIp.trim() ? { opacity: 0.4 } : {}"
            @click="retryPlate(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : "Đọc lại Biển" }}
          </button>

          <button class="btn btn-off" :disabled="lane.loading" @click="stopLane(lane)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>
            {{ lane.loading ? "Đang xử lý..." : "Tắt" }}
          </button>

          <button
            class="btn btn-confirm"
            :disabled="lane.loading || !lane.qr.employeeId || !lane.plate.confirmedPlate"
            @click="confirmLane(lane)"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Xác nhận
          </button>
        </div>

        <div class="ip-row">
          <div class="ip-box">
            <label>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
              QR Camera
            </label>
            <div
              class="search-box"
              :ref="(el) => setCameraSearchRef(lane.id, 'qr', el)"
            >
              <input
                v-model="cameraSearch[lane.id + '-qr']"
                placeholder="Tìm camera QR..."
                :disabled="lane.loading"
                @focus="openCameraDropdown(lane.id, 'qr')"
                @input="handleCameraSearchInput(lane, 'qr')"
                @keydown.esc="closeCameraDropdown(lane.id, 'qr')"
              />

              <div class="dropdown" v-if="isCameraDropdownOpen(lane.id, 'qr')">
                <div
                  v-if="!filterCameras(cameraSearch[lane.id + '-qr']).length"
                  class="dropdown-empty"
                >
                  Không tìm thấy camera phù hợp
                </div>
                <div
                  v-for="cam in filterCameras(cameraSearch[lane.id + '-qr'])"
                  :key="cam.cameraId"
                  @click="selectCamera(cam, lane, 'qr')"
                  class="dropdown-item"
                  :class="{ selected: String(cam.id ?? cam.cameraId) === String(lane.qr.cameraId ?? '') }"
                >
                  <span class="dropdown-item-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                  </span>
                  {{ cam.cameraName }} <span class="dropdown-item-id">#{{ cam.cameraId }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="ip-box">
            <label>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13" rx="2" ry="2"/><polygon points="16 8 20 4 20 16 16 12 16 8"/></svg>
              Plate Camera
            </label>
            <div
              class="search-box"
              :ref="(el) => setCameraSearchRef(lane.id, 'plate', el)"
            >
              <input
                v-model="cameraSearch[lane.id + '-plate']"
                placeholder="Tìm camera Plate..."
                :disabled="lane.loading"
                @focus="openCameraDropdown(lane.id, 'plate')"
                @input="handleCameraSearchInput(lane, 'plate')"
                @keydown.esc="closeCameraDropdown(lane.id, 'plate')"
              />

              <div class="dropdown" v-if="isCameraDropdownOpen(lane.id, 'plate')">
                <div
                  v-if="!filterCameras(cameraSearch[lane.id + '-plate']).length"
                  class="dropdown-empty"
                >
                  Không tìm thấy camera phù hợp
                </div>
                <div
                  v-for="cam in filterCameras(cameraSearch[lane.id + '-plate'])"
                  :key="cam.cameraId"
                  @click="selectCamera(cam, lane, 'plate')"
                  class="dropdown-item"
                  :class="{ selected: String(cam.id ?? cam.cameraId) === String(lane.plate.cameraId ?? '') }"
                >
                  <span class="dropdown-item-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                  </span>
                  {{ cam.cameraName }} <span class="dropdown-item-id">#{{ cam.cameraId }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="summary-bar">
          <div class="summary-item">
            <span class="label">Employee ID</span>
            <span class="value strong">{{ lane.qr.employeeId || "-----" }}</span>
          </div>

          <div class="summary-item">
            <span class="label">QR</span>
            <span class="value" :class="qrStateClass(lane.qr)">
              {{ qrStateText(lane.qr) }}
            </span>
          </div>

          <div class="summary-item">
            <span class="label">Cảnh báo QR</span>
            <span class="value" :class="lane.qr.alert ? 'danger-text' : 'ok-text'">
              {{ lane.qr.alert ? qrAlertText(lane.qr) : "BÌNH THƯỜNG" }}
            </span>
          </div>

          <div class="summary-item">
            <span class="label">Biển số</span>
            <span class="value strong plate">{{ lane.plate.confirmedPlate || "-----" }}</span>
          </div>
          <div class="summary-item direction-item">
            <span class="label">Chiều xe</span>
            <select
              v-model="lane.movementDirection"
              class="direction-select"
              :disabled="lane.loading"
              @change="handleLaneDirectionChange(lane)"
            >
              <option value="IN">Xe vào</option>
              <option value="OUT">Xe ra</option>
            </select>
            <span class="direction-hint">{{ laneDirectionText(lane) }}</span>
          </div>
        </div>

        <div class="camera-stack">
          <!-- QR -->
          <div class="cam-block">
            <div class="cam-head">
              <span class="cam-head-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h.01"/><path d="M17 7h.01"/><path d="M7 17h.01"/><path d="M17 17h.01"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
                QR Camera
              </span>
              <span class="mini-status" :class="lane.qr.previewHealthy ? 'ok' : 'wait'">
                {{
                  !lane.qr.previewRunning
                    ? "Preview OFF"
                    : lane.qr.lockedSnapshot
                      ? "Ảnh đã chụp"
                      : (lane.qr.previewHealthy ? "Preview OK" : "Preview...")
                }}
              </span>
            </div>

            <div class="cam-preview">
              <img
                v-if="lane.qr.previewRunning && lane.qr.lockedSnapshot"
                :src="lane.qr.lockedSnapshot"
                class="preview-image"
                alt="QR Snapshot"
              />
              <img
                v-else-if="lane.qr.previewRunning && lane.qr.previewMode === 'image' && lane.qr.directCameraUrl"
                :key="lane.qr.directCameraKey"
                :src="lane.qr.directCameraUrl"
                :ref="(el) => setQrImageRef(lane.id, el)"
                class="preview-image"
                alt="QR Preview"
                crossorigin="anonymous"
                @load="onQrPreviewLoaded(lane)"
                @error="onQrPreviewError(lane)"
              />
              <video
                v-else-if="lane.qr.previewRunning && (lane.qr.previewMode === 'video' || lane.qr.previewMode === 'hls')"
                :key="lane.qr.directCameraKey + '-video'"
                :ref="(el) => setQrVideoRef(lane.id, el)"
                class="preview-image"
                muted
                autoplay
                playsinline
                @loadeddata="onQrVideoPreviewLoaded(lane)"
                @error="onQrVideoPreviewError(lane)"
              ></video>
              <div v-else-if="lane.qr.previewRunning" class="cam-off">
                <div class="cam-off-icon pulse-anim">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
                </div>
                <span>Chờ ảnh chụp QR...</span>
              </div>
              <div v-else class="cam-off">
                <div class="cam-off-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="1" y1="1" x2="23" y2="23"/><path d="M21 21H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3m3-3h6l2 3h4a2 2 0 0 1 2 2v9.34m-7.72-2.06a4 4 0 1 1-5.56-5.56"/></svg>
                </div>
                <span>QR Offline</span>
              </div>
            </div>
            <canvas :ref="(el) => setQrCanvasRef(lane.id, el)" class="hidden-canvas"></canvas>

            <div class="quick-result">
              <div class="result-pill" :class="lane.qr.cameraRunning ? 'ok' : 'off'">
                <span class="pill-dot"></span>
                {{ lane.qr.cameraRunning ? "RUNNING" : "STOPPED" }}
              </div>
              <div class="result-pill" :class="lane.qr.sessionLocked ? 'ok' : 'wait'">
                <span class="pill-dot"></span>
                {{ lane.qr.sessionLocked ? "LOCKED" : "SCANNING" }}
              </div>
              <div class="result-pill" :class="lane.qr.alert ? 'danger' : 'neutral'">
                <span class="pill-dot"></span>
                {{ lane.qr.alert ? "INVALID" : "NORMAL" }}
              </div>
            </div>

            <div class="qr-data-grid">
              <div class="qr-data-box">
                <span class="small-label">Payload hiện tại</span>
                <span class="small-value">{{ shortText(lane.qr.qrPayload) }}</span>
              </div>
              <div class="qr-data-box">
                <span class="small-label">Payload đang giữ phiên</span>
                <span class="small-value">{{ shortText(lane.qr.activeSessionPayload) }}</span>
              </div>
              <div class="qr-data-box">
                <span class="small-label">Thông điệp verify</span>
                <span class="small-value">{{ lane.qr.verifyMessage || "-----" }}</span>
              </div>
              <div class="qr-data-box">
                <span class="small-label">Thiết bị quét</span>
                <span class="small-value">{{ lane.qr.scannerDevice || "-----" }}</span>
              </div>
            </div>

            <div class="verify-box" v-if="lane.qr.verifyData || lane.qr.verifyMessage">
              <div class="verify-message">
                <b>Kết quả verify:</b> {{ lane.qr.verifyMessage || "-----" }}
              </div>
              <div v-if="lane.qr.verifyData" class="verify-data">
                <div><b>Employee ID:</b> {{ lane.qr.verifyData.employeeId || "-----" }}</div>
                <div><b>Employee Name:</b> {{ lane.qr.verifyData.employeeName || "-----" }}</div>
                <div><b>Verified At:</b> {{ formatDate(lane.qr.verifyData.verifiedAtUtc) || "-----" }}</div>
                <div><b>Counter:</b> {{ lane.qr.verifyData.counter ?? "-----" }}</div>
                <div><b>Expires:</b> {{ formatDate(lane.qr.verifyData.expiresAtUtc) || "-----" }}</div>
              </div>
            </div>
          </div>

          <!-- PLATE -->
          <div class="cam-block">
            <div class="cam-head">
              <span class="cam-head-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13" rx="2" ry="2"/><polygon points="16 8 20 4 20 16 16 12 16 8"/></svg>
                Plate Camera
              </span>
              <span class="mini-status" :class="platePreviewStatusClass(lane.plate)">
                {{ platePreviewStatusText(lane.plate) }}
              </span>
            </div>

            <div class="cam-preview">
              <img
                v-if="lane.plate.previewRunning && lane.plate.directCameraUrl"
                :key="lane.plate.directCameraKey"
                :src="lane.plate.directCameraUrl"
                class="preview-image"
                alt="Plate Preview"
                @load="onPreviewLoaded(lane.plate)"
                @error="onPreviewError(lane.plate)"
              />
              <div v-else class="cam-off">
                <div class="cam-off-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13" rx="2" ry="2"/><polygon points="16 8 20 4 20 16 16 12 16 8"/></svg>
                </div>
                <span>Plate Offline</span>
              </div>
            </div>

            <div class="quick-result">
              <div class="result-pill" :class="lane.plate.cameraRunning ? 'ok' : 'off'">
                <span class="pill-dot"></span>
                {{ lane.plate.cameraRunning ? "RUNNING" : "STOPPED" }}
              </div>
              <div class="result-pill" :class="lane.plate.scanLocked ? 'ok' : 'wait'">
                <span class="pill-dot"></span>
                {{ lane.plate.scanLocked ? "LOCKED" : "SCANNING" }}
              </div>
              <div class="result-pill neutral">
                <span class="pill-dot"></span>
                {{ lane.plate.confirmedPlate || "NO PLATE" }}
              </div>
            </div>

            <div class="evidence-row">
              <div class="evidence-box">
                <img
                  v-if="lane.plate.lockedPlateCrop"
                  :src="lane.plate.lockedPlateCrop"
                  class="evidence-image"
                  alt="Plate Crop"
                />
                <div v-else class="evidence-empty">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                  <span>Plate Crop</span>
                </div>
              </div>

              <div class="evidence-box">
                <img
                  v-if="lane.plate.lockedSnapshot"
                  :src="lane.plate.lockedSnapshot"
                  class="evidence-image"
                  alt="Plate Snapshot"
                />
                <div v-else class="evidence-empty">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                  <span>Plate Snapshot</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-note">
          <span><b>QR Msg:</b> {{ lane.qr.message || "-----" }}</span>
          <span><b>Plate Msg:</b> {{ lane.plate.message || "-----" }}</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import jsQR from "jsqr"
import * as plateLane1Api from "../services/biensoApi"
import * as plateLane2Api from "../services/biensoApi"
import { confirmGateLocally } from "../services/thonghanhAPI"
import { verifyDynamicQr } from "../services/dynamicQrVerifyApi"
import { startQr, resetQr, stopQr, getQrResult, scanQr, getQrLockedImage } from "../services/qr_dAPI"
import { formatLicensePlateDisplay } from "../utils/licensePlateValidator"
import {
  fetchSetCamCatalog,
  inferMovementDirection,
  pickDefaultSetCamCamera,
} from "../services/setcamCatalog"

const LANE_CAMERA_STORAGE_PREFIX = "vshield-thonghanh-camera"
const LANE_DIRECTION_STORAGE_PREFIX = "vshield-thonghanh-direction"

function getDefaultLaneDirection(laneId) {
  return laneId === "lane2" ? "OUT" : "IN"
}

function normalizeLaneDirection(value, fallback = "IN") {
  const normalizedValue = String(value || "").trim().toUpperCase()
  if (normalizedValue === "IN" || normalizedValue === "OUT") {
    return normalizedValue
  }

  const normalizedFallback = String(fallback || "").trim().toUpperCase()
  if (normalizedFallback === "IN" || normalizedFallback === "OUT") {
    return normalizedFallback
  }

  return ""
}

function getLaneDirectionLabel(direction) {
  return normalizeLaneDirection(direction, "IN") === "OUT" ? "Xe ra" : "Xe vào"
}

function createQrModule(defaultScannerDevice) {
  return {
    cameraId: null,
    cameraName: "",
    cameraIp: "",
    currentIp: "",
    gateId: null,
    gateName: "",
    cameraRunning: false,
    previewRunning: false,
    pollingBusy: false,

    previewHealthy: false,
    imgBusy: false,
    decodeBusy: false,
    verifying: false,

    directCameraUrl: "",
    directCameraKey: 0,
    viewUrl: "", // 🔥 thêm dòng này
    previewMode: "empty",
    videoPreviewUrl: "",
    hlsInstance: null,

    scannerDevice: defaultScannerDevice,

    qrPayload: "",
    manualPayload: "",
    verifyMessage: "",
    verifyData: null,

    employeeId: "",
    employeeName: "",

    activeSessionPayload: "",
    activeSessionVerified: false,
    activeSessionVerifyState: "",
    activeSessionVerifyMessage: "",
    lastSeenAt: null,

    lastDecodedText: "",
    lastDecodedAt: 0,
    lastUpdate: "",
    message: "",

    previewTimer: null,
    resultTimer: null,
    sessionTimer: null,
    destroyed: false,

    previewIntervalMs: 350,
    absenceThresholdMs: 1500,
    decodeMaxWidth: 640,

    frameWidth: 0,
    frameHeight: 0,

    alert: false,
    sessionLocked: false,
    lockedSnapshot: ""
  }
}

function createPlateModule() {
  return {
    cameraId: null,
    cameraName: "",
    cameraIp: "",
    currentIp: "",
    gateId: null,
    gateName: "",
    cameraRunning: false,
    previewRunning: false,

    sessionId: 0,
    lastAppliedSessionId: 0,
    lastLockedImageSessionId: 0,

    confirmedPlate: "",
    lastRawPlate: "",
    scanLocked: false,

    lockedSnapshot: "",
    lockedPlateCrop: "",

    message: "",
    fps: 0,
    ocrRunning: false,
    stableCount: 0,
    movingFast: false,
    lastUpdate: "",

    directCameraUrl: "",
    directCameraKey: 0,
    viewUrl: "", // 🔥 thêm dòng này
    previewHealthy: false,

    resultTimer: null,
    busyResult: false,
    isFetchingLockedImages: false,
    destroyed: false
  }
}

function normalizePreviewStreamUrl(inputUrl) {
  const raw = String(inputUrl || "").trim()
  if (!raw) return ""

  try {
    const url = new URL(raw, window.location.origin)
    const src = url.searchParams.get("src")

    if (/\/stream\.html$/i.test(url.pathname) && src) {
      url.pathname = "/api/stream.mjpeg"
      url.search = ""
      url.searchParams.set("src", src)
      url.searchParams.set("_ts", String(Date.now()))
      return url.toString()
    }

    if (/\/api\/stream\.mjpeg$/i.test(url.pathname) || /\/api\/frame\.jpeg$/i.test(url.pathname)) {
      url.searchParams.set("_ts", String(Date.now()))
      return url.toString()
    }

    return url.toString()
  } catch {
    return raw
  }
}

function resolveQrPreviewMode(inputUrl) {
  const normalizedUrl = normalizePreviewStreamUrl(inputUrl)
  if (!normalizedUrl) return "empty"
  if (/(\.m3u8|\/api\/stream\.m3u8)(\?|$)/i.test(normalizedUrl)) return "hls"
  if (/(\.mp4|\/api\/stream\.mp4)(\?|$)/i.test(normalizedUrl)) return "video"
  return "image"
}

export default {
  name: "VShieldGateMinimalQr",

  data() {
    return {
      qrCanvasRefs: {},
      qrImageRefs: {},
      qrVideoRefs: {},
      cameraSearchRefs: {},
      cameras: [],
      cameraSearch: {},
      openCameraDropdownKey: "",
      lanes: [
        {
          id: "lane1",
          movementDirection: getDefaultLaneDirection("lane1"),
          name: "Làn 1",
          desc: "QR trên / Biển dưới",
          loading: false,
          plateApi: plateLane1Api,
          qr: createQrModule("WEB_SCANNER_GATE_01"),
          plate: createPlateModule()
        },
        {
          id: "lane2",
          movementDirection: getDefaultLaneDirection("lane2"),
          name: "Làn 2",
          desc: "QR trên / Biển dưới",
          loading: false,
          plateApi: plateLane2Api,
          qr: createQrModule("WEB_SCANNER_GATE_02"),
          plate: createPlateModule()
        }
      ]
    }
  },

  async mounted() {
    document.addEventListener("pointerdown", this.handleDocumentPointerDown)
    this.restoreLaneDirections()
  await this.loadCameraList() // 🔥 THÊM

  for (const lane of this.lanes) {
    lane.qr.destroyed = false
    lane.plate.destroyed = false
    await this.loadStatusPlate(lane)
    if (lane.plate.cameraRunning) this.startPlateLoop(lane)
  }
},

  beforeUnmount() {
    document.removeEventListener("pointerdown", this.handleDocumentPointerDown)

    for (const lane of this.lanes) {
      lane.qr.destroyed = true
      lane.plate.destroyed = true

      this.stopQrLoops(lane)
      this.stopQrPolling(lane)
      this.stopPlateLoop(lane)

      this.resetQrPreview(lane.id, lane.qr)
      this.resetPreview(lane.plate)
    }
  },

  activated() {
    this.loadCameraList()
    this.restoreLaneDirections()
    for (const lane of this.lanes) {
      lane.qr.destroyed = false
      lane.plate.destroyed = false

      if (lane.qr.cameraRunning) {
        if (lane.qr.viewUrl) {
          this.enableQrPreview(lane.qr, lane.qr.viewUrl, lane.id)
        } else {
          lane.qr.previewRunning = true
        }
        this.startQrPolling(lane)
      }

      if (lane.plate.cameraRunning) {
        if (lane.plate.viewUrl && !lane.plate.previewRunning) {
  this.mountPreview(lane.plate, lane.plate.viewUrl)
}
        this.startPlateLoop(lane)
      }
    }
  },

  deactivated() {
    this.openCameraDropdownKey = ""

    for (const lane of this.lanes) {
      this.stopQrLoops(lane)
      this.stopQrPolling(lane)
      this.stopPlateLoop(lane)
    }
  },

  methods: {
    setQrCanvasRef(laneId, el) {
      if (el) {
        this.qrCanvasRefs[laneId] = el
        return
      }

      delete this.qrCanvasRefs[laneId]
    },

    setQrImageRef(laneId, el) {
      if (el) {
        this.qrImageRefs[laneId] = el
        return
      }

      delete this.qrImageRefs[laneId]
    },

    setQrVideoRef(laneId, el) {
      if (el) {
        this.qrVideoRefs[laneId] = el
        return
      }

      delete this.qrVideoRefs[laneId]
    },

    startQrPolling(lane) {
  if (lane.qr.resultTimer) return

  lane.qr.resultTimer = setInterval(async () => {
    if (!lane.qr.cameraRunning) return

    const res = await getQrResult()

    if (!res) return

    // trạng thái
    lane.qr.cameraRunning = !!res.running
    lane.qr.message = res.message || lane.qr.message
    lane.qr.sessionLocked = res.locked

    if (res.locked && res.qr) {
  if (lane.qr.qrPayload === res.qr && lane.qr.verifyMessage) {
    return
  }

  lane.qr.qrPayload = res.qr
  lane.qr.sessionLocked = true
  lane.qr.previewRunning = true

  // 📸 Lấy ảnh từ backend Python (chụp đúng lúc quét được QR)
  try {
    const imgRes = await getQrLockedImage()
    if (imgRes?.success && imgRes.image) {
      lane.qr.lockedSnapshot = imgRes.image
    } else {
      // fallback: lấy frame từ go2rtc nếu backend không có ảnh
      lane.qr.lockedSnapshot = this.buildQrSnapshotUrl(lane.qr.viewUrl)
    }
  } catch {
    lane.qr.lockedSnapshot = this.buildQrSnapshotUrl(lane.qr.viewUrl)
  }

  const result = await this.doVerifyQr(lane, res.qr)

  if (result?.success) {
    lane.qr.employeeId = result.data.employeeId
    lane.qr.employeeName = result.data.employeeName
    lane.qr.alert = false
  } else {
    lane.qr.alert = true
  }

  return // 🔥 STOP scan
}



  }, 300)
},

    stopQrPolling(lane) {
      if (lane.qr.resultTimer) {
        clearInterval(lane.qr.resultTimer)
        lane.qr.resultTimer = null
      }
    },

    isLaneReady(lane) {
      return (
        lane.qr.sessionLocked &&
        lane.plate.scanLocked &&
        !!lane.qr.employeeId &&
        !!lane.plate.confirmedPlate &&
        !lane.qr.alert
      )
    },

    laneAnyRunning(lane) {
      return lane.qr.cameraRunning || lane.plate.cameraRunning
    },

    qrStateText(qr) {
      if (!qr.cameraRunning) return "CHỜ"
      if (!qr.activeSessionPayload) return "ĐANG QUÉT"
      if (qr.activeSessionVerifyState === "waiting") return "ĐANG XÁC THỰC"
      if (qr.activeSessionVerifyState === "success") return "ĐÃ NHẬN DIỆN"
      if (qr.activeSessionVerifyState === "expired") return "HẾT HẠN"
      if (qr.activeSessionVerifyState === "invalid") return "KHÔNG HỢP LỆ"
      if (qr.activeSessionVerifyState === "failed") return "THẤT BẠI"
      if (qr.activeSessionVerifyState === "system_error") return "LỖI HỆ THỐNG"
      return "ĐANG XỬ LÝ"
    },

    qrStateClass(qr) {
      if (qr.alert) return "danger-text"
      if (qr.sessionLocked && qr.employeeId) return "ok-text"
      return "warn-text"
    },

    qrAlertText(qr) {
      return qr.verifyMessage || "Mã không hợp lệ"
    },

    shortText(value, max = 60) {
      const text = String(value || "").trim()
      if (!text) return "-----"
      return text.length <= max ? text : text.slice(0, max) + "..."
    },

    formatDate(value) {
      if (!value) return ""
      return new Date(value).toLocaleString()
    },

    nowText() {
      return new Date().toLocaleString()
    },

    buildDirectCameraUrl(inputUrl) {
      return normalizePreviewStreamUrl(inputUrl)
    },

    buildQrSnapshotUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""

      try {
        const url = new URL(raw, window.location.origin)
        const src = url.searchParams.get("src")

        if (/\/stream\.html$/i.test(url.pathname) && src) {
          url.pathname = url.pathname.replace(/\/stream\.html$/i, "/api/frame.jpeg")
          url.search = ""
          url.searchParams.set("src", src)
          url.searchParams.set("_ts", String(Date.now()))
          return url.toString()
        }

        if (/\/api\/stream\.(mp4|m3u8|mjpeg)$/i.test(url.pathname) && src) {
          url.pathname = url.pathname.replace(/\/api\/stream\.(mp4|m3u8|mjpeg)$/i, "/api/frame.jpeg")
          url.search = ""
          url.searchParams.set("src", src)
          url.searchParams.set("_ts", String(Date.now()))
          return url.toString()
        }

        if (/\/api\/frame\.jpeg$/i.test(url.pathname)) {
          url.searchParams.set("_ts", String(Date.now()))
          return url.toString()
        }
      } catch {
        // fallback below
      }

      return raw
    },

    async attachQrVideoPreview(laneId, qr) {
      await this.$nextTick()
      const video = this.qrVideoRefs[laneId]
      if (!video) return

      this.destroyQrHls(qr)

      try {
        video.pause()
      } catch {
        // ignore
      }

      video.removeAttribute("src")
      video.load()

      qr.previewHealthy = false
      video.src = qr.videoPreviewUrl

      try {
        await video.play()
      } catch {
        // ignore autoplay rejection
      }
    },

    async attachQrHlsPreview(laneId, qr) {
      await this.$nextTick()
      const video = this.qrVideoRefs[laneId]
      if (!video) return

      this.destroyQrHls(qr)

      try {
        video.pause()
      } catch {
        // ignore
      }

      video.removeAttribute("src")
      video.load()

      qr.previewHealthy = false

      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = qr.videoPreviewUrl
        try {
          await video.play()
        } catch {
          // ignore autoplay rejection
        }
        return
      }

      try {
        const Hls = await this.ensureHlsLibrary()
        if (!Hls?.isSupported?.()) {
          throw new Error("Trình duyệt này không hỗ trợ HLS.")
        }

        qr.hlsInstance = new Hls({
          enableWorker: true,
          lowLatencyMode: true
        })

        qr.hlsInstance.on(Hls.Events.ERROR, (_, data) => {
          if (data?.fatal) {
            this.onQrVideoPreviewError({ qr })
          }
        })

        qr.hlsInstance.loadSource(qr.videoPreviewUrl)
        qr.hlsInstance.attachMedia(video)
        qr.hlsInstance.on(Hls.Events.MANIFEST_PARSED, async () => {
          try {
            await video.play()
          } catch {
            // ignore autoplay rejection
          }
        })
      } catch (error) {
        console.error("attachQrHlsPreview error:", error)
        this.onQrVideoPreviewError({ qr })
      }
    },

    destroyQrHls(qr) {
      if (qr?.hlsInstance) {
        qr.hlsInstance.destroy()
        qr.hlsInstance = null
      }
    },

    destroyQrPreviewMedia(laneId, qr) {
      this.destroyQrHls(qr)
      const video = this.qrVideoRefs[laneId]
      if (video) {
        try {
          video.pause()
        } catch {
          // ignore
        }

        video.removeAttribute("src")
        video.load()
      }
    },

    async enableQrPreview(qr, url, laneId) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return

      qr.previewMode = resolveQrPreviewMode(cleanUrl)
      qr.previewHealthy = false
      qr.previewRunning = true
      qr.directCameraKey += 1

      if (qr.previewMode === "image") {
        this.destroyQrPreviewMedia(laneId, qr)
        qr.videoPreviewUrl = ""
        qr.directCameraUrl = this.buildDirectCameraUrl(cleanUrl)
        return
      }

      qr.directCameraUrl = ""
      qr.videoPreviewUrl = cleanUrl

      if (qr.previewMode === "video") {
        await this.attachQrVideoPreview(laneId, qr)
        return
      }

      if (qr.previewMode === "hls") {
        await this.attachQrHlsPreview(laneId, qr)
      }
    },

    isImagePreviewableUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return false
      if (raw.startsWith("data:image/")) return true
      if (/^rtsp:\/\//i.test(raw)) return false
      if (/\.mp4(\?|$)/i.test(raw)) return false
      if (/\.m3u8(\?|$)/i.test(raw)) return false
      return /^https?:\/\//i.test(raw) || raw.startsWith("/")
    },

    mountPreview(module, url) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return
      module.directCameraUrl = this.buildDirectCameraUrl(cleanUrl)
      module.directCameraKey += 1
      module.previewHealthy = false
      module.previewRunning = true
    },

    enablePlatePreview(module, url) {
      module.previewRunning = true

      if (this.isImagePreviewableUrl(url)) {
        this.mountPreview(module, url)
        return
      }

      module.directCameraUrl = ""
      module.directCameraKey += 1
      module.previewHealthy = !!(module.lockedSnapshot || module.lockedPlateCrop)
    },

    platePreviewDisplayUrl(plate) {
      if (!plate.previewRunning) return ""
      return plate.lockedSnapshot || plate.lockedPlateCrop || plate.directCameraUrl || ""
    },

    platePreviewKey(plate) {
      if (plate.lockedSnapshot || plate.lockedPlateCrop) {
        return `plate-capture-${plate.sessionId}-${plate.lastLockedImageSessionId}`
      }

      return plate.directCameraKey
    },

    platePreviewStatusText(plate) {
      if (!plate.previewRunning) return "Preview OFF"
      if (plate.lockedSnapshot || plate.lockedPlateCrop) return "Ảnh đã chụp"
      return plate.previewHealthy ? "Preview OK" : "Chờ ảnh"
    },

    platePreviewStatusClass(plate) {
      if (!plate.previewRunning) return "wait"
      if (plate.lockedSnapshot || plate.lockedPlateCrop) return "ok"
      return plate.previewHealthy ? "ok" : "wait"
    },

    refreshDirectPreview(module) {
      if (!module.previewRunning || !module.viewUrl) return
      if (module.imgBusy) return
      module.imgBusy = true
      module.directCameraUrl = this.buildDirectCameraUrl(module.viewUrl)
    },

    resetPreview(module) {
      module.directCameraUrl = ""
      module.directCameraKey += 1
      module.previewHealthy = false
      module.previewRunning = false
      module.imgBusy = false
      module.decodeBusy = false
      module.frameWidth = 0
      module.frameHeight = 0
    },

    resetQrPreview(laneId, qr) {
      this.destroyQrPreviewMedia(laneId, qr)
      qr.directCameraUrl = ""
      qr.videoPreviewUrl = ""
      qr.previewMode = "empty"
      qr.directCameraKey += 1
      qr.previewHealthy = false
      qr.previewRunning = false
      qr.imgBusy = false
      qr.decodeBusy = false
      qr.frameWidth = 0
      qr.frameHeight = 0
    },

    onPreviewLoaded(module) {
      module.previewHealthy = true
    },

    onPreviewError(module) {
      module.previewHealthy = false
    },

    onQrPreviewError(lane) {
      lane.qr.previewHealthy = false
      lane.qr.imgBusy = false
    },

    async onQrPreviewLoaded(lane) {
      lane.qr.previewHealthy = true
      lane.qr.imgBusy = false

      if (lane.qr.decodeBusy || lane.qr.verifying) return
      await this.captureAndDecodeQr(lane)
    },

    async onQrVideoPreviewLoaded(lane) {
      lane.qr.previewHealthy = true
      if (lane.qr.decodeBusy || lane.qr.verifying) return
      await this.captureAndDecodeQr(lane)
    },

    onQrVideoPreviewError(lane) {
      lane.qr.previewHealthy = false
    },

    clearQrState(qr) {
      qr.qrPayload = ""
      qr.manualPayload = ""
      qr.verifyMessage = ""
      qr.verifyData = null
      qr.employeeId = ""
      qr.employeeName = ""

      qr.activeSessionPayload = ""
      qr.activeSessionVerified = false
      qr.activeSessionVerifyState = ""
      qr.activeSessionVerifyMessage = ""
      qr.lastSeenAt = null

      qr.lastDecodedText = ""
      qr.lastDecodedAt = 0
      qr.lastUpdate = ""
      qr.message = ""
      qr.alert = false
      qr.sessionLocked = false
      qr.lockedSnapshot = ""
    },

    clearPlateState(plate) {
      plate.confirmedPlate = ""
      plate.lastRawPlate = ""
      plate.scanLocked = false
      plate.lockedSnapshot = ""
      plate.lockedPlateCrop = ""
      plate.message = ""
      plate.fps = 0
      plate.ocrRunning = false
      plate.stableCount = 0
      plate.movingFast = false
      plate.lastUpdate = ""
      plate.lastLockedImageSessionId = 0
    },

    hardResetQr(qr) {
      qr.cameraRunning = false
      qr.currentIp = ""
      this.clearQrState(qr)
    },

    hardResetPlate(plate) {
      plate.cameraRunning = false
      plate.currentIp = ""
      plate.sessionId = 0
      plate.lastAppliedSessionId = 0
      this.clearPlateState(plate)
    },

    startQrPreviewLoop(lane) {
      this.stopQrPreviewLoop(lane)
      lane.qr.previewTimer = setInterval(() => {
        if (lane.qr.destroyed) return
        if (!lane.qr.cameraRunning) return
        if (lane.qr.previewMode === "image") {
          this.refreshDirectPreview(lane.qr)
          return
        }

        if (lane.qr.previewMode === "video" || lane.qr.previewMode === "hls") {
          this.captureAndDecodeQr(lane)
        }
      }, lane.qr.previewIntervalMs)
    },

    stopQrPreviewLoop(lane) {
      if (lane.qr.previewTimer) {
        clearInterval(lane.qr.previewTimer)
        lane.qr.previewTimer = null
      }
    },

    startQrSessionLoop(lane) {
      this.stopQrSessionLoop(lane)
      lane.qr.sessionTimer = setInterval(() => {
        if (lane.qr.destroyed) return
        if (!lane.qr.cameraRunning) return
        this.checkQrSessionExpiry(lane)
      }, 200)
    },

    stopQrSessionLoop(lane) {
      if (lane.qr.sessionTimer) {
        clearInterval(lane.qr.sessionTimer)
        lane.qr.sessionTimer = null
      }
    },

    stopQrLoops(lane) {
      this.stopQrPreviewLoop(lane)
      this.stopQrSessionLoop(lane)
    },

    checkQrSessionExpiry(lane) {
      const qr = lane.qr
      if (qr.sessionLocked) return
      if (!qr.activeSessionPayload || !qr.lastSeenAt) return

      const now = Date.now()
      const diff = now - qr.lastSeenAt

      if (diff >= qr.absenceThresholdMs) {
        this.clearQrState(qr)
        qr.message = "Mã đã biến mất khỏi camera, phiên cũ đã tự động kết thúc. Đang chờ mã mới."
        qr.lastUpdate = this.nowText()
      }
    },

    async captureAndDecodeQr(lane) {
      const qr = lane.qr
      const canvas = this.qrCanvasRefs[lane.id]
      const mode = qr.previewMode

      if (!canvas) return
      if (qr.decodeBusy) return

      let source = null
      let sourceWidth = 0
      let sourceHeight = 0

      if (mode === "image") {
        const img = this.qrImageRefs[lane.id]
        if (!img || !img.complete) return
        source = img
        sourceWidth = img.naturalWidth || img.width
        sourceHeight = img.naturalHeight || img.height
      } else if (mode === "video" || mode === "hls") {
        const video = this.qrVideoRefs[lane.id]
        if (!video || video.readyState < 2) return
        source = video
        sourceWidth = video.videoWidth || video.clientWidth
        sourceHeight = video.videoHeight || video.clientHeight
      } else {
        return
      }

      qr.decodeBusy = true

      try {
        if (!sourceWidth || !sourceHeight) return

        qr.frameWidth = sourceWidth
        qr.frameHeight = sourceHeight

        let targetWidth = sourceWidth
        let targetHeight = sourceHeight

        if (sourceWidth > qr.decodeMaxWidth) {
          const ratio = qr.decodeMaxWidth / sourceWidth
          targetWidth = Math.round(sourceWidth * ratio)
          targetHeight = Math.round(sourceHeight * ratio)
        }

        canvas.width = targetWidth
        canvas.height = targetHeight

        const ctx = canvas.getContext("2d", { willReadFrequently: true })
        ctx.clearRect(0, 0, targetWidth, targetHeight)
        ctx.drawImage(source, 0, 0, targetWidth, targetHeight)

        const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight)
        const code = jsQR(imageData.data, targetWidth, targetHeight, {
          inversionAttempts: "attemptBoth"
        })

        if (!code?.data) return

        const decodedText = String(code.data || "").trim()
        if (!decodedText) return

        const now = Date.now()

        qr.qrPayload = decodedText
        qr.manualPayload = decodedText
        qr.lastDecodedText = decodedText
        qr.lastDecodedAt = now

        if (qr.activeSessionPayload && decodedText === qr.activeSessionPayload) {
          qr.lastSeenAt = now
          return
        }

        qr.activeSessionPayload = decodedText
        qr.activeSessionVerified = false
        qr.activeSessionVerifyState = "waiting"
        qr.activeSessionVerifyMessage = "Đã phát hiện mã mới, đang xác thực..."
        qr.lastSeenAt = now
        qr.lastUpdate = this.nowText()
        qr.message = "Đang xác thực QR..."

        const result = await this.doVerifyQr(lane, decodedText)

        if (result?.success) {
          qr.activeSessionVerified = true
          qr.activeSessionVerifyState = "success"
          qr.activeSessionVerifyMessage = result.message || "Xác thực QR thành công."
          qr.sessionLocked = true
          qr.lockedSnapshot = canvas.toDataURL("image/jpeg", 0.92)
          qr.alert = false
          qr.employeeId = result?.data?.employeeId ? String(result.data.employeeId) : ""
          qr.employeeName = result?.data?.employeeName || ""
          qr.message = result.message || "QR hợp lệ"
          return
        }

        const message = String(result?.message || "")
        qr.sessionLocked = false
        qr.employeeId = ""
        qr.employeeName = ""

        if (message.includes("đã hết hạn") || message.includes("chưa đến hiệu lực")) {
          qr.activeSessionVerifyState = "expired"
        } else if (message.includes("không hợp lệ")) {
          qr.activeSessionVerifyState = "invalid"
        } else {
          qr.activeSessionVerifyState = "failed"
        }

        qr.activeSessionVerifyMessage = message || "Xác thực thất bại."
        qr.verifyMessage = message || "Xác thực thất bại."
        qr.alert = true
        qr.message = qr.verifyMessage
      } catch (e) {
        console.warn("Decode QR frame error:", e)
        qr.verifyMessage = "Không đọc được frame từ IP camera. Kiểm tra CORS, mixed content hoặc URL stream."
        qr.activeSessionVerifyState = "system_error"
        qr.activeSessionVerifyMessage = qr.verifyMessage
        qr.alert = true
        qr.sessionLocked = false
        qr.employeeId = ""
        qr.employeeName = ""
        qr.message = qr.verifyMessage
      } finally {
        qr.decodeBusy = false
      }
    },

    async doVerifyQr(lane, payload) {
      const qr = lane.qr
      qr.verifying = true

      try {
        const result = await verifyDynamicQr(payload, qr.scannerDevice)

        qr.verifyMessage = result?.message || ""
        qr.verifyData = result?.data || null
        qr.lastUpdate = this.nowText()

        return {
          success: !!result?.success,
          message: result?.message || "",
          data: result?.data || null
        }
      } catch (error) {
        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Xác thực thất bại."

        qr.verifyMessage = message
        qr.verifyData = null
        qr.lastUpdate = this.nowText()

        return {
          success: false,
          message,
          data: null
        }
      } finally {
        qr.verifying = false
      }
    },

    stopPlateLoop(lane) {
      const plate = lane.plate
      if (plate.resultTimer) {
        clearInterval(plate.resultTimer)
        plate.resultTimer = null
      }
      plate.busyResult = false
    },

    startPlateLoop(lane) {
      this.stopPlateLoop(lane)

      lane.plate.resultTimer = setInterval(async () => {
        if (lane.plate.destroyed) return
        if (!lane.plate.cameraRunning) return
        if (lane.plate.busyResult) return

        lane.plate.busyResult = true
        try {
          await this.refreshPlate(lane)
        } finally {
          lane.plate.busyResult = false
        }
      }, 500)
    },

    async loadStatusPlate(lane) {
      try {
        const res = await lane.plateApi.getCameraStatus()
        await this.applyPlateRealtimeState(lane, res, false)

        if (lane.plate.viewUrl) {
  this.mountPreview(lane.plate, lane.plate.viewUrl)
}
      } catch (e) {
        console.error("loadStatusPlate error:", e)
      }
    },

    async refreshPlate(lane) {
      try {
        const res = await lane.plateApi.getCameraResult()
        await this.applyPlateRealtimeState(lane, res, true)
      } catch (e) {
        console.warn("refreshPlate error:", e)
      }
    },

    async fetchPlateLockedImages(lane, force = false) {
      const plate = lane.plate
      if (plate.destroyed) return
      if (!plate.cameraRunning) return

      if (!plate.scanLocked) {
        plate.lockedSnapshot = ""
        plate.lockedPlateCrop = ""
        plate.lastLockedImageSessionId = 0
        return
      }

      if (plate.isFetchingLockedImages) return
      if (!force && plate.lastLockedImageSessionId === plate.sessionId) return

      plate.isFetchingLockedImages = true
      try {
        const res = await lane.plateApi.getLockedImages()
        const responseSessionId = Number(res?.session_id || 0)

        if (responseSessionId !== plate.sessionId) return

        if (res?.scan_locked) {
          plate.lockedSnapshot = res.locked_snapshot || ""
          plate.lockedPlateCrop = res.locked_plate_crop || ""
          plate.lastLockedImageSessionId = responseSessionId
          if (plate.previewRunning && (plate.lockedSnapshot || plate.lockedPlateCrop)) {
            plate.previewHealthy = true
          }
        } else {
          plate.lockedSnapshot = ""
          plate.lockedPlateCrop = ""
          plate.lastLockedImageSessionId = 0
        }
      } catch (e) {
        console.warn("fetchPlateLockedImages error:", e)
      } finally {
        plate.isFetchingLockedImages = false
      }
    },

    async applyPlateRealtimeState(lane, res, allowTurnOffReset = true) {
      if (!res || lane.plate.destroyed) return

      const plate = lane.plate
      const incomingSessionId = Number(res.session_id || 0)

      if (incomingSessionId > 0) {
        if (plate.lastAppliedSessionId > 0 && incomingSessionId < plate.lastAppliedSessionId) {
          return
        }

        if (incomingSessionId > plate.lastAppliedSessionId) {
          plate.lastAppliedSessionId = incomingSessionId
          plate.sessionId = incomingSessionId
          plate.lastLockedImageSessionId = 0
        } else if (!plate.sessionId) {
          plate.sessionId = incomingSessionId
        }
      }

      const incomingCameraEnabled = !!res.camera_enabled

      plate.cameraRunning = incomingCameraEnabled
      plate.currentIp = res.ip || plate.currentIp
      plate.confirmedPlate = formatLicensePlateDisplay(res.confirmed_plate || "")
      plate.lastRawPlate = res.last_raw_plate || ""
      plate.scanLocked = !!res.scan_locked
      plate.fps = Number(res.fps || 0)
      plate.ocrRunning = !!res.ocr_running
      plate.stableCount = Number(res.stable_count || 0)
      plate.movingFast = !!res.moving_fast
      plate.message = res.message || ""
      plate.lastUpdate = res.last_update || ""

      if (!plate.scanLocked) {
        plate.lockedSnapshot = ""
        plate.lockedPlateCrop = ""
        plate.lastLockedImageSessionId = 0
      }

      if (!incomingCameraEnabled && allowTurnOffReset) {
        this.stopPlateLoop(lane)
        this.hardResetPlate(plate)
        return
      }

      if (plate.scanLocked) {
        await this.fetchPlateLockedImages(lane, false)
      }
    },

    async previewLane(lane) {
  if (!lane.qr.cameraIp.trim() && !lane.plate.cameraIp.trim()) {
    alert("Vui lòng nhập ít nhất 1 URL camera")
    return
  }

  // 🔥 chống spam click
  if (lane.loading) return

  try {
    lane.loading = true
    

    // ===== QR =====
    if (lane.qr.viewUrl) {
      if (lane.qr.previewRunning) {
        // 🔥 STEP 1: tắt nhẹ
        this.resetQrPreview(lane.id, lane.qr)

        // 🔥 STEP 2: chờ camera release
        await new Promise(r => setTimeout(r, 300))
      }

      // 🔥 STEP 3: mở lại
      await this.enableQrPreview(lane.qr, lane.qr.viewUrl, lane.id)
      lane.qr.message = "Đã reload preview QR"
    }

    // ===== PLATE =====
    if (lane.plate.viewUrl) {
      if (lane.plate.previewRunning) {
        this.resetPreview(lane.plate)

        // 🔥 delay cực quan trọng
        await new Promise(r => setTimeout(r, 300))
      }

      this.mountPreview(lane.plate, lane.plate.viewUrl)
      lane.plate.message = "Đã reload preview Plate"
    }

  } catch (e) {
    console.error("previewLane error:", e)
    alert(e?.message || "Lỗi mở preview")
  } finally {
    lane.loading = false
  }
},

    async readAllLane(lane) {
      if (!lane.qr.cameraIp.trim() || !lane.plate.cameraIp.trim()) {
        alert("Vui lòng nhập đủ URL QR và Plate")
        return
      }

      try {
        lane.loading = true

        

        

 // 🔥 reset QR trước khi scan
await resetQr()

// 🧠 nếu chưa chạy → start
if (!lane.qr.cameraRunning) {
  await startQr(lane.qr.cameraIp)
}

// scan mới
await scanQr()

// 🔥 reset frontend state
this.clearQrState(lane.qr)

lane.qr.cameraRunning = true
if (lane.qr.viewUrl) {
  await this.enableQrPreview(lane.qr, lane.qr.viewUrl, lane.id)
} else {
  lane.qr.previewRunning = true
}
lane.qr.sessionLocked = false
lane.qr.message = "Đang scan QR từ Python"

this.startQrPolling(lane)

        // Plate: giữ nguyên API cũ
        if (!lane.plate.cameraRunning) {
          this.stopPlateLoop(lane)
          const resPlate = await lane.plateApi.turnOnCamera(lane.plate.currentIp)
          if (!resPlate?.success) {
            alert(resPlate?.message || "Không thể khởi tạo Plate")
            return
          }
          lane.plate.cameraRunning = true
          lane.plate.sessionId = Number(resPlate.session_id || 0)
          lane.plate.lastAppliedSessionId = lane.plate.sessionId
          lane.plate.message = resPlate.message || "Khởi tạo Plate thành công"
        } else {
          const resPlate = await lane.plateApi.resetCameraState()
          lane.plate.message = resPlate?.message || "Đã reset Plate"

          const newSessionId = Number(resPlate?.session_id || 0)
          if (newSessionId > 0) {
            lane.plate.sessionId = newSessionId
            lane.plate.lastAppliedSessionId = newSessionId
          }
        }

        await this.refreshPlate(lane)
        if (!lane.plate.resultTimer) this.startPlateLoop(lane)
      } catch (e) {
        console.error("readAllLane error:", e)
        alert(e?.message || "Lỗi đọc cả 2")
      } finally {
        lane.loading = false
      }
    },

    async retryQr(lane) {
  if (!lane.qr.cameraIp.trim()) {
    alert("Vui lòng nhập URL QR")
    return
  }

  try {
    lane.loading = true

    // 🧠 Nếu chưa chạy → mở cam trước
    if (!lane.qr.cameraRunning) {
      await startQr(lane.qr.cameraIp)
    }

    // reset state
    await resetQr()

    // scan lại
    await scanQr()

    this.clearQrState(lane.qr)

    lane.qr.cameraRunning = true
    if (lane.qr.viewUrl) {
      await this.enableQrPreview(lane.qr, lane.qr.viewUrl, lane.id)
    } else {
      lane.qr.previewRunning = true
    }
    lane.qr.sessionLocked = false
    lane.qr.message = "Đang scan lại QR..."

    // 🔥 đảm bảo polling chạy
    this.startQrPolling(lane)

  } catch (e) {
    console.error("retryQr error:", e)
    alert(e?.message || "Lỗi đọc lại QR")
  } finally {
    lane.loading = false
  }
},

    async retryPlate(lane) {
      if (!lane.plate.cameraIp.trim()) {
        alert("Vui lòng nhập URL Plate")
        return
      }

      try {
        lane.loading = true

        
        

        this.clearPlateState(lane.plate)

        if (!lane.plate.cameraRunning) {
          this.stopPlateLoop(lane)
          const res = await lane.plateApi.turnOnCamera(lane.plate.currentIp)
          if (!res?.success) {
            alert(res?.message || "Không thể khởi tạo Plate")
            return
          }
          lane.plate.cameraRunning = true
          lane.plate.sessionId = Number(res.session_id || 0)
          lane.plate.lastAppliedSessionId = lane.plate.sessionId
          lane.plate.message = res.message || "Khởi tạo Plate thành công"
        } else {
          const res = await lane.plateApi.resetCameraState()
          lane.plate.message = res?.message || "Đã reset Plate"

          const newSessionId = Number(res?.session_id || 0)
          if (newSessionId > 0) {
            lane.plate.sessionId = newSessionId
            lane.plate.lastAppliedSessionId = newSessionId
          }
        }

        await this.refreshPlate(lane)
        if (!lane.plate.resultTimer) this.startPlateLoop(lane)
      } catch (e) {
        console.error("retryPlate error:", e)
        alert(e?.message || "Lỗi đọc lại biển số")
      } finally {
        lane.loading = false
      }
    },

    async stopLane(lane) {
  try {
    lane.loading = true

    // 🔥 1. tắt Python scan
    try {
      await stopQr()
    } catch (e) {
      console.warn("stopQr warning:", e)
    }

    // 🔥 2. dừng polling QR
    if (lane.qr.resultTimer) {
      clearInterval(lane.qr.resultTimer)
      lane.qr.resultTimer = null
    }

    // 🔥 3. reset QR frontend
    this.stopQrLoops(lane)
    this.hardResetQr(lane.qr)
    this.resetQrPreview(lane.id, lane.qr)

    // ===== PLATE giữ nguyên =====
    this.stopPlateLoop(lane)

    try {
      const resPlate = await lane.plateApi.turnOffCamera()
      lane.plate.message = resPlate?.message || "Đã tắt Plate"
    } catch (e) {
      console.warn("turnOff plate warning:", e)
    }

    this.hardResetPlate(lane.plate)
    this.resetPreview(lane.plate)

  } catch (e) {
    console.error("stopLane error:", e)
    alert(e?.message || "Lỗi tắt làn")
  } finally {
    lane.loading = false
  }
},

    async confirmLane(lane) {
      const employeeId = Number(lane.qr.employeeId || 0)
      const licensePlate = String(lane.plate.confirmedPlate || "").trim()
      const gateId = lane.plate.gateId ?? lane.qr.gateId ?? null
      const cameraId = lane.plate.cameraId ?? lane.qr.cameraId ?? null
      const direction = normalizeLaneDirection(
        lane.movementDirection,
        getDefaultLaneDirection(lane.id)
      ) || "IN"

      if (!employeeId) {
        alert(`${lane.name}: chưa có Employee ID`)
        return
      }

      if (!licensePlate) {
        alert(`${lane.name}: chưa có biển số`)
        return
      }

      try {
        lane.loading = true

        // Vẫn dùng API thông hành cũ, chỉ lấy employeeId từ QR verify
        lane.movementDirection = direction
        this.persistLaneDirection(lane)

        const payload = {
          employeeId,
          licensePlate,
          direction,
          gateId,
          cameraId
        }

        const res = await confirmGateLocally(payload)
        const data = res.data

        if (data?.success) {
          alert(`${lane.name}: ${data.message}`)
        } else {
          alert(`${lane.name}: ${data?.message || "Xử lý thất bại"}`)
        }
      } catch (error) {
        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Không gọi được API Gate"

        alert(`${lane.name}: ${message}`)
      } finally {
        lane.loading = false
      }
    },

    // ================= CAMERA SEARCH =================

getLaneDirectionStorageKey(laneId) {
  return `${LANE_DIRECTION_STORAGE_PREFIX}-${laneId}`
},

restoreLaneDirections() {
  for (const lane of this.lanes) {
    const storageKey = this.getLaneDirectionStorageKey(lane.id)
    const savedDirection = localStorage.getItem(storageKey)
    lane.movementDirection = normalizeLaneDirection(
      savedDirection,
      getDefaultLaneDirection(lane.id)
    )
  }
},

persistLaneDirection(lane) {
  const storageKey = this.getLaneDirectionStorageKey(lane.id)
  const normalizedDirection = normalizeLaneDirection(
    lane.movementDirection,
    getDefaultLaneDirection(lane.id)
  )

  lane.movementDirection = normalizedDirection
  localStorage.setItem(storageKey, normalizedDirection)
},

handleLaneDirectionChange(lane) {
  this.persistLaneDirection(lane)
},

laneDirectionText(lane) {
  return getLaneDirectionLabel(lane.movementDirection)
},

syncLaneDirectionFromCamera(lane, camera) {
  const storageKey = this.getLaneDirectionStorageKey(lane.id)
  if (localStorage.getItem(storageKey)) {
    return
  }

  const inferredDirection = normalizeLaneDirection(
    camera?.movementDirection || inferMovementDirection(
      camera?.name || camera?.cameraName,
      camera?.gateName,
      camera?.cameraType
    ),
    ""
  )

  if (!inferredDirection) {
    return
  }

  lane.movementDirection = inferredDirection
  this.persistLaneDirection(lane)
},

getCameraSearchKey(laneId, type) {
  return `${laneId}-${type}`
},

setCameraSearchRef(laneId, type, el) {
  const key = this.getCameraSearchKey(laneId, type)

  if (el) {
    this.cameraSearchRefs[key] = el
    return
  }

  delete this.cameraSearchRefs[key]
},

openCameraDropdown(laneId, type) {
  this.openCameraDropdownKey = this.getCameraSearchKey(laneId, type)
},

closeCameraDropdown(laneId, type) {
  const key = this.getCameraSearchKey(laneId, type)
  if (this.openCameraDropdownKey === key) {
    this.openCameraDropdownKey = ""
  }
},

isCameraDropdownOpen(laneId, type) {
  return this.openCameraDropdownKey === this.getCameraSearchKey(laneId, type)
},

handleDocumentPointerDown(event) {
  const currentKey = this.openCameraDropdownKey
  if (!currentKey) return

  const searchBox = this.cameraSearchRefs[currentKey]
  if (searchBox?.contains?.(event.target)) return

  this.openCameraDropdownKey = ""
},

handleCameraSearchInput(lane, type) {
  this.openCameraDropdown(lane.id, type)
  const val = this.cameraSearch[this.getCameraSearchKey(lane.id, type)]
  if (!val || val.trim() === "") {
    if (type === "qr") {
      lane.qr.cameraId = null
      lane.qr.cameraIp = ""
      lane.qr.viewUrl = ""
      lane.qr.cameraRunning = false
      lane.qr.previewRunning = false
      this.resetQrPreview(lane.id, lane.qr)
    } else {
      lane.plate.cameraId = null
      lane.plate.cameraIp = ""
      lane.plate.viewUrl = ""
      lane.plate.cameraRunning = false
      lane.plate.previewRunning = false
      this.resetPreview(lane.plate)
    }
    this.persistLaneCameraSelection(lane, type)
  }
},


buildCameraSearchLabel(cam) {
  const cameraId = cam?.id ?? cam?.cameraId ?? ""
  const cameraName = cam?.name || cam?.cameraName || "Camera"
  return cameraId ? `${cameraName} (ID: ${cameraId})` : cameraName
},

async loadCameraList() {
  try {
    this.cameras = await fetchSetCamCatalog()
    // this.applyInitialCameraSelections()
  } catch (e) {
    console.error("loadCameraList error:", e)
  }
},

filterCameras(keyword) {
  const key = String(keyword || "").trim().toLowerCase()
  if (!key) return this.cameras

  return this.cameras.filter((camera) =>
    String(camera.cameraName || camera.name || "").toLowerCase().includes(key) ||
    String(camera.gateName || camera.label || "").toLowerCase().includes(key) ||
    String(camera.cameraId || camera.id || "").includes(key)
  )
},

selectCamera(cam, lane, type) {
  const sourceUrl = String(
    cam.sourceUrl || cam.streamUrl || cam.browserPreviewUrl || cam.urlView || ""
  ).trim()
  const previewUrl = String(cam.browserPreviewUrl || cam.urlView || sourceUrl).trim()
  const cameraId = cam.id ?? cam.cameraId ?? null
  const cameraName = cam.name || cam.cameraName || ""
  const selectedLabel = this.buildCameraSearchLabel(cam)

  if (!sourceUrl) {
    alert("Camera chưa có URL stream hoặc URL preview. Hãy reload go2rtc trước.")
    return
  }

  if (type === "qr") {
    lane.qr.cameraId = cameraId
    lane.qr.cameraName = cameraName
    lane.qr.cameraIp = sourceUrl
    lane.qr.gateId = cam.gateId ?? null
    lane.qr.gateName = cam.gateName || ""
    lane.qr.viewUrl = previewUrl
    lane.qr.currentIp = sourceUrl

    this.cameraSearch[this.getCameraSearchKey(lane.id, "qr")] = selectedLabel
    lane.qr.lockedSnapshot = ""
    if (lane.qr.viewUrl) {
      this.enableQrPreview(lane.qr, lane.qr.viewUrl, lane.id)
    } else {
      lane.qr.previewRunning = true
      lane.qr.previewHealthy = false
    }
    this.persistLaneCameraSelection(lane, "qr")
    this.syncLaneDirectionFromCamera(lane, cam)
  }

  if (type === "plate") {
    lane.plate.cameraId = cameraId
    lane.plate.cameraName = cameraName
    lane.plate.cameraIp = sourceUrl
    lane.plate.viewUrl = previewUrl
    lane.plate.currentIp = sourceUrl
    lane.plate.gateId = cam.gateId ?? null
    lane.plate.gateName = cam.gateName || ""

    this.cameraSearch[this.getCameraSearchKey(lane.id, "plate")] = selectedLabel
    if (lane.plate.viewUrl) {
      this.mountPreview(lane.plate, lane.plate.viewUrl)
    } else {
      lane.plate.previewRunning = true
      lane.plate.previewHealthy = false
    }
    this.persistLaneCameraSelection(lane, "plate")
    this.syncLaneDirectionFromCamera(lane, cam)
  }

  this.closeCameraDropdown(lane.id, type)
},

getLaneCameraStorageKey(laneId, type) {
  return `${LANE_CAMERA_STORAGE_PREFIX}:${laneId}:${type}`
},

persistLaneCameraSelection(lane, type) {
  const module = lane[type]
  const storageKey = this.getLaneCameraStorageKey(lane.id, type)

  if (module?.cameraId) {
    localStorage.setItem(storageKey, String(module.cameraId))
    return
  }

  localStorage.removeItem(storageKey)
},

applyInitialCameraSelections() {
  const usedQrCameraIds = []
  const usedPlateCameraIds = []
  let hasSavedSelection = false

  for (const lane of this.lanes) {
    const savedQrCameraId = localStorage.getItem(this.getLaneCameraStorageKey(lane.id, "qr")) || ""
    const savedPlateCameraId = localStorage.getItem(this.getLaneCameraStorageKey(lane.id, "plate")) || ""

    hasSavedSelection = hasSavedSelection || !!savedQrCameraId || !!savedPlateCameraId

    if (savedQrCameraId) {
      const qrCamera = this.cameras.find(
        (camera) => String(camera.id ?? camera.cameraId) === String(savedQrCameraId)
      )

      if (qrCamera) {
        usedQrCameraIds.push(String(qrCamera.id ?? qrCamera.cameraId))
        this.selectCamera(qrCamera, lane, "qr")
      }
    }

    if (savedPlateCameraId) {
      const plateCamera = this.cameras.find(
        (camera) => String(camera.id ?? camera.cameraId) === String(savedPlateCameraId)
      )

      if (plateCamera) {
        usedPlateCameraIds.push(String(plateCamera.id ?? plateCamera.cameraId))
        this.selectCamera(plateCamera, lane, "plate")
      }
    }
  }

  if (hasSavedSelection) {
    return
  }

  for (const lane of this.lanes) {
    const qrCamera = pickDefaultSetCamCamera(this.cameras, {
      role: "qr",
      excludedIds: usedQrCameraIds,
    })

    if (qrCamera) {
      usedQrCameraIds.push(String(qrCamera.id ?? qrCamera.cameraId))
      this.selectCamera(qrCamera, lane, "qr")
    }

    const plateCamera = pickDefaultSetCamCamera(this.cameras, {
      role: "plate",
      excludedIds: usedPlateCameraIds,
    })

    if (plateCamera) {
      usedPlateCameraIds.push(String(plateCamera.id ?? plateCamera.cameraId))
      this.selectCamera(plateCamera, lane, "plate")
    }
  }
}
    
  }
}
</script>

<style scoped>
/* ========== Page & Topbar ========== */
.page {
  padding: 0;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.topbar-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.topbar-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--accent-gradient);
  color: #fff;
  box-shadow: 0 12px 28px rgba(15, 124, 130, 0.22);
}

.topbar-desc {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 0.92rem;
}

/* ========== Lane Grid ========== */
.lane-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.lane-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--glass-blur);
  transition:
    border-color var(--transition-normal),
    box-shadow var(--transition-normal),
    transform var(--transition-normal);
}

.lane-card:hover {
  box-shadow: var(--shadow-md);
}

.lane-card.ready {
  border-color: rgba(15, 124, 130, 0.32);
  box-shadow: var(--shadow-glow);
}

/* ========== Lane Head ========== */
.lane-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
}

.lane-head-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lane-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(15, 124, 130, 0.1);
  color: var(--accent-primary);
  transition: all var(--transition-normal);
}

.lane-icon.active {
  background: var(--accent-gradient);
  color: #fff;
  box-shadow: 0 8px 20px rgba(15, 124, 130, 0.2);
}

.lane-head h2 {
  margin: 0;
  font-family: var(--font-heading);
  font-size: 1.28rem;
  font-weight: 700;
  color: var(--text-primary);
}

.lane-head p {
  margin: 3px 0 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.lane-final-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 180px;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.lane-final-status.ok {
  background: rgba(20, 134, 109, 0.12);
  color: var(--accent-success);
}

.lane-final-status.ok .status-dot {
  box-shadow: 0 0 0 4px rgba(20, 134, 109, 0.15);
  animation: pulseGlow 2s ease-in-out infinite;
}

.lane-final-status.wait {
  background: rgba(184, 111, 33, 0.1);
  color: var(--accent-warning);
}

/* ========== Lane Actions ========== */
.lane-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 40px;
  border: none;
  border-radius: 999px;
  padding: 0 16px;
  color: white;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-preview {
  background: var(--accent-gradient);
  box-shadow: 0 8px 20px rgba(15, 124, 130, 0.18);
}

.btn-preview:hover:not(:disabled) {
  box-shadow: 0 12px 28px rgba(15, 124, 130, 0.26);
}

.btn-main {
  background: linear-gradient(135deg, var(--steel-500), var(--steel-600));
  box-shadow: 0 8px 20px rgba(43, 109, 138, 0.18);
}

.btn-main:hover:not(:disabled) {
  box-shadow: 0 12px 28px rgba(43, 109, 138, 0.26);
}

.btn-sub {
  background: rgba(61, 93, 118, 0.12);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-sub:hover:not(:disabled) {
  background: rgba(61, 93, 118, 0.18);
  border-color: var(--border-color-hover);
  color: var(--text-primary);
}

.btn-off {
  background: rgba(195, 81, 70, 0.1);
  color: var(--accent-danger);
  border: 1px solid rgba(195, 81, 70, 0.2);
}

.btn-off:hover:not(:disabled) {
  background: rgba(195, 81, 70, 0.16);
}

.btn-confirm {
  background: linear-gradient(135deg, var(--ink-900), var(--ink-950));
  box-shadow: 0 8px 20px rgba(16, 32, 51, 0.18);
}

.btn-confirm:hover:not(:disabled) {
  box-shadow: 0 12px 28px rgba(16, 32, 51, 0.26);
}

/* ========== IP Row / Camera Search ========== */
.ip-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.ip-box label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.ip-box input {
  width: 100%;
  min-height: 44px;
  border: 1px solid rgba(24, 49, 77, 0.1);
  border-radius: 14px;
  padding: 0 14px;
  font-size: 0.92rem;
  background: var(--bg-input);
  color: var(--text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.ip-box input:focus {
  border-color: rgba(15, 124, 130, 0.36);
  box-shadow: 0 0 0 4px rgba(84, 196, 211, 0.18);
  background: rgba(255, 255, 255, 0.96);
}

.ip-box input::placeholder {
  color: var(--text-muted);
}

/* ========== Summary Bar ========== */
.summary-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.summary-item {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: 12px 14px;
  transition: border-color var(--transition-fast);
}

.summary-item:hover {
  border-color: var(--border-color-hover);
}

.summary-item .label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.summary-item .value {
  display: block;
  font-size: 0.94rem;
  font-weight: 700;
  word-break: break-word;
  color: var(--text-primary);
}

.direction-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.direction-select {
  width: 100%;
  min-height: 42px;
  border: 1px solid rgba(24, 49, 77, 0.1);
  border-radius: 12px;
  padding: 0 12px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.direction-select:focus {
  border-color: rgba(15, 124, 130, 0.36);
  box-shadow: 0 0 0 4px rgba(84, 196, 211, 0.18);
  outline: none;
}

.direction-hint {
  display: block;
  font-size: 0.78rem;
  color: var(--accent-primary);
  font-weight: 700;
}

.strong {
  font-size: 1.24rem !important;
  font-weight: 800 !important;
}

.plate {
  color: var(--accent-success);
  letter-spacing: 1.5px;
  font-family: var(--font-heading);
}

.ok-text {
  color: var(--accent-success);
}

.warn-text {
  color: var(--accent-warning);
}

.danger-text {
  color: var(--accent-danger);
}

/* ========== Camera Stack ========== */
.camera-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.cam-block {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: 14px;
  background: var(--bg-card-strong);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.cam-block:hover {
  border-color: var(--border-color-hover);
  box-shadow: var(--shadow-sm);
}

.cam-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.cam-head-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
}

.mini-status {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.mini-status.ok {
  background: rgba(20, 134, 109, 0.12);
  color: var(--accent-success);
}

.mini-status.wait {
  background: rgba(184, 111, 33, 0.1);
  color: var(--accent-warning);
}

/* ========== Camera Preview ========== */
.cam-preview {
  width: 100%;
  height: clamp(280px, 26vw, 460px);
  min-height: 280px;
  background: var(--ink-950);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  margin-bottom: 12px;
  position: relative;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border: 0;
}

.hidden-canvas {
  display: none;
}

.cam-off {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: rgba(188, 209, 218, 0.6);
  align-items: center;
  justify-content: center;
  font-size: 0.92rem;
  font-weight: 600;
}

.cam-off-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(188, 209, 218, 0.08);
  border: 1px solid rgba(188, 209, 218, 0.12);
}

/* ========== Result Pills ========== */
.quick-result {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.result-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.result-pill.ok {
  background: rgba(20, 134, 109, 0.12);
  color: var(--accent-success);
}

.result-pill.wait {
  background: rgba(184, 111, 33, 0.1);
  color: var(--accent-warning);
}

.result-pill.danger {
  background: rgba(195, 81, 70, 0.1);
  color: var(--accent-danger);
}

.result-pill.neutral {
  background: rgba(61, 93, 118, 0.08);
  color: var(--text-secondary);
}

.result-pill.off {
  background: rgba(24, 49, 77, 0.05);
  color: var(--text-muted);
}

/* ========== QR Data Grid ========== */
.qr-data-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.qr-data-box {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: border-color var(--transition-fast);
}

.qr-data-box:hover {
  border-color: var(--border-color-hover);
}

.small-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.small-value {
  font-size: 0.82rem;
  color: var(--text-primary);
  font-weight: 700;
  word-break: break-word;
}

/* ========== Verify Box ========== */
.verify-box {
  margin-top: 10px;
  padding: 14px;
  border-radius: var(--border-radius-sm);
  background: var(--bg-input);
  border: 1px solid var(--border-color);
}

.verify-message {
  margin-bottom: 8px;
  font-weight: 700;
  font-size: 0.92rem;
}

.verify-data > div {
  margin-bottom: 5px;
  font-size: 0.84rem;
  color: var(--text-secondary);
}

.verify-data b {
  color: var(--text-primary);
}

/* ========== Evidence Row ========== */
.evidence-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.evidence-box {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: var(--bg-input);
  border: 2px dashed var(--border-color);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  transition: border-color var(--transition-fast);
}

.evidence-box:hover {
  border-color: var(--border-color-hover);
}

.evidence-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.evidence-empty {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 600;
}

/* ========== Bottom Note ========== */
.bottom-note {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--text-muted);
  padding: 10px 14px;
  border-radius: var(--border-radius-sm);
  background: var(--bg-input);
  border: 1px solid var(--border-color);
}

.bottom-note b {
  color: var(--text-secondary);
}

/* ========== Dropdown ========== */
.search-box {
  position: relative;
}

.dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  width: 100%;
  max-height: 240px;
  overflow-y: auto;
  z-index: 9999;
  box-shadow: var(--shadow-lg);
  backdrop-filter: var(--glass-blur);
  animation: dropdownIn 0.18s ease;
}

.dropdown-item {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.dropdown-item:hover,
.dropdown-item.selected {
  background: #eff6ff;
  color: #1d4ed8;
}

.dropdown-empty {
  padding: 12px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 900px) {
  .camera-stack {
    grid-template-columns: 1fr;
  }

  .cam-preview {
    height: clamp(260px, 62vw, 380px);
    min-height: 260px;
  }
}
</style>

