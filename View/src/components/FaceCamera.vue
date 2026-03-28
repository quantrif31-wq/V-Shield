<template>
  <div class="security-container">
    <h1 class="title">V-Shield FaceID Monitor</h1>

    <div class="control-panel">
      <input
        v-model="cameraIp"
        type="text"
        class="ip-input"
        placeholder="Nhập URL camera / stream URL..."
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
      <span><b>Camera:</b> {{ cameraRunning ? "Đang chạy" : "Đang tắt" }}</span>
      <span><b>Kết nối:</b> {{ cameraConnected ? "Đã kết nối" : "Chưa kết nối" }}</span>
      <span><b>Preview:</b> {{ previewRunning ? "Đang mở" : "Đang tắt" }}</span>
      <span><b>Input URL:</b> {{ currentIp || cameraIp || "-----" }}</span>
      <span><b>FPS:</b> {{ fps }}</span>
      <span><b>Tracking:</b> {{ trackingActive ? "Đang theo dõi" : "Idle" }}</span>
      <span><b>Lock:</b> {{ scanLocked ? "Đã khóa" : "Đang quét" }}</span>
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

    <div class="face-panel">
      <div class="face-box">
        <div class="face-label">Employee ID</div>
        <div class="face-number confirmed">
          {{ employeeId || "-----" }}
        </div>
      </div>

      <div class="face-box">
        <div class="face-label">Recognition State</div>
        <div class="face-number raw">
          {{ detectionLabel }}
        </div>
      </div>
    </div>

    <div class="lock-banner" v-if="scanLocked">
      Đã có kết quả cuối và khóa phiên. Bấm “{{ sessionActionLabel }}” để quét người tiếp theo.
    </div>

    <div class="alert-banner" v-if="alert">
      🚨 CẢNH BÁO: Người lạ / không xác nhận được danh tính
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
        <div class="evidence-title">Ảnh crop khuôn mặt</div>
        <img
          v-if="lockedFaceCrop"
          :src="lockedFaceCrop"
          class="evidence-image"
          alt="Locked Face Crop"
        />
        <div v-else class="evidence-empty">Chưa có ảnh</div>
      </div>
    </div>

    <div class="live-panel">
      <div class="live-title">Face Realtime State</div>

      <div class="candidate-list">
        <div class="candidate-item">
          <span class="candidate-text">Face Match</span>
          <span class="candidate-meta">{{ faceMatch ? "Yes" : "No" }}</span>
        </div>

        <div class="candidate-item">
          <span class="candidate-text">Identity Confirmed</span>
          <span class="candidate-meta">{{ identityConfirmed ? "Yes" : "No" }}</span>
        </div>

        <div class="candidate-item">
          <span class="candidate-text">Confirm Count</span>
          <span class="candidate-meta">{{ confirmCount }}</span>
        </div>

        <div class="candidate-item">
          <span class="candidate-text">Distance</span>
          <span class="candidate-meta">{{ distanceText }}</span>
        </div>

        <div class="candidate-item">
          <span class="candidate-text">Lock Reason</span>
          <span class="candidate-meta">{{ lockReason || "-----" }}</span>
        </div>
      </div>
    </div>

    <div class="result-panel">
      <div><b>Box:</b> {{ bboxText }}</div>
      <div><b>Employee ID:</b> {{ employeeId || "-----" }}</div>
      <div><b>Tracking Active:</b> {{ trackingActive ? "Yes" : "No" }}</div>
      <div><b>Identity Confirmed:</b> {{ identityConfirmed ? "Yes" : "No" }}</div>
      <div><b>Face Match:</b> {{ faceMatch ? "Yes" : "No" }}</div>
      <div><b>Timeout:</b> {{ timeoutState ? "Yes" : "No" }}</div>
      <div><b>Alert:</b> {{ alert ? "Yes" : "No" }}</div>
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
} from "../services/faceApi"

