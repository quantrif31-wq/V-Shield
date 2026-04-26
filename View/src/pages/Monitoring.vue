<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Live monitoring</span>
                <h1 class="page-title">Giám sát trực tiếp</h1>
            </div>
            <div class="header-actions">
                <router-link to="/device-management" class="btn btn-primary">Quản lý camera & cổng</router-link>
                <router-link to="/exceptions" class="btn btn-secondary">Xem ngoại lệ</router-link>
            </div>
        </div>

        <section class="metric-grid">
            <article v-if="loadError" class="metric-tile error-card metric-error">
                <span class="metric-label">Kết nối dữ liệu</span>
                <strong class="metric-value">Cần kiểm tra</strong>
                <span class="metric-note">{{ loadError }}</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera đã cấu hình</span>
                <strong class="metric-value">{{ summary.camerasConfigured }}</strong>
                <span class="metric-note">Đọc từ bảng <code>Camera</code> trong hệ thống.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Cổng đang quản lý</span>
                <strong class="metric-value">{{ summary.gatesConfigured }}</strong>
                <span class="metric-note">Số vị trí cổng đang được khai báo.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera có gắn cổng</span>
                <strong class="metric-value">{{ summary.camerasLinkedToGate }}</strong>
                <span class="metric-note">Các camera đã liên kết đúng điểm truy cập.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera chưa gắn cổng</span>
                <strong class="metric-value">{{ summary.unassignedCameras }}</strong>
                <span class="metric-note">Cần kiểm tra lại cấu hình thiết bị.</span>
            </article>
        </section>

        <section class="ops-panel local-preview-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Local camera previews</span>
                    <h2 class="panel-title">Preview từ cấu hình local</h2>
                </div>
                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" @click="loadLocalCameraSettings">Tải lại preview</button>
                    <router-link to="/device-management" class="btn btn-primary btn-sm">Sửa cấu hình</router-link>
                </div>
            </div>

            <div v-if="localPreviewCameras.length" class="local-preview-grid">
                <article v-for="camera in localPreviewCameras" :key="camera.id" class="local-preview-card">
                    <div class="camera-card-head">
                        <div>
                            <strong>{{ camera.label || camera.name }}</strong>
                            <span>{{ camera.location || camera.name }}</span>
                        </div>
                        <span class="soft-chip" :class="getLocalCameraChipClass(camera)">
                            {{ getLocalCameraChipText(camera) }}
                        </span>
                    </div>

                    <StreamPreview :url="resolveCameraPreviewUrl(camera)" :label="camera.label || camera.name" />

                    <div class="chip-row">
                        <span class="soft-chip">{{ camera.name }}</span>
                        <span v-if="camera.url" class="soft-chip" :class="isRtspCameraUrl(camera.url) ? 'warn' : 'success'">
                            {{ isRtspCameraUrl(camera.url) ? 'RTSP source' : 'HTTP source' }}
                        </span>
                        <span v-if="camera.previewUrl" class="soft-chip success">Preview web</span>
                    </div>

                    <div class="source-list">
                        <p v-if="camera.url" class="surface-item-sub mono">
                            AI/source: {{ camera.url }}
                        </p>
                        <p v-if="camera.previewUrl" class="surface-item-sub mono">
                            Preview: {{ camera.previewUrl }}
                        </p>
                        <p v-else class="surface-item-sub">
                            Chưa có Preview URL cho browser. Nếu slot này chỉ có RTSP, web sẽ hiện thông báo thay vì video.
                        </p>
                    </div>
                </article>
            </div>
            <div v-else class="empty-card">
                Chưa có camera local nào được bật trong trình duyệt này. Hãy vào Quản lý camera để thêm RTSP và Preview
                URL.
            </div>
        </section>

        <section class="ops-panel ai-live-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Security AI</span>
                    <h2 class="panel-title">AI An Ninh trực tiếp</h2>
                </div>
                <div class="panel-actions">
                    <span class="soft-chip" :class="securityAiRunning ? 'success' : 'warn'">
                        {{ securityAiRunning ? 'Đang chạy' : 'Đã dừng' }}
                    </span>
                    <button v-if="securityAiRunning" class="btn btn-danger btn-sm" :disabled="securityBusy" @click="handleStopAi">
                        Dừng AI
                    </button>
                    <router-link to="/device-management" class="btn btn-secondary btn-sm">Mở Camera & cổng</router-link>
                </div>
            </div>

            <div v-if="securityError" class="empty-card error-card">
                {{ securityError }}
            </div>

            <div class="ai-live-grid">
                <article class="ai-live-stream-card">
                    <div class="camera-card-head">
                        <div>
                            <strong>Luồng AI hiện tại</strong>
                            <span>{{ securityStatus.source || securityStatus.ip || "Chưa chọn nguồn" }}</span>
                        </div>
                        <span class="soft-chip" :class="securityAiRunning ? 'success' : 'warn'">
                            {{ securityAiRunning ? "Đang chạy" : "Đã dừng" }}
                        </span>
                    </div>

                    <div v-if="securityAiRunning" class="ai-frame-wrap">
                        <img :src="securityFrameUrl" alt="Security AI frame" class="ai-live-frame" />
                    </div>
                    <div v-else class="ai-empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
                        <p>AI An Ninh đang dừng</p>
                        <span>Vào <router-link to="/device-management">Camera & cổng</router-link> để bật nguồn camera</span>
                    </div>
                </article>

                <article class="ai-live-data-card">
                    <div class="chip-row">
                        <span class="soft-chip">Người: {{ securityResult.person_count || 0 }}</span>
                        <span class="soft-chip" :class="(securityResult.abnormal_count || 0) > 0 ? 'warn' : 'success'">
                            Bất thường: {{ securityResult.abnormal_count || 0 }}
                        </span>
                        <span class="soft-chip" :class="(securityResult.danger_count || 0) > 0 ? 'danger' : 'success'">
                            Nguy cơ: {{ securityResult.danger_count || 0 }}
                        </span>
                        <span class="soft-chip">FPS: {{ securityResult.fps || 0 }}</span>
                    </div>

                    <p class="surface-item-sub">
                        {{ securityStatus.status || securityStatus.message || "Đang chờ trạng thái AI..." }}
                    </p>

                    <div v-if="securityActionItems.length" class="chip-row">
                        <span v-for="item in securityActionItems" :key="item.label" class="soft-chip">
                            {{ item.label }}: {{ item.count }}
                        </span>
                    </div>

                    <div v-if="securityPeople.length" class="surface-list scrollable-panel">
                        <article
                            v-for="person in securityPeople"
                            :key="`${person.track_id}-${person.final_action}-${person.confidence}`"
                            class="surface-item"
                        >
                            <div class="camera-card-head">
                                <div>
                                    <strong>ID {{ person.track_id }}</strong>
                                    <span>{{ person.final_action || person.action }}</span>
                                </div>
                                <span class="soft-chip">{{ person.confidence }}</span>
                            </div>
                        </article>
                    </div>
                    <div v-else class="empty-card">Chưa có dữ liệu hành vi mới từ AI.</div>
                </article>
            </div>

            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Security alerts</span>
                    <h3 class="panel-title">Ảnh cảnh báo gần nhất</h3>
                </div>
            </div>

            <div v-if="securityAlerts.length" class="ai-alert-grid">
                <article v-for="alert in securityAlerts" :key="alert.fileName" class="ai-alert-card">
                    <img v-if="alert.imageUrl" :src="resolveSecurityAlertUrl(alert.imageUrl)" :alt="alert.label || 'Alert'" class="ai-alert-image" />
                    <div class="ai-alert-meta">
                        <strong>{{ alert.label || "ALERT" }}</strong>
                        <span>{{ alert.trackId !== null && alert.trackId !== undefined ? `ID ${alert.trackId}` : "N/A" }}</span>
                        <span>{{ formatDateTime(alert.capturedAt) }}</span>
                    </div>
                </article>
            </div>
            <div v-else class="empty-card">
                Chưa có ảnh cảnh báo mới.
            </div>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Configured cameras</span>
                        <h2 class="panel-title">Camera & điểm đặt</h2>
                    </div>
                    <router-link to="/device-management" class="btn btn-secondary btn-sm">Mở cấu hình</router-link>
                </div>

                <div v-if="cameras.length" class="camera-grid scrollable-panel">
                    <article v-for="camera in displayedCameras" :key="camera.cameraId" class="camera-card">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ camera.cameraName }}</strong>
                                <span>{{ camera.gateName || "Chưa gắn cổng" }}</span>
                            </div>
                            <span class="soft-chip" :class="camera.gateId ? 'success' : 'warn'">
                                {{ camera.cameraType || "Không rõ loại" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ camera.accessLogCount }} log</span>
                            <span v-if="camera.latestPlate" class="soft-chip success">{{ camera.latestPlate }}</span>
                            <span v-else class="soft-chip warn">Chưa có biển số</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ camera.gateLocation || "Chưa có vị trí cổng" }}
                            <template v-if="camera.lastAccessAt">
                                - hoạt động gần nhất {{ formatDateTime(camera.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                    <div v-if="cameras.length > maxCameras" class="show-more-hint">
                        Hiển thị {{ maxCameras }}/{{ cameras.length }} camera. Vào
                        <router-link to="/device-management">Quản lý thiết bị</router-link> để xem tất cả.
                    </div>
                </div>
                <div v-else class="empty-card">Chưa có camera nào trong cơ sở dữ liệu.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Plate recognition</span>
                        <h2 class="panel-title">Biển số nhận diện gần nhất</h2>
                    </div>
                </div>

                <div v-if="recentPlates.length" class="surface-list scrollable-panel">
                    <article v-for="plate in displayedPlates" :key="`${plate.cameraIP}-${plate.plateNumber}-${plate.lastUpdate}`" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ plate.plateNumber }}</strong>
                                <span>{{ plate.cameraIP }}</span>
                            </div>
                            <span class="soft-chip success">{{ formatTime(plate.lastUpdate) }}</span>
                        </div>
                        <p class="surface-item-sub">
                            Bản ghi biển số mới nhất từ camera, dùng để đối soát nhanh với dòng ra vào.
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có dữ liệu nhận diện biển số gần đây.</div>
            </article>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Face & access</span>
                        <h2 class="panel-title">Dòng xác minh khuôn mặt gần nhất</h2>
                    </div>
                    <router-link to="/access-logs" class="btn btn-secondary btn-sm">Mở nhật ký</router-link>
                </div>

                <div v-if="recentActivities.length" class="surface-list scrollable-panel">
                    <article v-for="activity in displayedActivities" :key="activity.logId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ activity.actorName }}</strong>
                                <span>{{ activity.gateName || "Chưa gắn cổng" }}</span>
                            </div>
                            <span class="soft-chip" :class="activity.direction === 'IN' ? 'success' : 'warn'">
                                {{ activity.direction === "IN" ? "Vào" : "Ra" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span v-if="activity.capturedLicensePlate" class="soft-chip">{{ activity.capturedLicensePlate }}</span>
                            <span v-if="activity.resultStatus" class="soft-chip">{{ activity.resultStatus }}</span>
                            <span v-if="activity.isBypass" class="soft-chip danger">BYPASS</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ activity.cameraName || "Không có camera" }} - {{ formatDateTime(activity.timestamp) }}
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có log nhận diện nào gần đây.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Gate posture</span>
                        <h2 class="panel-title">Tình trạng cổng truy cập</h2>
                    </div>
                </div>

                <div v-if="gates.length" class="surface-list scrollable-panel">
                    <article v-for="gate in displayedGates" :key="gate.gateId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ gate.gateName }}</strong>
                                <span>{{ gate.location || "Chưa có vị trí" }}</span>
                            </div>
                            <span class="soft-chip">{{ gate.cameraCount }} camera</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ gate.accessLogCount }} log liên quan
                            <template v-if="gate.lastAccessAt">
                                - gần nhất {{ formatDateTime(gate.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa khai báo cổng nào trong hệ thống.</div>
            </article>
        </section>
    </div>
</template>

<script setup>
import { computed, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref } from "vue"
import StreamPreview from "../components/StreamPreview.vue"
import { getAccessLogs } from "../services/accessLogApi"
import { getDeviceOverview } from "../services/deviceManagementApi"
import { getDetectedPlates } from "../services/plateRecognitionApi"
import {
    getSecurityAiAlerts,
    getSecurityAiFrameUrl,
    getSecurityAiResult,
    getSecurityAiStatus,
    stopSecurityAi,
} from "../services/securityAiApi"
import { getResolvedLocalApiBaseUrl } from "../services/localApiClient"
import {
    CAMERA_NETWORK_STORAGE_KEY,
    isRtspCameraUrl,
    loadCameraNetworkSettings,
    resolveCameraPreviewUrl,
} from "../utils/cameraNetwork"

const maxCameras = 6
const maxPlates = 6
const maxActivities = 8
const maxGates = 6

const loadError = ref('')
const summary = ref({
    camerasConfigured: 0,
    gatesConfigured: 0,
    camerasLinkedToGate: 0,
    unassignedCameras: 0,
})
const cameras = ref([])
const gates = ref([])
const recentPlates = ref([])
const recentActivities = ref([])
const localCameraSettings = ref([])
const securityStatus = ref({})
const securityResult = ref({})
const securityAlerts = ref([])
const securityError = ref('')
const securityFrameTick = ref(Date.now())
const securityBusy = ref(false)
let securityPollTimer = null
let securityFrameTimer = null
let securityPollInFlight = false
let securityResultFailureCount = 0
let securityResultBackoffUntil = 0

const displayedCameras = computed(() => cameras.value.slice(0, maxCameras))
const displayedPlates = computed(() => recentPlates.value.slice(0, maxPlates))
const displayedActivities = computed(() => recentActivities.value.slice(0, maxActivities))
const displayedGates = computed(() => gates.value.slice(0, maxGates))
const localPreviewCameras = computed(() =>
    localCameraSettings.value.filter((camera) => camera.enabled && (camera.url || camera.previewUrl))
)
const securityAiRunning = computed(() =>
    Boolean(securityStatus.value?.running ?? securityStatus.value?.camera_enabled)
)
const securityFrameUrl = computed(() => getSecurityAiFrameUrl(securityFrameTick.value))
const securityPeople = computed(() => (securityResult.value?.people || []).slice(0, 8))
const securityActionItems = computed(() =>
    Object.entries(securityResult.value?.actions || {})
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => Number(b.count) - Number(a.count))
)

const formatDateTime = (value) => {
    if (!value) return "--"
    return new Date(value).toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
    })
}

