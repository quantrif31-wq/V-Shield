<template>
  <div class="page-container animate-in">
    <header class="page-header">
      <div>
        <h1 class="page-title">Cài đặt Hệ thống</h1>
        <p class="page-subtitle">
          Quản lý camera tại đây, còn trang Giám sát chỉ hiển thị camera đã cấu hình.
        </p>
      </div>
      <button class="save-btn" @click="saveSettings">Lưu cài đặt</button>
    </header>

    <div class="settings-layout">
      <aside class="settings-nav bento-card">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="settings-tab"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </aside>

      <section class="settings-content">
        <div v-if="activeTab === 'general'" class="bento-card section-card">
          <h2 class="section-title">Cài đặt chung</h2>
          <div class="form-grid">
            <div class="input-group">
              <label>Tên cơ sở / công ty</label>
              <input v-model="settings.companyName" class="field" type="text" />
            </div>
            <div class="two-col">
              <div class="input-group">
                <label>Giờ mở cổng</label>
                <input v-model="settings.openTime" class="field" type="time" />
              </div>
              <div class="input-group">
                <label>Giờ đóng cổng</label>
                <input v-model="settings.closeTime" class="field" type="time" />
              </div>
            </div>
            <div class="two-col">
              <div class="input-group">
                <label>Ngôn ngữ</label>
                <select v-model="settings.language" class="field">
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div class="input-group">
                <label>Múi giờ</label>
                <select v-model="settings.timezone" class="field">
                  <option value="UTC+7">UTC+7</option>
                  <option value="UTC+8">UTC+8</option>
                  <option value="UTC+9">UTC+9</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'camera'" class="camera-panel">
          <div class="bento-card section-card">
            <div class="section-head">
              <div>
                <h2 class="section-title">Mạng lưới Camera</h2>
                <p class="muted">
                  Nạp camera điện thoại hoặc camera LAN vào mạng lưới, sau đó xem tại trang Giám sát.
                </p>
              </div>
              <router-link to="/monitoring" class="link-btn">Mở trang Giám sát</router-link>
            </div>

            <div class="toolbar-grid">
              <input v-model="manualCameraName" class="field" placeholder="Tên hiển thị, ví dụ: iPhone cổng phụ" />
              <input v-model="manualCameraUrl" class="field" placeholder="http://IP:8081/video" />
              <select v-model="manualTargetId" class="field">
                <option value="auto">Nạp vào: Tự động</option>
                <option v-for="camera in cameraSettings" :key="camera.id" :value="String(camera.id)">
                  {{ camera.name }}
                </option>
              </select>
              <button class="ghost-btn" :disabled="discoveryLoading" @click="discoverLanCameras">
                {{ discoveryLoading ? "Đang quét camera LAN..." : "Tự tìm camera LAN" }}
              </button>
              <button class="primary-btn" :disabled="connectLoading" @click="applyManualCamera">
                {{ connectLoading ? "Đang nạp..." : "Nạp vào mạng lưới" }}
              </button>
              <button class="secondary-btn" :disabled="connectLoading || !discoveredCameras.length" @click="applyAllDiscoveredCameras">
                {{ connectLoading ? "Đang nạp..." : "Nạp tất cả" }}
              </button>
            </div>

            <p class="muted inline-note">
              iPhone IP Camera Lite nên dùng <code>http://IP:8081/video</code>. Nếu bạn chỉ nhập <code>IP:8081</code>, hệ thống sẽ tự bổ sung.
            </p>
            <p v-if="discoveryMessage" class="message success">{{ discoveryMessage }}</p>
            <p v-if="discoveryError" class="message danger">{{ discoveryError }}</p>
            <p v-if="connectMessage" class="message success">{{ connectMessage }}</p>
            <p v-if="connectError" class="message danger">{{ connectError }}</p>

            <div v-if="discoveredCameras.length" class="discovery-list">
              <div v-for="camera in discoveredCameras" :key="`${camera.ipAddress}:${camera.port}`" class="discovery-card">
                <div>
                  <strong>{{ camera.name }}</strong>
                  <p class="muted small">{{ camera.ipAddress }}:{{ camera.port }}</p>
                  <p class="small">URL chính: {{ getPreferredConnectUrl(camera) || "Chưa có" }}</p>
                </div>
                <div class="discovery-actions">
                  <select v-model="discoveredTargetIds[getCameraKey(camera)]" class="field mini-field">
                    <option value="auto">Tự động</option>
                    <option v-for="item in cameraSettings" :key="item.id" :value="String(item.id)">
                      {{ item.name }}
                    </option>
                  </select>
                  <button class="primary-btn small-btn" @click="applyDiscoveredCamera(camera)">Nạp vào camera</button>
                </div>
              </div>
            </div>
          </div>

          <div class="camera-grid">
            <article v-for="camera in cameraSettings" :key="camera.id" class="bento-card camera-card">
              <div class="camera-card-head">
                <div>
                  <h3>{{ camera.name }}</h3>
                  <p class="muted">{{ camera.label || "Chưa đặt tên hiển thị" }}</p>
                </div>
                <label class="toggle">
                  <input v-model="camera.enabled" type="checkbox" @change="handleCameraToggle(camera)" />
                  <span></span>
                </label>
              </div>

              <div class="status-line">
                <span class="status-pill" :class="getCameraStatusClass(camera)">
                  {{ getCameraStatusText(camera) }}
                </span>
              </div>

              <div class="form-grid">
                <div class="input-group">
                  <label>Tên hiển thị trên Giám sát</label>
                  <input v-model="camera.label" class="field" type="text" placeholder="Ví dụ: iPhone cổng phụ" @blur="persistCameraSettingsOnly" />
                </div>
                <div class="input-group">
                  <label>URL stream</label>
                  <input v-model="camera.url" class="field mono" type="text" placeholder="http://IP:8081/video" @blur="normalizeCameraCardUrl(camera.id)" />
                  <small class="muted">Web ưu tiên MJPEG/HTTP để xem trực tiếp. RTSP vẫn lưu được nhưng sẽ cần gateway để hiển thị.</small>
                </div>
                <div class="input-group">
                  <label>Vị trí lắp đặt</label>
                  <input v-model="camera.location" class="field" type="text" @blur="persistCameraSettingsOnly" />
                </div>
              </div>

              <div class="camera-card-actions">
                <button class="ghost-btn small-btn" :disabled="checkingIds.includes(camera.id)" @click="refreshSingleCameraStatus(camera.id)">
                  {{ checkingIds.includes(camera.id) ? "Đang kiểm tra..." : "Kiểm tra lại" }}
                </button>
                <button class="danger-btn small-btn" @click="clearCamera(camera.id)">Xóa camera</button>
              </div>
            </article>
          </div>
        </div>

        <div v-else-if="activeTab === 'recognition'" class="bento-card section-card">
          <h2 class="section-title">Hệ thống AI</h2>
          <div class="toggle-list">
            <label class="toggle-row"><span>Bật Face ID</span><input v-model="recognitionSettings.faceEnabled" type="checkbox" /></label>
            <label class="toggle-row"><span>Chống giả mạo hình ảnh</span><input v-model="recognitionSettings.antiSpoofing" type="checkbox" /></label>
            <label class="toggle-row"><span>Bật LPR</span><input v-model="recognitionSettings.plateEnabled" type="checkbox" /></label>
            <div class="input-group">
              <label>Ngưỡng khuôn mặt: {{ recognitionSettings.faceThreshold }}%</label>
              <input v-model.number="recognitionSettings.faceThreshold" type="range" min="50" max="100" />
            </div>
            <div class="input-group">
              <label>Ngưỡng biển số: {{ recognitionSettings.plateThreshold }}%</label>
              <input v-model.number="recognitionSettings.plateThreshold" type="range" min="50" max="100" />
            </div>
          </div>
        </div>

        <div v-else class="bento-card section-card">
          <h2 class="section-title">Cảnh báo tự động</h2>
          <div class="toggle-list">
            <label class="toggle-row"><span>Cảnh báo người lạ</span><input v-model="notifSettings.strangerAlert" type="checkbox" /></label>
            <label class="toggle-row"><span>Phương tiện chưa đăng ký</span><input v-model="notifSettings.unregisteredVehicle" type="checkbox" /></label>
            <label class="toggle-row"><span>Camera mất kết nối</span><input v-model="notifSettings.cameraOffline" type="checkbox" /></label>
            <label class="toggle-row"><span>Hoạt động ngoài giờ</span><input v-model="notifSettings.afterHours" type="checkbox" /></label>
          </div>
        </div>
      </section>
    </div>

    <transition name="toast-slide">
      <div v-if="toast" class="toast">{{ toast.message }}</div>
    </transition>
  </div>
