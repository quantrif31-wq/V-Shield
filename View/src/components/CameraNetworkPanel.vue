<template>
    <section class="ops-panel network-panel">
        <div class="panel-head">
            <div>
                <span class="panel-kicker">Network sources</span>
                <h2 class="panel-title">Dò camera từ IP Webcam và IP Camera Lite</h2>
                <p class="panel-copy">
                    Phần này quản lý nguồn stream trực tiếp từ điện thoại hoặc camera LAN. Dữ liệu được lưu cục bộ để phục vụ
                    giám sát nhanh, vì bảng <code>Camera</code> hiện chưa có cột IP hoặc URL stream.
                </p>
            </div>
            <div class="panel-actions">
                <button class="btn btn-secondary btn-sm" :disabled="isRefreshingAll" @click="refreshAllCameraStatuses">
                    {{ isRefreshingAll ? 'Đang kiểm tra...' : 'Kiểm tra tất cả' }}
                </button>
                <router-link to="/monitoring" class="btn btn-primary btn-sm">Mở giám sát</router-link>
            </div>
        </div>

        <div class="network-summary">
            <div class="network-stat">
                <span>Slot có stream</span>
                <strong>{{ localSummary.connected }}</strong>
            </div>
            <div class="network-stat">
                <span>Đang bật</span>
                <strong>{{ localSummary.enabled }}</strong>
            </div>
            <div class="network-stat">
                <span>Đang online</span>
                <strong>{{ localSummary.online }}</strong>
            </div>
        </div>

        <div class="network-toolbar">
            <label class="network-field">
                <span class="field-label">Tên hiển thị</span>
                <input v-model="manualCameraName" class="filter-select" type="text" placeholder="Ví dụ: iPhone cổng phụ" />
            </label>

            <label class="network-field">
                <span class="field-label">URL hoặc IP camera</span>
                <input v-model="manualCameraUrl" class="filter-select mono" type="text" placeholder="http://IP:8081/video" />
            </label>

            <label class="network-field">
                <span class="field-label">Nạp vào slot</span>
                <select v-model="manualTargetId" class="filter-select">
                    <option value="auto">Tự động</option>
                    <option v-for="camera in cameraSettings" :key="camera.id" :value="String(camera.id)">
                        {{ camera.name }}
                    </option>
                </select>
            </label>

            <div class="network-actions">
                <button class="btn btn-secondary btn-sm" :disabled="discoveryLoading" @click="discoverLanCameras">
                    {{ discoveryLoading ? 'Đang quét camera LAN...' : 'Tự tìm camera LAN' }}
                </button>
                <button class="btn btn-primary btn-sm" :disabled="connectLoading" @click="applyManualCamera">
                    {{ connectLoading ? 'Đang nạp...' : 'Nạp vào mạng lưới' }}
                </button>
                <button
                    class="btn btn-secondary btn-sm"
                    :disabled="connectLoading || !discoveredCameras.length"
                    @click="applyAllDiscoveredCameras"
                >
                    {{ connectLoading ? 'Đang nạp...' : 'Nạp tất cả camera tìm thấy' }}
                </button>
            </div>
        </div>

        <p class="network-note">
            iPhone IP Camera Lite nên dùng <code>http://IP:8081/video</code>. Nếu chỉ nhập <code>IP:8081</code>, hệ thống sẽ tự
            bổ sung. Với IP Webcam Android, cổng phổ biến là <code>8080</code> và hệ thống sẽ tự thêm
            <code>/videofeed</code> khi cần.
        </p>

        <div v-if="discoveryMessage || connectMessage || discoveryError || connectError" class="network-messages">
            <p v-if="discoveryMessage" class="message success">{{ discoveryMessage }}</p>
            <p v-if="discoveryError" class="message danger">{{ discoveryError }}</p>
            <p v-if="connectMessage" class="message success">{{ connectMessage }}</p>
            <p v-if="connectError" class="message danger">{{ connectError }}</p>
        </div>

        <div v-if="discoveredCameras.length" class="discovery-list">
            <article v-for="camera in discoveredCameras" :key="getCameraKey(camera)" class="discovery-card">
                <div>
                    <strong>{{ camera.name }}</strong>
                    <p class="muted small">{{ camera.ipAddress }}:{{ camera.port }}</p>
                    <p class="small">URL chính: {{ getPreferredConnectUrl(camera) || 'Chưa có URL phù hợp' }}</p>
                </div>
                <div class="discovery-actions">
                    <select v-model="discoveredTargetIds[getCameraKey(camera)]" class="filter-select mini-select">
                        <option value="auto">Tự động</option>
                        <option v-for="item in cameraSettings" :key="item.id" :value="String(item.id)">
                            {{ item.name }}
                        </option>
                    </select>
                    <button class="btn btn-primary btn-sm" @click="applyDiscoveredCamera(camera)">Nạp vào slot</button>
                </div>
            </article>
        </div>

        <div class="camera-slot-grid">
            <article v-for="camera in cameraSettings" :key="camera.id" class="camera-slot-card">
                <div class="camera-slot-head">
                    <div>
                        <h3>{{ camera.name }}</h3>
                        <p>{{ camera.label || 'Chưa đặt tên hiển thị' }}</p>
                    </div>
                    <label class="toggle">
                        <input v-model="camera.enabled" type="checkbox" @change="handleCameraToggle(camera)" />
                        <span></span>
                    </label>
                </div>

                <div class="chip-row">
                    <span class="soft-chip" :class="getCameraStatusClass(camera)">{{ getCameraStatusText(camera) }}</span>
                    <span class="soft-chip">{{ recognitionTypeLabel(camera.recognitionType) }}</span>
                    <span class="soft-chip">{{ camera.resolution }}</span>
                </div>

                <div class="slot-form">
                    <label class="network-field">
                        <span class="field-label">Tên hiển thị trên giám sát</span>
                        <input
                            v-model="camera.label"
                            class="filter-select"
                            type="text"
                            placeholder="Ví dụ: iPhone cổng phụ"
                            @blur="persistCameraSettingsOnly"
                        />
                    </label>

                    <label class="network-field">
                        <span class="field-label">URL stream</span>
                        <input
                            v-model="camera.url"
                            class="filter-select mono"
                            type="text"
                            placeholder="http://IP:8081/video"
                            @blur="normalizeCameraCardUrl(camera.id)"
                        />
                    </label>

                    <div class="slot-meta-grid">
                        <label class="network-field">
                            <span class="field-label">Vị trí lắp đặt</span>
                            <input v-model="camera.location" class="filter-select" type="text" @blur="persistCameraSettingsOnly" />
                        </label>

                        <label class="network-field">
                            <span class="field-label">Kiểu nhận diện</span>
                            <select v-model="camera.recognitionType" class="filter-select" @change="persistCameraSettingsOnly">
                                <option value="both">Khuôn mặt + biển số</option>
                                <option value="face">Khuôn mặt</option>
                                <option value="plate">Biển số</option>
                            </select>
                        </label>

                        <label class="network-field">
                            <span class="field-label">Độ phân giải</span>
                            <select v-model="camera.resolution" class="filter-select" @change="persistCameraSettingsOnly">
                                <option value="1080p">1080p</option>
                                <option value="720p">720p</option>
                                <option value="480p">480p</option>
                            </select>
                        </label>
                    </div>
                </div>

                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" :disabled="checkingIds.includes(camera.id)" @click="refreshSingleCameraStatus(camera.id)">
                        {{ checkingIds.includes(camera.id) ? 'Đang kiểm tra...' : 'Kiểm tra lại' }}
                    </button>
                    <button class="btn btn-danger btn-sm" @click="clearCamera(camera.id)">Xóa camera</button>
                </div>
            </article>
        </div>
    </section>
