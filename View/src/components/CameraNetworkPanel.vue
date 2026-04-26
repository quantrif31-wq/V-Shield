<template>
    <section class="ops-panel network-panel">
        <div class="panel-head">
            <div>
                <span class="panel-kicker">Camera connections</span>
                <h2 class="panel-title">Kết nối camera quản trị vào slot giám sát</h2>
                <p class="panel-copy">
                    Link stream được quản trị ở trang <code>Quản trị Camera</code>. Tại đây chỉ cần chọn camera đã cấu
                    hình để gán vào từng slot theo đúng kiểu combobox tìm kiếm như điều phối thông hành.
                </p>
            </div>
            <div class="panel-actions">
                <button class="btn btn-secondary btn-sm" :disabled="managedCameraLoading" @click="reloadManagedCameras">
                    {{ managedCameraLoading ? "Đang tải camera..." : "Tải lại camera" }}
                </button>
                <button class="btn btn-secondary btn-sm" :disabled="isRefreshingAll" @click="refreshAllCameraStatuses">
                    {{ isRefreshingAll ? "Đang kiểm tra..." : "Kiểm tra tất cả" }}
                </button>
                <router-link to="/setcam" class="btn btn-primary btn-sm">Quản trị Camera</router-link>
            </div>
        </div>

        <div class="network-summary">
            <div class="network-stat">
                <span>Slot có nguồn</span>
                <strong>{{ localSummary.connected }}</strong>
            </div>
            <div class="network-stat">
                <span>Đang bật</span>
                <strong>{{ localSummary.enabled }}</strong>
            </div>
            <div class="network-stat">
                <span>Preview online</span>
                <strong>{{ localSummary.online }}</strong>
            </div>
        </div>

        <p class="network-note">
            Sau khi admin thêm camera và link ở trang <code>Quản trị Camera</code>, danh sách camera sẽ hiện ở đây để
            chọn theo tên, cổng hoặc ID. Hai ô nhập link trực tiếp đã được bỏ khỏi mục này.
        </p>

        <div v-if="managedCameraError || connectMessage || connectError" class="network-messages">
            <p v-if="managedCameraError" class="message danger">{{ managedCameraError }}</p>
            <p v-if="connectMessage" class="message success">{{ connectMessage }}</p>
            <p v-if="connectError" class="message danger">{{ connectError }}</p>
        </div>

        <div v-if="!managedCameraLoading && !managedCameras.length" class="empty-card">
            Chưa có camera nào có stream/preview trong Quản trị Camera. Hãy vào <router-link to="/setcam">Quản trị Camera</router-link>
            để thêm link trước.
        </div>

        <div class="camera-slot-grid">
            <article v-for="camera in cameraSettings" :key="camera.id" class="camera-slot-card">
                <div class="camera-slot-head">
                    <div>
                        <h3>{{ camera.name }}</h3>
                        <p>{{ camera.label || "Chưa đặt tên hiển thị" }}</p>
                    </div>
                    <label class="toggle">
                        <input v-model="camera.enabled" type="checkbox" @change="handleCameraToggle(camera)" />
                        <span></span>
                    </label>
                </div>

                <div class="chip-row">
                    <span class="soft-chip status-chip" :class="getCameraStatusClass(camera)">{{ getCameraStatusText(camera) }}</span>
                    <span v-if="camera.linkedCameraId" class="soft-chip info-chip">
                        {{ camera.linkedCameraName || `Camera #${camera.linkedCameraId}` }}
                    </span>
                    <span v-if="camera.previewUrl" class="soft-chip success">Preview web</span>
                    <span v-else-if="camera.url && isRtspCameraUrl(camera.url)" class="soft-chip warn">Cần gateway web</span>
                </div>

                <div class="slot-form">
                    <label class="network-field">
                        <span class="field-label">Camera kết nối</span>
                        <div class="camera-search-box" :ref="(el) => setCameraSearchRef(camera.id, el)">
                            <input
                                v-model="slotSearch[getSlotSearchKey(camera.id)]"
                                class="filter-select camera-search-input"
                                type="text"
                                placeholder="Tìm camera theo tên, cổng hoặc ID..."
                                @focus="openCameraDropdown(camera.id)"
                                @input="handleCameraSearchInput(camera)"
                                @keydown.esc="closeCameraDropdown(camera.id)"
                            />
                            <button
                                v-if="slotSearch[getSlotSearchKey(camera.id)]"
                                type="button"
                                class="camera-search-clear"
                                title="Xóa chọn camera"
                                @click="clearCameraSelectionFromSearch(camera)"
                            >
                                ×
                            </button>
                            <span class="camera-search-caret" :class="{ open: isCameraDropdownOpen(camera.id) }">⌄</span>

                            <div v-if="isCameraDropdownOpen(camera.id)" class="camera-dropdown">
                                <div v-if="managedCameraLoading" class="camera-dropdown-empty">Đang tải camera...</div>
                                <div v-else-if="!filterManagedCameras(slotSearch[getSlotSearchKey(camera.id)]).length" class="camera-dropdown-empty">
                                    Không tìm thấy camera phù hợp
                                </div>
                                <button
                                    v-for="managedCamera in filterManagedCameras(slotSearch[getSlotSearchKey(camera.id)])"
                                    :key="managedCamera.id"
                                    type="button"
                                    class="camera-dropdown-item"
                                    :class="{ selected: String(managedCamera.id) === String(camera.linkedCameraId || '') }"
                                    @click="selectManagedCameraForSlot(managedCamera, camera)"
                                >
                                    <div class="camera-dropdown-title">
                                        <span>{{ managedCamera.name }}</span>
                                        <span class="camera-dropdown-id">#{{ managedCamera.id }}</span>
                                    </div>
                                    <div class="camera-dropdown-meta">
                                        {{ buildManagedCameraMeta(managedCamera) }}
                                    </div>
                                </button>
                            </div>
                        </div>
                        <span class="field-hint">
                            Chọn camera đã được thêm link ở trang Quản trị Camera. Danh sách có hỗ trợ tìm kiếm.
                        </span>
                    </label>

                    <label class="network-field">
                        <span class="field-label">Tên hiển thị trên giám sát</span>
                        <input
                            v-model="camera.label"
                            class="filter-select"
                            type="text"
                            placeholder="Ví dụ: Camera cổng trước"
                            @blur="persistCameraSettingsOnly"
                        />
                    </label>

                    <div v-if="camera.linkedCameraId" class="linked-meta-grid">
                        <div class="linked-meta-card">
                            <span class="linked-meta-label">Nguồn AI / backend</span>
                            <strong class="linked-meta-value" :title="camera.url || 'Chưa có nguồn stream'">
                                {{ truncateUrl(camera.url) || "Chưa có nguồn stream" }}
                            </strong>
                        </div>
                        <div class="linked-meta-card">
                            <span class="linked-meta-label">Preview trên web</span>
                            <strong class="linked-meta-value" :title="camera.previewUrl || 'Chưa có preview web'">
                                {{ truncateUrl(camera.previewUrl) || "Chưa có preview web" }}
                            </strong>
                        </div>
                    </div>

                    <div class="slot-meta-grid">
                        <label class="network-field">
                            <span class="field-label">Vị trí lắp đặt</span>
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
                        <strong>Preview trên web</strong>
                        <span>{{ camera.previewUrl ? "Đang dùng Preview URL" : "Đang dùng nguồn hiện có" }}</span>
                    </div>
                    <StreamPreview :url="resolveCameraPreviewUrl(camera)" :label="camera.label || camera.name" />
                </div>

                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" :disabled="checkingIds.includes(camera.id)" @click="refreshSingleCameraStatus(camera.id)">
                        {{ checkingIds.includes(camera.id) ? "Đang kiểm tra..." : "Kiểm tra lại" }}
                    </button>
                    <button class="btn btn-danger btn-sm" @click="clearCamera(camera.id)">Xóa camera</button>
                </div>
            </article>
        </div>
    </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import StreamPreview from "./StreamPreview.vue"
