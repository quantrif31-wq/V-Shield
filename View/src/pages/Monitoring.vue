<template>
  <div class="page-container animate-in">
    <header class="page-header bento-header">
      <div class="greeting">
        <h1 class="page-title">Giám sát Camera</h1>
        <p class="page-subtitle">
          Trang này chỉ hiển thị camera đã cấu hình trong Cài đặt &gt; Mạng lưới Camera.
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/settings" class="manage-btn">Quản lý mạng lưới</router-link>
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>LIVE</span>
        </div>
        <select v-model="layoutMode" class="layout-select">
          <option value="2x2">Hiển thị: 2 x 2</option>
          <option value="3x2">Hiển thị: 3 x 2</option>
          <option value="1x1">Toàn màn hình</option>
        </select>
      </div>
    </header>

    <div class="bento-card info-card">
      <div>
        <strong>{{ configuredCameraCount }}</strong> camera đang được cấu hình trong mạng lưới.
        <span class="info-muted">
          4 ô camera luôn hiển thị sẵn. Muốn đổi URL hoặc thêm camera điện thoại, hãy vào phần Cài đặt.
        </span>
      </div>
      <router-link to="/settings" class="link-inline">Mở Cài đặt</router-link>
    </div>

    <Teleport to="body">
      <div
        v-if="selectedExpandedCamera"
        class="camera-fullscreen-shell"
        @contextmenu.prevent="toggleExpand(null)"
      >
        <div class="camera-modal-backdrop" @click="toggleExpand(null)"></div>

        <article class="camera-card expanded camera-card-teleport" @click.stop>
          <div class="camera-feed">
            <img
              v-if="canRenderLivePreview(selectedExpandedCamera)"
              :src="getCameraPreviewSrc(selectedExpandedCamera)"
              :alt="selectedExpandedCamera.sourceName || selectedExpandedCamera.slotName"
              class="camera-stream"
              @load="handlePreviewLoad(selectedExpandedCamera.id)"
              @error="handlePreviewError(selectedExpandedCamera.id)"
            />

            <div v-else class="camera-state" :class="getStateClass(selectedExpandedCamera)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
              <p>{{ getCameraPlaceholder(selectedExpandedCamera) }}</p>
            </div>

            <div class="camera-overlay">
              <div class="camera-top-bar">
                <div>
                  <div class="camera-name">{{ selectedExpandedCamera.slotName }}</div>
                  <div class="camera-source">{{ selectedExpandedCamera.sourceName || "Chưa gắn thiết bị" }}</div>
                  <div v-if="selectedExpandedCamera.url && selectedExpandedCamera.isRtsp" class="camera-meta">
                    <span class="camera-meta-chip rtsp">RTSP</span>
                  </div>
                </div>
                <div class="camera-actions">
                  <button class="camera-btn" @click.stop="toggleExpand(null)">
                    Quay lại
                  </button>
                  <span class="camera-status" :class="getStatusClass(selectedExpandedCamera)">
                    {{ getCameraStatusText(selectedExpandedCamera) }}
                  </span>
                </div>
              </div>

              <div class="camera-bottom-bar">
                <span>{{ selectedExpandedCamera.location }}</span>
                <span>{{ selectedExpandedCamera.enabled && selectedExpandedCamera.url ? currentTime : "--" }}</span>
              </div>
            </div>
          </div>
        </article>
      </div>
    </Teleport>

    <div class="camera-grid" :class="layoutMode">
      <article
        v-for="camera in cameras"
        :key="camera.id"
        class="bento-card camera-card"
        @dblclick="handleDoubleClick(camera.id)"
        @contextmenu.prevent="handleContextMenu(camera.id)"
      >
        <div class="camera-feed">
          <img
            v-if="canRenderLivePreview(camera)"
            :src="getCameraPreviewSrc(camera)"
            :alt="camera.sourceName || camera.slotName"
            class="camera-stream"
            @load="handlePreviewLoad(camera.id)"
            @error="handlePreviewError(camera.id)"
          />

          <div v-else class="camera-state" :class="getStateClass(camera)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <p>{{ getCameraPlaceholder(camera) }}</p>
          </div>

          <div class="camera-overlay">
              <div class="camera-top-bar">
                <div>
                  <div class="camera-name">{{ camera.slotName }}</div>
                  <div class="camera-source">{{ camera.sourceName || "Chưa gắn thiết bị" }}</div>
                  <div v-if="camera.url && camera.isRtsp" class="camera-meta">
                    <span v-if="camera.isRtsp" class="camera-meta-chip rtsp">RTSP</span>
                  </div>
                </div>
                <div class="camera-actions">
                  <button class="camera-btn" :disabled="!camera.enabled || !camera.url" @click.stop="toggleExpand(camera.id)">
                    {{ expandedCameraId === camera.id ? "Quay lại" : "Toàn màn hình" }}
                  </button>
                <span class="camera-status" :class="getStatusClass(camera)">
                  {{ getCameraStatusText(camera) }}
                </span>
              </div>
            </div>

            <div class="camera-bottom-bar">
              <span>{{ camera.location }}</span>
              <span>{{ camera.enabled && camera.url ? currentTime : "--" }}</span>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import {
  extractCameraDisplayParts,
  loadCameraNetworkSettings,
} from "../utils/cameraNetwork"

