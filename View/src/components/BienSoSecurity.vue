<template>
  <div class="security-container">
    <h1 class="title">Gate Camera Monitor</h1>

    <div class="control-panel">
      <input
        v-model="cameraIp"
        type="text"
        class="ip-input"
        placeholder="Nhập URL camera / stream URL..."
        :disabled="loading"
      />

      <button class="btn btn-on" @click="handleTurnOnPreview" :disabled="loading">
        {{ loading ? "Đang xử lý..." : "Bật camera" }}
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
      <span><b>Input URL:</b> {{ currentIp || cameraIp || "-----" }}</span>
      <span><b>Session:</b> {{ sessionId || 0 }}</span>
      <span><b>FPS:</b> {{ fps }}</span>
      <span><b>OCR:</b> {{ ocrRunning ? "Đang xử lý" : "Sẵn sàng" }}</span>
      <span><b>Mode:</b> Direct Preview + Polling</span>
      <span><b>Khóa phiên:</b> {{ scanLocked ? "Đã khóa" : "Đang quét" }}</span>
      <span><b>Preview Health:</b> {{ previewHealthy ? "OK" : "Waiting..." }}</span>
    </div>

    <div class="video-wrapper">
      <img
        v-if="previewRunning && directCameraUrl"
        :key="directCameraKey"
        :src="directCameraUrl"
        class="video"
        alt="Direct Camera Preview"
        @load="handleDirectPreviewLoaded"
        @error="handleDirectPreviewError"
      />

      <div v-else class="video-off">
        Camera Offline
      </div>
    </div>

    <div class="plate-panel">
      <div class="plate-box">
        <div class="plate-label">Confirmed Plate</div>
        <div class="plate-number confirmed">
          {{ confirmedPlate || "-----" }}
        </div>
      </div>

      <div class="plate-box">
        <div class="plate-label">Last Raw Plate</div>
        <div class="plate-number raw">
          {{ lastRawPlate || "-----" }}
        </div>
      </div>
    </div>

    <div class="lock-banner" v-if="scanLocked">
      Đã đọc xong và khóa kết quả. Bấm “{{ sessionActionLabel }}” để quét biển mới.
    </div>

    <div class="evidence-panel">
      <div class="evidence-card">
        <div class="evidence-title">Ảnh chụp toàn khung</div>
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
      <div class="live-title">OCR Candidates</div>

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
import {
  turnOnCamera,
  turnOffCamera,
  resetCameraState,
  getCameraStatus,
  getCameraResult,
  getLockedImages
} from "../services/biensoApi"