</template>

<script setup>
import axios from "axios"
import { onMounted, onUnmounted, reactive, ref } from "vue"
import {
  createDefaultCameraSettings,
  loadCameraNetworkSettings,
  saveCameraNetworkSettings,
} from "../utils/cameraNetwork"

const SYSTEM_SETTINGS_STORAGE_KEY = "vshield-system-settings-v1"
const DISCOVERY_API_BASE = "https://localhost:7107/api/FaceID"
const CAMERA_PROBE_TIMEOUT_MS = 3500

const activeTab = ref("general")
const tabs = [
  { id: "general", label: "Cài đặt chung" },
  { id: "camera", label: "Mạng lưới Camera" },
  { id: "recognition", label: "Hệ thống AI" },
  { id: "notifications", label: "Cảnh báo tự động" },
]

const settings = reactive({
  companyName: "V-Shield Security Group",
  openTime: "06:00",
  closeTime: "22:00",
  language: "vi",
  timezone: "UTC+7",
})

const recognitionSettings = reactive({
  faceEnabled: true,
  faceThreshold: 88,
  antiSpoofing: true,
  plateEnabled: true,
  plateThreshold: 85,
})

const notifSettings = reactive({
  strangerAlert: true,
  unregisteredVehicle: true,
  cameraOffline: true,
  afterHours: false,
})

