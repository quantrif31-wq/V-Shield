<template>
    <div class="page-container animate-in">
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Giám sát Camera</h1>
                <p class="page-subtitle">Theo dõi luồng video trực tiếp và kết nối nhanh camera trong LAN</p>
            </div>
            <div class="header-actions">
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    <span class="live-txt">LIVE</span>
                </div>
                <select v-model="layoutMode" class="minimal-select layout-select">
                    <option value="2x2">Hiển thị: 2 x 2</option>
                    <option value="3x2">Hiển thị: 3 x 2</option>
                    <option value="1x1">Toàn màn hình</option>
                </select>
            </div>
        </header>

        <div class="bento-card quick-connect">
            <div class="bento-header-mini">
                <h3 class="bento-title">Kết nối điện thoại / IP Webcam</h3>
                <span class="badge minimal">LAN</span>
            </div>

            <div class="quick-grid">
                <input v-model="phoneCamName" class="minimal-input" placeholder="Tên hiển thị" />
                <input v-model="phoneCamUrl" class="minimal-input" placeholder="rtsp://user:pass@ip:554/stream" />
                <select v-model="selectedManualSlotId" class="minimal-select slot-select">
                    <option value="auto">Gán vào: Tự động</option>
                    <option v-for="slot in cameras" :key="slot.id" :value="String(slot.id)">
                        Gắn vào: {{ slot.slotName }}
                    </option>
                </select>
                <button class="btn-ghost" :disabled="discoveryLoading" @click="discoverPhoneCams">
                    {{ discoveryLoading ? "Đang quét IP Webcam..." : "Tự tìm IP Webcam" }}
                </button>
                <button class="btn-primary" :disabled="connectLoading" @click="connectPhoneCam">
                    {{ connectLoading ? "Đang kết nối..." : "Bật camera" }}
                </button>
                <button
                    class="btn-primary secondary"
                    :disabled="connectLoading || !discoveredCameras.length"
                    @click="connectAllDiscoveredCameras"
                >
                    {{ connectLoading ? "Đang kết nối..." : "Kết nối tất cả" }}
                </button>
                <button class="btn-danger" :disabled="connectLoading" @click="clearSavedMonitoringState">Xóa tất cả camera đã lưu</button>
            </div>

            <div v-if="discoveredCameras.length" class="discovery-list">
                <div v-for="camera in discoveredCameras" :key="`${camera.ipAddress}:${camera.port}`" class="discovery-card">
                    <div class="discovery-head">
                        <div>
                            <strong>{{ camera.name }}</strong>
                            <p>{{ camera.ipAddress }}:{{ camera.port }}</p>
                        </div>
                        <div class="discovery-actions">
                            <select v-model="slotSelections[getCameraKey(camera)]" class="minimal-select slot-select mini">
                                <option value="auto">Gán vào: Tự động</option>
                                <option v-for="slot in cameras" :key="slot.id" :value="String(slot.id)">
                                    {{ slot.slotName }}
                                </option>
                            </select>
                            <button class="btn-primary mini" @click="connectDiscoveredCamera(camera, getPrimaryRtspUrl(camera))">Kết nối ngay</button>
                        </div>
                    </div>

                    <div class="discovery-url">HTTP: {{ camera.baseUrl }}</div>
                    <div class="discovery-url">MJPEG: {{ camera.previewUrl }}</div>

                    <div class="rtsp-actions">
                        <button
                            v-for="rtspUrl in camera.rtspUrls"
                            :key="rtspUrl"
                            class="rtsp-chip"
                            @click="applyDiscoveredCamera(camera, rtspUrl)"
                        >
                            {{ getRtspLabel(rtspUrl) }}
                        </button>
                    </div>
                </div>
            </div>

            <p v-if="discoveryMessage" class="hint success">{{ discoveryMessage }}</p>
            <p v-if="discoveryError" class="hint danger">{{ discoveryError }}</p>
            <p v-if="connectMessage" class="hint success">{{ connectMessage }}</p>
            <p v-if="connectError" class="hint danger">{{ connectError }}</p>
            <p class="hint shortcut-hint">Desktop: nhấp đúp để mở toàn màn hình, chuột phải hoặc Esc để quay lại. Mobile: dùng nút Toàn màn hình / Quay lại trên camera.</p>
        </div>

        <div v-if="expandedCameraId" class="camera-modal-backdrop" @click="toggleCameraExpand(null)"></div>

        <div class="camera-grid" :class="layoutMode">
            <div
                v-for="cam in cameras"
                :key="cam.id"
                class="bento-card camera-card"
                :class="{ idle: !isCameraAssigned(cam), expanded: isCameraExpanded(cam.id) }"
                @dblclick="handleCameraDoubleClick(cam.id)"
                @contextmenu.prevent="handleCameraContextMenu(cam.id)"
            >
                <div class="camera-feed">
                    <img
                        v-if="isCameraAssigned(cam) && !isCameraOffline(cam) && cam.previewUrl"
                        :src="getCameraPreviewSrc(cam)"
                        :alt="cam.sourceName || cam.slotName"
                        class="camera-stream"
                        @load="handlePreviewLoad(cam.id)"
                        @error="handlePreviewError(cam.id)"
                    />

                    <div v-else-if="isCameraOffline(cam)" class="camera-offline">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <p>Offline - Mất kết nối camera</p>
                    </div>

                    <div v-else-if="isCameraAssigned(cam)" class="camera-placeholder">
                        <div class="camera-animation">
                            <div class="scan-line"></div>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="camera-watermark">
                                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                                <circle cx="12" cy="13" r="4" />
                            </svg>
                        </div>
                    </div>

                    <div v-else class="camera-empty">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                            <circle cx="12" cy="13" r="4" />
                        </svg>
                        <p>Chờ kết nối camera</p>
                    </div>

                    <div class="camera-overlay">
                        <div class="camera-top-bar">
                            <div class="camera-title-wrap">
                                <span class="camera-name">{{ cam.slotName }}</span>
                                <span class="camera-source">{{ cam.sourceName || "Chưa gắn thiết bị" }}</span>
                            </div>

                            <div class="camera-actions">
                                <button class="camera-action-btn wide" :disabled="!isCameraAssigned(cam)" @click.stop="toggleCameraExpand(cam.id)">
                                    {{ isCameraExpanded(cam.id) ? "Quay lại" : "Toàn màn hình" }}
                                </button>
                                <button class="camera-action-btn danger" :disabled="!isCameraAssigned(cam)" @click.stop="disconnectCamera(cam.id)">Ngắt</button>
                                <span class="camera-status" :class="{ online: isCameraOnline(cam), offline: isCameraOffline(cam) }">
                                    <span class="status-dot"></span>
                                    {{ getCameraStatusText(cam) }}
                                </span>
                            </div>
                        </div>

                        <div class="camera-bottom-bar">
                            <span class="camera-location flex-center gap-1">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px; height:12px">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                    <circle cx="12" cy="10" r="3"></circle>
                                </svg>
                                {{ cam.location }}
                            </span>
                            <span class="camera-time">{{ isCameraOnline(cam) ? currentTime : "--" }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue"
import axios from "axios"

const layoutMode = ref("2x2")
const currentTime = ref("")
const phoneCamName = ref("")
const phoneCamUrl = ref("")
const phoneCamPreviewUrl = ref("")
const selectedManualSlotId = ref("auto")
const connectLoading = ref(false)
const connectMessage = ref("")
const connectError = ref("")
const discoveryLoading = ref(false)
const discoveryMessage = ref("")
const discoveryError = ref("")
const discoveredCameras = ref([])
const slotSelections = ref({})
const expandedCameraId = ref(null)
const faceIdApiBase = "https://localhost:7107/api/FaceID"
const monitoringStorageKey = "vshield-monitoring-state-v1"
const healthCheckIntervalMs = 12000
const healthCheckTimeoutMs = 4000

const slotLocations = [
    "Cổng A - Trước",
    "Cổng A - Sau",
    "Cổng B - Trước",
    "Cổng B - Sau",
    "Bãi xe A",
    "Bãi xe B",
]

const createCameraSlots = () =>
    slotLocations.map((location, index) => ({
        id: index + 1,
        slotName: `CAM-${String(index + 1).padStart(2, "0")}`,
        sourceName: "",
        location,
        baseUrl: "",
        streamUrl: "",
        previewUrl: "",
        snapshotUrl: "",
        previewNonce: 0,
        isOffline: false,
    }))

const cameras = ref(createCameraSlots())

const normalizeCameras = (savedCameras) =>
    createCameraSlots().map((defaultSlot) => {
        const savedSlot = Array.isArray(savedCameras)
            ? savedCameras.find((item) => Number(item?.id) === defaultSlot.id)
            : null

        if (!savedSlot) {
            return defaultSlot
        }

        return {
            ...defaultSlot,
            sourceName: savedSlot.sourceName || "",
            baseUrl: savedSlot.baseUrl || "",
            streamUrl: savedSlot.streamUrl || "",
            previewUrl: savedSlot.previewUrl || "",
            snapshotUrl: savedSlot.snapshotUrl || "",
            previewNonce: savedSlot.previewNonce || 0,
            isOffline: Boolean(savedSlot.isOffline),
        }
    })

const saveMonitoringState = () => {
    const payload = {
        cameras: cameras.value,
        discoveredCameras: discoveredCameras.value,
        slotSelections: slotSelections.value,
        selectedManualSlotId: selectedManualSlotId.value,
        phoneCamName: phoneCamName.value,
        phoneCamUrl: phoneCamUrl.value,
        phoneCamPreviewUrl: phoneCamPreviewUrl.value,
    }

    localStorage.setItem(monitoringStorageKey, JSON.stringify(payload))
}

const restoreMonitoringState = () => {
    const rawState = localStorage.getItem(monitoringStorageKey)
    if (!rawState) {
        return
    }

    try {
        const parsedState = JSON.parse(rawState)

        cameras.value = normalizeCameras(parsedState?.cameras)
        discoveredCameras.value = Array.isArray(parsedState?.discoveredCameras) ? parsedState.discoveredCameras : []
        slotSelections.value = typeof parsedState?.slotSelections === "object" && parsedState?.slotSelections
            ? parsedState.slotSelections
            : {}
        selectedManualSlotId.value = parsedState?.selectedManualSlotId || "auto"
        phoneCamName.value = parsedState?.phoneCamName || ""
        phoneCamUrl.value = parsedState?.phoneCamUrl || ""
        phoneCamPreviewUrl.value = parsedState?.phoneCamPreviewUrl || ""
    } catch {
        cameras.value = createCameraSlots()
        discoveredCameras.value = []
        slotSelections.value = {}
        selectedManualSlotId.value = "auto"
        phoneCamName.value = ""
        phoneCamUrl.value = ""
        phoneCamPreviewUrl.value = ""
    }
}

let timer = null
let healthTimer = null
let isHealthCheckRunning = false

const updateTime = () => {
    currentTime.value = new Date().toLocaleTimeString("vi-VN")
}

const handleKeyDown = (event) => {
    if (event.key === "Escape" && expandedCameraId.value) {
        expandedCameraId.value = null
    }
}

onMounted(() => {
    restoreMonitoringState()
    updateTime()
    timer = setInterval(updateTime, 1000)
    healthTimer = setInterval(checkCameraHealth, healthCheckIntervalMs)
    window.addEventListener("keydown", handleKeyDown)
    setTimeout(checkCameraHealth, 1200)
})

onUnmounted(() => {
    clearInterval(timer)
    clearInterval(healthTimer)
    window.removeEventListener("keydown", handleKeyDown)
})

watch(
    [cameras, discoveredCameras, slotSelections, selectedManualSlotId, phoneCamName, phoneCamUrl, phoneCamPreviewUrl],
    () => {
        saveMonitoringState()
    },
    { deep: true }
)

const isCameraAssigned = (cam) => Boolean(cam.streamUrl)
const isCameraOffline = (cam) => Boolean(cam.streamUrl) && Boolean(cam.isOffline)
const isCameraOnline = (cam) => Boolean(cam.streamUrl) && !cam.isOffline
const isCameraExpanded = (cameraId) => expandedCameraId.value === cameraId

const clearDiscoveryState = () => {
    discoveryMessage.value = ""
    discoveryError.value = ""
}

const clearConnectState = () => {
    connectMessage.value = ""
    connectError.value = ""
}

const getCameraStatusText = (cam) => {
    if (!isCameraAssigned(cam)) return "Trống"
    return cam.isOffline ? "Offline" : "Online"
}

const getPrimaryRtspUrl = (camera) => camera?.rtspUrls?.[0] || ""
const getCameraKey = (camera) => `${camera.ipAddress}:${camera.port}`

const getRtspLabel = (url) => {
    if (!url) return "RTSP"
    if (url.includes("h264_ulaw")) return "RTSP ULAW"
    if (url.includes("h264_pcm")) return "RTSP PCM"
    return "RTSP H264"
}

const getPreviewUrlFromStream = (streamUrl) => {
    try {
        const parsedUrl = new URL(streamUrl)
        const port = parsedUrl.port || "8080"
        return `http://${parsedUrl.hostname}:${port}/videofeed`
    } catch {
        return ""
    }
}

const getBaseUrlFromStream = (streamUrl) => {
    try {
        const parsedUrl = new URL(streamUrl)
        const port = parsedUrl.port || "8080"
        return `http://${parsedUrl.hostname}:${port}`
    } catch {
        return ""
    }
}

const getSnapshotUrlFromStream = (streamUrl) => {
    const baseUrl = getBaseUrlFromStream(streamUrl)
    return baseUrl ? `${baseUrl}/shot.jpg` : ""
}

const buildCameraPayload = (name, streamUrl, previewUrl = "", snapshotUrl = "", baseUrl = "") => ({
    name: name?.trim() || "",
    baseUrl: baseUrl?.trim() || getBaseUrlFromStream(streamUrl),
    streamUrl: streamUrl?.trim() || "",
    previewUrl: previewUrl?.trim() || getPreviewUrlFromStream(streamUrl),
    snapshotUrl: snapshotUrl?.trim() || getSnapshotUrlFromStream(streamUrl),
})

const createEmptySlot = (slotId) => ({
    id: slotId,
    slotName: `CAM-${String(slotId).padStart(2, "0")}`,
    sourceName: "",
    location: slotLocations[slotId - 1],
    baseUrl: "",
    streamUrl: "",
    previewUrl: "",
    snapshotUrl: "",
    previewNonce: 0,
    isOffline: false,
})

const assignCameraToSlot = (payload, preferredSlotId = "auto") => {
    let existingIndex = cameras.value.findIndex((cam) => cam.streamUrl && cam.streamUrl === payload.streamUrl)
    let targetIndex = -1

    if (preferredSlotId !== "auto") {
        targetIndex = cameras.value.findIndex((cam) => cam.id === Number(preferredSlotId))
    } else if (existingIndex >= 0) {
        targetIndex = existingIndex
    } else {
        targetIndex = cameras.value.findIndex((cam) => !cam.streamUrl)
    }

    if (targetIndex < 0) {
        return null
    }

    if (existingIndex >= 0 && existingIndex !== targetIndex) {
        const existingSlotId = cameras.value[existingIndex].id
        cameras.value[existingIndex] = createEmptySlot(existingSlotId)
    }

    const slot = cameras.value[targetIndex]
    cameras.value[targetIndex] = {
        ...slot,
        sourceName: payload.name || `IP Webcam ${targetIndex + 1}`,
        baseUrl: payload.baseUrl,
        streamUrl: payload.streamUrl,
        previewUrl: payload.previewUrl,
        snapshotUrl: payload.snapshotUrl,
        previewNonce: Date.now(),
        isOffline: false,
    }
    cameras.value = [...cameras.value]

    return cameras.value[targetIndex]
}

const getCameraPreviewSrc = (cam) => {
    if (!cam.previewUrl) {
        return ""
    }

    const divider = cam.previewUrl.includes("?") ? "&" : "?"
    return `${cam.previewUrl}${divider}v=${cam.previewNonce || 0}`
}

const handlePreviewError = (cameraId) => {
    const idx = cameras.value.findIndex((cam) => cam.id === cameraId)
    if (idx >= 0) {
        cameras.value[idx].isOffline = true
        cameras.value = [...cameras.value]
    }
}

const handlePreviewLoad = (cameraId) => {
    const idx = cameras.value.findIndex((cam) => cam.id === cameraId)
    if (idx >= 0 && cameras.value[idx].isOffline) {
        cameras.value[idx].isOffline = false
        cameras.value = [...cameras.value]
    }
}

const applyDiscoveredCamera = (camera, rtspUrl) => {
    phoneCamName.value = camera.name || ""
    phoneCamUrl.value = rtspUrl || ""
    phoneCamPreviewUrl.value = camera.previewUrl || getPreviewUrlFromStream(rtspUrl || "")
    selectedManualSlotId.value = slotSelections.value[getCameraKey(camera)] || "auto"
    clearConnectState()
}

const toggleCameraExpand = (cameraId) => {
    expandedCameraId.value = expandedCameraId.value === cameraId ? null : cameraId
}

const handleCameraDoubleClick = (cameraId) => {
    const camera = cameras.value.find((cam) => cam.id === cameraId)
    if (camera && isCameraAssigned(camera)) {
        expandedCameraId.value = cameraId
    }
}

const handleCameraContextMenu = (cameraId) => {
    if (expandedCameraId.value === cameraId) {
        expandedCameraId.value = null
    }
}

const connectCameraPayload = async (payload, preferredSlotId = "auto") => {
    const slot = assignCameraToSlot(payload, preferredSlotId)

    if (!slot) {
        return {
            ok: false,
            error: "Không còn ô camera trống. Hãy tắt bớt camera hoặc tải lại trang để sắp xếp lại."
        }
    }

    return {
        ok: true,
        slot,
        message: `Đã gắn ${slot.sourceName} vào ${slot.slotName}.`
    }
}

const probeImageUrl = (url, timeoutMs = healthCheckTimeoutMs) =>
    new Promise((resolve) => {
        if (!url) {
            resolve(false)
            return
        }

        const img = new Image()
        let completed = false

        const cleanup = (result) => {
            if (completed) {
                return
            }

            completed = true
            clearTimeout(timerId)
            img.onload = null
            img.onerror = null
            resolve(result)
        }

        const timerId = window.setTimeout(() => cleanup(false), timeoutMs)

        img.onload = () => cleanup(true)
        img.onerror = () => cleanup(false)
        img.src = `${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`
    })

const checkCameraHealth = async () => {
    if (isHealthCheckRunning) {
        return
    }

    const assignedCameras = cameras.value.filter((cam) => cam.streamUrl)
    if (!assignedCameras.length) {
        return
    }

    isHealthCheckRunning = true

    try {
        const results = await Promise.all(
            assignedCameras.map(async (cam) => ({
                id: cam.id,
                ok: await probeImageUrl(cam.snapshotUrl || cam.previewUrl),
            }))
        )

        let hasChanged = false

        for (const result of results) {
            const idx = cameras.value.findIndex((cam) => cam.id === result.id)
            if (idx < 0) {
                continue
            }

            const nextOffline = !result.ok
            if (cameras.value[idx].isOffline !== nextOffline) {
                cameras.value[idx].isOffline = nextOffline
                if (!nextOffline) {
                    cameras.value[idx].previewNonce = Date.now()
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

const clearSavedMonitoringState = () => {
    cameras.value = createCameraSlots()
    discoveredCameras.value = []
    slotSelections.value = {}
    selectedManualSlotId.value = "auto"
    phoneCamName.value = ""
    phoneCamUrl.value = ""
    phoneCamPreviewUrl.value = ""
    expandedCameraId.value = null
    clearDiscoveryState()
    clearConnectState()
    localStorage.removeItem(monitoringStorageKey)
    connectMessage.value = "Đã xóa tất cả camera đã lưu."
}

const disconnectCamera = (cameraId) => {
    const idx = cameras.value.findIndex((cam) => cam.id === cameraId)
    if (idx < 0 || !cameras.value[idx].streamUrl) {
        return
    }

    const slotName = cameras.value[idx].slotName
    cameras.value[idx] = createEmptySlot(cameraId)
    cameras.value = [...cameras.value]

    if (expandedCameraId.value === cameraId) {
        expandedCameraId.value = null
    }

    clearConnectState()
    connectMessage.value = `Đã ngắt camera khỏi ${slotName}.`
}
const discoverPhoneCams = async () => {
    discoveryLoading.value = true
    clearDiscoveryState()

    try {
        const { data } = await axios.get(`${faceIdApiBase}/discover-ipwebcam`)
        discoveredCameras.value = data?.cameras || []
        const nextSelections = { ...slotSelections.value }

        for (const camera of discoveredCameras.value) {
            const cameraKey = getCameraKey(camera)
            if (!nextSelections[cameraKey]) {
                nextSelections[cameraKey] = "auto"
            }
        }

        slotSelections.value = nextSelections

        if (!discoveredCameras.value.length) {
            discoveryError.value = "Chưa tìm thấy IP Webcam trong cùng mạng LAN."
            return
        }

        discoveryMessage.value = `Tìm thấy ${discoveredCameras.value.length} thiết bị IP Webcam.`
    } catch (err) {
        discoveryError.value = err?.response?.data?.message || err?.message || "Quét IP Webcam thất bại."
    } finally {
        discoveryLoading.value = false
    }
}

const connectPhoneCam = async () => {
    clearConnectState()

    if (!phoneCamUrl.value.trim()) {
        connectError.value = "Nhập URL RTSP của điện thoại."
        return
    }

    connectLoading.value = true

    try {
        const payload = buildCameraPayload(phoneCamName.value, phoneCamUrl.value, phoneCamPreviewUrl.value)
        const result = await connectCameraPayload(payload, selectedManualSlotId.value)

        if (!result.ok) {
            connectError.value = result.error
            return
        }

        connectMessage.value = result.message
    } finally {
        connectLoading.value = false
    }
}

const connectDiscoveredCamera = async (camera, rtspUrl) => {
    clearConnectState()
    connectLoading.value = true

    try {
        applyDiscoveredCamera(camera, rtspUrl)

        const payload = buildCameraPayload(
            camera.name,
            rtspUrl || getPrimaryRtspUrl(camera),
            camera.previewUrl,
            camera.snapshotUrl,
            camera.baseUrl
        )

        if (!payload.streamUrl) {
            connectError.value = `Thiết bị ${camera.name} không có RTSP hợp lệ.`
            return
        }

        const result = await connectCameraPayload(
            payload,
            slotSelections.value[getCameraKey(camera)] || "auto"
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

const connectAllDiscoveredCameras = async () => {
    clearConnectState()

    if (!discoveredCameras.value.length) {
        connectError.value = "Hãy quét IP Webcam trước khi kết nối tất cả."
        return
    }

    connectLoading.value = true

    try {
        const assignedSlots = []
        const skippedNames = []

        for (const camera of discoveredCameras.value) {
            const rtspUrl = getPrimaryRtspUrl(camera)

            if (!rtspUrl) {
                skippedNames.push(camera.name || `${camera.ipAddress}:${camera.port}`)
                continue
            }

            const payload = buildCameraPayload(camera.name, rtspUrl, camera.previewUrl, camera.snapshotUrl, camera.baseUrl)
            const result = await connectCameraPayload(
                payload,
                slotSelections.value[getCameraKey(camera)] || "auto"
            )

            if (!result.ok) {
                skippedNames.push(camera.name || `${camera.ipAddress}:${camera.port}`)
                continue
            }

            assignedSlots.push(result.slot.slotName)
        }

        if (!assignedSlots.length) {
            connectError.value = "Không thể gắn camera nào vào màn hình. Có thể tất cả ô đã được dùng."
            return
        }

        let finalMessage = `Đã gắn ${assignedSlots.length} thiết bị vào ${assignedSlots.join(", ")}.`

        if (skippedNames.length) {
            finalMessage += ` Bỏ qua ${skippedNames.length} thiết bị chưa có RTSP hoặc không còn ô trống.`
        }

        connectMessage.value = finalMessage
    } finally {
        connectLoading.value = false
    }
}
</script>

<style scoped>
.bento-header {
    margin-bottom: 24px;
    padding: 0 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.bento-header .greeting h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
}

.bento-header .greeting p {
    color: var(--text-secondary);
    font-size: 0.95rem;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.bento-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    padding: 24px;
}

.bento-header-mini {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
    margin-bottom: 16px;
}

.bento-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.badge.minimal {
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 500;
}

.quick-connect {
    margin-bottom: 20px;
}

.quick-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    align-items: center;
}

.slot-select {
    min-width: 160px;
}

.slot-select.mini {
    min-width: 130px;
    padding: 8px 12px;
    font-size: 0.85rem;
}

.minimal-input {
    padding: 10px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    color: var(--text-primary);
    outline: none;
}

.btn-primary,
.btn-ghost,
.rtsp-chip {
    transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.btn-primary:hover,
.btn-ghost:hover,
.rtsp-chip:hover {
    transform: translateY(-1px);
}

.btn-primary {
    padding: 10px 14px;
    background: var(--accent-primary);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-weight: 700;
    cursor: pointer;
}

.btn-primary.secondary {
    background: linear-gradient(135deg, #0f766e, #0ea5a4);
}

.btn-danger {
    padding: 10px 14px;
    background: rgba(220, 38, 38, 0.12);
    border: 1px solid rgba(248, 113, 113, 0.3);
    border-radius: 10px;
    color: #ef4444;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.btn-danger:hover:not(:disabled) {
    transform: translateY(-1px);
    background: rgba(220, 38, 38, 0.18);
    border-color: rgba(248, 113, 113, 0.5);
}

.btn-danger:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.btn-primary:disabled,
.btn-ghost:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.btn-ghost {
    padding: 10px 14px;
    background: transparent;
    border: 1px dashed var(--border-color);
    color: var(--text-secondary);
    border-radius: 10px;
    cursor: pointer;
}

.btn-primary.mini {
    padding: 8px 12px;
}

.hint {
    margin-top: 8px;
    font-size: 0.9rem;
}

.hint.success {
    color: var(--accent-success);
}

.hint.danger {
    color: var(--accent-danger);
}

.shortcut-hint {
    color: var(--text-secondary);
}

.discovery-list {
    margin-top: 14px;
    display: grid;
    gap: 12px;
}

.discovery-card {
    padding: 14px;
    border-radius: 14px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
}

.discovery-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
}

.discovery-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

.discovery-head p {
    margin: 4px 0 0;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.discovery-url {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 4px;
    word-break: break-all;
}

.rtsp-actions {
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.rtsp-chip {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(16, 121, 196, 0.25);
    background: rgba(16, 121, 196, 0.08);
    color: var(--accent-primary);
    cursor: pointer;
    font-size: 0.8rem;
}

.live-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    color: var(--accent-danger);
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.15);
}

.live-txt {
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
}

.live-dot {
    width: 8px;
    height: 8px;
    background: var(--accent-danger);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.minimal-select {
    padding: 8px 14px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    cursor: pointer;
    outline: none;
    font-size: 0.9rem;
}

.layout-select {
    min-width: 150px;
}

.camera-grid {
    display: grid;
    gap: 16px;
    margin-bottom: 24px;
    transition: all 0.3s;
}

.camera-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(2, 6, 23, 0.72);
    backdrop-filter: blur(6px);
    z-index: 90;
}

.camera-grid.\32x2 {
    grid-template-columns: repeat(2, 1fr);
}

.camera-grid.\33x2 {
    grid-template-columns: repeat(3, 1fr);
}

.camera-grid.\31x1 {
    grid-template-columns: 1fr;
}

.camera-card {
    padding: 0;
    overflow: hidden;
    position: relative;
    border-radius: 16px;
    background: var(--bg-card);
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.camera-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    border-color: rgba(16, 121, 196, 0.3);
}

.camera-card.expanded {
    position: fixed;
    inset: 0;
    z-index: 100;
    margin: 0;
    transform: none;
    border-radius: 0;
    border: none;
    box-shadow: 0 24px 80px rgba(15, 23, 42, 0.6);
}

.camera-card.expanded .camera-feed {
    height: 100vh;
    aspect-ratio: auto;
}

.camera-card.idle {
    opacity: 0.92;
}

.camera-feed {
    position: relative;
    aspect-ratio: 16 / 9;
    background: #030712;
    overflow: hidden;
}

.camera-placeholder {
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, #0f172a 0%, #030712 100%);
    display: flex;
    justify-content: center;
    align-items: center;
}

.camera-empty {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: repeating-linear-gradient(45deg, #0f172a, #0f172a 10px, #030712 10px, #030712 20px);
}

.camera-empty svg {
    width: 48px;
    height: 48px;
    color: var(--text-muted);
    opacity: 0.35;
}

.camera-empty p {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 500;
    background: rgba(0, 0, 0, 0.35);
    padding: 5px 12px;
    border-radius: 999px;
}

.camera-offline {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: repeating-linear-gradient(45deg, #111827, #111827 10px, #1f2937 10px, #1f2937 20px);
}

.camera-offline svg {
    width: 50px;
    height: 50px;
    color: #f87171;
    opacity: 0.7;
}

.camera-offline p {
    color: #fecaca;
    font-size: 0.92rem;
    font-weight: 600;
    background: rgba(127, 29, 29, 0.35);
    padding: 6px 14px;
    border-radius: 999px;
}

.camera-stream {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    background: #030712;
}

.camera-animation {
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

.scan-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.5), transparent);
    animation: scan 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    box-shadow: 0 0 10px rgba(14, 165, 233, 0.5);
}

@keyframes scan {
    0%, 100% { top: 5%; opacity: 0; }
    10% { opacity: 1; }
    50% { top: 95%; }
    90% { opacity: 1; }
}

.camera-watermark {
    width: 56px;
    height: 56px;
    color: var(--accent-primary);
    opacity: 0.15;
    filter: drop-shadow(0 0 8px rgba(16, 121, 196, 0.5));
}

.camera-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 14px;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.7) 0%, transparent 20%, transparent 80%, rgba(0, 0, 0, 0.8) 100%);
    pointer-events: none;
}

.camera-top-bar,
.camera-bottom-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}

.camera-title-wrap {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}

.camera-name {
    font-weight: 700;
    font-size: 0.92rem;
    color: #fff;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
    letter-spacing: 0.5px;
}

.camera-source {
    font-size: 0.78rem;
    color: #cbd5e1;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 220px;
}

.camera-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    pointer-events: auto;
}

.camera-action-btn {
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(15, 23, 42, 0.7);
    color: #e2e8f0;
    border-radius: 8px;
    min-width: 34px;
    height: 34px;
    padding: 0 10px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.camera-action-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    background: rgba(30, 41, 59, 0.85);
    border-color: rgba(96, 165, 250, 0.4);
}

.camera-action-btn:disabled {
    cursor: not-allowed;
    opacity: 0.45;
}

.camera-action-btn.wide {
    min-width: 86px;
}

.camera-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
    background: rgba(71, 85, 105, 0.45);
    color: #cbd5e1;
    backdrop-filter: blur(4px);
    text-transform: uppercase;
}

.camera-status.online {
    background: rgba(5, 150, 105, 0.5);
    color: #6ee7b7;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
}

.camera-status.offline {
    background: rgba(185, 28, 28, 0.35);
    color: #fca5a5;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.18);
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
}

.camera-location {
    font-size: 0.8rem;
    color: #e2e8f0;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
    font-weight: 500;
}

.camera-time {
    font-family: "JetBrains Mono", monospace;
    font-weight: 600;
    font-size: 0.85rem;
    color: #fff;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
}

.flex-center {
    display: flex;
    align-items: center;
}

.gap-1 {
    gap: 4px;
}

@media (max-width: 1024px) {
    .camera-grid.\33x2 {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .bento-header,
    .header-actions,
    .discovery-head {
        flex-direction: column;
        align-items: stretch;
    }

    .camera-grid.\32x2,
    .camera-grid.\33x2 {
        grid-template-columns: 1fr;
    }

    .camera-action-btn.wide {
        min-width: 112px;
        height: 40px;
    }
}
</style>