</template>

<script setup>
import axios from 'axios'
import { computed, onMounted, ref } from 'vue'
import { API_ORIGIN } from '../config/api'
import {
    buildCameraHealthProbeUrl,
    createDefaultCameraSettings,
    isHttpCameraUrl,
    isRtspCameraUrl,
    loadCameraNetworkSettings,
    normalizeCameraUrl,
    saveCameraNetworkSettings,
} from '../utils/cameraNetwork'

const DISCOVERY_API_BASE = `${API_ORIGIN}/api/FaceID`
const CAMERA_PROBE_TIMEOUT_MS = 3500

const cameraSettings = ref(createDefaultCameraSettings())
const manualCameraName = ref('')
const manualCameraUrl = ref('')
const manualTargetId = ref('auto')
const discoveredCameras = ref([])
const discoveredTargetIds = ref({})
const discoveryLoading = ref(false)
const connectLoading = ref(false)
const discoveryMessage = ref('')
const discoveryError = ref('')
const connectMessage = ref('')
const connectError = ref('')
const checkingIds = ref([])
const isRefreshingAll = ref(false)

const localSummary = computed(() => {
    const connected = cameraSettings.value.filter((camera) => camera.url).length
    const enabled = cameraSettings.value.filter((camera) => camera.url && camera.enabled).length
    const online = cameraSettings.value.filter((camera) => camera.url && camera.enabled && camera.online).length

    return { connected, enabled, online }
})

