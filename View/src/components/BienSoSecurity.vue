<template>
  <div class="security-container">
    <h1 class="title">Quét biển số</h1>

    <div class="source-panel">
      <div class="source-field">
        <label class="source-label">Camera đã cấu hình</label>
        <select
          v-model="selectedConfiguredCameraId"
          class="ip-input source-select"
          :disabled="loading || configuredCameras.length === 0"
          @change="handleConfiguredCameraChange"
        >
          <option value="">Chọn camera đã cấu hình</option>
          <option
            v-for="camera in configuredCameras"
            :key="camera.id"
            :value="String(camera.id)"
          >
            {{ camera.name }} - {{ camera.label }}
          </option>
        </select>
      </div>

      <button
        class="btn btn-config"
        @click="applyConfiguredCameraSelection()"
        :disabled="loading || !selectedConfiguredCameraId"
      >
        Dùng camera này
      </button>
    </div>

    <div class="source-hint">
      {{ configuredCameraSummary }}
    </div>

    <div class="control-panel">
      <input
        v-model="cameraIp"
        type="text"
        class="ip-input"
        placeholder="Nguồn backend (RTSP / stream URL)..."
        :disabled="loading"
      />

      <input
        v-model="previewUrl"
        type="text"
        class="ip-input"
        placeholder="Preview URL trên web (MP4/HLS/MJPEG)..."
        :disabled="loading"
      />

      <button class="btn btn-on" @click="handleTurnOnPreview" :disabled="loading">
        {{ loading ? "Đang xử lý..." : "Bật preview" }}
      </button>

      <button
        class="btn btn-reset"
        @click="handleInitOrResetSession"
        :disabled="loading || !cameraIp.trim()"
      >
        {{ loading ? "Đang xử lý..." : sessionActionLabel }}
      </button>

      <button class="btn btn-off" @click="handleTurnOff" :disabled="loading">
        {{ loading ? "Đang xử lý..." : "Tắt camera" }}
      </button>
    </div>

    <div class="status-bar">
      <span><b>Trạng thái:</b> {{ cameraRunning ? "Đang chạy" : "Đang tắt" }}</span>
      <span><b>Preview:</b> {{ previewRunning ? "Đang mở" : "Đang tắt" }}</span>
      <span><b>Nguồn backend:</b> {{ currentIp || cameraIp || "-----" }}</span>
      <span><b>Preview URL:</b> {{ effectivePreviewUrl || "-----" }}</span>
      <span><b>Session:</b> {{ sessionId || 0 }}</span>
      <span><b>FPS:</b> {{ fps }}</span>
      <span><b>OCR:</b> {{ ocrRunning ? "Đang xử lý" : "Sẵn sàng" }}</span>
      <span><b>Khóa phiên:</b> {{ scanLocked ? "Đã khóa" : "Đang quét" }}</span>
      <span><b>Preview health:</b> {{ previewHealthy ? "OK" : "Waiting..." }}</span>
    </div>

    <div class="video-wrapper">
      <StreamPreview
        v-if="previewRunning && effectivePreviewUrl"
        :url="effectivePreviewUrl"
        class="video-stream"
        label="Plate camera preview"
        :show-controls="false"
        @ready="handlePreviewReady"
        @error="handlePreviewError"
      />

      <div v-else class="video-off">
        Camera chưa chạy
      </div>
    </div>

    <div class="plate-panel">
      <div class="plate-box">
        <div class="plate-label">Biển số đã chốt</div>
        <div class="plate-number confirmed">
          {{ confirmedPlate || "-----" }}
        </div>
      </div>

      <div class="plate-box">
        <div class="plate-label">Biển số thô gần nhất</div>
        <div class="plate-number raw">
          {{ lastRawPlate || "-----" }}
        </div>
      </div>
    </div>

    <div class="lock-banner" v-if="scanLocked">
      Đã khóa kết quả hiện tại. Bấm “{{ sessionActionLabel }}” để quét biển số mới.
    </div>

    <div class="evidence-panel">
      <div class="evidence-card">
        <div class="evidence-title">Ảnh toàn khung</div>
        <img
          v-if="lockedSnapshot"
          :src="lockedSnapshot"
          class="evidence-image"
          alt="Locked Snapshot"
        />
        <div v-else class="evidence-empty">Chưa có ảnh</div>
      </div>

      <div class="evidence-card">
        <div class="evidence-title">Ảnh crop biển số</div>
        <img
          v-if="lockedPlateCrop"
          :src="lockedPlateCrop"
          class="evidence-image"
          alt="Locked Plate Crop"
        />
        <div v-else class="evidence-empty">Chưa có ảnh</div>
      </div>
    </div>

    <div class="live-panel">
      <div class="live-title">Ứng viên OCR</div>

      <div v-if="liveCandidates.length > 0" class="candidate-list">
        <div
          v-for="(item, index) in liveCandidates"
          :key="`${item.text}-${index}`"
          class="candidate-item"
        >
          <span class="candidate-text">{{ item.text }}</span>
          <span class="candidate-meta">
            conf={{ formatConf(item.conf) }} | {{ item.valid ? "valid" : "raw" }}
          </span>
        </div>
      </div>

      <div v-else class="candidate-empty">
        Chưa có dữ liệu OCR
      </div>
    </div>

    <div class="result-panel">
      <div><b>Box:</b> {{ bboxText }}</div>
      <div><b>Stable Count:</b> {{ stableCount }}</div>
      <div><b>Moving Fast:</b> {{ movingFast ? "Yes" : "No" }}</div>
      <div><b>Message:</b> {{ message || "-----" }}</div>
      <div><b>Last Update:</b> {{ lastUpdate || "-----" }}</div>
    </div>
  </div>