const cameraSettings = ref(createDefaultCameraSettings())
const manualCameraName = ref("")
const manualCameraUrl = ref("")
const manualTargetId = ref("auto")
const discoveredCameras = ref([])
const discoveredTargetIds = ref({})
const discoveryLoading = ref(false)
const connectLoading = ref(false)
const discoveryMessage = ref("")
const discoveryError = ref("")
const connectMessage = ref("")
const connectError = ref("")
const checkingIds = ref([])
const toast = ref(null)

let toastTimer = null

const showToast = (message) => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { message }
  toastTimer = setTimeout(() => {
    toast.value = null
  }, 3500)
}

const loadSystemSettings = () => {
  cameraSettings.value = loadCameraNetworkSettings()
  const rawValue = localStorage.getItem(SYSTEM_SETTINGS_STORAGE_KEY)
  if (!rawValue) return

  try {
    const parsed = JSON.parse(rawValue)
    Object.assign(settings, parsed.settings || {})
    Object.assign(recognitionSettings, parsed.recognitionSettings || {})
    Object.assign(notifSettings, parsed.notifSettings || {})
  } catch {
    // Giữ giá trị mặc định.
  }
}

const persistSystemSettings = () => {
  localStorage.setItem(
    SYSTEM_SETTINGS_STORAGE_KEY,
    JSON.stringify({
      settings: { ...settings },
      recognitionSettings: { ...recognitionSettings },
      notifSettings: { ...notifSettings },
    })
  )
}

const persistCameraSettingsOnly = () => {
  cameraSettings.value = saveCameraNetworkSettings(cameraSettings.value)
}

const isHttpCameraUrl = (url) => /^https?:\/\//i.test(url || "")
const isRtspCameraUrl = (url) => /^rtsp:\/\//i.test(url || "")
const looksLikeHostInput = (value) =>
  /^[\w.-]+(?::\d+)?(?:\/.*)?$/i.test((value || "").trim())

const normalizeCameraUrl = (rawValue) => {
  let value = (rawValue || "").trim()
  if (!value) return ""

  value = value.replace(/^\/+/, "")
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(value) && looksLikeHostInput(value)) {
    value = `http://${value}`
  }

  try {
    const parsedUrl = new URL(value)
    if (
      (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") &&
      (!parsedUrl.pathname || parsedUrl.pathname === "/")
    ) {
      if (parsedUrl.port === "8081") {
        parsedUrl.pathname = "/video"
      } else if (parsedUrl.port === "8080") {
        parsedUrl.pathname = "/videofeed"
      }
    }

    return parsedUrl.toString()
  } catch {
    return (rawValue || "").trim()
  }
}

const probeHttpCameraUrl = async (url, timeoutMs = CAMERA_PROBE_TIMEOUT_MS) => {
  if (!url) {
    return false
  }

  const controller = new AbortController()
  const timerId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    await fetch(`${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`, {
      method: "GET",
      mode: "no-cors",
      cache: "no-store",
      signal: controller.signal,
    })
    return true
  } catch {
    return false
  } finally {
    clearTimeout(timerId)
  }
}

const markChecking = (cameraId, value) => {
  if (value && !checkingIds.value.includes(cameraId)) {
    checkingIds.value = [...checkingIds.value, cameraId]
    return
  }
  if (!value) {
    checkingIds.value = checkingIds.value.filter((id) => id !== cameraId)
  }
}

