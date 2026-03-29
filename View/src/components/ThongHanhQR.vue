<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h1>V-Shield Gate Monitor</h1>
        <p>2 làn - QR + Biển số - dùng employeeId từ QR để gọi API thông hành cũ</p>
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
            :disabled="lane.loading || !lane.qr.cameraIp.trim() || !lane.plate.cameraIp.trim()"
            @click="readAllLane(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : laneAnyRunning(lane) ? "Đọc lại cả 2" : "Đọc cả 2" }}
          </button>

          <button
            class="btn btn-sub"
            :disabled="lane.loading || !lane.qr.cameraIp.trim()"
            @click="retryQr(lane)"
          >
            {{ lane.loading ? "Đang xử lý..." : "Đọc lại QR" }}
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
            :disabled="lane.loading || !lane.qr.employeeId || !lane.plate.confirmedPlate"
            @click="confirmLane(lane)"
          >
            Xác nhận
          </button>
        </div>

        <div class="ip-row">
          <div class="ip-box">
            <label>QR Camera URL</label>
            <div class="search-box">
  <input
    v-model="cameraSearch[lane.id + '-qr']"
    placeholder="Tìm camera QR..."
    :disabled="lane.loading"
  />

  <div class="dropdown" v-if="cameraSearch[lane.id + '-qr']">
    <div
      v-for="cam in filterCameras(cameraSearch[lane.id + '-qr'])"
      :key="cam.cameraId"
      @click="selectCamera(cam, lane, 'qr')"
      class="dropdown-item"
    >
      {{ cam.cameraName }} (ID: {{ cam.cameraId }})
    </div>
  </div>
</div>
          </div>

          <div class="ip-box">
            <label>Plate Camera URL</label>
            <div class="search-box">
  <input
    v-model="cameraSearch[lane.id + '-plate']"
    placeholder="Tìm camera Plate..."
    :disabled="lane.loading"
  />

  <div class="dropdown" v-if="cameraSearch[lane.id + '-plate']">
    <div
      v-for="cam in filterCameras(cameraSearch[lane.id + '-plate'])"
      :key="cam.cameraId"
      @click="selectCamera(cam, lane, 'plate')"
      class="dropdown-item"
    >
      {{ cam.cameraName }} (ID: {{ cam.cameraId }})
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
            <span class="label">Biển số</span>
            <span class="value strong plate">{{ lane.plate.confirmedPlate || "-----" }}</span>
          </div>

          <div class="summary-item">
            <span class="label">Cảnh báo</span>
            <span class="value" :class="lane.qr.alert ? 'danger-text' : 'ok-text'">
              {{ lane.qr.alert ? "MÃ KHÔNG HỢP LỆ" : "BÌNH THƯỜNG" }}
            </span>
          </div>
        </div>

        <div class="camera-stack">
          <!-- QR -->
          <div class="cam-block">
            <div class="cam-head">
              <span>QR Camera</span>
              <span class="mini-status" :class="lane.qr.previewHealthy ? 'ok' : 'wait'">
                {{ lane.qr.previewRunning ? (lane.qr.previewHealthy ? "Preview OK" : "Preview...") : "Preview OFF" }}
              </span>
            </div>

            <div class="cam-preview">
              <iframe
  v-if="lane.qr.previewRunning && lane.qr.directCameraUrl"
  :key="lane.qr.directCameraKey"
  :src="lane.qr.directCameraUrl"
  class="preview-image"
  style="border: none;"