const formatTime = (value) => {
    if (!value) return "--"
    return new Date(value).toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
    })
}

const resolveSecurityAlertUrl = (rawUrl) => {
    const value = String(rawUrl || '').trim()
    if (!value) return ''
    if (value.startsWith('http://') || value.startsWith('https://')) {
        return value
    }

    const base = getResolvedLocalApiBaseUrl().replace(/\/+$/, '')
    if (value.startsWith('/api/')) {
        const originBase = base.endsWith('/api') ? base.slice(0, -4) : base
        return `${originBase}${value}`
    }

    const normalizedPath = value.startsWith('/') ? value : `/${value}`
    return `${base}${normalizedPath}`
}

const getLocalCameraChipText = (camera) => {
    if (camera.previewUrl && camera.url && isRtspCameraUrl(camera.url)) return "RTSP + preview"
    if (camera.url && isRtspCameraUrl(camera.url)) return "RTSP cho AI"
    return camera.online ? "Preview online" : "Preview chưa xác nhận"
}

const getLocalCameraChipClass = (camera) => {
    if (camera.previewUrl) return camera.online ? "success" : "warn"
    if (camera.url && isRtspCameraUrl(camera.url)) return "warn"
    return camera.online ? "success" : "warn"
}

const loadLocalCameraSettings = () => {
    localCameraSettings.value = loadCameraNetworkSettings()
}