import { fetchSetCamCatalog } from "../services/setcamCatalog"
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

const CAMERA_PROBE_TIMEOUT_MS = 3500

const cameraSettings = ref(createDefaultCameraSettings())
const managedCameras = ref([])
const managedCameraLoading = ref(false)
const managedCameraError = ref("")
const connectMessage = ref("")
const connectError = ref("")
const checkingIds = ref([])
const isRefreshingAll = ref(false)
const slotSearch = ref({})
const cameraSearchRefs = ref({})
const openCameraDropdownKey = ref("")

const hasCameraSource = (camera) => Boolean(camera?.url?.trim() || camera?.previewUrl?.trim())

const normalizeKeywordText = (value = "") =>
    String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()

const localSummary = computed(() => {
    const connected = cameraSettings.value.filter((camera) => hasCameraSource(camera)).length
    const enabled = cameraSettings.value.filter((camera) => hasCameraSource(camera) && camera.enabled).length
    const online = cameraSettings.value.filter((camera) => hasCameraSource(camera) && camera.enabled && camera.online).length

    return { connected, enabled, online }
})

const getSlotSearchKey = (cameraId) => `slot-${cameraId}`

const buildManagedCameraSearchLabel = (camera) => {
    const cameraId = camera?.id ?? ""
    const cameraName = String(camera?.name || camera?.cameraName || "Camera").trim()
    return cameraId ? `${cameraName} (ID: ${cameraId})` : cameraName
}