const MONITORING_PREFERENCES_KEY = "vshield-monitoring-preferences-v2"
const HEALTH_CHECK_INTERVAL_MS = 12000
const HEALTH_CHECK_TIMEOUT_MS = 4000

const layoutMode = ref(localStorage.getItem(MONITORING_PREFERENCES_KEY) || "2x2")
const currentTime = ref("")
const expandedCameraId = ref(null)
const cameras = ref([])

let timeTimer = null
let healthTimer = null
let isHealthCheckRunning = false

const syncImmersiveMode = (isActive) => {
  document.body.classList.toggle("monitoring-immersive", isActive)
}

const isHttpCameraUrl = (url) => /^https?:\/\//i.test(url || "")
const isRtspCameraUrl = (url) => /^rtsp:\/\//i.test(url || "")

const normalizePreviewUrl = (url) => {
  if (!isHttpCameraUrl(url)) return ""

  try {
    const parsedUrl = new URL(url)
    if (!parsedUrl.pathname || parsedUrl.pathname === "/") {
      if (parsedUrl.port === "8081") {
        parsedUrl.pathname = "/video"
      } else if (parsedUrl.port === "8080") {
        parsedUrl.pathname = "/videofeed"
      }
    }
    return parsedUrl.toString()
  } catch {
    return url || ""
  }
}

const rebuildCameras = () => {
  const previousState = new Map(cameras.value.map((camera) => [camera.id, camera]))
  const configuredCameras = loadCameraNetworkSettings()

  cameras.value = configuredCameras.map((camera, index) => {
    const previous = previousState.get(camera.id)
    const displayParts = extractCameraDisplayParts(camera, index + 1)
    return {
      id: camera.id,
      slotName: displayParts.slotName,
      sourceName: camera.label || displayParts.sourceName,
      location: camera.location,
      enabled: Boolean(camera.enabled && camera.url),
      url: camera.url || "",
      previewUrl: normalizePreviewUrl(camera.url),
      isRtsp: isRtspCameraUrl(camera.url),
      isOffline: previous?.isOffline ?? false,
      previewNonce: previous?.previewNonce || Date.now(),
    }
  })
}

const configuredCameraCount = computed(
  () => cameras.value.filter((camera) => camera.enabled && camera.url).length
)

const selectedExpandedCamera = computed(
  () => cameras.value.find((camera) => camera.id === expandedCameraId.value) || null
)

const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString("vi-VN")
}

const getCameraStatusText = (camera) => {
  if (!camera.url) return "TRỐNG"
  if (!camera.enabled) return "TẮT"
  if (camera.isRtsp) return "RTSP"
  return camera.isOffline ? "OFFLINE" : "ONLINE"
}

const getStatusClass = (camera) => {
  if (!camera.url || !camera.enabled) return "neutral"
  if (camera.isRtsp) return "info"
  return camera.isOffline ? "danger" : "success"
}