</template>

<script>
import StreamPreview from "./StreamPreview.vue"
import {
  turnOnCamera,
  turnOffCamera,
  resetCameraState,
  getCameraStatus,
  getCameraResult,
  getLockedImages
} from "../services/biensoApi"
import {
  getConfiguredCameraSettings,
  resolveCameraPreviewUrl,
  resolveCameraSourceUrl
} from "../utils/cameraNetwork"

const PLATE_CAMERA_SELECTION_STORAGE_KEY = "vshield-plate-selected-camera"

export default {
  name: "BienSoSecurity",
  components: {
    StreamPreview
  },

  data() {
    return {
      cameraIp: "",
      previewUrl: "",
      activePreviewUrl: "",
      currentIp: "",
      cameraRunning: false,
      previewRunning: false,
      loading: false,

      configuredCameras: [],
      selectedConfiguredCameraId: "",

      sessionId: 0,
      lastAppliedSessionId: 0,
      lastLockedImageSessionId: 0,

      confirmedPlate: "",
      lastRawPlate: "",
      liveCandidates: [],
      lockedSnapshot: "",
      lockedPlateCrop: "",
      scanLocked: false,

      fps: 0,
      ocrRunning: false,
      stableCount: 0,
      movingFast: false,
      bbox: null,
      message: "",
      lastUpdate: "",

      previewHealthy: false,

      resultTimer: null,
      busyResult: false,
      isFetchingLockedImages: false,

      destroyed: false
    }
  },

  computed: {
    bboxText() {
      if (!this.bbox) return "-----"
      return `x1=${this.bbox.x1}, y1=${this.bbox.y1}, x2=${this.bbox.x2}, y2=${this.bbox.y2}`
    },

    sessionActionLabel() {
      return this.cameraRunning ? "Reset phiên đọc" : "Khởi tạo phiên đọc"
    },

    selectedConfiguredCamera() {
      return this.configuredCameras.find(
        (camera) => String(camera.id) === String(this.selectedConfiguredCameraId || "")
      ) || null
    },

    configuredCameraSummary() {
      if (this.configuredCameras.length === 0) {
        return "Chưa có camera nào được bật trong Quản lý camera."
      }

      if (!this.selectedConfiguredCamera) {
        return "Chọn một camera đã cấu hình để nạp đồng thời nguồn backend và preview URL."
      }

      const sourceUrl = this.selectedConfiguredCamera.sourceUrl || "-----"
      const previewUrl = this.selectedConfiguredCamera.browserPreviewUrl || "-----"

      return `Đang chọn ${this.selectedConfiguredCamera.name}: backend = ${sourceUrl} | preview = ${previewUrl}`
    },

    effectivePreviewUrl() {
      return String(this.activePreviewUrl || this.previewUrl || "").trim()
    }
  },

  async mounted() {
    this.destroyed = false
    this.loadConfiguredCameras()
    await this.loadCurrentStatus()

    if (this.cameraRunning) {
      this.startResultLoop()
    }
  },

  beforeUnmount() {
    this.destroyed = true
    this.stopResultLoop()
    this.resetPreviewState()
  },

  activated() {
    this.destroyed = false
    this.loadConfiguredCameras()

    if (this.cameraRunning) {
      if (!this.previewRunning && this.effectivePreviewUrl) {
        this.activatePreview(this.effectivePreviewUrl)
      }
      this.startResultLoop()
    }
  },

  deactivated() {
    this.stopResultLoop()
  },

  methods: {
    loadConfiguredCameras() {
      const cameras = getConfiguredCameraSettings().map((camera) => ({
        ...camera,
        sourceUrl: resolveCameraSourceUrl(camera),
        browserPreviewUrl: resolveCameraPreviewUrl(camera),
      }))

      this.configuredCameras = cameras

      const savedCameraId = localStorage.getItem(PLATE_CAMERA_SELECTION_STORAGE_KEY) || ""
      const currentSelectionValid = cameras.some(
        (camera) => String(camera.id) === String(this.selectedConfiguredCameraId || "")
      )

      if (!currentSelectionValid) {
        if (savedCameraId && cameras.some((camera) => String(camera.id) === savedCameraId)) {
          this.selectedConfiguredCameraId = savedCameraId
        } else if (cameras.length === 1) {
          this.selectedConfiguredCameraId = String(cameras[0].id)
        } else if (!cameras.length) {
          this.selectedConfiguredCameraId = ""
        }
      }

      if (!this.cameraIp && !this.previewUrl && this.selectedConfiguredCameraId) {
        this.applyConfiguredCameraSelection({ silent: true, autoPreview: false })
      }
    },

    rememberConfiguredCameraSelection() {
      if (this.selectedConfiguredCameraId) {
        localStorage.setItem(
          PLATE_CAMERA_SELECTION_STORAGE_KEY,
          String(this.selectedConfiguredCameraId)
        )
      } else {
        localStorage.removeItem(PLATE_CAMERA_SELECTION_STORAGE_KEY)
      }
    },

    handleConfiguredCameraChange() {
      this.rememberConfiguredCameraSelection()
      this.applyConfiguredCameraSelection({ silent: true, autoPreview: false })
    },

    applyConfiguredCameraSelection(options = {}) {
      const { silent = false, autoPreview = false } = options
      const selectedCamera = this.selectedConfiguredCamera

      if (!selectedCamera) {
        if (!silent) {
          alert("Vui lòng chọn một camera đã cấu hình.")
        }
        return
      }

      this.cameraIp = selectedCamera.sourceUrl || ""
      this.previewUrl = selectedCamera.browserPreviewUrl || ""
      this.rememberConfiguredCameraSelection()

      if (autoPreview && this.previewUrl) {
        this.activatePreview(this.previewUrl)
      }

      this.message = `Đã nạp ${selectedCamera.name} vào màn quét biển số`
      this.lastUpdate = new Date().toLocaleString()
    },

    formatConf(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return num.toFixed(4)
    },

    clearResultStateOnly() {
      this.confirmedPlate = ""
      this.lastRawPlate = ""
      this.liveCandidates = []
      this.lockedSnapshot = ""
      this.lockedPlateCrop = ""
      this.scanLocked = false
      this.fps = 0
      this.ocrRunning = false
      this.stableCount = 0
      this.movingFast = false
      this.bbox = null
      this.message = ""
      this.lastUpdate = ""
      this.lastLockedImageSessionId = 0
    },

    hardResetUiState() {
      this.cameraRunning = false
      this.currentIp = ""
      this.sessionId = 0
      this.lastAppliedSessionId = 0
      this.clearResultStateOnly()
    },

    activatePreview(url) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return

      this.activePreviewUrl = cleanUrl
      this.previewRunning = true
      this.previewHealthy = false
    },

    resetPreviewState() {
      this.activePreviewUrl = ""
      this.previewHealthy = false
      this.previewRunning = false
    },

    stopResultLoop() {
      if (this.resultTimer) {
        clearInterval(this.resultTimer)
        this.resultTimer = null
      }
      this.busyResult = false
    },

    startResultLoop() {
      this.stopResultLoop()

      this.resultTimer = setInterval(async () => {
        if (this.destroyed) return
        if (!this.cameraRunning) return
        if (this.busyResult) return

        this.busyResult = true
        try {
          await this.refreshResult()
        } finally {
          this.busyResult = false
        }
      }, 500)
    },

    async loadCurrentStatus() {
      try {
        const res = await getCameraStatus()
        await this.applyRealtimeState(res, false)

        if (this.currentIp) {
          this.cameraIp = this.currentIp
        }

        if ((!this.cameraIp || !this.previewUrl) && this.selectedConfiguredCameraId) {
          this.applyConfiguredCameraSelection({ silent: true, autoPreview: false })
        }

        const previewSource = this.previewUrl || this.cameraIp
        if (previewSource) {
          this.activatePreview(previewSource)
        } else {
          this.resetPreviewState()
        }

        if (this.cameraRunning) {
          await this.fetchLockedImagesIfNeeded(true)
        }
      } catch (error) {
        console.error("Load status error:", error)
      }
    },

    async handleTurnOnPreview() {
      const previewSource = (this.previewUrl || this.cameraIp || "").trim()
      if (!previewSource) {
        alert("Vui lòng nhập Preview URL hoặc chọn camera đã cấu hình.")
        return
      }

      try {
        this.loading = true
        this.activatePreview(previewSource)
        this.message = "Đã mở preview camera trên giao diện"
      } catch (error) {
        console.error("Turn on preview error:", error)
        alert(error?.message || "Lỗi mở preview camera")
      } finally {
        this.loading = false
      }
    },

    async handleInitOrResetSession() {
      const ip = (this.cameraIp || this.currentIp || "").trim()
      if (!ip) {
        alert("Vui lòng nhập URL camera cho backend OCR")
        return
      }

      try {
        this.loading = true

        this.currentIp = ip
        const previewSource = (this.previewUrl || ip).trim()
        if (!this.previewRunning && previewSource) {
          this.activatePreview(previewSource)
        }

        this.clearResultStateOnly()

        if (!this.cameraRunning) {
          this.stopResultLoop()

          const res = await turnOnCamera(ip)
          if (!res?.success) {
            alert(res?.message || "Không thể khởi tạo phiên đọc")
            return
          }

          this.cameraRunning = true
          this.currentIp = ip
          this.sessionId = Number(res.session_id || 0)
          this.lastAppliedSessionId = this.sessionId
          this.message = res.message || "Khởi tạo phiên đọc thành công"

          await this.refreshResult()
          this.startResultLoop()
          return
        }

        const res = await resetCameraState()
        this.message = res?.message || "Đã reset phiên đọc"

        const newSessionId = Number(res?.session_id || 0)
        if (newSessionId > 0) {
          this.sessionId = newSessionId
          this.lastAppliedSessionId = newSessionId
        }

        await this.refreshResult()

        if (!this.resultTimer) {
          this.startResultLoop()
        }
      } catch (error) {
        console.error("Init/Reset session error:", error)
        alert(error?.message || "Lỗi khởi tạo / reset phiên đọc")
      } finally {
        this.loading = false
      }
    },

    async handleTurnOff() {
      try {
        this.loading = true
        this.stopResultLoop()

        try {
          const res = await turnOffCamera()
          this.message = res?.message || "Đã tắt camera"
        } catch (error) {
          console.warn("Turn off warning:", error)
        }

        this.hardResetUiState()
        this.resetPreviewState()
      } catch (error) {
        console.error("Turn off error:", error)
        alert(error?.message || "Lỗi tắt camera")
      } finally {
        this.loading = false
      }
    },

    async refreshResult() {
      try {
        const res = await getCameraResult()
        await this.applyRealtimeState(res, true)
      } catch (error) {
        console.warn("Result polling error:", error)
      }
    },

    async fetchLockedImagesIfNeeded(force = false) {
      if (this.destroyed || !this.cameraRunning) return

      if (!this.scanLocked) {
        this.lockedSnapshot = ""
        this.lockedPlateCrop = ""
        this.lastLockedImageSessionId = 0
        return
      }

      if (this.isFetchingLockedImages) return
      if (!force && this.lastLockedImageSessionId === this.sessionId) return

      this.isFetchingLockedImages = true
      try {
        const res = await getLockedImages()
        const responseSessionId = Number(res?.session_id || 0)

        if (responseSessionId !== this.sessionId) {
          return
        }

        if (res?.scan_locked) {
          this.lockedSnapshot = res.locked_snapshot || ""
          this.lockedPlateCrop = res.locked_plate_crop || ""
          this.lastLockedImageSessionId = responseSessionId
        } else {
          this.lockedSnapshot = ""
          this.lockedPlateCrop = ""
          this.lastLockedImageSessionId = 0
        }
      } catch (error) {
        console.warn("Fetch locked images error:", error)
      } finally {
        this.isFetchingLockedImages = false
      }
    },

    async applyRealtimeState(res, allowTurnOffReset = true) {
      if (!res || this.destroyed) return

      const incomingSessionId = Number(res.session_id || 0)

      if (incomingSessionId > 0) {
        if (
          this.lastAppliedSessionId > 0 &&
          incomingSessionId < this.lastAppliedSessionId
        ) {
          return
        }

        if (incomingSessionId > this.lastAppliedSessionId) {
          this.lastAppliedSessionId = incomingSessionId
          this.sessionId = incomingSessionId
          this.lastLockedImageSessionId = 0
        } else if (!this.sessionId) {
          this.sessionId = incomingSessionId
        }
      }

      const incomingCameraEnabled = !!res.camera_enabled

      this.cameraRunning = incomingCameraEnabled
      this.currentIp = res.ip || this.currentIp
      this.confirmedPlate = res.confirmed_plate || ""
      this.lastRawPlate = res.last_raw_plate || ""
      this.liveCandidates = Array.isArray(res.live_candidates)
        ? res.live_candidates.slice(0, 5)
        : []
      this.scanLocked = !!res.scan_locked
      this.fps = Number(res.fps || 0)
      this.ocrRunning = !!res.ocr_running
      this.stableCount = Number(res.stable_count || 0)
      this.movingFast = !!res.moving_fast
      this.bbox = res.bbox || null
      this.message = res.message || ""
      this.lastUpdate = res.last_update || ""

      if (!this.scanLocked) {
        this.lockedSnapshot = ""
        this.lockedPlateCrop = ""
        this.lastLockedImageSessionId = 0
      }

      if (!incomingCameraEnabled && allowTurnOffReset) {
        this.stopResultLoop()
        this.hardResetUiState()
        return
      }

      if (this.scanLocked) {
        await this.fetchLockedImagesIfNeeded(false)
      }
    },

    handlePreviewReady() {
      this.previewHealthy = true
    },

    handlePreviewError() {
      this.previewHealthy = false
    }
  }
}
</script>