const loadMonitoring = async () => {
    loadError.value = ''
    try {
        const [overviewRes, platesRes, activitiesRes] = await Promise.all([
            getDeviceOverview(),
            getDetectedPlates(),
            getAccessLogs({ page: 1, pageSize: 6 }),
        ])

        summary.value = { ...summary.value, ...(overviewRes.data.summary || {}) }
        cameras.value = overviewRes.data.cameras || []
        gates.value = overviewRes.data.gates || []
        recentPlates.value = (platesRes.data || []).slice(0, 6)
        recentActivities.value = activitiesRes.data.items || []
    } catch (error) {
        console.error('Monitoring load error:', error)
        loadError.value = error.response?.data?.message || 'Không thể tải dữ liệu giám sát. Hãy kiểm tra API backend và cổng kết nối.'
    }
}

const normalizeSecurityStatus = (payload) => payload?.status || payload || {}

const markSecurityResultFetchSuccess = () => {
    securityResultFailureCount = 0
    securityResultBackoffUntil = 0
}

const markSecurityResultFetchFailure = () => {
    securityResultFailureCount = Math.min(6, securityResultFailureCount + 1)
    const delayMs = Math.min(30000, 2000 * (2 ** (securityResultFailureCount - 1)))
    securityResultBackoffUntil = Date.now() + delayMs
}