const getStateClass = (camera) => {
  if (!camera.url) return "empty"
  if (!camera.enabled) return "disabled"
  if (camera.isRtsp) return "rtsp"
  return camera.isOffline ? "offline" : "loading"
}

const getCameraPlaceholder = (camera) => {
  if (!camera.url) return "Chưa cấu hình camera trong mạng lưới"
  if (!camera.enabled) return "Camera đang tắt trong Cài đặt"
  if (camera.isRtsp) return "Camera RTSP đã được cấu hình. Cần gateway MJPEG/HLS để xem trên web"
  if (camera.isOffline) return "Offline - Mất kết nối camera"
  return "Đang tải luồng camera"
}

const canRenderLivePreview = (camera) =>
  Boolean(camera.enabled && camera.previewUrl && !camera.isRtsp && !camera.isOffline)

const getCameraPreviewSrc = (camera) => {
  if (!camera.previewUrl) return ""
  const divider = camera.previewUrl.includes("?") ? "&" : "?"
  return `${camera.previewUrl}${divider}v=${camera.previewNonce || 0}`
}

const handlePreviewError = (cameraId) => {
  const camera = cameras.value.find((item) => item.id === cameraId)
  if (!camera) return
  camera.isOffline = true
  cameras.value = [...cameras.value]
}

const handlePreviewLoad = (cameraId) => {
  const camera = cameras.value.find((item) => item.id === cameraId)
  if (!camera) return
  camera.isOffline = false
  cameras.value = [...cameras.value]
}

const toggleExpand = (cameraId) => {
  expandedCameraId.value = expandedCameraId.value === cameraId ? null : cameraId
}

const handleDoubleClick = (cameraId) => {
  const camera = cameras.value.find((item) => item.id === cameraId)
  if (!camera || !camera.enabled || !camera.url) return
  expandedCameraId.value = cameraId
}

const handleContextMenu = (cameraId) => {
  if (expandedCameraId.value === cameraId) {
    expandedCameraId.value = null
  }
}

const probeHttpCameraUrl = async (url, timeoutMs = HEALTH_CHECK_TIMEOUT_MS) => {
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

const checkCameraHealth = async () => {
  if (isHealthCheckRunning) return

  const liveHttpCameras = cameras.value.filter(
    (camera) => camera.enabled && camera.previewUrl && !camera.isRtsp
  )
  if (!liveHttpCameras.length) return

  isHealthCheckRunning = true
  try {
    const results = await Promise.all(
      liveHttpCameras.map(async (camera) => ({
        id: camera.id,
        ok: await probeHttpCameraUrl(camera.previewUrl),
      }))
    )

    let hasChanged = false
    for (const result of results) {
      const camera = cameras.value.find((item) => item.id === result.id)
      if (!camera) continue
      const nextOffline = !result.ok
      if (camera.isOffline !== nextOffline) {
        camera.isOffline = nextOffline
        if (!nextOffline) {
          camera.previewNonce = Date.now()
        }
        hasChanged = true
      }
    }

    if (hasChanged) {
      cameras.value = [...cameras.value]
    }
  } finally {
    isHealthCheckRunning = false
  }
}

const handleKeyDown = (event) => {
  if (event.key === "Escape" && expandedCameraId.value) {
    expandedCameraId.value = null
  }
}

const handleWindowFocus = async () => {
  rebuildCameras()
  await checkCameraHealth()
}

watch(layoutMode, (value) => {
  localStorage.setItem(MONITORING_PREFERENCES_KEY, value)
})

watch(expandedCameraId, (value) => {
  syncImmersiveMode(Boolean(value))
})

onMounted(async () => {
  syncImmersiveMode(Boolean(expandedCameraId.value))
  rebuildCameras()
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  healthTimer = setInterval(checkCameraHealth, HEALTH_CHECK_INTERVAL_MS)
  window.addEventListener("keydown", handleKeyDown)
  window.addEventListener("focus", handleWindowFocus)
  document.addEventListener("visibilitychange", handleWindowFocus)
  await checkCameraHealth()
})

onUnmounted(() => {
  syncImmersiveMode(false)
  clearInterval(timeTimer)
  clearInterval(healthTimer)
  window.removeEventListener("keydown", handleKeyDown)
  window.removeEventListener("focus", handleWindowFocus)
  document.removeEventListener("visibilitychange", handleWindowFocus)
})
</script>

<style scoped>
.bento-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.manage-btn,
.primary-btn,
.link-inline,
.camera-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 700;
}