const buildManagedCameraMeta = (camera) => {
    const parts = [camera?.gateName, camera?.cameraType].filter(Boolean)
    if (!parts.length) {
        return camera?.browserPreviewUrl ? "Có preview web" : "Có stream AI/backend"
    }

    return parts.join(" · ")
}

const truncateUrl = (value, maxLength = 62) => {
    const text = String(value || "").trim()
    if (!text) return ""
    return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text
}

const getLinkedManagedCamera = (slotCamera) =>
    managedCameras.value.find((camera) => String(camera.id) === String(slotCamera.linkedCameraId || ""))

const primeSlotSearchLabels = () => {
    const nextSearch = {}

    for (const camera of cameraSettings.value) {
        const searchKey = getSlotSearchKey(camera.id)
        const linkedManagedCamera = getLinkedManagedCamera(camera)
        if (linkedManagedCamera) {
            nextSearch[searchKey] = buildManagedCameraSearchLabel(linkedManagedCamera)
            continue
        }

        if (camera.linkedCameraId || camera.linkedCameraName) {
            nextSearch[searchKey] = buildManagedCameraSearchLabel({
                id: camera.linkedCameraId,
                name: camera.linkedCameraName,
            })
            continue
        }

        nextSearch[searchKey] = ""
    }

    slotSearch.value = nextSearch
}

const loadCameraSettings = () => {
    cameraSettings.value = loadCameraNetworkSettings()
    primeSlotSearchLabels()
}

const persistCameraSettingsOnly = () => {
    cameraSettings.value = saveCameraNetworkSettings(cameraSettings.value)
}

const clearStatusMessages = () => {
    connectMessage.value = ""
    connectError.value = ""
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
    if (!hasCameraSource(camera)) return "Chưa gắn"
    if (!camera.enabled) return "Đã tắt"
    if (checkingIds.value.includes(camera.id)) return "Đang kiểm tra"
    if (camera.url && isRtspCameraUrl(camera.url) && camera.previewUrl) return "RTSP + preview"
    if (camera.url && isRtspCameraUrl(camera.url)) return "RTSP cho AI"
    return camera.online ? "Trực tuyến" : "Ngoại tuyến"
}

const getCameraStatusClass = (camera) => {
    if (!hasCameraSource(camera) || !camera.enabled) return "warn"
    if (checkingIds.value.includes(camera.id)) return ""
    if (camera.url && isRtspCameraUrl(camera.url) && !camera.previewUrl) return ""
    return camera.online ? "success" : "danger"
}

const setCameraSearchRef = (cameraId, el) => {
    const key = getSlotSearchKey(cameraId)

    if (el) {
        cameraSearchRefs.value[key] = el
        return
    }

    delete cameraSearchRefs.value[key]
}

const openCameraDropdown = (cameraId) => {
    openCameraDropdownKey.value = getSlotSearchKey(cameraId)
}

const closeCameraDropdown = (cameraId) => {
    const key = getSlotSearchKey(cameraId)
    if (openCameraDropdownKey.value === key) {
        openCameraDropdownKey.value = ""
    }
}

const isCameraDropdownOpen = (cameraId) => openCameraDropdownKey.value === getSlotSearchKey(cameraId)

const filterManagedCameras = (keyword) => {
    const normalizedKeyword = normalizeKeywordText(keyword).trim()
    if (!normalizedKeyword) {
        return managedCameras.value
    }

    return managedCameras.value.filter((camera) => {
        const haystack = normalizeKeywordText([camera.name, camera.gateName, camera.cameraType, camera.id].join(" "))
        return haystack.includes(normalizedKeyword)
    })
}

