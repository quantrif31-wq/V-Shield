<template>
    <section class="ops-panel network-panel">
        <div class="panel-head">
            <div>
                <span class="panel-kicker">Network sources</span>
                <h2 class="panel-title">Nguon camera local va preview tren web</h2>
                <p class="panel-copy">
                    RTSP co the dung cho AI va xu ly backend. Neu muon xem tren trinh duyet, hay them mot
                    <code>Preview URL</code> dang HLS, MJPEG, MP4 hoac WebRTC gateway.
                </p>
            </div>
            <div class="panel-actions">
                <button class="btn btn-secondary btn-sm" :disabled="isRefreshingAll" @click="refreshAllCameraStatuses">
                    {{ isRefreshingAll ? "Dang kiem tra..." : "Kiem tra tat ca" }}
                </button>
                <router-link to="/monitoring" class="btn btn-primary btn-sm">Mo giam sat</router-link>
            </div>
        </div>

        <div class="network-summary">
            <div class="network-stat">
                <span>Slot co nguon</span>
                <strong>{{ localSummary.connected }}</strong>
            </div>
            <div class="network-stat">
                <span>Dang bat</span>
                <strong>{{ localSummary.enabled }}</strong>
            </div>
            <div class="network-stat">
                <span>Preview online</span>
                <strong>{{ localSummary.online }}</strong>
            </div>
        </div>

        <div class="network-toolbar">
            <label class="network-field">
                <span class="field-label">Ten hien thi</span>
                <input
                    v-model="manualCameraName"
                    class="filter-select"
                    type="text"
                    placeholder="Vi du: Imou cong truoc"
                />
            </label>

            <label class="network-field">
                <span class="field-label">URL stream cho AI / nguon goc</span>
                <input
                    v-model="manualCameraUrl"
                    class="filter-select mono"
                    type="text"
                    placeholder="rtsp://... hoac http://IP:8081/video"
                />
            </label>

            <label class="network-field">
                <span class="field-label">Preview URL tren web (tuy chon)</span>
                <input
                    v-model="manualCameraPreviewUrl"
                    class="filter-select mono"
                    type="text"
                    placeholder="http://.../videofeed hoac https://.../stream.m3u8"
                />
            </label>

            <label class="network-field">
                <span class="field-label">Nap vao slot</span>
                <select v-model="manualTargetId" class="filter-select">
                    <option value="auto">Tu dong</option>
                    <option v-for="camera in cameraSettings" :key="camera.id" :value="String(camera.id)">
                        {{ camera.name }}
                    </option>
                </select>
            </label>

            <div class="network-actions">
                <button class="btn btn-secondary btn-sm" :disabled="discoveryLoading" @click="discoverLanCameras">
                    {{ discoveryLoading ? "Dang quet camera LAN..." : "Tu tim camera LAN" }}
                </button>
                <button class="btn btn-primary btn-sm" :disabled="connectLoading" @click="applyManualCamera">
                    {{ connectLoading ? "Dang nap..." : "Nap vao mang luoi" }}
                </button>
                <button
                    class="btn btn-secondary btn-sm"
                    :disabled="connectLoading || !discoveredCameras.length"
                    @click="applyAllDiscoveredCameras"
                >
                    {{ connectLoading ? "Dang nap..." : "Nap tat ca camera tim thay" }}
                </button>
            </div>
        </div>

        <p class="network-note">
            IP Webcam / IP Camera Lite van co the tu nhan URL HTTP. Voi Imou hoac RTSP, ban nen luu RTSP o
            <code>URL stream</code> va them mot <code>Preview URL</code> da duoc bridge sang HLS, MJPEG hoac WebRTC
            neu muon xem tren web.
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
                    <p class="small">Nguon uu tien: {{ getPreferredConnectUrl(camera) || "Chua co URL phu hop" }}</p>
                </div>
                <div class="discovery-actions">
                    <select v-model="discoveredTargetIds[getCameraKey(camera)]" class="filter-select mini-select">
                        <option value="auto">Tu dong</option>
                        <option v-for="item in cameraSettings" :key="item.id" :value="String(item.id)">
                            {{ item.name }}
                        </option>
                    </select>
                    <button class="btn btn-primary btn-sm" @click="applyDiscoveredCamera(camera)">Nap vao slot</button>
                </div>
            </article>
        </div>

        <div class="camera-slot-grid">
            <article v-for="camera in cameraSettings" :key="camera.id" class="camera-slot-card">
                <div class="camera-slot-head">
                    <div>
                        <h3>{{ camera.name }}</h3>
                        <p>{{ camera.label || "Chua dat ten hien thi" }}</p>
                    </div>
                    <label class="toggle">
                        <input v-model="camera.enabled" type="checkbox" @change="handleCameraToggle(camera)" />
                        <span></span>
                    </label>
                </div>

                <div class="chip-row">
                    <span class="soft-chip" :class="getCameraStatusClass(camera)">{{ getCameraStatusText(camera) }}</span>
                    <span v-if="camera.previewUrl" class="soft-chip success">Preview web</span>
                    <span v-else-if="camera.url && isRtspCameraUrl(camera.url)" class="soft-chip warn">Can gateway web</span>
                </div>

                <div class="slot-form">
                    <label class="network-field">
                        <span class="field-label">Ten hien thi tren giam sat</span>
                        <input
                            v-model="camera.label"
                            class="filter-select"
                            type="text"
                            placeholder="Vi du: Imou cong truoc"
                            @blur="persistCameraSettingsOnly"
                        />
                    </label>

                    <label class="network-field">
                        <span class="field-label">URL stream cho AI / backend</span>
                        <input
                            v-model="camera.url"
                            class="filter-select mono"
                            type="text"
                            placeholder="rtsp://... hoac http://IP:8081/video"
                            @blur="normalizeCameraCardUrls(camera.id)"
                        />
                    </label>

                    <label class="network-field">
                        <span class="field-label">Preview URL tren web</span>
                        <input
                            v-model="camera.previewUrl"
                            class="filter-select mono"
                            type="text"
                            placeholder="https://.../stream.m3u8 hoac http://IP:8080/videofeed"
                            @blur="normalizeCameraCardUrls(camera.id)"
                        />
                        <span class="field-hint">
                            Neu chi co RTSP, browser se khong phat truc tiep. Hay them URL HLS, MJPEG, MP4 hoac
                            WebRTC gateway.
                        </span>
                    </label>

                    <div class="slot-meta-grid">
                        <label class="network-field">
                            <span class="field-label">Vi tri lap dat</span>
                            <input
                                v-model="camera.location"
                                class="filter-select"
                                type="text"
                                @blur="persistCameraSettingsOnly"
                            />
                        </label>
                    </div>
                </div>

                <div class="slot-preview">
                    <div class="slot-preview-head">
                        <strong>Preview tren web</strong>
                        <span>{{ camera.previewUrl ? "Dang dung Preview URL" : "Dang dung nguon hien co" }}</span>
                    </div>
                    <StreamPreview :url="resolveCameraPreviewUrl(camera)" :label="camera.label || camera.name" />
                </div>

                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" :disabled="checkingIds.includes(camera.id)" @click="refreshSingleCameraStatus(camera.id)">
                        {{ checkingIds.includes(camera.id) ? "Dang kiem tra..." : "Kiem tra lai" }}
                    </button>
                    <button class="btn btn-danger btn-sm" @click="clearCamera(camera.id)">Xoa camera</button>
                </div>
            </article>
        </div>
    </section>