.manage-btn,
.primary-btn {
  padding: 10px 14px;
  border: none;
  background: var(--accent-primary);
  color: #fff;
}

.link-inline {
  color: var(--accent-primary);
}

.info-card,
.empty-network {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.info-muted {
  margin-left: 8px;
  color: var(--text-secondary);
}

.empty-network {
  flex-direction: column;
  align-items: flex-start;
}

.empty-network h3,
.empty-network p {
  margin: 0;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.18);
  color: var(--accent-danger);
  font-weight: 700;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.layout-select {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  color: var(--text-primary);
}

.camera-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(2, 6, 23, 0.7);
  backdrop-filter: blur(5px);
}

.camera-fullscreen-shell {
  position: fixed;
  inset: 0;
  z-index: 1210;
}

.camera-grid {
  display: grid;
  gap: 16px;
}

.camera-grid.\32x2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.camera-grid.\33x2 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.camera-grid.\31x1 {
  grid-template-columns: 1fr;
}

.camera-card {
  padding: 0;
  overflow: hidden;
  position: relative;
}

.camera-card.expanded {
  position: fixed;
  inset: 0;
  z-index: 1211;
  margin: 0;
  border-radius: 0;
}

.camera-card-teleport {
  background: #020617;
  box-shadow: none;
}

.camera-feed {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #020617;
  overflow: hidden;
}

.camera-card.expanded .camera-feed {
  height: 100vh;
  aspect-ratio: auto;
}

.camera-stream {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #020617;
}

.camera-state {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.camera-state svg {
  width: 52px;
  height: 52px;
  opacity: 0.42;
}

.camera-state p {
  max-width: 360px;
  margin: 0;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 600;
}

.camera-state.empty,
.camera-state.disabled,
.camera-state.loading {
  background: repeating-linear-gradient(45deg, #0f172a, #0f172a 12px, #020617 12px, #020617 24px);
  color: #cbd5e1;
}

.camera-state.offline {
  background: repeating-linear-gradient(45deg, #111827, #111827 12px, #1f2937 12px, #1f2937 24px);
  color: #fca5a5;
}

.camera-state.rtsp {
  background: radial-gradient(circle at top, #13203a, #020617 65%);
  color: #93c5fd;
}

.camera-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 14px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.72) 0%, transparent 22%, transparent 78%, rgba(0, 0, 0, 0.82) 100%);
}

.camera-top-bar,
.camera-bottom-bar,
.camera-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.camera-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: #fff;
}

.camera-source,
.camera-bottom-bar {
  color: #dbeafe;
  font-size: 0.82rem;
}

.camera-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.camera-meta-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.46);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.camera-meta-chip.rtsp {
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.28);
  background: rgba(37, 99, 235, 0.2);
}

.camera-btn {
  min-width: 88px;
  height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(15, 23, 42, 0.7);
  color: #e2e8f0;
  cursor: pointer;
}

.camera-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.camera-status {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  background: rgba(100, 116, 139, 0.25);
  color: #cbd5e1;
}

.camera-status.success {
  background: rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
}

.camera-status.danger {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.camera-status.info {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.camera-status.neutral {
  background: rgba(100, 116, 139, 0.25);
  color: #cbd5e1;
}

@media (max-width: 1200px) {
  .camera-grid.\33x2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .bento-header,
  .header-actions,
  .info-card,
  .camera-top-bar,
  .camera-bottom-bar,
  .camera-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .camera-grid.\32x2,
  .camera-grid.\33x2 {
    grid-template-columns: 1fr;
  }

  .info-muted {
    display: block;
    margin: 8px 0 0;
  }
}
</style>
