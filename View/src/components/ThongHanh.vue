<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h1>V-Shield Gate Monitor</h1>
        <p>Giao diện tối giản cho bảo an vận hành nhanh</p>
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
          <div>
            <h2>{{ lane.name }}</h2>
            <p>{{ lane.desc }}</p>
          </div>

          <div class="lane-final-status" :class="isLaneReady(lane) ? 'ok' : 'wait'">
            {{ isLaneReady(lane) ? "SẴN SÀNG XÁC NHẬN" : "ĐANG XỬ LÝ" }}
          </div>
        </div>

        <div class="lane-actions">
          <button class="btn btn-preview" :disabled="lane.loading" @click="previewLane(lane)">
            {{ lane.loading ? "Đang xử lý..." : "Preview" }}
          </button>

          <button
            class="btn btn-main"
            :disabled="lane.loading || !lane.face.cameraIp.trim() || !lane.plate.cameraIp.trim()"
            @click="readAllLane(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : laneAnyRunning(lane) ? "Đọc lại cả 2" : "Đọc cả 2" }}
          </button>

          <button
            class="btn btn-sub"
            :disabled="lane.loading || !lane.face.cameraIp.trim()"
            @click="retryFace(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : "Đọc lại Face" }}
          </button>

          <button
            class="btn btn-sub"
            :disabled="lane.loading || !lane.plate.cameraIp.trim()"
            @click="retryPlate(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : "Đọc lại Biển" }}
          </button>

          <button class="btn btn-off" :disabled="lane.loading" @click="stopLane(lane)">
            {{ lane.loading ? "Đang xử lý..." : "Tắt" }}
          </button>

          <button
  class="btn btn-confirm"
  :disabled="lane.loading || !lane.face.employeeId || !lane.plate.confirmedPlate"
  @click="confirmLane(lane)"
>
  Xác nhận