</template>

<script setup>
import axios from "axios"
import { computed, onMounted, ref } from "vue"
import { API_ORIGIN } from "../config/api"
import StreamPreview from "./StreamPreview.vue"
import {
    buildCameraHealthProbeUrl,
    createDefaultCameraSettings,
    isHttpCameraUrl,
    isRtspCameraUrl,
    loadCameraNetworkSettings,
    normalizeCameraUrl,
    resolveCameraPreviewUrl,
    saveCameraNetworkSettings,
} from "../utils/cameraNetwork"

const DISCOVERY_API_BASE = `${API_ORIGIN}/api/FaceID`
const CAMERA_PROBE_TIMEOUT_MS = 3500

const cameraSettings = ref(createDefaultCameraSettings())
const manualCameraName = ref("")
const manualCameraUrl = ref("")
const manualCameraPreviewUrl = ref("")
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
const isRefreshingAll = ref(false)

const hasCameraSource = (camera) => Boolean(camera?.url?.trim() || camera?.previewUrl?.trim())

const localSummary = computed(() => {
    const connected = cameraSettings.value.filter((camera) => hasCameraSource(camera)).length
    const enabled = cameraSettings.value.filter((camera) => hasCameraSource(camera) && camera.enabled).length
    const online = cameraSettings.value.filter((camera) => hasCameraSource(camera) && camera.enabled && camera.online).length

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
        const previewCandidate = resolveCameraPreviewUrl(camera)
        if (!hasCameraSource(camera) || !camera.enabled) {
            camera.online = false
        } else if (isHttpCameraUrl(previewCandidate)) {
            camera.online = await probeHttpCameraUrl(previewCandidate)
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
    if (!hasCameraSource(camera)) return "Chua gan"
    if (!camera.enabled) return "Da tat"
    if (checkingIds.value.includes(camera.id)) return "Dang kiem tra"
    if (camera.url && isRtspCameraUrl(camera.url) && camera.previewUrl) return "RTSP + preview"
    if (camera.url && isRtspCameraUrl(camera.url)) return "RTSP cho AI"
    return camera.online ? "Truc tuyen" : "Ngoai tuyen"
}

const getCameraStatusClass = (camera) => {
    if (!hasCameraSource(camera) || !camera.enabled) return "warn"
    if (checkingIds.value.includes(camera.id)) return ""
    if (camera.url && isRtspCameraUrl(camera.url) && !camera.previewUrl) return ""
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
const getPreferredConnectUrl = (camera) => camera?.previewUrl || camera?.rtspUrls?.[0] || camera?.baseUrl || ""

const guessCameraLabel = (url) => {
    try {
        return `Camera ${new URL(url).hostname}`
    } catch {
        return "Camera LAN"
    }
}

const resolveTargetCameraId = (preferredId = "auto", urlCandidates = []) => {
    if (preferredId !== "auto") return Number(preferredId)

    const existing = cameraSettings.value.find((camera) =>
        urlCandidates.some((candidate) => candidate && (camera.url === candidate || camera.previewUrl === candidate))
    )
    if (existing) return existing.id

    const empty = cameraSettings.value.find((camera) => !hasCameraSource(camera))
    if (empty) return empty.id

    const disabled = cameraSettings.value.find((camera) => !camera.enabled)
    if (disabled) return disabled.id

    return null
}

const applyCameraToNetwork = async (payload, preferredId = "auto") => {
    const normalizedUrl = normalizeCameraUrl(payload.url)
    const normalizedPreviewUrl = normalizeCameraUrl(payload.previewUrl)
    const primaryUrl = normalizedUrl || normalizedPreviewUrl

    if (!primaryUrl) {
        return { ok: false, error: "Hay nhap it nhat mot URL hop le truoc khi nap." }
    }

    const targetId = resolveTargetCameraId(preferredId, [normalizedUrl, normalizedPreviewUrl, primaryUrl])
    if (!targetId) {
        return {
            ok: false,
            error: "Mang luoi camera da day. Hay chon mot slot cu the hoac xoa bot camera cu.",
        }
    }

    const index = cameraSettings.value.findIndex((camera) => camera.id === targetId)
    if (index < 0) {
        return { ok: false, error: "Khong tim thay slot camera phu hop." }
    }

    const current = cameraSettings.value[index]
    cameraSettings.value[index] = {
        ...current,
        label: payload.label?.trim() || current.label || guessCameraLabel(primaryUrl),
        url: normalizedUrl,
        previewUrl: normalizedPreviewUrl,
        enabled: true,
        online: false,
        location: payload.location?.trim() || current.location,
    }

    persistCameraSettingsOnly()
    await refreshSingleCameraStatus(targetId)

    return {
        ok: true,
        camera: cameraSettings.value[index],
        message: `Da nap ${cameraSettings.value[index].label} vao ${cameraSettings.value[index].name}.`,
    }
}

const applyManualCamera = async () => {
    clearConnectState()
    connectLoading.value = true
    try {
        const result = await applyCameraToNetwork(
            {
                label: manualCameraName.value,
                url: manualCameraUrl.value,
                previewUrl: manualCameraPreviewUrl.value,
            },
            manualTargetId.value
        )

        if (!result.ok) {
            connectError.value = result.error
            return
        }

        manualCameraUrl.value = normalizeCameraUrl(manualCameraUrl.value)
        manualCameraPreviewUrl.value = normalizeCameraUrl(manualCameraPreviewUrl.value)
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
            discoveryError.value = "Chua tim thay camera LAN phu hop trong cung mang."
            return
        }

        discoveryMessage.value = `Tim thay ${discoveredCameras.value.length} thiet bi camera LAN.`
    } catch (error) {
        discoveryError.value = error?.response?.data?.message || error?.message || "Quet camera LAN that bai."
    } finally {
        discoveryLoading.value = false
    }
}

const buildDiscoveredCameraPayload = (camera) => {
    const previewUrl = camera?.previewUrl || camera?.baseUrl || ""
    const rtspUrl = camera?.rtspUrls?.[0] || ""
    const sourceUrl = rtspUrl || previewUrl

    return {
        label: camera.name,
        url: sourceUrl,
        previewUrl,
    }
}

const applyDiscoveredCamera = async (camera) => {
    clearConnectState()
    connectLoading.value = true
    try {
        const payload = buildDiscoveredCameraPayload(camera)
        if (!payload.url && !payload.previewUrl) {
            connectError.value = `Thiet bi ${camera.name} chua co URL phu hop de nap.`
            return
        }

        const result = await applyCameraToNetwork(
            payload,
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
        connectError.value = "Hay quet camera LAN truoc khi nap toan bo."
        return
    }

    connectLoading.value = true
    try {
        const assigned = []
        const skipped = []

        for (const camera of discoveredCameras.value) {
            const payload = buildDiscoveredCameraPayload(camera)
            if (!payload.url && !payload.previewUrl) {
                skipped.push(camera.name || `${camera.ipAddress}:${camera.port}`)
                continue
            }

            const result = await applyCameraToNetwork(
                payload,
                discoveredTargetIds.value[getCameraKey(camera)] || "auto"
            )

            if (!result.ok) {
                skipped.push(camera.name || `${camera.ipAddress}:${camera.port}`)
                continue
            }

            assigned.push(result.camera.name)
        }

        if (!assigned.length) {
            connectError.value = "Khong the nap camera nao vao mang luoi."
            return
        }

        connectMessage.value = `Da nap ${assigned.length} camera vao ${assigned.join(", ")}${
            skipped.length ? `. Bo qua ${skipped.length} thiet bi.` : "."
        }`
    } finally {
        connectLoading.value = false
    }
}

const normalizeCameraCardUrls = async (cameraId) => {
    const camera = cameraSettings.value.find((item) => item.id === cameraId)
    if (!camera) return

    camera.url = normalizeCameraUrl(camera.url)
    camera.previewUrl = normalizeCameraUrl(camera.previewUrl)

    if (!hasCameraSource(camera)) {
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
    if (!hasCameraSource(camera) && camera.enabled) {
        camera.enabled = false
        connectError.value = `Hay nhap it nhat mot URL truoc khi bat ${camera.name}.`
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
        previewUrl: "",
        enabled: false,
        online: false,
    }

    persistCameraSettingsOnly()
    clearConnectState()
    connectMessage.value = `Da xoa cau hinh khoi ${current.name}.`
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
    grid-template-columns: repeat(4, minmax(0, 1fr));
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

.field-hint {
    color: var(--text-muted);
    font-size: 0.78rem;
    line-height: 1.5;
}

.network-actions {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    flex-wrap: wrap;
    grid-column: 1 / -1;
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
    font-family: "JetBrains Mono", monospace;
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
    grid-template-columns: 1fr;
}

.slot-preview {
    display: grid;
    gap: 10px;
}

.slot-preview-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    color: var(--text-secondary);
    font-size: 0.84rem;
}

.mono {
    font-family: "JetBrains Mono", monospace;
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
    .camera-slot-head,
    .slot-preview-head {
        flex-direction: column;
        align-items: stretch;
    }

    .network-actions .btn {
        width: 100%;
    }
}
</style>