const refreshSingleCameraStatus = async (cameraId) => {
  const camera = cameraSettings.value.find((item) => item.id === cameraId)
  if (!camera) return

  markChecking(cameraId, true)
  try {
    if (!camera.url || !camera.enabled) {
      camera.online = false
    } else if (isHttpCameraUrl(camera.url)) {
      camera.online = await probeHttpCameraUrl(camera.url)
    } else {
      camera.online = true
    }
    persistCameraSettingsOnly()
  } finally {
    markChecking(cameraId, false)
  }
}

const refreshAllCameraStatuses = async () => {
  for (const camera of cameraSettings.value) {
    await refreshSingleCameraStatus(camera.id)
  }
}

const getCameraStatusText = (camera) => {
  if (!camera.url) return "Chưa gắn"
  if (!camera.enabled) return "Đã tắt"
  if (checkingIds.value.includes(camera.id)) return "Đang kiểm tra"
  if (isRtspCameraUrl(camera.url)) return "RTSP"
  return camera.online ? "Trực tuyến" : "Ngoại tuyến"
}

const getCameraStatusClass = (camera) => {
  if (!camera.url || !camera.enabled) return "neutral"
  if (checkingIds.value.includes(camera.id)) return "info"
  if (isRtspCameraUrl(camera.url)) return "info"
  return camera.online ? "success" : "danger"
}

const clearDiscoveryState = () => {
  discoveryMessage.value = ""
  discoveryError.value = ""
}

const clearConnectState = () => {
  connectMessage.value = ""
  connectError.value = ""
}

const getCameraKey = (camera) => `${camera.ipAddress}:${camera.port}`
const getPreferredConnectUrl = (camera) =>
  camera?.previewUrl || camera?.rtspUrls?.[0] || camera?.baseUrl || ""

const guessCameraLabel = (url) => {
  try {
    return `Camera ${new URL(url).hostname}`
  } catch {
    return "Camera LAN"
  }
}

const resolveTargetCameraId = (preferredId = "auto", preferredUrl = "") => {
  if (preferredId !== "auto") return Number(preferredId)

  const existing = cameraSettings.value.find((camera) => camera.url === preferredUrl)
  if (existing) return existing.id

  const empty = cameraSettings.value.find((camera) => !camera.url)
  if (empty) return empty.id

  const disabled = cameraSettings.value.find((camera) => !camera.enabled)
  if (disabled) return disabled.id

  return null
}

const applyCameraToNetwork = async (payload, preferredId = "auto") => {
  const normalizedUrl = normalizeCameraUrl(payload.url)
  if (!normalizedUrl) {
    return { ok: false, error: "Hãy nhập URL camera hợp lệ trước khi nạp." }
  }

  const targetId = resolveTargetCameraId(preferredId, normalizedUrl)
  if (!targetId) {
    return {
      ok: false,
      error: "Mạng lưới camera đã đầy. Hãy chọn một ô cụ thể hoặc xóa bớt camera cũ.",
    }
  }

  const index = cameraSettings.value.findIndex((camera) => camera.id === targetId)
  if (index < 0) {
    return { ok: false, error: "Không tìm thấy ô camera phù hợp." }
  }

  const current = cameraSettings.value[index]
  cameraSettings.value[index] = {
    ...current,
    label: payload.label?.trim() || current.label || guessCameraLabel(normalizedUrl),
    url: normalizedUrl,
    enabled: true,
    online: false,
    location: payload.location?.trim() || current.location,
    recognitionType: payload.recognitionType || current.recognitionType,
    resolution: payload.resolution || current.resolution,
  }

  persistCameraSettingsOnly()
  await refreshSingleCameraStatus(targetId)

  return {
    ok: true,
    camera: cameraSettings.value[index],
    message: `Đã nạp ${cameraSettings.value[index].label} vào ${cameraSettings.value[index].name}.`,
  }
}

const applyManualCamera = async () => {
  clearConnectState()
  connectLoading.value = true
  try {
    const result = await applyCameraToNetwork(
      { label: manualCameraName.value, url: manualCameraUrl.value },
      manualTargetId.value
    )

    if (!result.ok) {
      connectError.value = result.error
      return
    }

    manualCameraUrl.value = normalizeCameraUrl(manualCameraUrl.value)
    connectMessage.value = result.message
  } finally {
    connectLoading.value = false
  }
}