</button>
        </div>

        <div class="ip-row">
          <div class="ip-box">
            <label>Face Camera URL</label>
            <input
              v-model="lane.face.cameraIp"
              type="text"
              placeholder="Nhập URL face camera..."
              :disabled="lane.loading"
            />
          </div>

          <div class="ip-box">
            <label>Plate Camera URL</label>
            <input
              v-model="lane.plate.cameraIp"
              type="text"
              placeholder="Nhập URL plate camera..."
              :disabled="lane.loading"
            />
          </div>
        </div>

        <div class="summary-bar">
          <div class="summary-item">
            <span class="label">Employee ID</span>
            <span class="value strong">{{ lane.face.employeeId || "-----" }}</span>
          </div>

          <div class="summary-item">
            <span class="label">Face</span>
            <span class="value" :class="faceStateClass(lane.face)">
              {{ faceStateText(lane.face) }}
            </span>
          </div>

          <div class="summary-item">
            <span class="label">Biển số</span>
            <span class="value strong plate">{{ lane.plate.confirmedPlate || "-----" }}</span>
          </div>

          <div class="summary-item">
            <span class="label">Cảnh báo</span>
            <span class="value" :class="lane.face.alert ? 'danger-text' : 'ok-text'">
              {{ lane.face.alert ? "NGƯỜI LẠ" : "BÌNH THƯỜNG" }}
            </span>
          </div>
        </div>

        <div class="camera-stack">
          <!-- FACE -->
          <div class="cam-block">
            <div class="cam-head">
              <span>Face Camera</span>
              <span class="mini-status" :class="lane.face.previewHealthy ? 'ok' : 'wait'">
                {{ lane.face.previewRunning ? (lane.face.previewHealthy ? "Preview OK" : "Preview...") : "Preview OFF" }}
              </span>
            </div>

            <div class="cam-preview">
              <img
                v-if="lane.face.previewRunning && lane.face.directCameraUrl"
                :key="lane.face.directCameraKey"
                :src="lane.face.directCameraUrl"
                class="preview-image"
                alt="Face Preview"
                @load="onPreviewLoaded(lane.face)"
                @error="onPreviewError(lane.face)"
              />
              <div v-else class="cam-off">Face Offline</div>
            </div>

            <div class="quick-result">
              <div class="result-pill" :class="lane.face.cameraRunning ? 'ok' : 'off'">
                {{ lane.face.cameraRunning ? "RUNNING" : "STOPPED" }}
              </div>
              <div class="result-pill" :class="lane.face.scanLocked ? 'ok' : 'wait'">
                {{ lane.face.scanLocked ? "LOCKED" : "SCANNING" }}
              </div>
              <div class="result-pill" :class="lane.face.alert ? 'danger' : 'neutral'">
                {{ lane.face.alert ? "ALERT" : "NORMAL" }}
              </div>
            </div>

            <div class="evidence-row">
              <div class="evidence-box">
                <img
                  v-if="lane.face.lockedFaceCrop"
                  :src="lane.face.lockedFaceCrop"
                  class="evidence-image"
                  alt="Face Crop"
                />
                <div v-else class="evidence-empty">Face Crop</div>
              </div>

              <div class="evidence-box">
                <img
                  v-if="lane.face.lockedSnapshot"
                  :src="lane.face.lockedSnapshot"
                  class="evidence-image"
                  alt="Face Snapshot"
                />
                <div v-else class="evidence-empty">Face Snapshot</div>
              </div>
            </div>
          </div>

          <!-- PLATE -->
          <div class="cam-block">
            <div class="cam-head">
              <span>Plate Camera</span>
              <span class="mini-status" :class="platePreviewStatusClass(lane.plate)">
                {{ platePreviewStatusText(lane.plate) }}
              </span>
            </div>

            <div class="cam-preview">
              <img
                v-if="platePreviewDisplayUrl(lane.plate)"
                :key="platePreviewKey(lane.plate)"
                :src="platePreviewDisplayUrl(lane.plate)"
                class="preview-image"
                alt="Plate Preview"
                @load="onPreviewLoaded(lane.plate)"
                @error="onPreviewError(lane.plate)"
              />
              <div v-else-if="lane.plate.previewRunning" class="cam-off">Chờ ảnh chụp biển...</div>
              <div v-else class="cam-off">Plate Offline</div>
            </div>

            <div class="quick-result">
              <div class="result-pill" :class="lane.plate.cameraRunning ? 'ok' : 'off'">
                {{ lane.plate.cameraRunning ? "RUNNING" : "STOPPED" }}
              </div>
              <div class="result-pill" :class="lane.plate.scanLocked ? 'ok' : 'wait'">
                {{ lane.plate.scanLocked ? "LOCKED" : "SCANNING" }}
              </div>
              <div class="result-pill neutral">
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
                <div v-else class="evidence-empty">Plate Crop</div>
              </div>

              <div class="evidence-box">
                <img
                  v-if="lane.plate.lockedSnapshot"
                  :src="lane.plate.lockedSnapshot"
                  class="evidence-image"
                  alt="Plate Snapshot"
                />
                <div v-else class="evidence-empty">Plate Snapshot</div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-note">
          <span><b>Face Msg:</b> {{ lane.face.message || "-----" }}</span>
          <span><b>Plate Msg:</b> {{ lane.plate.message || "-----" }}</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
/*
  ĐỔI TÊN FILE SERVICE Ở ĐÂY LÀ XONG

  Ví dụ:
  - Lane 1:
    ../services/faceApiLane1
    ../services/biensoApiLane1

  - Lane 2:
    ../services/faceApiLane2
    ../services/biensoApiLane2
*/

import * as faceLane1Api from "../services/faceApi"
import * as plateLane1Api from "../services/biensoApi"
import * as faceLane2Api from "../services/faceApi"
import * as plateLane2Api from "../services/biensoApi"
import { scanGate } from "../services/thonghanhAPI"
import { formatLicensePlateDisplay } from "../utils/licensePlateValidator"

function createFaceModule() {
  return {
    cameraIp: "",
    currentIp: "",
    cameraRunning: false,
    cameraConnected: false,
    previewRunning: false,

    employeeId: "",
    trackingActive: false,
    identityConfirmed: false,
    faceMatch: false,
    confirmCount: 0,
    distance: null,
    timeoutState: false,
    alert: false,
    scanLocked: false,
    lockReason: "",

    lockedSnapshot: "",
    lockedFaceCrop: "",

    message: "",
    fps: 0,
    lastUpdate: "",

    directCameraUrl: "",
    directCameraKey: 0,
    previewHealthy: false,

    resultTimer: null,
    busyResult: false,
    isFetchingLockedImages: false,
    destroyed: false
  }
}