<style scoped>
.security-container {
  width: min(1180px, 100%);
  margin: auto;
  text-align: center;
  font-family: Arial, sans-serif;
  padding: 20px;
}

.title {
  margin-bottom: 20px;
}

.source-panel {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.source-field {
  min-width: 320px;
  flex: 1 1 420px;
  text-align: left;
}

.source-label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.92rem;
  font-weight: 700;
}

.source-select {
  width: 100%;
}

.source-hint {
  margin: 0 auto 16px;
  max-width: 1060px;
  font-size: 0.92rem;
  color: #5c6f82;
  text-align: left;
}

.control-panel {
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 15px;
}

.ip-input {
  width: 320px;
  padding: 10px 12px;
  font-size: 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-size: 14px;
  min-width: 150px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-on {
  background: #198754;
}

.btn-reset {
  background: #0d6efd;
}

.btn-off {
  background: #dc3545;
}

.btn-config {
  background: #0f7c82;
}

.status-bar {
  display: flex;
  gap: 18px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
  font-size: 14px;
}

.video-wrapper {
  width: min(900px, 100%);
  background: black;
  margin: 20px auto 0;
  overflow: hidden;
  border-radius: 12px;
}

.video-stream {
  min-height: 0;
}

.video-off {
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 450px;
  font-size: 20px;
}

.plate-panel {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.plate-box {
  min-width: 280px;
}

.plate-label {
  font-size: 16px;
  margin-bottom: 8px;
  color: #666;
}

.plate-number {
  font-size: 36px;
  font-weight: bold;
  letter-spacing: 2px;
  padding: 14px 20px;
  border-radius: 12px;
  background: #111;
  color: #fff;
  min-width: 280px;
}

.plate-number.confirmed {
  border: 2px solid #198754;
}

.plate-number.raw {
  border: 2px solid #6c757d;
}

.lock-banner {
  margin: 18px auto 0;
  background: #fff3cd;
  color: #7a4d00;
  border: 1px solid #f5d48c;
  padding: 12px 16px;
  border-radius: 10px;
  max-width: 920px;
}

.evidence-panel {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.evidence-card,
.live-panel,
.result-panel {
  background: #fff;
  border: 1px solid #e3e6ea;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.evidence-title,
.live-title {
  font-weight: 700;
  margin-bottom: 12px;
}

.evidence-image {
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 10px;
  background: #0f172a;
}

.evidence-empty,
.candidate-empty {
  color: #6b7280;
}

.live-panel {
  margin-top: 20px;
}

.candidate-list {
  display: grid;
  gap: 10px;
}

.candidate-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.candidate-text {
  font-weight: 700;
}

.candidate-meta {
  color: #64748b;
  font-size: 0.92rem;
}

.result-panel {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  text-align: left;
}

@media (max-width: 960px) {
  .evidence-panel,
  .result-panel {
    grid-template-columns: 1fr;
  }

  .ip-input {
    width: 100%;
  }

  .source-field {
    width: 100%;
  }

  .video-off {
    min-height: 280px;
  }
}
</style>
