<template>
  <div class="scanner-page">
    <div class="scanner-card">
      <h2>Dynamic QR IP Scanner</h2>

      <div class="form-group">
        <label>IP Camera URL</label>
        <input
          v-model="cameraIp"
          type="text"
          class="ip-input"
          placeholder="Ví dụ: http://192.168.1.100:8080/shot.jpg"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Chu kỳ làm mới ảnh (ms)</label>
          <input v-model.number="previewIntervalMs" type="number" min="150" step="50" class="ip-input" />
        </div>

        <div class="form-group">
          <label>Ngưỡng mất mã để đóng phiên (ms)</label>
          <input v-model.number="absenceThresholdMs" type="number" min="500" step="100" class="ip-input" />
        </div>

        <div class="form-group">
          <label>Chiều rộng decode tối đa (px)</label>
          <input v-model.number="decodeMaxWidth" type="number" min="240" step="20" class="ip-input" />
        </div>
      </div>

      <div class="button-row">
        <button class="btn btn-primary" @click="startCamera" :disabled="loading || cameraRunning">
          {{ loading ? "Đang khởi động..." : "Bật camera" }}
        </button>

        <button class="btn btn-danger" @click="stopCamera" :disabled="loading || !cameraRunning">
          {{ loading ? "Đang tắt..." : "Tắt camera" }}
        </button>

        <button class="btn btn-reset" @click="manualResetSession">
          Reset phiên quét
        </button>
      </div>

      <div class="preview-wrap">
        <img
          v-if="previewRunning && directCameraUrl"
          ref="cameraImage"
          :src="directCameraUrl"
          class="video"
          alt="Camera Preview"
          crossorigin="anonymous"
          @load="handleDirectPreviewLoaded"
          @error="handleDirectPreviewError"
        />

        <div v-else class="preview-placeholder">
          Camera chưa chạy
        </div>

        <canvas ref="captureCanvas" style="display:none;"></canvas>
      </div>

      <div class="status-grid">
        <div><b>Camera URL:</b> {{ currentIp || "-----" }}</div>
        <div><b>Camera running:</b> {{ cameraRunning ? "Yes" : "No" }}</div>
        <div><b>Preview healthy:</b> {{ previewHealthy ? "Yes" : "No" }}</div>
        <div><b>Image loading:</b> {{ imgBusy ? "Yes" : "No" }}</div>

        <div><b>Thiết bị quét:</b> {{ scannerDevice || "-----" }}</div>
        <div><b>Payload hiện tại:</b> {{ shortPayload }}</div>
        <div><b>Payload đang theo dõi:</b> {{ shortTrackedPayload }}</div>
        <div><b>Trạng thái phiên:</b> {{ sessionStateText }}</div>

        <div><b>Thông điệp phiên:</b> {{ trackedVerifyStateText }}</div>
        <div><b>Last decoded:</b> {{ formatDateTime(lastDecodedAt) || "-----" }}</div>
        <div><b>Lần cuối thấy mã:</b> {{ formatDateTime(lastSeenAt) || "-----" }}</div>
        <div><b>Last update:</b> {{ lastUpdate || "-----" }}</div>

        <div><b>Refresh ảnh:</b> {{ previewIntervalMs }} ms</div>
        <div><b>Đóng phiên khi mất mã:</b> {{ absenceThresholdMs }} ms</div>
        <div><b>Decode max width:</b> {{ decodeMaxWidth }} px</div>
        <div><b>Độ phân giải ảnh hiện tại:</b> {{ currentFrameInfo }}</div>
      </div>

      <div class="verify-box" v-if="verifyMessage">
        <div class="verify-message"><b>Kết quả verify:</b> {{ verifyMessage }}</div>
        <div v-if="verifyData" class="verify-data">
          <div><b>Employee ID:</b> {{ verifyData.employeeId || "-----" }}</div>
          <div><b>Employee Name:</b> {{ verifyData.employeeName || "-----" }}</div>
          <div><b>Verified At:</b> {{ formatDate(verifyData.verifiedAtUtc) || "-----" }}</div>
          <div><b>Counter:</b> {{ verifyData.counter ?? "-----" }}</div>
          <div><b>Expires:</b> {{ formatDate(verifyData.expiresAtUtc) || "-----" }}</div>
        </div>
      </div>
    </div>

    <div class="manual-panel">
      <h3>Test verify thủ công</h3>

      <div class="form-group">
        <label>Tên thiết bị quét</label>
        <input
          v-model="scannerDevice"
          type="text"
          class="ip-input"
          placeholder="Ví dụ: WEB_SCANNER_GATE_01"
        />
      </div>

      <div class="form-group">
        <label>QR Payload</label>
        <textarea
          v-model="manualPayload"
          rows="4"
          class="text-area"
          placeholder="Dán payload QR vào đây để test"
        ></textarea>
      </div>

      <button class="btn btn-reset" @click="verifyManual" :disabled="verifying">
        {{ verifying ? "Đang xác thực..." : "Xác thực thủ công" }}
      </button>
    </div>
  </div>