></iframe>
              <div v-else class="cam-off">QR Offline</div>
              <canvas :ref="el => setQrCanvasRef(lane.id, el)" style="display:none;"></canvas>
            </div>

            <div class="quick-result">
              <div class="result-pill" :class="lane.qr.cameraRunning ? 'ok' : 'off'">
                {{ lane.qr.cameraRunning ? "RUNNING" : "STOPPED" }}
              </div>
              <div class="result-pill" :class="lane.qr.sessionLocked ? 'ok' : 'wait'">
                {{ lane.qr.sessionLocked ? "LOCKED" : "SCANNING" }}
              </div>
              <div class="result-pill" :class="lane.qr.alert ? 'danger' : 'neutral'">
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
              <span>Plate Camera</span>
              <span class="mini-status" :class="lane.plate.previewHealthy ? 'ok' : 'wait'">
                {{ lane.plate.previewRunning ? (lane.plate.previewHealthy ? "Preview OK" : "Preview...") : "Preview OFF" }}
              </span>
            </div>

            <div class="cam-preview">
              <iframe
  v-if="lane.plate.previewRunning && lane.plate.directCameraUrl"
  :key="lane.plate.directCameraKey"
  :src="lane.plate.directCameraUrl"
  class="preview-image"
  style="border: none;"
></iframe>
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
import { scanGate } from "../services/thonghanhAPI"
import { verifyDynamicQr } from "../services/dynamicQrVerifyApi"
import { getCameras } from "../services/setcamAPI"
import { startQr, resetQr, stopQr, getQrResult, scanQr } from "../services/qr_dAPI"
function createQrModule(defaultScannerDevice) {
  return {
    cameraIp: "",
    currentIp: "",
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
    sessionTimer: null,
    destroyed: false,

    previewIntervalMs: 350,
    absenceThresholdMs: 1500,
    decodeMaxWidth: 640,

    frameWidth: 0,
    frameHeight: 0,

    alert: false,
    sessionLocked: false
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
    viewUrl: "", // 🔥 thêm dòng này
    previewHealthy: false,

    resultTimer: null,
    busyResult: false,
    isFetchingLockedImages: false,
    destroyed: false
  }
}

