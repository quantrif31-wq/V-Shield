<template>
  <div class="scanner-page">
    <div class="scanner-card">
      <h2>Quét QR để điểm danh</h2>

      <div class="source-panel">
        <div class="source-field">
          <label>Camera đã cấu hình</label>
          <select
            v-model="selectedConfiguredCameraId"
            class="ip-input"
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

      <div class="form-group">
        <label>Preview URL để quét QR</label>
        <input
          v-model="cameraIp"
          type="text"
          class="ip-input"
          placeholder="Ví dụ: https://.../stream.mp4 hoặc .../stream.m3u8"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Chu kỳ đọc frame (ms)</label>
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
          v-if="previewRunning && previewMode === 'image' && directCameraUrl"
          ref="cameraImage"
          :src="directCameraUrl"
          class="video"
          alt="Camera Preview"
          crossorigin="anonymous"
          @load="handleImagePreviewLoaded"
          @error="handleImagePreviewError"
        />

        <video
          v-else-if="previewRunning && (previewMode === 'video' || previewMode === 'hls')"
          ref="cameraVideo"
          class="video"
          autoplay
          muted
          playsinline
          crossorigin="anonymous"
          @loadeddata="handleVideoPreviewLoaded"
          @canplay="handleVideoPreviewLoaded"
          @ended="handleVideoPreviewEnded"
          @error="handleVideoPreviewError"
        ></video>

        <div v-else-if="previewRunning && previewMode === 'rtsp'" class="preview-placeholder preview-note">
          RTSP không quét trực tiếp được trên trình duyệt. Hãy dùng Preview URL dạng MP4, HLS hoặc MJPEG.
        </div>

        <div v-else-if="previewRunning && previewMode === 'unsupported'" class="preview-placeholder preview-note">
          URL này chưa được hỗ trợ cho quét QR trên trình duyệt.
        </div>

        <div v-else class="preview-placeholder">
          Camera chưa chạy
        </div>

        <canvas ref="captureCanvas" class="hidden-canvas"></canvas>
      </div>

      <div class="status-grid">
        <div><b>Preview URL:</b> {{ currentIp || "-----" }}</div>
        <div><b>Camera running:</b> {{ cameraRunning ? "Yes" : "No" }}</div>
        <div><b>Preview healthy:</b> {{ previewHealthy ? "Yes" : "No" }}</div>
        <div><b>Mode:</b> {{ previewMode }}</div>

        <div><b>Thiết bị quét:</b> {{ scannerDevice || "-----" }}</div>
        <div><b>Payload hiện tại:</b> {{ shortPayload }}</div>
        <div><b>Payload đang theo dõi:</b> {{ shortTrackedPayload }}</div>
        <div><b>Trạng thái phiên:</b> {{ sessionStateText }}</div>

        <div><b>Thông điệp phiên:</b> {{ trackedVerifyStateText }}</div>
        <div><b>Last decoded:</b> {{ formatDateTime(lastDecodedAt) || "-----" }}</div>
        <div><b>Lần cuối thấy mã:</b> {{ formatDateTime(lastSeenAt) || "-----" }}</div>
        <div><b>Last update:</b> {{ lastUpdate || "-----" }}</div>

        <div><b>Chu kỳ đọc frame:</b> {{ previewIntervalMs }} ms</div>
        <div><b>Đóng phiên khi mất mã:</b> {{ absenceThresholdMs }} ms</div>
        <div><b>Decode max width:</b> {{ decodeMaxWidth }} px</div>
        <div><b>Độ phân giải frame:</b> {{ currentFrameInfo }}</div>
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
import {
  getConfiguredCameraSettings,
  isBrowserVideoCameraUrl,
  isHlsCameraUrl,
  isHttpCameraUrl,
  isRtspCameraUrl,
  resolveCameraPreviewUrl,
  resolveCameraSourceUrl
} from "../utils/cameraNetwork"

const QR_CAMERA_SELECTION_STORAGE_KEY = "vshield-qr-selected-camera"
const HLS_SCRIPT_SRC = "https://cdn.jsdelivr.net/npm/hls.js@1/dist/hls.min.js"

let hlsScriptPromise