</template>

<script>
import jsQR from "jsqr"
import { verifyDynamicQr } from "../services/dynamicQrVerifyApi"

export default {
  name: "DynamicQrIpScanner",

  data() {
    return {
      cameraIp: "",
      currentIp: "",
      cameraRunning: false,
      previewRunning: false,
      loading: false,

      directCameraUrl: "",
      previewHealthy: false,
      imgBusy: false,
      decodeBusy: false,

      scannerDevice: "WEB_SCANNER_GATE_01",
      qrPayload: "",
      manualPayload: "",
      verifyMessage: "",
      verifyData: null,
      verifying: false,

      activeSessionPayload: "",
      activeSessionVerified: false,
      activeSessionVerifyState: "",
      activeSessionVerifyMessage: "",
      lastSeenAt: null,

      lastDecodedText: "",
      lastDecodedAt: 0,
      lastUpdate: "",

      previewTimer: null,
      sessionTimer: null,
      destroyed: false,

      previewIntervalMs: 350,
      absenceThresholdMs: 1500,
      decodeMaxWidth: 640,

      frameWidth: 0,
      frameHeight: 0
    }
  },

  computed: {
    shortPayload() {
      if (!this.qrPayload) return "-----"
      return this.qrPayload.length <= 60 ? this.qrPayload : this.qrPayload.slice(0, 60) + "..."
    },

    shortTrackedPayload() {
      if (!this.activeSessionPayload) return "-----"
      return this.activeSessionPayload.length <= 60
        ? this.activeSessionPayload
        : this.activeSessionPayload.slice(0, 60) + "..."
    },

    sessionStateText() {
      if (!this.cameraRunning) return "Chưa quét"
      if (!this.activeSessionPayload) return "Đang tự động chờ mã mới"

      if (this.activeSessionVerifyState === "waiting") return "Đang xử lý phiên hiện tại"
      if (this.activeSessionVerifyState === "success") return "Đã xác thực, đang giữ phiên"
      if (this.activeSessionVerifyState === "expired") return "Phiên hiện tại hết hiệu lực"
      if (this.activeSessionVerifyState === "invalid") return "Mã không hợp lệ, đang giữ phiên"
      if (this.activeSessionVerifyState === "failed") return "Xác thực thất bại, đang giữ phiên"
      if (this.activeSessionVerifyState === "system_error") return "Lỗi hệ thống khi verify"

      return "Đang giữ phiên hiện tại"
    },

    trackedVerifyStateText() {
      if (!this.activeSessionPayload) return "-----"
      return this.activeSessionVerifyMessage || "Chưa verify"
    },

    currentFrameInfo() {
      if (!this.frameWidth || !this.frameHeight) return "-----"
      return `${this.frameWidth} x ${this.frameHeight}`
    }
  },

  beforeUnmount() {
    this.destroyed = true
    this.stopPreviewLoop()
    this.stopSessionLoop()
    this.resetDirectPreview()
  },

  methods: {
    nowText() {
      return new Date().toLocaleString()
    },

    buildDirectCameraUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""
      const sep = raw.includes("?") ? "&" : "?"
      return `${raw}${sep}_ts=${Date.now()}`
    },

    mountDirectPreview(url) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return

      this.directCameraUrl = this.buildDirectCameraUrl(cleanUrl)
      this.previewHealthy = false
      this.previewRunning = true
    },

    refreshDirectPreview() {
      if (!this.previewRunning || !this.currentIp) return
      if (this.imgBusy) return

      this.imgBusy = true
      this.directCameraUrl = this.buildDirectCameraUrl(this.currentIp)
    },

    resetDirectPreview() {
      this.directCameraUrl = ""
      this.previewHealthy = false
      this.previewRunning = false
      this.imgBusy = false
      this.decodeBusy = false
      this.frameWidth = 0
      this.frameHeight = 0
    },

    formatDate(dateValue) {
      if (!dateValue) return ""
      return new Date(dateValue).toLocaleString()
    },

    formatDateTime(value) {
      if (!value) return ""
      return new Date(value).toLocaleString()
    },

    resetSessionState() {
      this.activeSessionPayload = ""
      this.activeSessionVerified = false
      this.activeSessionVerifyState = ""
      this.activeSessionVerifyMessage = ""
      this.lastSeenAt = null
    },

    manualResetSession() {
      this.resetSessionState()
      this.verifyMessage = "Đã reset phiên thủ công. Đang chờ mã mới."
      this.verifyData = null
      this.lastUpdate = this.nowText()
    },

    async startCamera() {
      const ip = String(this.cameraIp || "").trim()
      if (!ip) {
        alert("Vui lòng nhập IP camera URL.")
        return
      }

      this.loading = true
      try {
        this.currentIp = ip
        this.cameraRunning = true
        this.resetSessionState()
        this.mountDirectPreview(ip)
        this.startPreviewLoop()
        this.startSessionLoop()
        this.lastUpdate = this.nowText()
      } catch (e) {
        console.error("Start camera error:", e)
        alert(e?.message || "Lỗi bật camera")
      } finally {
        this.loading = false
      }
    },

    async stopCamera() {
      this.loading = true
      try {
        this.stopPreviewLoop()
        this.stopSessionLoop()
        this.cameraRunning = false
        this.currentIp = ""
        this.resetSessionState()
        this.resetDirectPreview()
      } catch (e) {
        console.error("Turn off error:", e)
        alert(e?.message || "Lỗi tắt camera")
      } finally {
        this.loading = false
      }
    },

    startPreviewLoop() {
      this.stopPreviewLoop()

      this.previewTimer = setInterval(() => {
        if (this.destroyed) return
        if (!this.cameraRunning) return
        this.refreshDirectPreview()
      }, this.previewIntervalMs)
    },

    stopPreviewLoop() {
      if (this.previewTimer) {
        clearInterval(this.previewTimer)
        this.previewTimer = null
      }
    },

    startSessionLoop() {
      this.stopSessionLoop()

      this.sessionTimer = setInterval(() => {
        if (this.destroyed) return
        if (!this.cameraRunning) return
        this.checkSessionExpiry()
      }, 200)
    },

    stopSessionLoop() {
      if (this.sessionTimer) {
        clearInterval(this.sessionTimer)
        this.sessionTimer = null
      }
    },

    checkSessionExpiry() {
      if (!this.activeSessionPayload || !this.lastSeenAt) return

      const now = Date.now()
      const diff = now - this.lastSeenAt

      if (diff >= this.absenceThresholdMs) {
        this.resetSessionState()
        this.verifyMessage = "Mã đã biến mất khỏi camera, phiên cũ đã tự động kết thúc. Đang chờ mã mới."
        this.verifyData = null
        this.lastUpdate = this.nowText()
      }
    },

    async handleDirectPreviewLoaded() {
      this.previewHealthy = true
      this.imgBusy = false

      if (this.decodeBusy || this.verifying) return

      await this.captureAndDecode()
    },

    handleDirectPreviewError() {
      this.previewHealthy = false
      this.imgBusy = false
    },

    async captureAndDecode() {
      const img = this.$refs.cameraImage
      const canvas = this.$refs.captureCanvas

      if (!img || !canvas) return
      if (!img.complete) return
      if (this.decodeBusy) return

      this.decodeBusy = true

      try {
        const sourceWidth = img.naturalWidth || img.width
        const sourceHeight = img.naturalHeight || img.height
        if (!sourceWidth || !sourceHeight) return

        this.frameWidth = sourceWidth
        this.frameHeight = sourceHeight

        let targetWidth = sourceWidth
        let targetHeight = sourceHeight

        if (sourceWidth > this.decodeMaxWidth) {
          const ratio = this.decodeMaxWidth / sourceWidth
          targetWidth = Math.round(sourceWidth * ratio)
          targetHeight = Math.round(sourceHeight * ratio)
        }

        canvas.width = targetWidth
        canvas.height = targetHeight

        const ctx = canvas.getContext("2d", { willReadFrequently: true })
        ctx.clearRect(0, 0, targetWidth, targetHeight)
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight)

        const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight)
        const code = jsQR(imageData.data, targetWidth, targetHeight, {
          inversionAttempts: "attemptBoth"
        })

        if (!code?.data) return

        const decodedText = String(code.data || "").trim()
        if (!decodedText) return

        const now = Date.now()

        this.qrPayload = decodedText
        this.manualPayload = decodedText
        this.lastDecodedText = decodedText
        this.lastDecodedAt = now

        if (this.activeSessionPayload && decodedText === this.activeSessionPayload) {
          this.lastSeenAt = now
          return
        }

        this.activeSessionPayload = decodedText
        this.activeSessionVerified = false
        this.activeSessionVerifyState = "waiting"
        this.activeSessionVerifyMessage = "Đã phát hiện mã mới, đang xác thực..."
        this.lastSeenAt = now
        this.lastUpdate = this.nowText()

        const result = await this.doVerify(decodedText)

        if (result?.success) {
          this.activeSessionVerified = true
          this.markSessionVerifyState("success", result.message || "Xác thực QR động thành công.")
          return
        }

        const message = String(result?.message || "")
        if (message.includes("đã hết hạn") || message.includes("chưa đến hiệu lực")) {
          this.markSessionVerifyState("expired", message)
        } else if (message.includes("không hợp lệ")) {
          this.markSessionVerifyState("invalid", message)
        } else {
          this.markSessionVerifyState("failed", message || "Xác thực thất bại.")
        }
      } catch (e) {
        console.warn("Decode frame error:", e)
        this.verifyMessage =
          "Không đọc được frame từ IP camera. Kiểm tra CORS, mixed content hoặc URL stream."
        this.markSessionVerifyState("system_error", this.verifyMessage)
      } finally {
        this.decodeBusy = false
      }
    },

    async doVerify(payload) {
      this.verifying = true
      try {
        const result = await verifyDynamicQr(payload, this.scannerDevice)

        this.verifyMessage = result?.message || ""
        this.verifyData = result?.data || null
        this.lastUpdate = this.nowText()

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

        this.verifyMessage = message
        this.verifyData = null
        this.lastUpdate = this.nowText()

        return {
          success: false,
          message,
          data: null
        }
      } finally {
        this.verifying = false
      }
    },

    markSessionVerifyState(state, message) {
      this.activeSessionVerifyState = state
      this.activeSessionVerifyMessage = message || ""
      this.lastUpdate = this.nowText()
    },

    async verifyManual() {
      const payload = String(this.manualPayload || "").trim()
      if (!payload) {
        alert("Vui lòng nhập QR payload.")
        return
      }

      const result = await this.doVerify(payload)

      if (result?.success) {
        this.markSessionVerifyState("success", result.message || "Xác thực QR động thành công.")
      } else {
        const message = String(result?.message || "")
        if (message.includes("đã hết hạn") || message.includes("chưa đến hiệu lực")) {
          this.markSessionVerifyState("expired", message)
        } else if (message.includes("không hợp lệ")) {
          this.markSessionVerifyState("invalid", message)
        } else {
          this.markSessionVerifyState("failed", message || "Xác thực thất bại.")
        }
      }
    }
  }
}
</script>

<style scoped>
.scanner-page {
  max-width: 1200px;
  margin: 24px auto;
  padding: 16px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.scanner-card,
.manual-panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}

.ip-input,
.text-area {
  width: 100%;
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 10px 12px;
  outline: none;
  font-size: 14px;
  box-sizing: border-box;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
}

.btn-danger {
  background: #dc2626;
  color: #fff;
}

.btn-reset {
  background: #111827;
  color: #fff;
}

.preview-wrap {
  width: 100%;
  min-height: 360px;
  background: #f3f4f6;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.video {
  width: 100%;
  display: block;
}

.preview-placeholder {
  color: #6b7280;
  font-weight: 600;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  font-size: 14px;
}

.verify-box {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.verify-message {
  margin-bottom: 8px;
  font-weight: 600;
}

.verify-data > div {
  margin-bottom: 4px;
}

@media (max-width: 900px) {
  .scanner-page {
    grid-template-columns: 1fr;
  }

  .status-grid,
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>