export default {
  name: "FaceIdSecurity",

  data() {
    return {
      cameraIp: "",
      currentIp: "",
      cameraRunning: false,
      cameraConnected: false,
      previewRunning: false,
      loading: false,

      employeeId: "",
      trackingActive: false,
      identityConfirmed: false,
      faceMatch: false,
      confirmCount: 0,
      distance: null,
      bbox: null,
      timeoutState: false,
      alert: false,

      lockedSnapshot: "",
      lockedFaceCrop: "",
      scanLocked: false,
      lockReason: "",

      fps: 0,
      message: "",
      lastUpdate: "",

      directCameraUrl: "",
      directCameraKey: 0,
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

      return `left=${this.bbox.left}, top=${this.bbox.top}, right=${this.bbox.right}, bottom=${this.bbox.bottom}`
    },

    sessionActionLabel() {
      return this.cameraRunning ? "Reset phiên nhận diện" : "Khởi tạo phiên nhận diện"
    },

    detectionLabel() {
      if (this.scanLocked) {
        if (this.lockReason === "confirmed") return "LOCKED - IDENTIFIED"
        if (this.lockReason === "timeout") return "LOCKED - TIMEOUT"
        if (this.lockReason === "alert") return "LOCKED - ALERT"
        return "LOCKED"
      }

      if (!this.trackingActive) return "IDLE"
      if (this.identityConfirmed) return "IDENTIFIED"
      if (this.faceMatch) return "VERIFYING"
      return "UNKNOWN"
    },

    distanceText() {
      const num = Number(this.distance)
      if (Number.isNaN(num)) return "-----"
      return num.toFixed(4)
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
    // Resuming from keep-alive: restart timers if camera was running
    this.destroyed = false
    if (this.cameraRunning) {
      if (this.currentIp && !this.previewRunning) {
        this.mountDirectPreview(this.currentIp)
      }
      this.startResultLoop()
    }
  },

  deactivated() {
    // Pausing for keep-alive: stop timers but keep state
    this.stopResultLoop()
  },

  methods: {
    buildDirectCameraUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""

      const sep = raw.includes("?") ? "&" : "?"
      return `${raw}${sep}t=${Date.now()}`
    },

    clearResultStateOnly() {
      this.employeeId = ""
      this.trackingActive = false
      this.identityConfirmed = false
      this.faceMatch = false
      this.confirmCount = 0
      this.distance = null
      this.bbox = null
      this.timeoutState = false
      this.alert = false

      this.lockedSnapshot = ""
      this.lockedFaceCrop = ""
      this.scanLocked = false
      this.lockReason = ""

      this.fps = 0
      this.message = ""
      this.lastUpdate = ""
    },

    hardResetUiState() {
      this.cameraRunning = false
      this.cameraConnected = false
      this.currentIp = ""
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

        this.currentIp = ip
        if (!this.previewRunning) {
          this.mountDirectPreview(ip)
        }

        this.clearResultStateOnly()

        if (!this.cameraRunning) {
          this.stopResultLoop()

          const res = await turnOnCamera(ip)
          if (!res?.success) {
            alert(res?.message || "Không thể khởi tạo phiên nhận diện")
            return
          }

          this.cameraRunning = true
          this.currentIp = ip
          this.message = res.message || "Khởi tạo phiên nhận diện thành công"

          await this.refreshResult()
          this.startResultLoop()
          return
        }

        const res = await resetCameraState()
        this.message = res?.message || "Đã reset phiên nhận diện"

        await this.refreshResult()

        if (!this.resultTimer) {
          this.startResultLoop()
        }
      } catch (e) {
        console.error("Init/Reset session error:", e)
        alert(e?.message || "Lỗi khởi tạo / reset phiên nhận diện")
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
      if (!this.scanLocked && !force) {
        this.lockedSnapshot = ""
        this.lockedFaceCrop = ""
        return
      }
      if (this.isFetchingLockedImages) return

      this.isFetchingLockedImages = true
      try {
        const res = await getLockedImages()

        if (res?.scan_locked) {
          this.lockedSnapshot = res.locked_snapshot || ""
          this.lockedFaceCrop = res.locked_face_crop || ""
        } else {
          this.lockedSnapshot = ""
          this.lockedFaceCrop = ""
        }
      } catch (e) {
        console.warn("Fetch locked images error:", e)
      } finally {
        this.isFetchingLockedImages = false
      }
    },

    async applyRealtimeState(res, allowTurnOffReset = true) {
      if (!res || this.destroyed) return

      const incomingCameraEnabled = !!res.camera_enabled

      this.cameraRunning = incomingCameraEnabled
      this.cameraConnected = !!res.camera_connected
      this.currentIp = res.ip || this.currentIp

      this.employeeId = res.employee_id || ""
      this.trackingActive = !!res.tracking_active
      this.identityConfirmed = !!res.identity_confirmed
      this.faceMatch = !!res.face_match
      this.confirmCount = Number(res.confirm_count || 0)
      this.distance = res.distance ?? null
      this.bbox = res.bbox || null
      this.timeoutState = !!res.timeout
      this.alert = !!res.alert

      this.scanLocked = !!res.scan_locked
      this.lockReason = res.lock_reason || ""

      this.fps = Number(res.fps || 0)
      this.message = res.message || ""
      this.lastUpdate = res.last_update || ""

      if (!this.scanLocked) {
        this.lockedSnapshot = ""
        this.lockedFaceCrop = ""
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

.face-panel {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.face-box {
  min-width: 280px;
}

.face-label {
  font-size: 16px;
  margin-bottom: 8px;
  color: #666;
}

.face-number {
  font-size: 30px;
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

.alert-banner {
  width: 800px;
  margin: 20px auto 0;
  padding: 12px 16px;
  background: #f8d7da;
  border: 1px solid #f1aeb5;
  border-radius: 10px;
  color: #842029;
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
  font-size: 16px;
  font-weight: 700;
  color: #0d6efd;
}

.candidate-meta {
  font-size: 13px;
  color: #666;
}

.result-panel {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
}
</style>