const loadSecurityMonitoring = async ({ silent = false } = {}) => {
    if (securityPollInFlight) return

    securityPollInFlight = true
    try {
        const statusPayload = await getSecurityAiStatus()
        const normalizedStatus = normalizeSecurityStatus(statusPayload)
        const isRunning = Boolean(normalizedStatus?.running ?? normalizedStatus?.camera_enabled)
        const serviceReachable = normalizedStatus?.serviceReachable !== false
        const canRequestResult = isRunning &&
            serviceReachable &&
            Date.now() >= securityResultBackoffUntil

        securityStatus.value = normalizedStatus

        try {
            const alertsPayload = await getSecurityAiAlerts({ take: 8 })
            securityAlerts.value = alertsPayload?.items || []
        } catch {
            securityAlerts.value = []
        }

        if (canRequestResult) {
            try {
                const resultPayload = await getSecurityAiResult()
                securityResult.value = resultPayload || {}
                markSecurityResultFetchSuccess()
            } catch {
                // Keep UI stable and avoid repeated /result failures.
                markSecurityResultFetchFailure()
            }
        } else {
            if (!isRunning || !serviceReachable) {
                securityResult.value = {}
            }
            if (!isRunning) {
                markSecurityResultFetchSuccess()
            }
        }

        securityError.value = ''
    } catch (error) {
        securityStatus.value = {}
        securityResult.value = {}
        securityAlerts.value = []
        if (!silent) {
            console.error('Security AI load error:', error)
            securityError.value = error?.message || 'Khong tai duoc du lieu AI An Ninh.'
        }
    } finally {
        securityPollInFlight = false
    }
}