const resolvePreviewMode = (url) => {
  const value = String(url || "").trim()
  if (!value) return "empty"
  if (isHlsCameraUrl(value)) return "hls"
  if (isBrowserVideoCameraUrl(value)) return "video"
  if (isRtspCameraUrl(value)) return "rtsp"
  if (isHttpCameraUrl(value)) return "image"
  return "unsupported"
}

export default {
  name: "DynamicQrIpScanner",

  data() {
    return {
      configuredCameras: [],
      selectedConfiguredCameraId: "",

      cameraIp: "",
      currentIp: "",
      cameraRunning: false,
      previewRunning: false,
      loading: false,

      directCameraUrl: "",
      videoPreviewUrl: "",
      previewHealthy: false,
      imgBusy: false,
      decodeBusy: false,
      hlsInstance: null,

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
      return this.qrPayload.length <= 60 ? this.qrPayload : `${this.qrPayload.slice(0, 60)}...`
    },

    shortTrackedPayload() {
      if (!this.activeSessionPayload) return "-----"
      return this.activeSessionPayload.length <= 60
        ? this.activeSessionPayload
        : `${this.activeSessionPayload.slice(0, 60)}...`
    },

    sessionStateText() {
      if (!this.cameraRunning) return "Chưa quét"
      if (!this.activeSessionPayload) return "Đang chờ mã mới"

      if (this.activeSessionVerifyState === "waiting") return "Đang xác thực phiên hiện tại"
      if (this.activeSessionVerifyState === "success") return "Đã xác thực, đang giữ phiên"
      if (this.activeSessionVerifyState === "expired") return "Phiên hiện tại hết hiệu lực"
      if (this.activeSessionVerifyState === "invalid") return "Mã không hợp lệ"
      if (this.activeSessionVerifyState === "failed") return "Xác thực thất bại"
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
        return "Chọn camera đã cấu hình để nạp Preview URL vào màn quét QR."
      }

      return `Đang chọn ${this.selectedConfiguredCamera.name}: preview = ${
        this.selectedConfiguredCamera.browserPreviewUrl || this.selectedConfiguredCamera.sourceUrl || "-----"
      }`
    },

    previewMode() {
      return resolvePreviewMode(this.currentIp || this.cameraIp)
    }
  },

  mounted() {
    this.destroyed = false
    this.loadConfiguredCameras()
  },

  beforeUnmount() {
    this.destroyed = true
    this.stopPreviewLoop()
    this.stopSessionLoop()
    this.resetPreviewState()
  },

  activated() {
    this.destroyed = false
    this.loadConfiguredCameras()

    if (this.cameraRunning && this.currentIp) {
      this.restorePreview()
      this.startPreviewLoop()
      this.startSessionLoop()
    }
  },

  deactivated() {
    this.stopPreviewLoop()
    this.stopSessionLoop()

    const video = this.$refs.cameraVideo
    if (video) {
      try {
        video.pause()
      } catch {
        // ignore
      }
    }
  },

  methods: {
    async ensureHlsLibrary() {
      if (window.Hls) return window.Hls

      if (!hlsScriptPromise) {
        hlsScriptPromise = new Promise((resolve, reject) => {
          const existing = document.querySelector(`script[src="${HLS_SCRIPT_SRC}"]`)
          if (existing) {
            existing.addEventListener("load", () => resolve(window.Hls), { once: true })
            existing.addEventListener("error", () => reject(new Error("Không tải được HLS player.")), { once: true })
            return
          }

          const script = document.createElement("script")
          script.src = HLS_SCRIPT_SRC
          script.async = true
          script.onload = () => resolve(window.Hls)
          script.onerror = () => reject(new Error("Không tải được HLS player."))
          document.head.appendChild(script)
        })
      }

      return hlsScriptPromise
    },

    loadConfiguredCameras() {
      const cameras = getConfiguredCameraSettings().map((camera) => ({
        ...camera,
        sourceUrl: resolveCameraSourceUrl(camera),
        browserPreviewUrl: resolveCameraPreviewUrl(camera),
      }))

      this.configuredCameras = cameras

      const savedCameraId = localStorage.getItem(QR_CAMERA_SELECTION_STORAGE_KEY) || ""
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

      if (!this.cameraIp && this.selectedConfiguredCameraId) {
        this.applyConfiguredCameraSelection({ silent: true })
      }
    },

    rememberConfiguredCameraSelection() {
      if (this.selectedConfiguredCameraId) {
        localStorage.setItem(
          QR_CAMERA_SELECTION_STORAGE_KEY,
          String(this.selectedConfiguredCameraId)
        )
      } else {
        localStorage.removeItem(QR_CAMERA_SELECTION_STORAGE_KEY)
      }
    },

    handleConfiguredCameraChange() {
      this.rememberConfiguredCameraSelection()
      this.applyConfiguredCameraSelection({ silent: true })
    },

    applyConfiguredCameraSelection(options = {}) {
      const { silent = false } = options
      const selectedCamera = this.selectedConfiguredCamera

      if (!selectedCamera) {
        if (!silent) {
          alert("Vui lòng chọn một camera đã cấu hình.")
        }
        return
      }

      const previewCandidate = selectedCamera.browserPreviewUrl || selectedCamera.sourceUrl || ""
      if (!previewCandidate) {
        if (!silent) {
          alert("Camera này chưa có Preview URL dùng cho trình duyệt.")
        }
        return
      }

      this.cameraIp = previewCandidate
      this.rememberConfiguredCameraSelection()
      this.verifyMessage = `Đã nạp ${selectedCamera.name} vào màn quét QR.`
      this.lastUpdate = this.nowText()
    },

    nowText() {
      return new Date().toLocaleString()
    },

    buildDirectCameraUrl(inputUrl) {
      const raw = String(inputUrl || "").trim()
      if (!raw) return ""
      const sep = raw.includes("?") ? "&" : "?"
      return `${raw}${sep}_ts=${Date.now()}`
    },

    async attachVideoPreview() {
      await this.$nextTick()
      const video = this.$refs.cameraVideo
      if (!video) return

      this.destroyHls()

      video.pause()
      video.removeAttribute("src")
      video.load()

      this.previewHealthy = false
      video.src = this.videoPreviewUrl

      try {
        await video.play()
      } catch {
        // ignore autoplay rejection
      }
    },

    async attachHlsPreview() {
      await this.$nextTick()
      const video = this.$refs.cameraVideo
      if (!video) return

      this.destroyHls()

      video.pause()
      video.removeAttribute("src")
      video.load()

      this.previewHealthy = false

      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = this.videoPreviewUrl
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

        this.hlsInstance = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
        })

        this.hlsInstance.on(Hls.Events.ERROR, (_, data) => {
          if (data?.fatal) {
            this.handleVideoPreviewError()
          }
        })

        this.hlsInstance.loadSource(this.videoPreviewUrl)
        this.hlsInstance.attachMedia(video)
        this.hlsInstance.on(Hls.Events.MANIFEST_PARSED, async () => {
          try {
            await video.play()
          } catch {
            // ignore autoplay rejection
          }
        })
      } catch (error) {
        console.error("HLS preview error:", error)
        this.handleVideoPreviewError()
      }
    },

    destroyHls() {
      if (this.hlsInstance) {
        this.hlsInstance.destroy()
        this.hlsInstance = null
      }
    },

    async restorePreview() {
      if (!this.currentIp) return

      const mode = resolvePreviewMode(this.currentIp)
      this.previewRunning = true
      this.previewHealthy = false

      if (mode === "image") {
        this.directCameraUrl = this.buildDirectCameraUrl(this.currentIp)
        this.videoPreviewUrl = ""
        return
      }

      if (mode === "video" || mode === "hls") {
        this.directCameraUrl = ""
        this.videoPreviewUrl = this.currentIp

        if (mode === "video") {
          await this.attachVideoPreview()
        } else {
          await this.attachHlsPreview()
        }
        return
      }

      this.directCameraUrl = ""
      this.videoPreviewUrl = ""
    },

    resetPreviewState() {
      this.destroyHls()

      const video = this.$refs.cameraVideo
      if (video) {
        try {
          video.pause()
        } catch {
          // ignore
        }
        video.removeAttribute("src")
        video.load()
      }

      this.directCameraUrl = ""
      this.videoPreviewUrl = ""
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
        alert("Vui lòng nhập Preview URL của camera.")
        return
      }

      const mode = resolvePreviewMode(ip)
      if (mode === "rtsp") {
        alert("RTSP không thể quét QR trực tiếp trên trình duyệt. Hãy dùng Preview URL dạng MP4, HLS hoặc MJPEG.")
        return
      }

      if (mode === "unsupported") {
        alert("URL này chưa được hỗ trợ để quét QR trên trình duyệt.")
        return
      }

      this.loading = true
      try {
        this.currentIp = ip
        this.cameraRunning = true
        this.resetSessionState()
        await this.restorePreview()
        this.startPreviewLoop()
        this.startSessionLoop()
        this.lastUpdate = this.nowText()
      } catch (error) {
        console.error("Start camera error:", error)
        alert(error?.message || "Lỗi bật camera")
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
        this.resetPreviewState()
      } catch (error) {
        console.error("Turn off error:", error)
        alert(error?.message || "Lỗi tắt camera")
      } finally {
        this.loading = false
      }
    },

    startPreviewLoop() {
      this.stopPreviewLoop()

      this.previewTimer = setInterval(async () => {
        if (this.destroyed) return
        if (!this.cameraRunning) return

        if (this.previewMode === "image") {
          this.refreshDirectPreview()
          return
        }

        if (this.previewMode === "video" || this.previewMode === "hls") {
          await this.captureAndDecode()
        }
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

    refreshDirectPreview() {
      if (!this.previewRunning || !this.currentIp) return
      if (this.imgBusy) return

      this.imgBusy = true
      this.directCameraUrl = this.buildDirectCameraUrl(this.currentIp)
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

    async handleImagePreviewLoaded() {
      this.previewHealthy = true
      this.imgBusy = false

      if (this.decodeBusy || this.verifying) return
      await this.captureAndDecode()
    },

    handleImagePreviewError() {
      this.previewHealthy = false
      this.imgBusy = false
    },

    handleVideoPreviewLoaded() {
      this.previewHealthy = true
    },

    handleVideoPreviewError() {
      this.previewHealthy = false
    },

    async handleVideoPreviewEnded() {
      if (!this.previewRunning || !this.currentIp) return
      if (this.previewMode !== "video" && this.previewMode !== "hls") return
      await this.restorePreview()
    },

    async captureAndDecode() {
      const canvas = this.$refs.captureCanvas
      if (!canvas || this.decodeBusy) return

      const mode = this.previewMode
      const source = mode === "image" ? this.$refs.cameraImage : this.$refs.cameraVideo
      if (!source) return

      if (mode === "image" && !source.complete) return
      if ((mode === "video" || mode === "hls") && source.readyState < 2) return

      this.decodeBusy = true

      try {
        const sourceWidth =
          mode === "image"
            ? (source.naturalWidth || source.width)
            : (source.videoWidth || source.clientWidth)
        const sourceHeight =
          mode === "image"
            ? (source.naturalHeight || source.height)
            : (source.videoHeight || source.clientHeight)

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
        ctx.drawImage(source, 0, 0, targetWidth, targetHeight)

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
      } catch (error) {
        console.warn("Decode frame error:", error)
        this.verifyMessage =
          "Không đọc được frame từ camera. Kiểm tra Preview URL, CORS hoặc cấu hình go2rtc."
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
  max-width: 1280px;
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

.source-panel {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.source-field {
  flex: 1 1 320px;
}

.source-field label,
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}

.source-hint {
  margin-bottom: 14px;
  color: #5c6f82;
  font-size: 0.92rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.form-group {
  margin-bottom: 14px;
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
  color: #fff;
}

.btn-primary {
  background: #2563eb;
}

.btn-danger {
  background: #dc2626;
}

.btn-reset {
  background: #111827;
}

.btn-config {
  background: #0f7c82;
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
  background: #0f172a;
  aspect-ratio: 16 / 9;
  object-fit: contain;
}

.preview-placeholder {
  color: #6b7280;
  font-weight: 600;
  padding: 24px;
  text-align: center;
}

.preview-note {
  color: #92400e;
}

.hidden-canvas {
  display: none;
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
  margin-top: 6px;
}

@media (max-width: 1024px) {
  .scanner-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .form-row,
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