export default {
  name: "VShieldGateMinimalQr",

  data() {
    return {
      qrCanvasRefs: {},
      cameras: [],
  cameraSearch: {},
      lanes: [
        {
          id: "lane1",
          name: "Làn 1",
          desc: "QR trên / Biển dưới",
          loading: false,
          plateApi: plateLane1Api,
          qr: createQrModule("WEB_SCANNER_GATE_01"),
          plate: createPlateModule()
        },
        {
          id: "lane2",
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
  await this.loadCameraList() // 🔥 THÊM

  for (const lane of this.lanes) {
    lane.qr.destroyed = false
    lane.plate.destroyed = false
    await this.loadStatusPlate(lane)
    if (lane.plate.cameraRunning) this.startPlateLoop(lane)
  }
},

  beforeUnmount() {
    for (const lane of this.lanes) {
      lane.qr.destroyed = true
      lane.plate.destroyed = true

      this.stopQrLoops(lane)
      this.stopPlateLoop(lane)

      this.resetPreview(lane.qr)
      this.resetPreview(lane.plate)
    }
  },

  activated() {
    for (const lane of this.lanes) {
      lane.qr.destroyed = false
      lane.plate.destroyed = false

      if (lane.qr.cameraRunning) {
        if (lane.qr.viewUrl && !lane.qr.previewRunning) {
  this.mountPreview(lane.qr, lane.qr.viewUrl)
}
        this.startQrPreviewLoop(lane)
        this.startQrSessionLoop(lane)
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
    for (const lane of this.lanes) {
      this.stopQrLoops(lane)
      this.stopPlateLoop(lane)
    }
  },

  methods: {
    setQrCanvasRef(laneId, el) {
      if (el) this.qrCanvasRefs[laneId] = el
    },

    startQrPolling(lane) {
  if (lane.qr.resultTimer) return

  lane.qr.resultTimer = setInterval(async () => {
    if (!lane.qr.cameraRunning) return

    const res = await getQrResult()

    if (!res) return

    // trạng thái
    lane.qr.sessionLocked = res.locked

    if (res.locked && res.qr) {
  lane.qr.qrPayload = res.qr
  lane.qr.sessionLocked = true

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
  return String(inputUrl || "").trim()
},

    mountPreview(module, url) {
      const cleanUrl = String(url || "").trim()
      if (!cleanUrl) return
      module.directCameraUrl = this.buildDirectCameraUrl(cleanUrl)
      module.directCameraKey += 1
      module.previewHealthy = false
      module.previewRunning = true
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
        this.refreshDirectPreview(lane.qr)
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
      const img = this.$el.querySelector(`[alt="QR Preview"]`)
      const canvas = this.qrCanvasRefs[lane.id]

      if (!img || !canvas) return
      if (!img.complete) return
      if (qr.decodeBusy) return

      qr.decodeBusy = true

      try {
        const sourceWidth = img.naturalWidth || img.width
        const sourceHeight = img.naturalHeight || img.height
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
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight)

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
      plate.confirmedPlate = res.confirmed_plate || ""
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
        this.resetPreview(lane.qr)

        // 🔥 STEP 2: chờ camera release
        await new Promise(r => setTimeout(r, 300))
      }

      // 🔥 STEP 3: mở lại
      this.mountPreview(lane.qr, lane.qr.viewUrl)
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

await new Promise(r => setTimeout(r, 200))

// 🧠 nếu chưa chạy → start
if (!lane.qr.cameraRunning) {
  await startQr(lane.qr.cameraIp)
  await new Promise(r => setTimeout(r, 800))
}

// scan mới
await scanQr()

// 🔥 reset frontend state
this.clearQrState(lane.qr)

lane.qr.cameraRunning = true
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

      // ⏳ chờ cam mở
      await new Promise(r => setTimeout(r, 800))
    }

    // reset state
    await resetQr()

    await new Promise(r => setTimeout(r, 200))

    // scan lại
    await scanQr()

    this.clearQrState(lane.qr)

    lane.qr.cameraRunning = true
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
    await stopQr()

    // 🔥 2. dừng polling QR
    if (lane.qr.resultTimer) {
      clearInterval(lane.qr.resultTimer)
      lane.qr.resultTimer = null
    }

    // 🔥 3. reset QR frontend
    this.stopQrLoops(lane)
    this.hardResetQr(lane.qr)
    this.resetPreview(lane.qr)

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
        const payload = {
          employeeId,
          licensePlate
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
    },

    // ================= CAMERA SEARCH =================

async loadCameraList() {
  try {
    const res = await getCameras()
    this.cameras = res || []
  } catch (e) {
    console.error("loadCameraList error:", e)
  }
},

filterCameras(keyword) {
  if (!keyword) return this.cameras

  const key = keyword.toLowerCase()

  return this.cameras.filter(c =>
    String(c.cameraName || "").toLowerCase().includes(key) ||
    String(c.cameraId).includes(key)
  )
},

selectCamera(cam, lane, type) {
  if (!cam.urlView) {
    alert("Camera chưa có UrlView. Hãy reload go2rtc trước")
    return
  }

  if (type === "qr") {
    lane.qr.cameraIp = cam.streamUrl
    lane.qr.viewUrl = cam.urlView   // 🔥 thêm
    lane.qr.currentIp = cam.urlView

    this.cameraSearch[lane.id + '-qr'] = cam.cameraName
    this.mountPreview(lane.qr, cam.urlView)
  }

  if (type === "plate") {
    lane.plate.cameraIp = cam.streamUrl
    lane.plate.viewUrl = cam.urlView
    lane.plate.currentIp = cam.streamUrl

    this.cameraSearch[lane.id + '-plate'] = cam.cameraName
    this.mountPreview(lane.plate, cam.urlView)
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
  position: relative;
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

.qr-data-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.qr-data-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.small-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 700;
}

.small-value {
  font-size: 13px;
  color: #0f172a;
  font-weight: 700;
  word-break: break-word;
}

.verify-box {
  margin-top: 10px;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.verify-message {
  margin-bottom: 8px;
  font-weight: 700;
}

.verify-data > div {
  margin-bottom: 4px;
  font-size: 13px;
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
  .evidence-row,
  .qr-data-grid {
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
.search-box {
  position: relative;
}

.dropdown {
  position: absolute;
  background: white;
  border: 1px solid #ccc;
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  z-index: 9999;
}

.dropdown-item {
  padding: 8px;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #eee;
}
</style>