const discoverLanCameras = async () => {
  discoveryLoading.value = true
  clearDiscoveryState()
  try {
    const { data } = await axios.get(`${DISCOVERY_API_BASE}/discover-ipwebcam`)
    discoveredCameras.value = Array.isArray(data?.cameras) ? data.cameras : []

    const nextSelections = { ...discoveredTargetIds.value }
    for (const camera of discoveredCameras.value) {
      const key = getCameraKey(camera)
      if (!nextSelections[key]) nextSelections[key] = "auto"
    }
    discoveredTargetIds.value = nextSelections

    if (!discoveredCameras.value.length) {
      discoveryError.value = "Chưa tìm thấy camera LAN phù hợp trong cùng mạng."
      return
    }

    discoveryMessage.value = `Tìm thấy ${discoveredCameras.value.length} thiết bị camera LAN.`
  } catch (error) {
    discoveryError.value =
      error?.response?.data?.message || error?.message || "Quét camera LAN thất bại."
  } finally {
    discoveryLoading.value = false
  }
}

const applyDiscoveredCamera = async (camera) => {
  clearConnectState()
  connectLoading.value = true
  try {
    const connectUrl = getPreferredConnectUrl(camera)
    if (!connectUrl) {
      connectError.value = `Thiết bị ${camera.name} chưa có URL phù hợp để nạp.`
      return
    }

    const result = await applyCameraToNetwork(
      { label: camera.name, url: connectUrl },
      discoveredTargetIds.value[getCameraKey(camera)] || "auto"
    )

    if (!result.ok) {
      connectError.value = result.error
      return
    }

    connectMessage.value = result.message
  } finally {
    connectLoading.value = false
  }
}

const applyAllDiscoveredCameras = async () => {
  clearConnectState()
  if (!discoveredCameras.value.length) {
    connectError.value = "Hãy quét camera LAN trước khi nạp toàn bộ."
    return
  }

  connectLoading.value = true
  try {
    const assigned = []
    const skipped = []

    for (const camera of discoveredCameras.value) {
      const connectUrl = getPreferredConnectUrl(camera)
      if (!connectUrl) {
        skipped.push(camera.name || `${camera.ipAddress}:${camera.port}`)
        continue
      }

      const result = await applyCameraToNetwork(
        { label: camera.name, url: connectUrl },
        discoveredTargetIds.value[getCameraKey(camera)] || "auto"
      )

      if (!result.ok) {
        skipped.push(camera.name || `${camera.ipAddress}:${camera.port}`)
        continue
      }

      assigned.push(result.camera.name)
    }

    if (!assigned.length) {
      connectError.value = "Không thể nạp camera nào vào mạng lưới."
      return
    }

    connectMessage.value = `Đã nạp ${assigned.length} camera vào ${assigned.join(", ")}${
      skipped.length ? `. Bỏ qua ${skipped.length} thiết bị.` : "."
    }`
  } finally {
    connectLoading.value = false
  }
}

const normalizeCameraCardUrl = async (cameraId) => {
  const camera = cameraSettings.value.find((item) => item.id === cameraId)
  if (!camera) return

  camera.url = normalizeCameraUrl(camera.url)
  if (!camera.url) {
    camera.enabled = false
    camera.online = false
    persistCameraSettingsOnly()
    return
  }

  persistCameraSettingsOnly()
  await refreshSingleCameraStatus(cameraId)
}

const handleCameraToggle = async (camera) => {
  clearConnectState()
  if (!camera.url && camera.enabled) {
    camera.enabled = false
    connectError.value = `Hãy nhập URL trước khi bật ${camera.name}.`
    persistCameraSettingsOnly()
    return
  }

  if (!camera.enabled) {
    camera.online = false
    persistCameraSettingsOnly()
    return
  }

  persistCameraSettingsOnly()
  await refreshSingleCameraStatus(camera.id)
}

const clearCamera = (cameraId) => {
  const index = cameraSettings.value.findIndex((camera) => camera.id === cameraId)
  if (index < 0) return

  const current = cameraSettings.value[index]
  cameraSettings.value[index] = {
    ...current,
    url: "",
    enabled: false,
    online: false,
  }

  persistCameraSettingsOnly()
  clearConnectState()
  connectMessage.value = `Đã xóa cấu hình khỏi ${current.name}.`
}

const saveSettings = async () => {
  clearDiscoveryState()
  clearConnectState()
  persistSystemSettings()
  persistCameraSettingsOnly()
  await refreshAllCameraStatuses()
  showToast("Đã lưu cấu hình hệ thống thành công.")
}