const handleDocumentPointerDown = (event) => {
    const currentKey = openCameraDropdownKey.value
    if (!currentKey) return

    const searchBox = cameraSearchRefs.value[currentKey]
    if (searchBox?.contains?.(event.target)) return

    openCameraDropdownKey.value = ""
}

const syncSelectedManagedCameras = () => {
    let hasChanges = false

    for (const slotCamera of cameraSettings.value) {
        const linkedManagedCamera = getLinkedManagedCamera(slotCamera)
        if (!linkedManagedCamera) {
            continue
        }

        const nextSourceUrl = normalizeCameraUrl(linkedManagedCamera.sourceUrl || "")
        const nextPreviewUrl = normalizeCameraUrl(linkedManagedCamera.browserPreviewUrl || "")

        if (
            String(slotCamera.linkedCameraId || "") !== String(linkedManagedCamera.id) ||
            slotCamera.linkedCameraName !== linkedManagedCamera.name ||
            slotCamera.url !== nextSourceUrl ||
            slotCamera.previewUrl !== nextPreviewUrl
        ) {
            slotCamera.linkedCameraId = String(linkedManagedCamera.id)
            slotCamera.linkedCameraName = linkedManagedCamera.name
            slotCamera.url = nextSourceUrl
            slotCamera.previewUrl = nextPreviewUrl
            hasChanges = true
        }

        if (!slotCamera.location?.trim() && linkedManagedCamera.gateName) {
            slotCamera.location = linkedManagedCamera.gateName
            hasChanges = true
        }
    }

    if (hasChanges) {
        persistCameraSettingsOnly()
    }

    primeSlotSearchLabels()
}

const reloadManagedCameras = async () => {
    managedCameraLoading.value = true
    managedCameraError.value = ""

    try {
        managedCameras.value = await fetchSetCamCatalog()
        syncSelectedManagedCameras()
    } catch (error) {
        console.error("Load managed cameras error:", error)
        managedCameras.value = []
        managedCameraError.value =
            error?.response?.data?.message || error?.message || "Không tải được danh sách camera quản trị."
    } finally {
        managedCameraLoading.value = false
    }
}

const selectManagedCameraForSlot = async (managedCamera, slotCamera) => {
    clearStatusMessages()

    const sourceUrl = normalizeCameraUrl(managedCamera.sourceUrl || "")
    const previewUrl = normalizeCameraUrl(managedCamera.browserPreviewUrl || "")

    if (!sourceUrl && !previewUrl) {
        connectError.value = "Camera chưa có URL stream hoặc preview hợp lệ."
        return
    }

    const previousLinkedName = String(slotCamera.linkedCameraName || "").trim()
    const shouldApplyCameraNameToLabel = !slotCamera.label?.trim() || slotCamera.label === previousLinkedName

    slotCamera.linkedCameraId = String(managedCamera.id)
    slotCamera.linkedCameraName = managedCamera.name
    slotCamera.url = sourceUrl
    slotCamera.previewUrl = previewUrl
    slotCamera.enabled = true
    slotCamera.online = false

    if (shouldApplyCameraNameToLabel) {
        slotCamera.label = managedCamera.name
    }

    if (!slotCamera.location?.trim() && managedCamera.gateName) {
        slotCamera.location = managedCamera.gateName
    }

    slotSearch.value[getSlotSearchKey(slotCamera.id)] = buildManagedCameraSearchLabel(managedCamera)
    persistCameraSettingsOnly()
    closeCameraDropdown(slotCamera.id)

    connectMessage.value = `Đã kết nối ${managedCamera.name} vào ${slotCamera.name}.`
    await refreshSingleCameraStatus(slotCamera.id)
}

const clearCamera = (cameraId, options = {}) => {
    const { preserveMessage = false } = options
    const index = cameraSettings.value.findIndex((camera) => camera.id === cameraId)
    if (index < 0) return

    const current = cameraSettings.value[index]
    cameraSettings.value[index] = {
        ...current,
        linkedCameraId: "",
        linkedCameraName: "",
        url: "",
        previewUrl: "",
        enabled: false,
        online: false,
    }

    slotSearch.value[getSlotSearchKey(cameraId)] = ""
    persistCameraSettingsOnly()
    closeCameraDropdown(cameraId)

    if (!preserveMessage) {
        clearStatusMessages()
        connectMessage.value = `Đã xóa cấu hình khỏi ${current.name}.`
    }
}