function createPlateModule() {
  return {
    cameraIp: "",
    currentIp: "",
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
    previewHealthy: false,

    resultTimer: null,
    busyResult: false,
    isFetchingLockedImages: false,
    destroyed: false
  }
}

export default {
  name: "VShieldGateMinimal",

  data() {
    return {
      lanes: [
        {
          id: "lane1",
          name: "Làn 1",
          desc: "Face trên / Biển dưới",
          loading: false,
          faceApi: faceLane1Api,
          plateApi: plateLane1Api,
          face: createFaceModule(),
          plate: createPlateModule()
        },
        {
          id: "lane2",
          name: "Làn 2",
          desc: "Face trên / Biển dưới",
          loading: false,
          faceApi: faceLane2Api,
          plateApi: plateLane2Api,
          face: createFaceModule(),
          plate: createPlateModule()
        }
      ]
    }
  },

  async mounted() {
    for (const lane of this.lanes) {
      lane.face.destroyed = false
      lane.plate.destroyed = false

      await this.loadStatusFace(lane)
      await this.loadStatusPlate(lane)

      if (lane.face.cameraRunning) this.startFaceLoop(lane)
      if (lane.plate.cameraRunning) this.startPlateLoop(lane)
    }
  },

  beforeUnmount() {
    for (const lane of this.lanes) {
      lane.face.destroyed = true
      lane.plate.destroyed = true
      this.stopFaceLoop(lane)
      this.stopPlateLoop(lane)
      this.resetPreview(lane.face)
      this.resetPreview(lane.plate)
    }
  },

  methods: {
    isLaneReady(lane) {
      return (
        lane.face.scanLocked &&
        lane.plate.scanLocked &&
        !!lane.face.employeeId &&
        !!lane.plate.confirmedPlate &&
        !lane.face.alert
      )
    },

    laneAnyRunning(lane) {
      return lane.face.cameraRunning || lane.plate.cameraRunning
    },

    faceStateText(face) {
      if (face.scanLocked) {
        if (face.lockReason === "confirmed") return "ĐÃ NHẬN DIỆN"
        if (face.lockReason === "alert") return "CẢNH BÁO"
        if (face.lockReason === "timeout") return "TIMEOUT"
        return "ĐÃ KHÓA"
      }

      if (!face.trackingActive) return "CHỜ"
      if (face.identityConfirmed) return "ĐANG XÁC NHẬN"
      if (face.faceMatch) return "ĐANG SO KHỚP"
      return "ĐANG QUÉT"
    },

    faceStateClass(face) {
      if (face.alert) return "danger-text"
      if (face.scanLocked && face.identityConfirmed) return "ok-text"
      return "warn-text"
    },

    buildDirectCameraUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""
      const sep = raw.includes("?") ? "&" : "?"
      return `${raw}${sep}t=${Date.now()}`
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

    resetPreview(module) {
      module.directCameraUrl = ""
      module.directCameraKey += 1
      module.previewHealthy = false
      module.previewRunning = false
    },

    onPreviewLoaded(module) {
      module.previewHealthy = true
    },

    onPreviewError(module) {
      module.previewHealthy = false
    },

    clearFaceState(face) {
      face.employeeId = ""
      face.trackingActive = false
      face.identityConfirmed = false
      face.faceMatch = false
      face.confirmCount = 0
      face.distance = null
      face.timeoutState = false
      face.alert = false
      face.scanLocked = false
      face.lockReason = ""
      face.lockedSnapshot = ""
      face.lockedFaceCrop = ""
      face.message = ""
      face.fps = 0
      face.lastUpdate = ""
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

    hardResetFace(face) {
      face.cameraRunning = false
      face.cameraConnected = false
      face.currentIp = ""
      this.clearFaceState(face)
    },

    hardResetPlate(plate) {
      plate.cameraRunning = false
      plate.currentIp = ""
      plate.sessionId = 0
      plate.lastAppliedSessionId = 0
      this.clearPlateState(plate)
    },

    stopFaceLoop(lane) {
      const face = lane.face
      if (face.resultTimer) {
        clearInterval(face.resultTimer)
        face.resultTimer = null
      }
      face.busyResult = false
    },

    stopPlateLoop(lane) {
      const plate = lane.plate
      if (plate.resultTimer) {
        clearInterval(plate.resultTimer)
        plate.resultTimer = null
      }
      plate.busyResult = false
    },

    startFaceLoop(lane) {
      this.stopFaceLoop(lane)

      lane.face.resultTimer = setInterval(async () => {
        if (lane.face.destroyed) return
        if (!lane.face.cameraRunning) return
        if (lane.face.busyResult) return

        lane.face.busyResult = true
        try {
          await this.refreshFace(lane)
        } finally {
          lane.face.busyResult = false
        }
      }, 500)
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

    async loadStatusFace(lane) {
      try {
        const res = await lane.faceApi.getCameraStatus()
        await this.applyFaceRealtimeState(lane, res, false)

        if (lane.face.currentIp) {
          lane.face.cameraIp = lane.face.currentIp
          this.mountPreview(lane.face, lane.face.currentIp)
        }
      } catch (e) {
        console.error("loadStatusFace error:", e)
      }
    },

    async loadStatusPlate(lane) {
      try {
        const res = await lane.plateApi.getCameraStatus()
        await this.applyPlateRealtimeState(lane, res, false)

        if (lane.plate.currentIp) {
          lane.plate.cameraIp = lane.plate.currentIp
          this.enablePlatePreview(lane.plate, lane.plate.currentIp)
        }
      } catch (e) {
        console.error("loadStatusPlate error:", e)
      }
    },

    async refreshFace(lane) {
      try {
        const res = await lane.faceApi.getCameraResult()
        await this.applyFaceRealtimeState(lane, res, true)
      } catch (e) {
        console.warn("refreshFace error:", e)
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

    async fetchFaceLockedImages(lane, force = false) {
      const face = lane.face
      if (face.destroyed) return
      if (!face.cameraRunning) return
      if (!face.scanLocked && !force) {
        face.lockedSnapshot = ""
        face.lockedFaceCrop = ""
        return
      }
      if (face.isFetchingLockedImages) return

      face.isFetchingLockedImages = true
      try {
        const res = await lane.faceApi.getLockedImages()
        if (res?.scan_locked) {
          face.lockedSnapshot = res.locked_snapshot || ""
          face.lockedFaceCrop = res.locked_face_crop || ""
        } else {
          face.lockedSnapshot = ""
          face.lockedFaceCrop = ""
        }
      } catch (e) {
        console.warn("fetchFaceLockedImages error:", e)
      } finally {
        face.isFetchingLockedImages = false
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

    async applyFaceRealtimeState(lane, res, allowTurnOffReset = true) {
      if (!res || lane.face.destroyed) return

      const face = lane.face
      const incomingCameraEnabled = !!res.camera_enabled

      face.cameraRunning = incomingCameraEnabled
      face.cameraConnected = !!res.camera_connected
      face.currentIp = res.ip || face.currentIp

      face.employeeId = res.employee_id || ""
      face.trackingActive = !!res.tracking_active
      face.identityConfirmed = !!res.identity_confirmed
      face.faceMatch = !!res.face_match
      face.confirmCount = Number(res.confirm_count || 0)
      face.distance = res.distance ?? null
      face.timeoutState = !!res.timeout
      face.alert = !!res.alert

      face.scanLocked = !!res.scan_locked
      face.lockReason = res.lock_reason || ""

      face.fps = Number(res.fps || 0)
      face.message = res.message || ""
      face.lastUpdate = res.last_update || ""

      if (!face.scanLocked) {
        face.lockedSnapshot = ""
        face.lockedFaceCrop = ""
      }

      if (!incomingCameraEnabled && allowTurnOffReset) {
        this.stopFaceLoop(lane)
        this.hardResetFace(face)
        return
      }

      if (face.scanLocked) {
        await this.fetchFaceLockedImages(lane, false)
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
      if (!lane.face.cameraIp.trim() && !lane.plate.cameraIp.trim()) {
        alert("Vui lòng nhập ít nhất 1 URL camera")
        return
      }

      try {
        lane.loading = true

        if (lane.face.cameraIp.trim()) {
          lane.face.currentIp = lane.face.cameraIp.trim()
          this.mountPreview(lane.face, lane.face.currentIp)
          lane.face.message = "Đã mở preview Face"
        }

        if (lane.plate.cameraIp.trim()) {
          lane.plate.currentIp = lane.plate.cameraIp.trim()
          this.enablePlatePreview(lane.plate, lane.plate.currentIp)
          lane.plate.message = this.isImagePreviewableUrl(lane.plate.currentIp)
            ? "Đã mở preview Plate"
            : "Sẽ hiển thị ảnh chụp sau khi đọc được biển"
        }
      } catch (e) {
        console.error("previewLane error:", e)
        alert(e?.message || "Lỗi mở preview")
      } finally {
        lane.loading = false
      }
    },

    async readAllLane(lane) {
      if (!lane.face.cameraIp.trim() || !lane.plate.cameraIp.trim()) {
        alert("Vui lòng nhập đủ URL Face và Plate")
        return
      }

      try {
        lane.loading = true

        lane.face.currentIp = lane.face.cameraIp.trim()
        lane.plate.currentIp = lane.plate.cameraIp.trim()

        if (!lane.face.previewRunning) this.mountPreview(lane.face, lane.face.currentIp)
        if (!lane.plate.previewRunning) this.enablePlatePreview(lane.plate, lane.plate.currentIp)

        this.clearFaceState(lane.face)
        this.clearPlateState(lane.plate)

        if (!lane.face.cameraRunning) {
          this.stopFaceLoop(lane)
          const resFace = await lane.faceApi.turnOnCamera(lane.face.currentIp)
          if (!resFace?.success) {
            alert(resFace?.message || "Không thể khởi tạo Face")
            return
          }
          lane.face.cameraRunning = true
          lane.face.message = resFace.message || "Khởi tạo Face thành công"
        } else {
          const resFace = await lane.faceApi.resetCameraState()
          lane.face.message = resFace?.message || "Đã reset Face"
        }

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

        await this.refreshFace(lane)
        await this.refreshPlate(lane)

        if (!lane.face.resultTimer) this.startFaceLoop(lane)
        if (!lane.plate.resultTimer) this.startPlateLoop(lane)
      } catch (e) {
        console.error("readAllLane error:", e)
        alert(e?.message || "Lỗi đọc cả 2")
      } finally {
        lane.loading = false
      }
    },

    async retryFace(lane) {
      if (!lane.face.cameraIp.trim()) {
        alert("Vui lòng nhập URL Face")
        return
      }

      try {
        lane.loading = true

        lane.face.currentIp = lane.face.cameraIp.trim()
        if (!lane.face.previewRunning) {
          this.mountPreview(lane.face, lane.face.currentIp)
        }

        this.clearFaceState(lane.face)

        if (!lane.face.cameraRunning) {
          this.stopFaceLoop(lane)
          const res = await lane.faceApi.turnOnCamera(lane.face.currentIp)
          if (!res?.success) {
            alert(res?.message || "Không thể khởi tạo Face")
            return
          }
          lane.face.cameraRunning = true
          lane.face.message = res.message || "Khởi tạo Face thành công"
        } else {
          const res = await lane.faceApi.resetCameraState()
          lane.face.message = res?.message || "Đã reset Face"
        }

        await this.refreshFace(lane)
        if (!lane.face.resultTimer) this.startFaceLoop(lane)
      } catch (e) {
        console.error("retryFace error:", e)
        alert(e?.message || "Lỗi đọc lại Face")
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

        lane.plate.currentIp = lane.plate.cameraIp.trim()
        if (!lane.plate.previewRunning) {
          this.enablePlatePreview(lane.plate, lane.plate.currentIp)
        }

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

        this.stopFaceLoop(lane)
        this.stopPlateLoop(lane)

        try {
          const resFace = await lane.faceApi.turnOffCamera()
          lane.face.message = resFace?.message || "Đã tắt Face"
        } catch (e) {
          console.warn("turnOff face warning:", e)
        }

        try {
          const resPlate = await lane.plateApi.turnOffCamera()
          lane.plate.message = resPlate?.message || "Đã tắt Plate"
        } catch (e) {
          console.warn("turnOff plate warning:", e)
        }

        this.hardResetFace(lane.face)
        this.hardResetPlate(lane.plate)
        this.resetPreview(lane.face)
        this.resetPreview(lane.plate)
      } catch (e) {
        console.error("stopLane error:", e)
        alert(e?.message || "Lỗi tắt làn")
      } finally {
        lane.loading = false
      }
    },

    async confirmLane(lane) {
  const employeeId = Number(lane.face.employeeId || 0)
  const licensePlate = String(lane.plate.confirmedPlate || "").trim()

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

    const payload = {
      employeeId: employeeId,
      licensePlate: licensePlate
    }

    const res = await scanGate(payload)
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
}
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  background: #f3f6fb;
  padding: 20px;
  font-family: Inter, Arial, sans-serif;
  color: #0f172a;
}

.topbar {
  margin-bottom: 18px;
}

.topbar h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
}

.topbar p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 14px;
}

.lane-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.lane-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.lane-card.ready {
  border-color: #93c5fd;
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.12);
}

.lane-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.lane-head h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
}

.lane-head p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 13px;
}

.lane-final-status {
  min-width: 180px;
  text-align: center;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.lane-final-status.ok {
  background: #dcfce7;
  color: #166534;
}

.lane-final-status.wait {
  background: #fff7ed;
  color: #c2410c;
}

.lane-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.btn {
  height: 40px;
  border: none;
  border-radius: 10px;
  padding: 0 14px;
  color: white;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-preview {
  background: #0f766e;
}

.btn-main {
  background: #2563eb;
}

.btn-sub {
  background: #475569;
}

.btn-off {
  background: #dc2626;
}

.btn-confirm {
  background: #111827;
}

.ip-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.ip-box label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #334155;
}

.ip-box input {
  width: 100%;
  height: 42px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
}

.ip-box input:focus {
  border-color: #60a5fa;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.summary-bar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.summary-item {
  background: #f8fafc;
  border: 1px solid #e9eef5;
  border-radius: 12px;
  padding: 10px 12px;
}

.summary-item .label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 6px;
}

.summary-item .value {
  display: block;
  font-size: 15px;
  font-weight: 800;
  word-break: break-word;
}

.strong {
  font-size: 20px !important;
  font-weight: 900 !important;
}

.plate {
  color: #15803d;
  letter-spacing: 1px;
}

.ok-text {
  color: #15803d;
}

.warn-text {
  color: #c2410c;
}

.danger-text {
  color: #b91c1c;
}

.camera-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.cam-block {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px;
  background: #fcfdff;
}

.cam-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 800;
}

.mini-status {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
}

.mini-status.ok {
  background: #dcfce7;
  color: #166534;
}

.mini-status.wait {
  background: #fff7ed;
  color: #c2410c;
}

.cam-preview {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #0f172a;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 10px;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.cam-off {
  width: 100%;
  height: 100%;
  display: flex;
  color: #cbd5e1;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.quick-result {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.result-pill {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.result-pill.ok {
  background: #dcfce7;
  color: #166534;
}

.result-pill.wait {
  background: #fff7ed;
  color: #c2410c;
}

.result-pill.danger {
  background: #fee2e2;
  color: #b91c1c;
}

.result-pill.neutral {
  background: #e2e8f0;
  color: #1e293b;
}

.result-pill.off {
  background: #f1f5f9;
  color: #64748b;
}

.evidence-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.evidence-box {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  overflow: hidden;
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
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.bottom-note {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #475569;
}

@media (max-width: 1200px) {
  .lane-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .summary-bar,
  .ip-row,
  .evidence-row {
    grid-template-columns: 1fr;
  }

  .lane-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .lane-final-status {
    min-width: unset;
    width: 100%;
  }
}
</style>