onMounted(async () => {
  loadSystemSettings()
  await refreshAllCameraStatuses()
})

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.save-btn,
.primary-btn,
.secondary-btn,
.ghost-btn,
.danger-btn,
.link-btn {
  border-radius: 12px;
  font-weight: 700;
  transition: transform 0.2s ease, opacity 0.2s ease, background 0.2s ease;
}

.save-btn:hover,
.primary-btn:hover,
.secondary-btn:hover,
.ghost-btn:hover,
.danger-btn:hover,
.link-btn:hover {
  transform: translateY(-1px);
}

.save-btn,
.primary-btn {
  padding: 12px 16px;
  border: none;
  background: var(--accent-primary);
  color: #fff;
  cursor: pointer;
}

.secondary-btn {
  padding: 12px 16px;
  border: none;
  background: linear-gradient(135deg, #0f766e, #0ea5a4);
  color: #fff;
  cursor: pointer;
}

.ghost-btn {
  padding: 12px 16px;
  border: 1px dashed var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.danger-btn {
  padding: 12px 16px;
  border: 1px solid rgba(239, 68, 68, 0.28);
  background: rgba(239, 68, 68, 0.08);
  color: var(--accent-danger);
  cursor: pointer;
}

.small-btn {
  padding: 9px 12px;
  font-size: 0.84rem;
}

.primary-btn:disabled,
.secondary-btn:disabled,
.ghost-btn:disabled,
.danger-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  text-decoration: none;
  border: 1px solid rgba(16, 121, 196, 0.2);
  background: rgba(16, 121, 196, 0.08);
  color: var(--accent-primary);
}

.settings-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  align-items: start;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: sticky;
  top: calc(var(--header-height) + 24px);
}

.settings-tab {
  text-align: left;
  padding: 12px 14px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--text-secondary);
  font-weight: 600;
  cursor: pointer;
}

.settings-tab.active {
  background: rgba(16, 121, 196, 0.12);
  color: var(--accent-primary);
  box-shadow: inset 3px 0 0 var(--accent-primary);
}

.section-card,
.camera-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.section-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
}

.muted {
  color: var(--text-secondary);
}

.small {
  font-size: 0.84rem;
}

.inline-note {
  font-size: 0.9rem;
}

.inline-note code {
  font-family: "JetBrains Mono", monospace;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.06);
}

.toolbar-grid,
.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.toolbar-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
}

.field {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-input);
  color: var(--text-primary);
  outline: none;
}

.field:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15);
}

.mono {
  font-family: "JetBrains Mono", monospace;
}

.mini-field {
  min-width: 130px;
  padding: 9px 12px;
  font-size: 0.84rem;
}

.message {
  margin: 0;
  font-size: 0.9rem;
}

.message.success {
  color: var(--accent-success);
}

.message.danger {
  color: var(--accent-danger);
}

.discovery-list {
  display: grid;
  gap: 12px;
}

.discovery-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: var(--bg-input);
}

.discovery-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.camera-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.camera-card-head,
.camera-card-actions,
.toggle-row,
.status-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.camera-card-head h3 {
  margin: 0;
  font-size: 1.05rem;
  color: var(--text-primary);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  background: rgba(100, 116, 139, 0.08);
  color: #64748b;
}

.status-pill.success {
  background: rgba(16, 185, 129, 0.12);
  color: var(--accent-success);
}

.status-pill.danger {
  background: rgba(239, 68, 68, 0.12);
  color: var(--accent-danger);
}

.status-pill.info {
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
}

.status-pill.neutral {
  background: rgba(100, 116, 139, 0.08);
  color: #64748b;
}

.toggle {
  position: relative;
  width: 46px;
  height: 26px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle span {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.3);
  border: 1px solid var(--border-color);
}

.toggle span::before {
  content: "";
  position: absolute;
  left: 3px;
  top: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #94a3b8;
  transition: transform 0.2s ease;
}

.toggle input:checked + span {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

.toggle input:checked + span::before {
  transform: translateX(20px);
  background: #fff;
}

.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
  padding: 14px 18px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow: var(--shadow-xl);
  color: var(--text-primary);
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.25s ease;
}

.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

@media (max-width: 1024px) {
  .settings-layout,
  .camera-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header,
  .section-head,
  .discovery-card,
  .discovery-actions,
  .camera-card-actions,
  .camera-card-head {
    flex-direction: column;
    align-items: stretch;
  }

  .settings-nav {
    position: static;
  }

  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