const handleStopAi = async () => {
    securityBusy.value = true
    try {
        await stopSecurityAi()
        await loadSecurityMonitoring()
    } catch (error) {
        console.error('Stop AI error:', error)
        securityError.value = error?.message || 'Không dừng được AI An Ninh.'
    } finally {
        securityBusy.value = false
    }
}

const handleStorageChange = (event) => {
    if (!event.key || event.key === CAMERA_NETWORK_STORAGE_KEY) {
        loadLocalCameraSettings()
    }
}

const stopSecurityRealtime = () => {
    if (securityPollTimer) {
        window.clearInterval(securityPollTimer)
        securityPollTimer = null
    }
    if (securityFrameTimer) {
        window.clearInterval(securityFrameTimer)
        securityFrameTimer = null
    }
}

const startSecurityRealtime = async () => {
    await loadSecurityMonitoring({ silent: true })
    if (!securityPollTimer) {
        securityPollTimer = window.setInterval(() => {
            void loadSecurityMonitoring({ silent: true })
        }, 2500)
    }
    if (!securityFrameTimer) {
        securityFrameTimer = window.setInterval(() => {
            if (securityAiRunning.value) {
                securityFrameTick.value = Date.now()
            }
        }, 800)
    }
}

onMounted(async () => {
    loadLocalCameraSettings()
    window.addEventListener("storage", handleStorageChange)
    await loadMonitoring()
    await startSecurityRealtime()
})