export default {
  name: "BienSoSecurity",

  data() {
    return {
      cameraIp: "",
      currentIp: "",
      cameraRunning: false, // backend OCR/camera state
      previewRunning: false, // chỉ preview Vue
      loading: false,

      // session / state chống dữ liệu cũ
      sessionId: 0,
      lastAppliedSessionId: 0,
      lastLockedImageSessionId: 0,

      // result state
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

      // direct preview từ camera
      directCameraUrl: "",
      directCameraKey: 0,
      previewHealthy: false,

      // polling
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
    }
  },

  async mounted() {
    this.destroyed = false
    await this.loadCurrentStatus()

    if (this.cameraRunning) {
      this.startResultLoop()
    }
  },

  beforeUnmount() {
    this.destroyed = true
    this.stopResultLoop()
    this.resetDirectPreview()
  },

  activated() {
    this.destroyed = false
    if (this.cameraRunning) {
      if (this.currentIp && !this.previewRunning) {
        this.mountDirectPreview(this.currentIp)
      }
      this.startResultLoop()
    }
  },

  deactivated() {
    this.stopResultLoop()
  },

  methods: {
    formatConf(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return num.toFixed(4)
    },

    buildDirectCameraUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""

      const sep = raw.includes("?") ? "&" : "?"
      return `${raw}${sep}t=${Date.now()}`
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

    mountDirectPreview(url) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return

      this.directCameraUrl = this.buildDirectCameraUrl(cleanUrl)
      this.directCameraKey += 1
      this.previewHealthy = false
      this.previewRunning = true
    },

    resetDirectPreview() {
      this.directCameraUrl = ""
      this.directCameraKey += 1
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

        // Khi load lại trang:
        // - backend có thể đang chạy
        // - preview Vue thì tự mở lại để đồng bộ trải nghiệm
        if (this.currentIp) {
          this.mountDirectPreview(this.currentIp)
        } else {
          this.resetDirectPreview()
        }

        if (this.cameraRunning) {
          await this.fetchLockedImagesIfNeeded(true)
        }
      } catch (e) {
        console.error("Load status error:", e)
      }
    },

    async handleTurnOnPreview() {
      const ip = (this.cameraIp || this.currentIp || "").trim()
      if (!ip) {
        alert("Vui lòng nhập URL camera")
        return
      }

      try {
        this.loading = true

        // Chỉ mở preview Vue, không gọi backend
        this.currentIp = ip
        this.mountDirectPreview(ip)
        this.message = "Đã mở preview camera trên giao diện"
      } catch (e) {
        console.error("Turn on preview error:", e)
        alert(e?.message || "Lỗi mở preview camera")
      } finally {
        this.loading = false
      }
    },

    async handleInitOrResetSession() {
      const ip = (this.cameraIp || this.currentIp || "").trim()
      if (!ip) {
        alert("Vui lòng nhập URL camera")
        return
      }

      try {
        this.loading = true

        // luôn đảm bảo preview có thể xem được
        this.currentIp = ip
        if (!this.previewRunning) {
          this.mountDirectPreview(ip)
        }

        // clear dữ liệu UI trước khi bắt đầu/reset
        this.clearResultStateOnly()

        // Trường hợp 1: backend chưa chạy -> gửi URL để mở camera backend
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

        // Trường hợp 2: backend đang chạy -> reset phiên đọc
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
      } catch (e) {
        console.error("Init/Reset session error:", e)
        alert(e?.message || "Lỗi khởi tạo / reset phiên đọc")
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
        } catch (e) {
          console.warn("Turn off warning:", e)
        }

        this.hardResetUiState()
        this.resetDirectPreview()
      } catch (e) {
        console.error("Turn off error:", e)
        alert(e?.message || "Lỗi tắt camera")
      } finally {
        this.loading = false
      }
    },

    async refreshResult() {
      try {
        const res = await getCameraResult()
        await this.applyRealtimeState(res, true)
      } catch (e) {
        console.warn("Result polling error:", e)
      }
    },

    async fetchLockedImagesIfNeeded(force = false) {
      if (this.destroyed) return
      if (!this.cameraRunning) return

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
      } catch (e) {
        console.warn("Fetch locked images error:", e)
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

      // nếu preview đang tắt nhưng đã có IP thì không tự ép mở,
      // vì theo yêu cầu preview phải do nút Vue điều khiển.
      // Chỉ mounted() mới tự restore preview khi reload trang.
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

    handleDirectPreviewLoaded() {
      this.previewHealthy = true
    },

    handleDirectPreviewError() {
      this.previewHealthy = false
    }
  }
}
</script>

<style scoped>
.security-container {
  width: 1100px;
  margin: auto;
  text-align: center;
  font-family: Arial, sans-serif;
  padding: 20px;
}

.title {
  margin-bottom: 20px;
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
  width: 420px;
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
  min-width: 170px;
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

.status-bar {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
  font-size: 14px;
}

.video-wrapper {
  width: 800px;
  height: 450px;
  background: black;
  margin: auto;
  position: relative;
  margin-top: 20px;
  overflow: hidden;
  border-radius: 12px;
}

.video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.video-off {
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
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
}

.confirmed {
  color: #00aa00;
}

.raw {
  color: #ff8800;
}

.lock-banner {
  width: 800px;
  margin: 20px auto 0;
  padding: 12px 16px;
  background: #fff3cd;
  border: 1px solid #ffe69c;
  border-radius: 10px;
  color: #7a5b00;
  font-weight: bold;
}

.evidence-panel {
  width: 1000px;
  margin: 20px auto 0;
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.evidence-card {
  width: 460px;
  background: #f7f7f7;
  border-radius: 12px;
  padding: 16px;
  text-align: left;
}

.evidence-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
}

.evidence-image {
  width: 100%;
  border-radius: 10px;
  border: 1px solid #ddd;
}

.evidence-empty {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
  background: white;
  border-radius: 10px;
  border: 1px dashed #ccc;
}

.live-panel {
  margin-top: 20px;
  text-align: left;
  width: 800px;
  margin-left: auto;
  margin-right: auto;
  background: #f7f7f7;
  border-radius: 12px;
  padding: 16px;
}

.live-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.candidate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 10px 12px;
}

.candidate-text {
  font-size: 18px;
  font-weight: 700;
  color: #0d6efd;
}

.candidate-meta {
  font-size: 13px;
  color: #666;
}

.candidate-empty {
  color: #777;
  font-style: italic;
}

.result-panel {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
}
</style>