const loadCameraSettings = () => {
    cameraSettings.value = loadCameraNetworkSettings()
}

const persistCameraSettingsOnly = () => {
    cameraSettings.value = saveCameraNetworkSettings(cameraSettings.value)
}

const probeHttpCameraUrl = async (url, timeoutMs = CAMERA_PROBE_TIMEOUT_MS) => {
    if (!url) return false

    const probeUrl = buildCameraHealthProbeUrl(url)
    if (!probeUrl) return false

    const controller = new AbortController()
    const timerId = window.setTimeout(() => controller.abort(), timeoutMs)

    try {
        await fetch(probeUrl, {
            method: 'GET',
            mode: 'no-cors',
            cache: 'no-store',
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
    isRefreshingAll.value = true
    try {
        for (const camera of cameraSettings.value) {
            await refreshSingleCameraStatus(camera.id)
        }
    } finally {
        isRefreshingAll.value = false
    }
}

const getCameraStatusText = (camera) => {
    if (!camera.url) return 'Chưa gắn'
    if (!camera.enabled) return 'Đã tắt'
    if (checkingIds.value.includes(camera.id)) return 'Đang kiểm tra'
    if (isRtspCameraUrl(camera.url)) return 'RTSP'
    return camera.online ? 'Trực tuyến' : 'Ngoại tuyến'
}

const getCameraStatusClass = (camera) => {
    if (!camera.url || !camera.enabled) return 'warn'
    if (checkingIds.value.includes(camera.id)) return ''
    if (isRtspCameraUrl(camera.url)) return ''
    return camera.online ? 'success' : 'danger'
}

const recognitionTypeLabel = (value) => {
    const labels = {
        both: 'Face + plate',
        face: 'Face',
        plate: 'Plate',
    }
    return labels[value] || 'Unknown'
}

const clearDiscoveryState = () => {
    discoveryMessage.value = ''
    discoveryError.value = ''
}

const clearConnectState = () => {
    connectMessage.value = ''
    connectError.value = ''
}

const getCameraKey = (camera) => `${camera.ipAddress}:${camera.port}`
const getPreferredConnectUrl = (camera) => camera?.previewUrl || camera?.rtspUrls?.[0] || camera?.baseUrl || ''

const guessCameraLabel = (url) => {
    try {
        return `Camera ${new URL(url).hostname}`
    } catch {
        return 'Camera LAN'
    }
}

const resolveTargetCameraId = (preferredId = 'auto', preferredUrl = '') => {
    if (preferredId !== 'auto') return Number(preferredId)

    const existing = cameraSettings.value.find((camera) => camera.url === preferredUrl)
    if (existing) return existing.id

    const empty = cameraSettings.value.find((camera) => !camera.url)
    if (empty) return empty.id

    const disabled = cameraSettings.value.find((camera) => !camera.enabled)
    if (disabled) return disabled.id

    return null
}

const applyCameraToNetwork = async (payload, preferredId = 'auto') => {
    const normalizedUrl = normalizeCameraUrl(payload.url)
    if (!normalizedUrl) {
        return { ok: false, error: 'Hãy nhập URL camera hợp lệ trước khi nạp.' }
    }

    const targetId = resolveTargetCameraId(preferredId, normalizedUrl)
    if (!targetId) {
        return {
            ok: false,
            error: 'Mạng lưới camera đã đầy. Hãy chọn một slot cụ thể hoặc xóa bớt camera cũ.',
        }
    }

    const index = cameraSettings.value.findIndex((camera) => camera.id === targetId)
    if (index < 0) {
        return { ok: false, error: 'Không tìm thấy slot camera phù hợp.' }
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
            if (!nextSelections[key]) nextSelections[key] = 'auto'
        }
        discoveredTargetIds.value = nextSelections

        if (!discoveredCameras.value.length) {
            discoveryError.value = 'Chưa tìm thấy camera LAN phù hợp trong cùng mạng.'
            return
        }

        discoveryMessage.value = `Tìm thấy ${discoveredCameras.value.length} thiết bị camera LAN.`
    } catch (error) {
        discoveryError.value = error?.response?.data?.message || error?.message || 'Quét camera LAN thất bại.'
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
            discoveredTargetIds.value[getCameraKey(camera)] || 'auto'
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
        connectError.value = 'Hãy quét camera LAN trước khi nạp toàn bộ.'
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
                discoveredTargetIds.value[getCameraKey(camera)] || 'auto'
            )

            if (!result.ok) {
                skipped.push(camera.name || `${camera.ipAddress}:${camera.port}`)
                continue
            }

            assigned.push(result.camera.name)
        }

        if (!assigned.length) {
            connectError.value = 'Không thể nạp camera nào vào mạng lưới.'
            return
        }

        connectMessage.value = `Đã nạp ${assigned.length} camera vào ${assigned.join(', ')}${
            skipped.length ? `. Bỏ qua ${skipped.length} thiết bị.` : '.'
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
        url: '',
        enabled: false,
        online: false,
    }

    persistCameraSettingsOnly()
    clearConnectState()
    connectMessage.value = `Đã xóa cấu hình khỏi ${current.name}.`
}

onMounted(async () => {
    loadCameraSettings()
    await refreshAllCameraStatuses()
})
</script>

<style scoped>
.network-panel {
    display: grid;
    gap: 18px;
}

.network-summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
}

.network-stat {
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.68);
}

.network-stat span {
    color: var(--text-secondary);
    font-size: 0.8rem;
}

.network-stat strong {
    display: block;
    margin-top: 8px;
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 1.35rem;
}

.network-toolbar {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.3fr) minmax(180px, 0.7fr);
    gap: 14px;
}

.network-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.field-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 700;
}

.network-actions {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    flex-wrap: wrap;
}

.network-note {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.network-note code,
.panel-copy code {
    padding: 2px 6px;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.06);
    font-family: 'JetBrains Mono', monospace;
}

.network-messages {
    display: grid;
    gap: 6px;
}

.message {
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
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px;
    border-radius: 18px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.discovery-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.mini-select {
    min-width: 140px;
}

.camera-slot-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
}

.camera-slot-card {
    display: grid;
    gap: 14px;
    padding: 18px;
    border-radius: 22px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.camera-slot-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
}

.camera-slot-head h3 {
    color: var(--text-primary);
    font-size: 1rem;
}

.camera-slot-head p,
.muted {
    color: var(--text-muted);
}

.small {
    font-size: 0.84rem;
}

.slot-form,
.slot-meta-grid {
    display: grid;
    gap: 14px;
}

.slot-meta-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mono {
    font-family: 'JetBrains Mono', monospace;
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
    content: '';
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

@media (max-width: 1180px) {
    .network-toolbar,
    .camera-slot-grid,
    .slot-meta-grid {
        grid-template-columns: 1fr;
    }

    .network-summary {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .discovery-card,
    .discovery-actions,
    .camera-slot-head {
        flex-direction: column;
        align-items: stretch;
    }

    .network-actions .btn {
        width: 100%;
    }
}
</style>