onActivated(() => {
    void startSecurityRealtime()
})

onDeactivated(() => {
    stopSecurityRealtime()
})

onBeforeUnmount(() => {
    window.removeEventListener("storage", handleStorageChange)
    stopSecurityRealtime()
})
</script>

<style scoped>
.local-preview-panel {
    display: grid;
    gap: 18px;
}

.local-preview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
}

.local-preview-card {
    display: grid;
    gap: 14px;
    padding: 18px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.camera-grid {
    display: grid;
    gap: 12px;
}

.camera-card,
.camera-card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
}

.camera-card {
    padding: 16px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
    flex-direction: column;
}

.camera-card-head strong {
    display: block;
    color: var(--text-primary);
    font-size: 0.94rem;
}

.camera-card-head span {
    display: block;
    margin-top: 5px;
    color: var(--text-muted);
    font-size: 0.8rem;
}

.metric-error {
    grid-column: 1 / -1;
}

.error-card {
    border: 1px solid rgba(195, 81, 70, 0.24);
    background: rgba(255, 239, 236, 0.9);
}

.error-card .metric-label,
.error-card .metric-value,
.error-card .metric-note {
    color: var(--accent-danger);
}

.ai-live-panel {
    display: grid;
    gap: 16px;
    margin-bottom: 20px;
}

.ai-live-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: minmax(0, 1.35fr) minmax(300px, 1fr);
}

.ai-live-stream-card,
.ai-live-data-card {
    display: grid;
    gap: 12px;
    padding: 16px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.ai-frame-wrap {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(24, 49, 77, 0.1);
    min-height: 280px;
    background: rgba(17, 30, 45, 0.9);
}

.ai-live-frame {
    width: 100%;
    height: 100%;
    min-height: 280px;
    object-fit: cover;
    display: block;
}

.ai-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-height: 280px;
    padding: 24px;
    border-radius: 14px;
    background: radial-gradient(circle at top left, rgba(31, 94, 143, 0.18), transparent 48%),
                linear-gradient(140deg, #0f172a, #12263f 60%, #17324d);
    border: 1px solid rgba(255, 255, 255, 0.06);
    text-align: center;
}

.ai-empty-state svg {
    color: rgba(191, 209, 229, 0.4);
}

.ai-empty-state p {
    font-size: 0.94rem;
    font-weight: 600;
    color: rgba(226, 232, 240, 0.88);
    margin: 0;
}

.ai-empty-state span {
    font-size: 0.82rem;
    color: rgba(191, 209, 229, 0.64);
}

.ai-empty-state a {
    color: #60a5fa;
    text-decoration: none;
}

.ai-empty-state a:hover {
    text-decoration: underline;
}

.ai-alert-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}

.ai-alert-card {
    display: grid;
    gap: 8px;
    padding: 10px;
    border-radius: 14px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.ai-alert-image {
    width: 100%;
    height: 120px;
    object-fit: cover;
    border-radius: 10px;
    background: rgba(17, 30, 45, 0.9);
}

.ai-alert-meta {
    display: grid;
    gap: 4px;
}

.ai-alert-meta strong {
    font-size: 0.84rem;
}

.ai-alert-meta span {
    font-size: 0.78rem;
    color: var(--text-muted);
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }

    .ai-live-grid {
        grid-template-columns: 1fr;
    }

    .ai-alert-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>