const clearCameraSelectionFromSearch = (slotCamera) => {
    clearCamera(slotCamera.id, { preserveMessage: true })
    clearStatusMessages()
    openCameraDropdown(slotCamera.id)
}

const handleCameraSearchInput = (slotCamera) => {
    clearStatusMessages()
    openCameraDropdown(slotCamera.id)

    const value = slotSearch.value[getSlotSearchKey(slotCamera.id)] || ""
    if (!value.trim() && (slotCamera.linkedCameraId || slotCamera.linkedCameraName)) {
        clearCamera(slotCamera.id, { preserveMessage: true })
    }
}

const handleCameraToggle = async (camera) => {
    clearStatusMessages()
    if (!hasCameraSource(camera) && camera.enabled) {
        camera.enabled = false
        connectError.value = `Hãy chọn camera kết nối trước khi bật ${camera.name}.`
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

onMounted(async () => {
    loadCameraSettings()
    await reloadManagedCameras()
    await refreshAllCameraStatuses()
    document.addEventListener("pointerdown", handleDocumentPointerDown)
})

onBeforeUnmount(() => {
    document.removeEventListener("pointerdown", handleDocumentPointerDown)
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

.status-chip {
    padding: 4px 9px;
    font-size: 0.8rem;
    font-weight: 600;
}

.info-chip {
    background: rgba(37, 99, 235, 0.12);
    color: #1d4ed8;
}

.camera-slot-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
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

.camera-slot-head p {
    color: var(--text-muted);
}

.slot-form,
.slot-meta-grid {
    display: grid;
    gap: 14px;
}

.slot-meta-grid {
    grid-template-columns: 1fr;
}

.linked-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.linked-meta-card {
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(255, 255, 255, 0.6);
    display: grid;
    gap: 6px;
}

.linked-meta-label {
    color: var(--text-muted);
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.linked-meta-value {
    color: var(--text-primary);
    font-size: 0.82rem;
    font-family: "JetBrains Mono", monospace;
    word-break: break-all;
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

.camera-search-box {
    position: relative;
}

.camera-search-input {
    padding-right: 64px;
}

.camera-search-clear {
    position: absolute;
    top: 50%;
    right: 34px;
    transform: translateY(-50%);
    width: 22px;
    height: 22px;
    border: none;
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.18);
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.9rem;
    line-height: 1;
}

.camera-search-clear:hover {
    background: rgba(195, 81, 70, 0.12);
    color: var(--accent-danger);
}

.camera-search-caret {
    position: absolute;
    top: 50%;
    right: 12px;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
    transition: transform 0.2s ease;
}

.camera-search-caret.open {
    transform: translateY(-50%) rotate(180deg);
}

.camera-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    max-height: 260px;
    overflow-y: auto;
    border-radius: 16px;
    border: 1px solid rgba(24, 49, 77, 0.12);
    background: rgba(255, 255, 255, 0.98);
    box-shadow: var(--shadow-lg);
    z-index: 40;
    padding: 6px;
}

.camera-dropdown-item {
    width: 100%;
    border: none;
    background: transparent;
    text-align: left;
    padding: 10px 12px;
    border-radius: 12px;
    cursor: pointer;
    display: grid;
    gap: 4px;
    transition: background-color 0.16s ease, color 0.16s ease;
}

.camera-dropdown-item:hover,
.camera-dropdown-item.selected {
    background: rgba(37, 99, 235, 0.08);
}

.camera-dropdown-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    color: var(--text-primary);
    font-size: 0.92rem;
    font-weight: 700;
}

.camera-dropdown-id {
    color: var(--accent-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 0.78rem;
}

.camera-dropdown-meta {
    color: var(--text-muted);
    font-size: 0.78rem;
}

.camera-dropdown-empty {
    padding: 14px;
    color: var(--text-muted);
    font-size: 0.84rem;
    text-align: center;
}

@media (max-width: 1180px) {
    .camera-slot-grid,
    .linked-meta-grid {
        grid-template-columns: 1fr;
    }

    .network-summary {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .camera-slot-head,
    .slot-preview-head {
        flex-direction: column;
        align-items: stretch;
    }

    .panel-actions .btn {
        width: 100%;
    }
}
</style>
